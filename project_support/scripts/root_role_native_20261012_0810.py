"""Same-forward native semantic role intervention; original model untouched."""
import copy
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import types

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "7"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    from framework.dataset.scannetv2 import get_positive_map
    from m95_multiword_native_31_20260928 import selected_loader
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.20)
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    audit_path = PIPE / "root_role_audit_v2_20261012_0810.json"
    loss_path = ROOT / f"framework/model/Quard_model/{NAME}/loss.py"
    dataset_path = ROOT / "framework/dataset/scannetv2.py"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    assert sha(audit_path) == "436f88ddba6c991ec8328a383b595ed22808f5db08db73b743f5aaf8b335ac00"
    assert sha(loss_path) == "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"
    assert sha(dataset_path) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    audit = json.loads(audit_path.read_text())
    chosen = [r for r in audit["rows"]
              if r["literal_status"] == "literal_target_outside_root"]
    assert len(chosen) == 1
    evidence = chosen[0]
    cfg = gorilla.Config.fromfile(
        str(ROOT / f"configs/Quard/ctf_hcg_csort/{NAME}.yaml"))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("root-role"))
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    original = model.criterion.loss_sem_align
    captures, pred_capture = [], {}

    def capture(self, *args):
        captures.append(args)
        return original(*args)

    model.criterion.loss_sem_align = types.MethodType(capture, model.criterion)
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: pred_capture.update(pred=inputs[0]))
    rows, prior = [], None
    for trial in (0, 1):
        gorilla.set_random_seed(1999)
        batch = next(iter(selected_loader(source, [evidence["native_group"]], DataLoader)))
        index = list(map(int, batch["ann_ids"])).index(evidence["ann_id"])
        assert batch["scan_ids"] == [evidence["scene"]]
        assert list(map(int, batch["object_idss"][index])) == evidence["targets"]
        captures.clear()
        pred_capture.clear()
        gorilla.set_random_seed(1999)
        with torch.no_grad():
            native_loss, native_components = model(batch, mode="loss")
        assert torch.isfinite(native_loss).all()
        tokens, queries, masks, targets, indices, num_boxes = captures[0]
        encoded = source.tokenizer.batch_encode_plus(
            [evidence["caption"]], padding="longest", return_tensors="pt")
        correct = torch.from_numpy(get_positive_map(
            encoded, np.asarray(evidence["literal_target_spans"]))).sum(0)
        nodes = evidence["object_nodes"]
        wrong_node = next(n for n in nodes
                          if n["node_id"] != 0 and n["lemma_head"] != evidence["root_lemma"]
                          and n["spans"])
        wrong = torch.from_numpy(get_positive_map(
            encoded, np.asarray(wrong_node["spans"]))).sum(0)
        assert bool(correct.any()) and bool(wrong.any())
        native_map = targets[index]["positive_map"][0]
        assert not bool(((native_map[:len(correct)].detach().cpu() > 0)
                         & (correct > 0)).any())

        def intervention(proposed):
            altered = [{k: v.clone() if torch.is_tensor(v) else copy.deepcopy(v)
                        for k, v in t.items()} for t in targets]
            t = altered[index]
            old = t["positive_map"].clone()
            new = torch.zeros_like(old)
            new[:, :len(proposed)] = proposed.to(new.device)
            t["positive_map"] = new
            t["other_entity_map"] = (t["other_entity_map"] + old).clamp_max(1)
            t["other_entity_map"].masked_fill_(new > 0, 0)
            return altered

        outcomes, gradients = {}, {}
        for variant, target_map in (
            ("original", targets), ("identity_control", targets),
            ("target_anchored", intervention(correct)),
            ("wrong_reference", intervention(wrong)),
        ):
            tt = tokens.detach().clone().requires_grad_(True)
            qq = queries.detach().clone().requires_grad_(True)
            value = original(tt, qq, masks, target_map, indices, num_boxes)
            grad = torch.autograd.grad(value.sum(), (tt, qq))
            assert torch.isfinite(value).all() and all(torch.isfinite(g).all() for g in grad)
            gradients[variant] = tuple(g.detach().cpu() for g in grad)
            outcomes[variant] = {
                "semantic_loss": float(value.detach()),
                "token_gradient_max": float(grad[0].abs().max()),
                "query_gradient_max": float(grad[1].abs().max()),
                "token_gradient_nonzero": int((grad[0] != 0).sum()),
                "query_gradient_nonzero": int((grad[1] != 0).sum()),
            }
        differences = {}
        for left, right in (("original", "identity_control"),
                            ("original", "target_anchored"),
                            ("target_anchored", "wrong_reference")):
            differences[left + "_vs_" + right] = {
                "loss_delta": outcomes[right]["semantic_loss"] - outcomes[left]["semantic_loss"],
                "token_gradient_max_delta": float(
                    (gradients[left][0] - gradients[right][0]).abs().max()),
                "query_gradient_max_delta": float(
                    (gradients[left][1] - gradients[right][1]).abs().max()),
            }
        fingerprint = batch_fingerprint(torch, batch)
        logits = pred_capture["pred"]["indis"].detach().cpu()
        native_masks = pred_capture["pred"]["masks"].detach().cpu()
        repeat = None
        if prior:
            repeat = {
                "input_equal": fingerprint == prior["fingerprint"],
                "native_loss_delta": abs(float(native_loss) - prior["native_loss"]),
                "native_logit_max_delta": float((logits - prior["logits"]).abs().max()),
                "native_mask_max_delta": float((native_masks - prior["masks"]).abs().max()),
                "target_role_loss_delta": abs(
                    outcomes["target_anchored"]["semantic_loss"] - prior["role_loss"]),
                "target_role_token_grad_max_delta": float(
                    (gradients["target_anchored"][0] - prior["role_grad"][0]).abs().max()),
                "target_role_query_grad_max_delta": float(
                    (gradients["target_anchored"][1] - prior["role_grad"][1]).abs().max()),
            }
        rows.append({
            "trial": trial, "scene": evidence["scene"], "ann_id": evidence["ann_id"],
            "group_expression_count": len(batch["ann_ids"]), "target_batch_index": index,
            "target_ids": evidence["targets"], "native_root": evidence["root_lemma"],
            "annotated_target_name": evidence["annotation_object_name"],
            "wrong_reference": wrong_node["lemma_head"],
            "native_matched_queries": indices[index][0].detach().cpu().tolist(),
            "native_positive_token_ids": (native_map > 0).nonzero().flatten().tolist(),
            "target_positive_token_ids": (correct > 0).nonzero().flatten().tolist(),
            "wrong_positive_token_ids": (wrong > 0).nonzero().flatten().tolist(),
            "native_loss": float(native_loss), "input_sha256": fingerprint,
            "outcomes": outcomes, "differences": differences, "repeat": repeat,
        })
        prior = {"fingerprint": fingerprint, "native_loss": float(native_loss),
                 "logits": logits, "masks": native_masks,
                 "role_loss": outcomes["target_anchored"]["semantic_loss"],
                 "role_grad": gradients["target_anchored"]}
    hook.remove()
    result = {
        "contract": "native_target_role_same_forward_gradient_v1",
        "rows": rows, "seed": 1999, "native_forward_count": 2,
        "checkpoint_sha256": sha(checkpoint), "audit_sha256": sha(audit_path),
        "loss_sha256": sha(loss_path), "dataset_sha256": sha(dataset_path),
        "script_sha256": sha(Path(__file__)), "admission": False,
        "scope": "Detached native projected tensor gradients and same-forward role intervention; NOT new-model full backward/resources/efficacy.",
    }
    output = PIPE / "root_role_native_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
