"""Persist static work without rewriting queue or scientific admission."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def evidence(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def main():
    paths = ["scripts/capture_support_20260916.py",
             "scripts/test_capture_support_20260916.py",
             "pipeline/bugfixes/bugfix_20260916-1415.md",
             "pipeline/decisions/20260916-141228_other.md"]
    report = dict(
        scope="Static implementation/tests only; no native diagnostic capture",
        closure_tests_passed=16, capture_tests_passed=7,
        native_training_observation=dict(
            server="server-6", gpu=7, epoch=3, steps=[2401, 2407],
            utilization_percent=18, memory_mib=19955,
            provenance="Read-only SSH unique M197 log tail, 2026-09-16 14:10 +08:00"),
        limitations=["Feature hooks and native endpoint capture pending.",
                     "No scientific efficacy or admission from fixtures.",
                     "Terminal PIRS paired analysis pending."],
        evidence=[evidence(p) for p in paths])
    path = ROOT / "pipeline/reports/capture_support_20260916-1415.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    new = [evidence(p) for p in paths[:2]]
    new.append(evidence(path.relative_to(ROOT).as_posix()))
    actions = {
        "referent-causality-audit": "Await terminal PIRS for preregistered paired scenes; use adapter exact axes, not archive row joins. Baseline scene-balanced=.6875; oracle restriction is not relabeling efficacy.",
        "modality-identity-preservation": "Integrate CaptureDataset into serial native TRAIN loader; add raw/projected/fused/final hooks on identical support; run on server6GPU7 after occupancy check.",
        "referent-discrimination": "Connect bind_queries to criterion hook with native positive indices, seed containment and scores; execute same-forward capture with full axes.",
        "instance-identity-representation": "Use adapter support and instance_labels to bind physical endpoints; capture native same-class feature/rank contrasts without archive row joins.",
        "referent-query-selection": "Verify native deployment tie rule; connect all-acceptable rank to native query outputs and report no-acceptable separately.",
        "input-modality-distinguishability": "Capture paired 2D/3D vectors with adapter original IDs/inverse; extend physical_join to scene_occurrence/producer identity and test reordered vectors.",
        "same-target-description-grounding": "Bind seven connected control IDs to native adapter scene/annotation/support and actual instance_labels; retain12 disconnected controls. No binding claim from fixtures.",
        "same-forward-coverage-diagnosis": "Integrate adapter/bind_queries into native FPS/sample/mask capture with exact query axes; no repeat cluster audit or row-position join.",
    }
    work_path = ROOT / "pipeline/research_work.json"
    work = json.loads(work_path.read_text(encoding="utf-8"))
    for c in work["candidates"]:
        if c["id"] in actions:
            c["evidence"].extend(e for e in new if e not in c["evidence"])
            c["next_action"] = actions[c["id"]]
            c["capture_adapter_progress"] = dict(
                timestamp="2026-09-16T14:15:00+08:00",
                stage_completed="static support preservation and query binding tests",
                native_capture_completed=False, tests_passed=7)
    work_path.write_text(json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
