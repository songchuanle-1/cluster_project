"""Persist bounded saved-geometry diagnosis for three existing work IDs."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_nearest_provenance_20260923-1211.json"
DECISION = "pipeline/decisions/20260923-121212_route_change.md"
IDS = (
    "referent-supervision-axis",
    "referent-discrimination",
    "instance-identity-representation",
)
NEXT = {
    IDS[0]: (
        "Nearest-GT cause cannot be replayed from frozen capture. Specify a distinct "
        "referent supervision unit and matched native-positive/objectness controls; "
        "do not infer mislabeled positives or admit a loss before native backward "
        "and resource/independence gates."
    ),
    IDS[1]: (
        "Preserve target26/peer5/outside-registered-peers1 physical strata. "
        "Seek independent coordinate/cause evidence only for a falsifiable "
        "discrimination mechanism; do not add a selector from the six unattributed cases."
    ),
    IDS[2]: (
        "Saved mask logits differ in all 32 discordant classes. Specify an independently "
        "captured query-state and matched-control test before claiming representation "
        "collapse; no new capture from binary-mask equivalence alone."
    ),
}


def ref(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
    work_path = ROOT / "pipeline/research_work.json"
    work = json.loads(work_path.read_text(encoding="utf-8"))
    assert context["mode"] == "event"
    assert set(context["research_work"]["due_ids"]) == set(IDS)
    assert report["discordant_class_ids_with_positive_outside_target_seed"] == [0, 11, 23, 65, 79, 253]
    assert report["acceptable_class_ids"] == [0, 23, 65]
    assert not report["admission"] and not report["queue_mutation"]
    assert report["source_provenance_sha256"] == ref(report["source_provenance_report"])["sha256"]
    assert report["source_criterion_sha256"] == ref(report["source_criterion"])["sha256"]
    now = datetime.now().astimezone().isoformat()
    refs = [ref(p) for p in (REPORT, DECISION, "scripts/native_manifest_capture_20260922.py", __file__)]
    assert {c["id"] for c in work["candidates"] if c["id"] in IDS} == set(IDS)
    for candidate in work["candidates"]:
        if candidate["id"] not in IDS:
            continue
        candidate["stage"] = "diagnosis"
        candidate["next_action"] = NEXT[candidate["id"]]
        candidate["blocker"] = candidate["retry_after"] = candidate["unblock_condition"] = None
        candidate["nearest_provenance_completed_20260923"] = {
            "timestamp": now,
            "report": ref(REPORT),
            "decision": ref(DECISION),
            "exact_replay_possible": False,
            "admission": False,
        }
        known = {item["path"]: item["sha256"] for item in candidate["evidence"]}
        for item in refs:
            if item["path"] in known:
                assert known[item["path"]] == item["sha256"]
            else:
                candidate["evidence"].append(item)
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = (
        "Three diagnosis IDs retain distinct mechanism/control gates; saved capture "
        "cannot attribute six outside-seed positives to nearest-GT matching."
    )
    temporary = work_path.with_suffix(".nearest.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temporary.replace(work_path)
    print(json.dumps({"report": ref(REPORT), "decision": ref(DECISION),
                      "stages": dict.fromkeys(IDS, "diagnosis")}))


if __name__ == "__main__":
    main()
