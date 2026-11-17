"""Static evaluation contract; no native inference or new scientific admission."""
import hashlib
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AXES = ("capture_id", "scene", "ann_id", "expression_slot",
        "original_superpoint_ids", "sample_inverse")


def physical_join(left, right):
    for row in (left, right):
        if any(key not in row for key in AXES):
            raise ValueError("Missing physical support axes")
    if any(left[key] != right[key] for key in AXES):
        raise ValueError("Different capture or physical support")
    return True


def best_acceptable_rank(scores, ious):
    if not scores or len(scores) != len(ious):
        raise ValueError("Invalid query axes")
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    return next((rank for rank, i in enumerate(order, 1) if ious[i] > .5), None)


def scene_delta(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["scene"]].append(
            int(row["positive_success"]) - int(row["deployed_success"]))
    return sum(sum(v) / len(v) for v in groups.values()) / len(groups)


class Tests(unittest.TestCase):
    def test_all_acceptable_not_oracle_best(self):
        self.assertEqual(best_acceptable_rank([.9, .8, .1], [.6, .1, .99]), 1)

    def test_no_acceptable(self):
        self.assertIsNone(best_acceptable_rank([.9, .1], [.5, .1]))

    def test_tie_order_is_explicit(self):
        self.assertEqual(best_acceptable_rank([.9, .9], [.1, .8]), 2)

    def test_repeated_scenes_not_independent(self):
        rows = [{"scene": "a", "positive_success": True, "deployed_success": False}] * 9
        rows += [{"scene": "b", "positive_success": False, "deployed_success": False}]
        self.assertEqual(scene_delta(rows), .5)

    def test_text_id_is_not_physical_identity(self):
        with self.assertRaises(ValueError):
            physical_join({"scene": "a", "ann_id": 1}, {"scene": "a", "ann_id": 1})

    def test_reordered_support_rejected(self):
        row = dict(capture_id="x", scene="a", ann_id=1, expression_slot=0,
                   original_superpoint_ids=[4, 8], sample_inverse=[0, 1])
        self.assertTrue(physical_join(row, dict(row)))
        with self.assertRaises(ValueError):
            physical_join(row, dict(row, original_superpoint_ids=[8, 4]))

    def test_cross_capture_rejected(self):
        row = dict(capture_id="x", scene="a", ann_id=1, expression_slot=0,
                   original_superpoint_ids=[4, 8], sample_inverse=[0, 1])
        with self.assertRaises(ValueError):
            physical_join(row, dict(row, capture_id="y"))


def main():
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():
        raise SystemExit(1)
    paths = {
        "intervention": "pipeline/reports/positive_membership_intervention_20260916.json",
        "ownership": "pipeline/reports/ownership_path_contract_20260916.json",
        "instance": "pipeline/reports/instance_feature_separability_20260916.json",
        "membership": "pipeline/reports/matched_positive_composition_20260916.json",
        "modality": "pipeline/reports/modality_identity_claim_audit_20260916.json",
        "indexing": "pipeline/reports/modality_index_contract_20260916.json",
    }
    data = {k: json.loads((ROOT / p).read_text(encoding="utf-8")) for k, p in paths.items()}
    rows = data["intervention"]["rows"]
    delta = scene_delta(rows)
    assert abs(delta - data["intervention"]["summary"]
               ["paired_delta_positive_minus_deployed"]["scene_balanced"]) < 1e-12
    audits = {}
    for name, key in (("intervention", "rows"), ("ownership", "rows"),
                      ("instance", "rows"), ("membership", "per_expression")):
        items = data[name][key]
        audits[name] = {
            "rows": len(items),
            "missing_axes_counts": {axis: sum(axis not in r for r in items) for axis in AXES},
            "physical_join_ready": all(all(a in r for a in AXES) for r in items),
        }
    connected = [r for r in data["ownership"]["rows"] if r["distance_to_target"] is not None]
    assert len(connected) == 7
    report = {
        "scope": "Static archive and evaluation-contract tests only. No native capture.",
        "tests_passed": result.testsRun,
        "recomputed_intervention": {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "scene_balanced_delta": delta,
            "scene_balanced_deployed": data["intervention"]["summary"]["success"]
                ["deployed_success"]["scene_balanced"],
            "fixed": sum(r["positive_success"] and not r["deployed_success"] for r in rows),
            "broken": sum(r["deployed_success"] and not r["positive_success"] for r in rows),
        },
        "archive_support_audits": audits,
        "connected_control_ids": [
            {k: r[k] for k in ("scene", "ann_id", "node_id")} for r in connected],
        "instance_scene_counts": dict(Counter(r["scene"] for r in data["instance"]["rows"])),
        "modality_required_capture": data["modality"].get("required_single_capture"),
        "indexing_limitations": data["indexing"].get("limitations"),
        "interpretation": [
            "The exact scene-balanced baseline is .6875, not pooled .6910569.",
            "Keep pre-registered thresholds; report pooled and scene-balanced separately.",
            "All-acceptable rank is not the rank of the single highest-IoU query.",
            "These archives cannot certify a cross-capture physical join.",
            "Seven connected text controls are not seven bound physical interventions.",
            "Do not infer missing information in native data from missing archive fields.",
            "Pending native endpoint capture remains executable work, not an external blocker.",
        ],
        "sources": [{"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
                    for p in [*paths.values(), str(Path(__file__).relative_to(ROOT)).replace("\\", "/")]],
    }
    out = ROOT / "pipeline/reports/evaluation_contract_20260916-1310.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"tests": result.testsRun, "delta": delta, "audits": audits}))


if __name__ == "__main__":
    main()
