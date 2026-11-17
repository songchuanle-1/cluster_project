"""Record champion instantiation + backbone native backward progress."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
NEW_RECEIPTS = (
    "pipeline/diagnostic_bundles/model_instantiation_probe_server6_20260921.json",
    "pipeline/diagnostic_bundles/champion_backbone_native_backward_server6_20260921.json",
    "pipeline/diagnostic_bundles/champion_param_census_server6_20260921.json",
)
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
    "2026-09-21T21:56:00+08:00: measured the bound champion. Constructor and assets "
    "are viable on server-6 GPU7: 157,484,090 params in 847 tensors, of which "
    "124,645,632 (RoBERTa text encoder) are frozen and only 32,838,458 are "
    "trainable; weight transfer peaked at 602.45 MiB (646 MiB reserved). A "
    "synthetic native forward/backward through the real production sequence "
    "(voxelization_idx -> voxelization -> SparseConvTensor -> extract_feat) "
    "produced finite nonzero gradients on the input and on all 139 exercised "
    "backbone tensors (input_conv 1 + unet 136 + output_layer 2)."
)
NEXT = (
    "Next bounded step: extend the synthetic native path through the decoder "
    "(dec) and the criterion to reach a full-model native backward on server-6 "
    "GPU7, then measure resource gates (FLOPs, latency, peak memory) with the "
    "standard calibrated method before any candidate admission. Text encoder, "
    "decoder, matcher and criterion remain unexecuted, so full-model backward, "
    "resources and admission are still unverified; M197 stays stopped_unknown "
    "with no restart and no successor."
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipts = {p: sha256(ROOT / p) for p in NEW_RECEIPTS}
    work = json.loads(WORK.read_text(encoding="utf-8"))
    touched = []
    purged = 0
    for candidate in work["candidates"]:
        # The per-tick context snapshot is regenerated every tick and is not a
        # stable scientific artifact; pinning it breaks closure across ticks.
        kept = []
        for entry in candidate.get("evidence", []):
            if entry.get("path", "").endswith(".tick_context.json"):
                purged += 1
                continue
            kept.append(entry)
        candidate["evidence"] = kept
        if candidate.get("id") not in DUE:
            continue
        existing = {e["path"] for e in candidate["evidence"]}
        for path, digest in receipts.items():
            if path not in existing:
                candidate["evidence"].append({"path": path, "sha256": digest})
        candidate["latest_progress"] = PROGRESS
        candidate["next_action"] = NEXT
        candidate["champion_measurement_progress"] = {
            "instantiation_receipt": NEW_RECEIPTS[0],
            "instantiation_sha256": receipts[NEW_RECEIPTS[0]],
            "backward_receipt": NEW_RECEIPTS[1],
            "backward_sha256": receipts[NEW_RECEIPTS[1]],
            "census_receipt": NEW_RECEIPTS[2],
            "census_sha256": receipts[NEW_RECEIPTS[2]],
            "total_params": 157484090,
            "trainable_params": 32838458,
            "frozen_params": 124645632,
            "peak_transfer_mib": 602.45458984375,
            "backbone_native_backward": True,
            "backbone_tensors_with_grad": 139,
            "backbone_tensors_total": 648,
            "full_model_native_backward_verified": False,
            "resources_verified": False,
            "admission": False,
        }
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
