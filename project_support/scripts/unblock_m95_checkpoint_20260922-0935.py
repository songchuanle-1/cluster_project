"""Unblock the four native capture routes now that the exact M95 checkpoint is bound."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
RECEIPT = "pipeline/reports/checkpoint_binding_m95_20260922-0935.json"
TARGETS = {
    "referent-causality-audit",
    "referent-discrimination",
    "instance-identity-representation",
    "modality-identity-preservation",
}
PRIOR_BLOCKER = (
    "The exact M95 checkpoint payload is absent from allowed server-6 storage; "
    "server reachability and GPU7 capacity are no longer blockers."
)
PROGRESS = (
    "2026-09-22T09:35:00+08:00: exact-checkpoint blocker resolved. The M95 "
    "champion payload was located on allowed server-6 storage at "
    "/data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth "
    "with sha256 fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e, "
    "byte-exact against the frozen capture identity, and meta.best_miou 0.5024607 "
    "matching the historical exact maximum. It was missed because it is a "
    "parent-model copy staged inside a 2026-09-14 SCM variant directory rather "
    "than under a directory named for the champion stem."
)
NEXT = (
    "Run the deployed frozen capture on server-6 GPU7 against the now-bound "
    "exact M95 checkpoint, without evicting foreign work: verify the config "
    "digest, bind the checkpoint hash, execute the frozen same-forward capture, "
    "and persist per-candidate controls. Then continue that candidate's "
    "diagnosis. This unblock is checkpoint availability only; it is not "
    "admission, efficacy or independence evidence."
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt_hash = sha256(ROOT / RECEIPT)
    work = json.loads(WORK.read_text(encoding="utf-8"))
    touched = []
    for candidate in work["candidates"]:
        if candidate.get("id") not in TARGETS:
            continue
        if candidate.get("stage") != "blocked":
            raise ValueError("Expected blocked stage for " + candidate["id"])
        candidate["prior_blocker"] = candidate.get("blocker", PRIOR_BLOCKER)
        candidate["blocker_resolved_at"] = "2026-09-22T09:35:00+08:00"
        candidate["blocker_resolved_by"] = RECEIPT
        # Clear the stale blocking contract so closure stops treating it as blocked.
        for key in ("blocker", "retry_after", "unblock_condition"):
            candidate.pop(key, None)
        candidate["stage"] = "diagnosis"
        candidate["latest_progress"] = PROGRESS
        candidate["next_action"] = NEXT
        candidate["checkpoint_binding"] = {
            "receipt": RECEIPT,
            "sha256": receipt_hash,
            "remote_path": (
                "/data3/songcl/Project/Cluster_project/pipeline/"
                "scm_admission_20260914/best.pth"),
            "checkpoint_sha256": (
                "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"),
            "identity_match": "exact",
            "meta_best_miou": 0.5024607,
            "host": "server-6",
            "gpu": 7,
            "admission": False,
        }
        existing = {e["path"] for e in candidate.get("evidence", [])}
        if RECEIPT not in existing:
            candidate["evidence"].append(
                {"path": RECEIPT, "sha256": receipt_hash})
        touched.append(candidate["id"])
    if set(touched) != TARGETS:
        raise ValueError("Target set mismatch: %s" % sorted(touched))
    work["next_action"] = NEXT
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("unblocked %d candidates; receipt=%s" % (len(touched), receipt_hash[:12]))


if __name__ == "__main__":
    main()
