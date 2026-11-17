"""Native TRAIN full backward for provisional interchange; not admission."""
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = parent.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(parent)}
exec(compile(source, str(parent), "exec"), ns)
torch, model = ns["torch"], ns["model"]
state = {}


def donors(batch):
    result = list(range(len(batch["object_idss"])))
    offset = 0
    for count in batch["scenes_len"]:
        groups = defaultdict(list)
        for i in range(offset, offset + int(count)):
            ids = tuple(sorted(int(v) for v in batch["object_idss"][i]))
            if len(ids) == 1:
                groups[ids].append(i)
        for members in groups.values():
            for i, j in zip(members, members[1:] + members[:1]):
                result[i] = j
        offset += int(count)
    assert offset == len(result)
    assert sorted(result) == list(range(len(result)))
    return result


def exchange(module, args, output):
    language, visual = output
    visual.retain_grad()
    language.retain_grad()
    state["visual"], state["language"] = visual, language
    permutation = torch.tensor(state["donors"], device=visual.device)
    changed = visual[permutation]
    changed.retain_grad()
    state["changed"] = changed
    return language, changed


model.dec.encoder_layers[-1].register_forward_hook(exchange)
model.train()
records = []
for step, batch in enumerate(ns["batches"]):
    permutation = donors(batch)
    if permutation == list(range(len(permutation))):
        continue
    state["donors"] = permutation
    model.zero_grad(set_to_none=True)
    ns["gorilla"].set_random_seed(1999)
    loss, _ = model(copy.deepcopy(batch), mode="loss")
    assert torch.isfinite(loss).all()
    loss.backward()
    visual, changed = state["visual"], state["changed"]
    expected = torch.zeros_like(visual)
    expected.index_add_(0, torch.tensor(permutation, device=visual.device), changed.grad)
    assert torch.allclose(expected, visual.grad, atol=1e-6, rtol=1e-5)
    finite = all(torch.isfinite(p.grad).all().item() for p in model.parameters() if p.grad is not None)
    assert finite
    assert float(changed.grad.abs().sum()) > 0
    records.append(dict(batch=step, donors=permutation,
        scene_lengths=[int(v) for v in batch["scenes_len"]],
        object_ids=[[int(v) for v in ids] for ids in batch["object_idss"]],
        loss=float(loss.detach()), all_parameter_gradients_finite=finite,
        donor_gradient_max_error=float((expected-visual.grad).abs().max()),
        donor_gradient_l1=float(visual.grad.abs().sum()),
        language_gradient_l1=float(state["language"].grad.abs().sum()),
        peak_memory_mib=torch.cuda.max_memory_allocated()/2**20))
    print(json.dumps(records[-1]), flush=True)
    if len(records) == 2:
        break
assert len(records) == 2
destination = ns["ROOT"].parent / "pipeline/interchange_backward_20260916"
destination.mkdir(exist_ok=True)
(destination / "result.json").write_text(json.dumps(dict(records=records,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), parent, ns["checkpoint"], ns["config"])},
    limitations="Original nativeTRAIN batches;cyclic permutation correctness probe,not "
    "uniform-orbit training or production implementation. No optimizer update,AMP,DDP, "
    "performance benefit,resource admission or novelty PASS."), indent=2))
