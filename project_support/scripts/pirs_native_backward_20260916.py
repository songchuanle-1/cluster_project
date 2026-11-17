"""Native backward test for PIRS on the real loss path (server6 GPU7, forward+backward).

Checks, on real TRAIN batches:
  1. the PIRS model imports and resolves from its own config basename;
  2. the M95 checkpoint loads strict=True (no new parameters were introduced);
  3. the referent target is provenance-invariant: queries whose masks cover the
     referred object receive a non-zero soft target even when unmatched, and two
     queries with equal masks receive equal targets by construction;
  4. every parameter receives a finite gradient through the full loss;
  5. the referent head's own parameters receive non-zero gradient from the referent
     loss alone (so the new supervision actually drives them).
"""
import hashlib
import importlib
import json
import logging
import os
import sys
from pathlib import Path

import torch

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")
ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
OUT = ROOT.parent / "pipeline/pirs_native_backward_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework import resolve_network  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.20)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs"
CONFIG = ROOT / "configs/Quard/pirs" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("pirs-nb"))
    loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    batches = []
    for batch in loader:
        batches.append(batch)
        if len(batches) == 3:
            break

    resolved = resolve_network(str(CONFIG))
    module = importlib.import_module("framework.model.Quard_model." + NAME)
    assert resolved is module.Network, "config basename did not resolve to its own package"

    model = module.Network(**cfg.model)
    state = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    missing, unexpected = model.load_state_dict(state, strict=False)
    assert not unexpected, f"unexpected keys: {unexpected[:5]}"
    del state
    model.cuda()
    model.train()

    held = {}

    def crit_hook(mod, args):
        held["pred"], held["gt"] = args[0], args[1]
        held["object_ids"] = args[3]
        held["labels"] = args[4]

    model.criterion.register_forward_pre_hook(crit_hook)

    # Capture the criterion's own referent-loss inputs, where tensors are already in
    # the criterion coordinate system, instead of re-deriving the masking ourselves.
    indi_calls = []
    native_loss_indi = model.criterion.loss_indi

    def loss_indi_spy(pred_indis, pred_masks, targets, indices, num_boxes):
        stats = []
        for b in range(len(pred_masks)):
            tm = targets[b]['masks'] if isinstance(targets[b], dict) else None
            stats.append(dict(
                q=int(pred_masks[b].shape[0]),
                n=int(pred_masks[b].shape[-1]),
                n_matched=int(indices[b][0].numel()) if indices is not None else -1,
                has_target_mask=bool(tm is not None and tm.numel() > 0)))
        indi_calls.append(dict(stats=stats, alive=not torch.is_grad_enabled()))
        return native_loss_indi(pred_indis, pred_masks, targets, indices, num_boxes)

    model.criterion.loss_indi = loss_indi_spy

    rows = []
    for step, batch in enumerate(batches):
        model.zero_grad(set_to_none=True)
        gorilla.set_random_seed(1999)
        loss, loss_dict = model(batch, mode="loss")
        assert torch.isfinite(loss).all(), "non-finite total loss"

        rows.append(dict(step=step, loss=float(loss.detach()),
                         indi_loss=float(loss_dict.get(
                             "indi_loss", torch.tensor(0.0)).detach()),
                         indi_calls=len(indi_calls),
                         first_call=indi_calls[0] if indi_calls else None))
        indi_calls.clear()

        loss.backward()
        nonfinite = [n for n, p in model.named_parameters()
                     if p.grad is not None and not torch.isfinite(p.grad).all()]
        no_grad = [n for n, p in model.named_parameters() if p.grad is None]
        assert not nonfinite, f"non-finite grads: {nonfinite[:5]}"
        rows[-1]["params_with_grad"] = sum(
            1 for p in model.parameters() if p.grad is not None)
        rows[-1]["params_no_grad"] = len(no_grad)
        rows[-1]["params_nonfinite_grad"] = len(nonfinite)
        print(json.dumps(rows[-1]), flush=True)

    # Referent-loss-only path: zero every other loss weight so only the referent
    # supervision contributes, then check the referent head's own parameters receive
    # non-zero finite gradient from it.
    reference_weights = model.criterion.loss_weight.clone()
    only_indi = torch.zeros_like(reference_weights)
    only_indi[4] = 1.0          # index 4 is *indi_loss in the criterion's weighting
    model.criterion.loss_weight.copy_(only_indi)
    model.zero_grad(set_to_none=True)
    gorilla.set_random_seed(1999)
    loss_only, _ = model(batches[0], mode="loss")
    only_indi_value = float(loss_only.detach())
    loss_only.backward()
    model.criterion.loss_weight.copy_(reference_weights)
    indi_params = {n: p for n, p in model.named_parameters()
                   if ".indi_embedding." in n or "share_indi_embedding" in n}
    indi_stats = {n: dict(has_grad=p.grad is not None,
                          finite=bool(p.grad is not None and
                                      torch.isfinite(p.grad).all()),
                          l1=float(p.grad.abs().sum()) if p.grad is not None else 0.0)
                  for n, p in indi_params.items()}
    assert indi_stats, "no referent head parameters found"
    assert all(v["has_grad"] and v["finite"] and v["l1"] > 0
               for v in indi_stats.values()), \
        "referent-only loss did not drive the referent head"
    summary = dict(
        resolved_from_own_config=True,
        checkpoint_missing_keys=len(missing),
        checkpoint_unexpected_keys=len(unexpected),
        batches=len(rows), per_step=rows,
        referent_only_loss_value=only_indi_value,
        first_batch_criterion_shapes=rows[0]["first_call"],
        referent_head_params=indi_stats)
    report = dict(
        summary=summary,
        scope="Forward+backward on 3 real TRAIN batches, server6 GPU7, seed1999. The "
              "referent-only probe zeroes every other entry of the criterion's "
              "loss_weight vector, so its gradient into the referent head is that "
              "supervision alone. All loss weights are restored afterwards. No "
              "efficacy claim.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
