"""Record full-model native backward progress for the champion diagnostic."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
RECEIPT = (
    "pipeline/diagnostic_bundles/"
    "champion_full_model_native_backward_server6_20260922.json")
SOURCE = "scripts/champion_full_model_native_backward_20260922.py"
TEST = "scripts/test_champion_full_model_native_backward_20260922.py"
NEW_EVIDENCE = (RECEIPT, SOURCE, TEST)
DUE = {
    "referent-supervision-axis",
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
    "referent-query-selection",
    "input-modality-distinguishability",
    "same-target-description-grounding",
}
PROGRESS = (
    "2026-09-22T02:24:00+08:00: completed a synthetic full-model native "
    "forward/backward through the production champion loss entry on server-6 "
    "GPU7. Text encoder, decoder, cluster attention, sampler, criterion and "
    "backward all executed; total loss 0.81725. All 630 trainable tensors on "
    "the active path received finite nonzero gradients. Six registered legacy "
    "cluster-routing Q/K/V tensors are intentionally bypassed by ctf_hcg_csort; "
    "12 of 24 conditional score tensors were selected by the model-derived "
    "target and per-layer IoU filter. Peak training-graph memory was 870.81 MiB "
    "allocated / 910.00 MiB reserved. This is runtime-contract evidence, not "
    "resource-gate, efficacy or admission evidence."
)
NEXT = (
    "Next bounded step: run the project's calibrated resource gate on real "
    "validation input with the same fvcore FLOPs counter, bs=1 warmup20/repeat100 "
    "latency protocol and peak-memory method used for the historical baseline/"
    "champion; compare champion increments and record the inherited absolute "
    "10.20585 G FLOPs overage. Then complete independence and admission gates. "
    "M197 stays stopped_unknown with no restart and no successor."
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipts = {path: sha256(ROOT / path) for path in NEW_EVIDENCE}
    work = json.loads(WORK.read_text(encoding="utf-8"))
    touched = []
    purged = 0
    for candidate in work["candidates"]:
        kept = []
        for entry in candidate.get("evidence", []):
            if entry.get("path", "").endswith(".tick_context.json"):
                purged += 1
                continue
            kept.append(entry)
        candidate["evidence"] = kept
        if candidate.get("id") not in DUE:
            continue
        existing = {entry["path"] for entry in candidate["evidence"]}
        for path, digest in receipts.items():
            if path not in existing:
                candidate["evidence"].append(
                    {"path": path, "sha256": digest})
        candidate["latest_progress"] = PROGRESS
        candidate["next_action"] = NEXT
        measurement = candidate.setdefault(
            "champion_measurement_progress", {})
        measurement.update({
            "full_model_backward_receipt": RECEIPT,
            "full_model_backward_sha256": receipts[RECEIPT],
            "full_model_source_sha256": receipts[SOURCE],
            "full_model_test_sha256": receipts[TEST],
            "text_encoder_executed": True,
            "decoder_executed": True,
            "criterion_executed": True,
            "full_model_loss": 0.817247211933136,
            "trainable_tensors": 648,
            "active_trainable_tensors": 630,
            "inactive_routing_tensors": 6,
            "conditional_score_tensors_total": 24,
            "conditional_score_tensors_with_grad": 12,
            "peak_training_allocated_mib": 870.80517578125,
            "peak_training_reserved_mib": 910.0,
            "full_model_native_backward_verified": True,
            "resources_verified": False,
            "admission": False,
        })
        touched.append(candidate["id"])
    if set(touched) != DUE:
        raise ValueError("Due candidate set mismatch: %s" % sorted(touched))
    work["next_action"] = NEXT
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("updated %d candidates; purged %d transient context refs"
          % (len(touched), purged))


if __name__ == "__main__":
    main()
