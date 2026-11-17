"""CPU-only head-ownership and synthetic parameter-coupling audit.

This worker does not run real data through either model and does not mutate a
checkpoint.  It verifies actual module/parameter identity, then tests whether
parameter tying induces a second-layer coupling term in a synthetic margin
derivative.  The synthetic result is an implementation check, not evidence for
a real training failure or a novel mechanism.
"""
import argparse
import copy
import gc
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

BUFFER_KEYS = {
    "text_encoder.embeddings.position_ids",
    "text_encoder.embeddings.token_type_ids",
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tensor_pointer(tensor):
    return int(tensor.untyped_storage().data_ptr()) if tensor.numel() else 0


def head_records(model):
    layers = list(model.dec.decoder_layers)
    records = []
    for layer_index, layer in enumerate(layers):
        head = layer.indi_embedding
        record = dict(
            layer_index=layer_index,
            module_id=id(head),
            class_name=type(head).__name__,
            parameter_names=[],
            parameter_ids=[],
            storage_pointers=[],
            parameter_shapes=[],
        )
        for name, parameter in head.named_parameters():
            record["parameter_names"].append(name)
            record["parameter_ids"].append(id(parameter))
            record["storage_pointers"].append(tensor_pointer(parameter))
            record["parameter_shapes"].append(list(parameter.shape))
        records.append(record)
    return records


def audit_ownership(model, state):
    layers = list(model.dec.decoder_layers)
    module_ids = [id(layer.indi_embedding) for layer in layers]
    parameters = [p for layer in layers for p in layer.indi_embedding.parameters()]
    parameter_ids = [id(p) for p in parameters]
    pointers = [tensor_pointer(p) for p in parameters]
    state_head_keys = sorted(k for k in state if ".indi_embedding." in k)
    shared_module = len(set(module_ids)) < len(module_ids)
    shared_parameter = len(set(parameter_ids)) < len(parameter_ids)
    shared_storage = len(set(pointers)) < len(pointers)
    duplicate_value_groups = []
    for pointer in sorted(set(pointers)):
        group = [p for p in parameters if tensor_pointer(p) == pointer]
        if len(group) > 1:
            duplicate_value_groups.append(dict(
                storage_pointer=pointer,
                parameter_count=len(group),
                shapes=[list(p.shape) for p in group],
                all_equal=all(bool((group[0] == p).all()) for p in group[1:]),
            ))
    checkpoint_duplicate_value_groups = []
    model_state = model.state_dict()
    for pointer in sorted(set(pointers)):
        names = sorted(name for name, tensor in model_state.items()
                       if tensor_pointer(tensor) == pointer and ".indi_embedding." in name)
        if len(names) < 2:
            continue
        present = [name for name in names if name in state]
        checkpoint_duplicate_value_groups.append(dict(
            parameter_names=names,
            checkpoint_values_equal=all(
                name in state and bool(torch.equal(state[present[0]], state[name]))
                for name in present[1:]
            ) if present else None,
        ))
    return dict(
        layer_head_module_ids=module_ids,
        unique_head_module_ids=len(set(module_ids)),
        layer_count=len(module_ids),
        shared_module_object=shared_module,
        shared_parameter_object=shared_parameter,
        shared_storage_pointer=shared_storage,
        unique_head_parameter_objects=len(set(parameter_ids)),
        total_head_parameter_objects=len(parameter_ids),
        unique_head_storage_pointers=len(set(pointers)),
        total_head_storage_pointers=len(pointers),
        state_head_key_count=len(state_head_keys),
        state_head_keys=state_head_keys,
        duplicate_value_groups=duplicate_value_groups,
        checkpoint_duplicate_value_groups=checkpoint_duplicate_value_groups,
        head_records=head_records(model),
    )


def clone_head(head):
    result = copy.deepcopy(head).double().cpu().eval()
    for parameter in result.parameters():
        parameter.requires_grad_(True)
        parameter.grad = None
    return result


def flatten_parameters(heads):
    unique = []
    seen = set()
    for head in heads:
        for parameter in head.parameters():
            if id(parameter) not in seen:
                unique.append(parameter)
                seen.add(id(parameter))
    return unique


def margin(head, inputs, s=0, h=1):
    logits = head(inputs)
    return (logits[0, s, 1] - logits[0, s, 0]
            - logits[0, h, 1] + logits[0, h, 0])


def cross_entropy(head, inputs, labels, eos=0.1):
    logits = head(inputs)
    log_prob = logits.log_softmax(-1)
    weights = torch.where(labels > 0, 1.0, float(eos))
    losses = -log_prob[:, 1] * labels - log_prob[:, 0] * (1.0 - labels)
    return (losses * weights).sum() / labels.sum()


def finite_difference_margin(head, inputs, direction, epsilon):
    with torch.no_grad():
        base = margin(head, inputs).detach()
        for parameter, delta in zip(head.parameters(), direction):
            parameter.add_(epsilon * delta)
        plus = margin(head, inputs).detach()
        for parameter, delta in zip(head.parameters(), direction):
            parameter.sub_(2 * epsilon * delta)
        minus = margin(head, inputs).detach()
        for parameter, delta in zip(head.parameters(), direction):
            parameter.add_(epsilon * delta)
    return float((plus - minus) / (2 * epsilon))


def synthetic(tied):
    torch.manual_seed(1999)
    if tied:
        head = clone_head(shared_layers[0])
        heads = [head, head]
    else:
        heads = [clone_head(shared_layers[0]), clone_head(shared_layers[1])]
    parameters = flatten_parameters(heads)
    inputs = torch.randn(2, 2, 256, dtype=torch.float64)
    labels = torch.tensor([1.0, 0.0], dtype=torch.float64)
    m1 = margin(heads[0], inputs)
    l1 = cross_entropy(heads[0], inputs, labels)
    l2 = cross_entropy(heads[1], inputs, labels)
    q1 = torch.autograd.grad(m1, parameters, retain_graph=True, allow_unused=True)
    u1 = torch.autograd.grad(l1, parameters, retain_graph=True, allow_unused=True)
    u2 = torch.autograd.grad(l2, parameters, retain_graph=True, allow_unused=True)
    q1 = [torch.zeros_like(p) if g is None else g.detach() for g, p in zip(q1, parameters)]
    u1 = [torch.zeros_like(p) if g is None else g.detach() for g, p in zip(u1, parameters)]
    u2 = [torch.zeros_like(p) if g is None else g.detach() for g, p in zip(u2, parameters)]
    q1_dot_u1 = sum(float((a * b).sum()) for a, b in zip(q1, u1))
    q1_dot_u2 = sum(float((a * b).sum()) for a, b in zip(q1, u2))
    local = -q1_dot_u1
    coupling = -q1_dot_u2
    total = local + coupling
    direction = [a + b for a, b in zip(u1, u2)]
    fd = finite_difference_margin(
        heads[0], inputs, [-delta for delta in direction], 1e-5
    )
    relu_min = float("inf")
    for head in heads:
        with torch.no_grad():
            value = head[0](inputs)
            relu_min = min(relu_min, float(value.min().abs()))
    return dict(
        shared_parameters=tied,
        layer_count=2,
        input_shape=list(inputs.shape),
        local_margin_velocity=local,
        cross_layer_coupling=coupling,
        total_margin_velocity=total,
        finite_difference=fd,
        finite_difference_error=abs(fd - total),
        q1_dot_u2=q1_dot_u2,
        relu_min_abs_preactivation=relu_min,
        relu_crossing_warning=relu_min < 1e-6,
    )


def main():
    parser = argparse.ArgumentParser()
    for name in ("code-root", "baseline-audit", "m95-audit", "out", "model"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    assert args.model in ("baseline", "m95")
    root, output = Path(args.code_root), Path(args.out)
    assert not output.exists()
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    global torch
    import torch
    import yaml

    torch.set_num_threads(1)
    audit = json.loads(Path(
        args.baseline_audit if args.model == "baseline" else args.m95_audit
    ).read_text())
    result = dict(
        created=__import__("datetime").datetime.now().isoformat(),
        cuda_visible_devices=os.environ["CUDA_VISIBLE_DEVICES"],
        torch_version=torch.__version__,
        workers=[],
        limitation=(
            "Synthetic parameter-coupling and finite-difference checks only; "
            "not real-data forward, historical training replay, or mechanism causality."
        ),
    )
    global shared_layers
    for name in (args.model,):
        assert digest(audit["checkpoint"]) == audit["checkpoint_sha256"]
        assert digest(audit["config"]) == audit["config_sha256"]
        module = importlib.import_module(audit["explicit_module"])
        package = Path(module.__file__).parent
        assert {p.name: digest(p) for p in sorted(package.glob("*.py"))} == audit["package_sha256"]
        cfg = yaml.safe_load(Path(audit["config"]).read_text())
        model = module.Network(**cfg["model"]).cpu().eval()
        state = torch.load(audit["checkpoint"], map_location="cpu", weights_only=False)["model"]
        expected = model.state_dict()
        assert set(state) - set(expected) == BUFFER_KEYS
        assert not set(expected) - set(state)
        model.load_state_dict({k: v for k, v in state.items() if k not in BUFFER_KEYS}, strict=True)
        ownership = audit_ownership(model, state)
        shared_layers = [layer.indi_embedding for layer in model.dec.decoder_layers]
        # Synthetic tests only use the first two actual layer heads.
        synthetic_shared = synthetic(tied=True)
        synthetic_independent = synthetic(tied=False)
        result["workers"].append(dict(
            model=name,
            checkpoint_sha256=audit["checkpoint_sha256"],
            config_sha256=audit["config_sha256"],
            explicit_module=audit["explicit_module"],
            ownership=ownership,
            synthetic_shared=synthetic_shared,
            synthetic_independent=synthetic_independent,
            cuda_initialized=torch.cuda.is_initialized(),
        ))
        del model, state, expected
        gc.collect()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    assert not torch.cuda.is_initialized()


if __name__ == "__main__":
    main()
