"""Execute archive availability and scene sensitivity checks without a GPU."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import unittest


def main():
    root = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(
        str(root / "scripts"), pattern="test_physical_mask_endpoints_20260916.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    source = root / "pipeline/reports/native_support_capture_20260916-1517.json"
    capture = json.loads(source.read_text(encoding="utf-8"))
    scenes = defaultdict(list)
    for row in capture["rows"]:
        n = len(row["scores"])
        assert n == len(row["ious"]) == len(row["seed_inside"]) == len(row["native_positive"])
        scenes[row["scene"]].append(row)
    rates = {}
    for scene, rows in scenes.items():
        rates[scene] = dict(
            expressions=len(rows),
            selected_success=sum(r["ious"][r["selected_query"]] > .5 for r in rows) / len(rows),
            recoverable_failure=sum(r["ious"][r["selected_query"]] <= .5
                                    and max(r["ious"]) > .5 for r in rows) / len(rows))
    leave_one_out = {
        excluded: sum(v["selected_success"] for scene, v in rates.items() if scene != excluded)
        / (len(rates) - 1) for excluded in rates}
    missing = {
        key: sum(key not in row for row in capture["rows"])
        for key in ("selected_mask", "semantic_labels", "selected_mask_endpoints")}
    report = dict(
        scope="Executed static physical endpoint adapter tests and archived scene sensitivity",
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        tests_run=result.testsRun, tests_passed=result.testsRun,
        scene_rates=rates, leave_one_scene_out_selected_success=leave_one_out,
        missing_fields=missing,
        stratum_contract="oracle superpoint IoU > .5; selected <= .5; unique wrong physical endpoint; known same semantic class",
        limitations=[
            "Adapter is not integrated or executed in native capture.",
            "No same-class membership can be established from this archive.",
            "Delete-one scene sensitivity is not a confidence interval.",
            "Four-scene smoke sample is not the predefined expanded sample.",
            "No seven-control binding, terminal PIRS evaluation, or efficacy claim."],
        next_action="Integrate adapter in a new versioned native capture, bind native semantic labels to exact support, execute existing predefined TRAIN/control sample.")
    path = root / "pipeline/reports/endpoint_audit_20260916-1715.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
