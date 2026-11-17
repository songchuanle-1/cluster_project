"""Bind the completed M95 same-forward capture and its derived controls."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
CAPTURE = "pipeline/diagnostic_runs/m95_same_forward_20260922-0945/capture.json"
CONTROL = "pipeline/reports/m95_same_forward_control_20260922-0955.json"
TARGETS = (
    "referent-causality-audit",
    "referent-discrimination",
    "instance-identity-representation",
    "modality-identity-preservation",
)


def sha256(path):
    digest = hashlib.sha256()
    with (ROOT / path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_evidence(candidate, path, digest):
    evidence = candidate.setdefault("evidence", [])
    for item in evidence:
        if item.get("path") == path:
            item["sha256"] = digest
            return
    evidence.append({"path": path, "sha256": digest})


def main():
    capture_hash = sha256(CAPTURE)
    control_hash = sha256(CONTROL)
    capture = json.loads((ROOT / CAPTURE).read_text(encoding="utf-8"))
    control = json.loads((ROOT / CONTROL).read_text(encoding="utf-8"))
    if capture_hash != "975c718ddefb122ef8368c117439e9562b9893bb40abf8d80d1fc31c05824c80":
        raise ValueError("Unexpected capture hash")
    if control_hash != "8f6cd55f2edf61dd4af05780108838444871af6194876ba35fcc4b777564d2ab":
        raise ValueError("Unexpected control hash")
    if control["source_capture"]["local_sha256"] != capture_hash:
        raise ValueError("Control receipt does not bind the local capture")

    work = json.loads(WORK.read_text(encoding="utf-8"))
    common = {
        "capture_path": CAPTURE,
        "capture_sha256": capture_hash,
        "control_receipt": CONTROL,
        "control_receipt_sha256": control_hash,
        "remote_capture_path": control["source_capture"]["remote_path"],
        "checkpoint_sha256": capture["checkpoint_sha256"],
        "model_source_sha256": capture["model_source_sha256"],
        "config_sha256": capture["config_sha256"],
        "producer_sha256": capture["producer_sha256"],
        "feature_artifacts": capture["feature_artifacts"],
        "expressions": 16,
        "scenes": 4,
        "native_capture_completed": True,
        "admission": False,
    }
    progress = {
        "referent-causality-audit": (
            "2026-09-22T09:55:00+08:00: completed the bounded two-batch frozen M95 "
            "same-forward capture on server-6 GPU7 (16 TRAIN expressions, 4 scenes). "
            "Selected-query success was 8/16; the native-positive oracle selection "
            "and the objectness-only any-seed selection each reached 13/16 "
            "(+43.75pp scene-balanced; 7 fixed, 0 broken). Because the any-seed "
            "control also improves, this run diagnoses a broad object-region "
            "selection failure and does not isolate referent identity. It is not "
            "population, admission, efficacy or independence evidence."
        ),
        "referent-discrimination": (
            "2026-09-22T09:55:00+08:00: the completed frozen M95 same-forward "
            "capture contains 16 expressions with exact per-query scores and masks. "
            "Eight selected-query failures all have at least one acceptable query "
            "in the same forward (best acceptable ranks 2-72), but only 2 of the 8 "
            "failures are recoverable within the same class. This supports a "
            "selection/ranking diagnosis while leaving class confusion unresolved; "
            "it is not admission or population evidence."
        ),
        "instance-identity-representation": (
            "2026-09-22T09:55:00+08:00: the exact M95 checkpoint is now bound and "
            "a two-batch same-forward capture completed with raw/projected 3D and "
            "2D features saved in features_000.pt and features_001.pt. The capture "
            "establishes availability of paired representations but does not yet "
            "establish instance-identity separability or any mechanism effect."
        ),
        "modality-identity-preservation": (
            "2026-09-22T09:55:00+08:00: the exact M95 checkpoint is now bound and "
            "a two-batch same-forward capture completed with paired 3D/2D feature "
            "artifacts and exact native input identities. This makes a new "
            "same-forward modality control possible, but preservation is not yet "
            "measured by this capture alone."
        ),
    }
    next_actions = {
        "referent-causality-audit": (
            "Continue CPU-side diagnosis: on a larger pre-registered manifest, "
            "separate native-positive reference identity from the any-seed "
            "objectness control before treating selection repair as a referent "
            "mechanism. Do not enqueue or claim admission."
        ),
        "referent-discrimination": (
            "Continue CPU-side diagnosis on the captured candidate ranks: add a "
            "paired same-class referent/control rank test and determine whether the "
            "six non-same-class failures are class confusion. No queue mutation."
        ),
        "instance-identity-representation": (
            "Derive paired identity-separability controls from the saved 3D/2D "
            "features on CPU; no new GPU run unless the feature-only test is "
            "inconclusive. No admission."
        ),
        "modality-identity-preservation": (
            "Derive a same-forward modality preservation/alignment control from "
            "the saved feature artifacts and existing frozen evaluators on CPU; "
            "do not reuse the historical cross-capture result as new evidence. No "
            "queue mutation."
        ),
    }

    touched = []
    for candidate in work["candidates"]:
        if candidate.get("id") not in TARGETS:
            continue
        if candidate.get("stage") != "diagnosis":
            raise ValueError("Expected diagnosis stage for " + candidate["id"])
        candidate["latest_progress"] = progress[candidate["id"]]
        candidate["next_action"] = next_actions[candidate["id"]]
        candidate["native_capture_20260922"] = common
        add_evidence(candidate, CAPTURE, capture_hash)
        add_evidence(candidate, CONTROL, control_hash)
        touched.append(candidate["id"])
    if set(touched) != set(TARGETS):
        raise ValueError("Target set mismatch: %s" % sorted(touched))
    work["next_action"] = (
        "Continue CPU-side candidate diagnosis from the completed M95 capture; "
        "only candidates that pass the full admission chain may be enqueued. No "
        "training launch or queue mutation occurred."
    )
    work["updated_at"] = "2026-09-22T09:55:00+08:00"
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("updated %d candidates; capture=%s control=%s" %
          (len(touched), capture_hash[:12], control_hash[:12]))


if __name__ == "__main__":
    main()
