"""Exact native repeated-input diagnosis; no optimizer or production edits."""
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
DATA = Path("/data3/songcl/data/data_cluster")
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "7"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT), str(ROOT / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    mp = PIPE / "point_detail_population_20261009/result.manifest.json"
    assert sha(mp) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    config = ROOT / f"configs/Quard/ctf_hcg_csort/{NAME}.yaml"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = str(DATA) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("caption-equivalence"))
    row = next(r for r in json.loads(mp.read_text()) if r["scene"] == "scene0358_00")
    index = int(row["native_group"])
    group = source.scene_inputs[index]
    assert {(int(a["ann_id"]), int(a["object_id"])) for a in group
            if int(a["ann_id"]) in (0, 1)} == {(0, 12), (1, 8)}
    item = source[index]
    batch = source.collate_fn([item])
    positions = [batch["ann_ids"].index(a) for a in (0, 1)]
    p, q = positions
    assert torch.equal(batch["lang_tokenss"][p], batch["lang_tokenss"][q])
    assert torch.equal(batch["lang_masks"][p], batch["lang_masks"][q])
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    criterion = model.criterion
    held, last = {}, {}
    hook = criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(pred=inputs[0], args=inputs))
    original = criterion.loss_indi

    def capture(self, logits, targets, indices, count):
        if logits is held["pred"]["indis"]:
            last.update(logits=logits, targets=targets, indices=indices, count=count)
        return original(logits, targets, indices, count)
    criterion.loss_indi = types.MethodType(capture, criterion)
    trials = []
    previous = None
    try:
        for trial in (0, 1):
            gorilla.set_random_seed(1999)
            held.clear()
            last.clear()
            with torch.no_grad():
                value, _ = model(batch, mode="loss")
            pred = held["pred"]
            # Native FPS and indication axes must refer to the same physical seeds.
            fps = held["args"][7]
            assert torch.equal(fps[p], fps[q])
            assert torch.equal(pred["sample_inds"][p], pred["sample_inds"][q])
            logits = last["logits"].detach()
            masks = pred["masks"].detach()
            indices = last["indices"]
            positives = [set(indices[i][0].tolist()) for i in (p, q)]
            disagreement = sorted(positives[0] ^ positives[1])
            gradients = []
            losses = []
            for i in (p, q):
                z = logits[i:i+1].clone().requires_grad_(True)
                idx = [indices[i]]
                n = torch.tensor([max(1, len(idx[0][0]))], dtype=z.dtype, device=z.device)
                with torch.enable_grad():
                    loss = original(z, [last["targets"][i]], idx, n)
                    g = torch.autograd.grad(loss, z)[0]
                gradients.append(g.detach())
                losses.append(float(loss))
            opposite = [j for j in disagreement
                        if float(gradients[0][0, j, 1] * gradients[1][0, j, 1]) < 0]
            same_z = logits[p:p+1].clone().requires_grad_(True)
            n = torch.tensor([max(1, len(indices[p][0]))],
                             dtype=same_z.dtype, device=same_z.device)
            with torch.enable_grad():
                a = original(same_z, [last["targets"][p]], [indices[p]], n)
                b = original(same_z, [last["targets"][p]], [indices[p]], n)
                ga = torch.autograd.grad(a, same_z, retain_graph=True)[0]
                gb = torch.autograd.grad(b, same_z)[0]
            control = float((ga - gb).abs().max())
            saved = {"logits": logits.cpu().clone(), "masks": masks.cpu().clone(),
                     "gradients": torch.stack(gradients).cpu().clone()}
            deltas = ({k: float((saved[k] - previous[k]).abs().max()) for k in saved}
                      if previous is not None else None)
            entry = {"trial": trial, "native_total_loss": float(value),
                     "exact_input_token_equality": True, "physical_query_seed_equality": True,
                     "same_input_indication_max_delta": float((logits[p] - logits[q]).abs().max()),
                     "same_input_mask_max_delta": float((masks[p] - masks[q]).abs().max()),
                     "positive_query_ids": [sorted(x) for x in positives],
                     "positive_set_disagreement_queries": disagreement,
                     "opposite_sign_positive_logit_grad_queries": opposite,
                     "positive_logit_gradient_values": [[float(g[0, j, 1]) for j in disagreement]
                                                        for g in gradients],
                     "native_indication_losses": losses,
                     "same_target_control_gradient_max_delta": control,
                     "finite_gradients": all(bool(torch.isfinite(g).all()) for g in gradients),
                     "repeat_max_deltas": deltas}
            trials.append(entry)
            previous = saved
            torch.save({"scene": "scene0358_00", "ann_ids": [0, 1],
                        "logits": logits[[p, q]].cpu(),
                        "positive_ids": [indices[i][0].cpu() for i in (p, q)]},
                       PIPE / f"caption_equivalence_capture_20261012_trial{trial}.pt")
    finally:
        criterion.loss_indi = original
        hook.remove()
    result = {"contract": "caption_equivalence_same_native_forward_v1",
              "admission": False, "seed": 1999, "input_sha256": batch_fingerprint(torch, batch),
              "checkpoint_sha256": sha(checkpoint), "manifest_sha256": sha(mp),
              "script_sha256": sha(Path(__file__)), "native_batch_size": 1,
              "expressions": len(batch["ann_ids"]), "target_annotations": [0, 1],
              "trials": trials,
              "strict_repeat_pass": all(d <= 1e-6 for d in trials[1]["repeat_max_deltas"].values()),
              "captures": [{"path": str(PIPE / f"caption_equivalence_capture_20261012_trial{i}.pt"),
                            "sha256": sha(PIPE / f"caption_equivalence_capture_20261012_trial{i}.pt")}
                           for i in (0, 1)],
              "limits": "Existing native loss-mode eval and detached native indication backward only. No optimizer/full new-model backward/resource admission/efficacy. A true observable ambiguity cannot identify which original single object was intended."}
    output = PIPE / "caption_equivalence_native_20261012.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
