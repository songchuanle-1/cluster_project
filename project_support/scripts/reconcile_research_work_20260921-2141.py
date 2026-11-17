"""Reconcile due candidates with this tick's context snapshot and new receipt."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
CONTEXT = ROOT / "pipeline" / "headless" / ".tick_context.json"
RECEIPT = "pipeline/diagnostic_bundles/model_loader_boundary_server6_20260921.json"
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


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    context_hash = sha256(CONTEXT)
    receipt_hash = sha256(ROOT / RECEIPT)
    work = json.loads(WORK.read_text(encoding="utf-8"))
    touched = []
    for candidate in work["candidates"]:
        if candidate.get("id") not in DUE:
            continue
        # The per-tick context snapshot is regenerated every tick; repin it.
        for entry in candidate["evidence"]:
            if entry.get("path", "").endswith(".tick_context.json"):
                entry["sha256"] = context_hash
        if not any(e.get("path") == RECEIPT for e in candidate["evidence"]):
            candidate["evidence"].append(
                {"path": RECEIPT, "sha256": receipt_hash})
        touched.append(candidate["id"])
    if set(touched) != DUE:
        raise ValueError("Due candidate set mismatch: %s" % sorted(touched))
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("reconciled %d candidates; context=%s receipt=%s"
          % (len(touched), context_hash[:12], receipt_hash[:12]))


if __name__ == "__main__":
    main()
