"""Persist bounded implementation evidence on the existing diagnosis IDs."""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = "pipeline/reports/m95_match_cause_capture_20260923-1711.md"
NEXT = {
    "referent-supervision-axis":
        "Derive an expression-level causal supervision unit and matched native-positive, objectness and listwise controls; native matcher cause remains unobserved.",
    "referent-discrimination":
        "When server-6 GPU7 is free, validate host/runtime/data/checkpoint and run the opt-in frozen-manifest native matcher-cause capture; check all 256 rows and six outside-seed cases.",
    "instance-identity-representation":
        "Independently capture query-state vectors for four same-physical-ID classes with exact-seed/coordinate and physical-identity controls and a predeclared rejection rule.",
}


def ref(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    decision = sys.argv[1]
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
    assert context["mode"] == "event" and not context["changes"]["new_terminal_ids"]
    assert set(context["research_work"]["due_ids"]) == set(NEXT)
    target = ROOT / "pipeline/research_work.json"
    work = json.loads(target.read_text(encoding="utf-8"))
    refs = [ref(p) for p in (
        REPORT, decision, "scripts/native_manifest_capture_20260922.py",
        "scripts/test_manifest_match_cause_20260923.py",
        "scripts/m95_match_cause_contract_20260923.py",
    )]
    now = datetime.now().astimezone().isoformat()
    found = set()
    for item in work["candidates"]:
        if item["id"] not in NEXT:
            continue
        assert item["stage"] == "diagnosis"
        found.add(item["id"])
        item["next_action"] = NEXT[item["id"]]
        item["match_capture_readiness_20260923"] = {
            "timestamp": now,
            "report": refs[0],
            "decision": refs[1],
            "synthetic_tests_passed": 9,
            "native_execution_completed": False,
            "admission": False,
        }
        known = {e["path"]: e["sha256"] for e in item["evidence"]}
        for evidence in refs:
            if evidence["path"] in known:
                if known[evidence["path"]] != evidence["sha256"]:
                    assert evidence["path"] == "scripts/native_manifest_capture_20260922.py"
                    item["match_capture_readiness_20260923"]["prior_producer_sha256"] = known[evidence["path"]]
                    for entry in item["evidence"]:
                        if entry["path"] == evidence["path"]:
                            entry["sha256"] = evidence["sha256"]
            else:
                item["evidence"].append(evidence)
    assert found == set(NEXT)
    producer = refs[2]
    for item in work["candidates"]:
        if item["id"] in NEXT:
            continue
        for evidence in item["evidence"]:
            if (evidence["path"] == producer["path"]
                    and evidence["sha256"] != producer["sha256"]):
                item.setdefault("superseded_producer_hashes_20260923", []).append(
                    evidence["sha256"]
                )
                evidence["sha256"] = producer["sha256"]
    work["updated_at"] = work["last_event_tick"] = now
    work["next_action"] = "Three diagnosis tracks open; native matcher cause and admission unverified."
    temp = target.with_suffix(".match_capture.tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    temp.replace(target)
    print(json.dumps({"report": refs[0], "decision": refs[1]}))


if __name__ == "__main__":
    main()
