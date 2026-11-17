"""Persist hierarchical partition capture evidence without changing the queue."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = "pipeline/reports/hierarchical_partition_20260916-2310.json"
TEST_MODULES = [
    "test_model_pair_audit_20260916",
    "test_hierarchical_partition_contract_20260916",
    "test_sampling_pair_contract_20260916",
    "test_frozen_capture_contract_20260916",
    "test_paired_capture_evaluation_20260916",
    "test_native_endpoint_capture_20260916",
    "test_native_support_capture_20260916",
    "test_capture_support_20260916",
    "test_physical_mask_endpoints_20260916",
]
EVIDENCE_PATHS = [
    "scripts/hierarchical_partition_contract_20260916.py",
    "scripts/test_hierarchical_partition_contract_20260916.py",
    "scripts/native_support_capture_v2_20260916.py",
    "scripts/native_frozen_capture_20260916.py",
    "scripts/sampling_pair_contract_20260916.py",
    "scripts/test_sampling_pair_contract_20260916.py",
    "scripts/persist_hierarchical_partition_20260916.py",
]


def evidence(path):
    raw = (ROOT / path).read_bytes()
    return dict(path=path, sha256=hashlib.sha256(raw).hexdigest())


def merge_evidence(entries):
    merged = {}
    for entry in entries:
        merged[entry["path"]] = entry
    return list(merged.values())


def run_tests():
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(name)
        for name in TEST_MODULES)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    return result.testsRun


def main():
    tests_passed = run_tests()
    model_audit = json.loads(
        (ROOT / "pipeline/reports/model_pair_audit_20260916-2211.json")
        .read_text(encoding="utf-8"))
    configs = [
        "Cluster/configs/Quard/ctf_hcg_csort/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml",
        "Cluster/configs/Quard/pirs/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs.yaml",
    ]
    blocker = dict(
        blocker="GPU7 has two processes, PIRS1134192 and foreign3827570.",
        retry_after="2026-09-17T00:07:00+08:00",
        unblock_condition=(
            "Fewer than two GPU7 processes and sufficient measured free memory."),
        alternatives_attempted=(
            "Implemented and tested exact hierarchical partition capture and "
            "PIRS model/config binding; no native capture or training launched."))
    report = dict(
        scope="Static implementation and archived evidence only",
        tests_passed=tests_passed,
        new_tests_passed=11,
        native_execution_completed=False,
        scientific_validation_complete=False,
        capture_contract=dict(
            entry_fps_field="fps_superpoints",
            hierarchical_fps_field="hierarchical_fps_positions",
            hierarchical_cluster_field="hierarchical_cluster_ids",
            hierarchical_child_map_field="hierarchical_child_maps",
            partition_hash_field="hierarchical_partition_sha256",
            model_class_argument="--model-class",
            config_argument="--config",
            checkpoint_identity="checkpoint_sha256"),
        bound_models=[
            "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort",
            "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs",
        ],
        config_evidence=[evidence(path) for path in configs],
        model_source_audit=dict(
            report="pipeline/reports/model_pair_audit_20260916-2211.json",
            sha256=hashlib.sha256(
                (ROOT / "pipeline/reports/model_pair_audit_20260916-2211.json")
                .read_bytes()).hexdigest(),
            matcher_ast_equal=model_audit["matcher_ast_equal"],
            source_equal=model_audit["source_equal"]),
        remote_observation=dict(
            gpu=7,
            used_mib=62473,
            free_mib=18607,
            utilization_percent=100,
            pids=[1134192, 3827570],
            epoch=9,
            best_miou=0.4621,
            capture_launched=False),
        blocker=blocker,
        next_action=(
            "After terminal PIRS and a later capacity check with fewer than two "
            "GPU7 processes, capture the frozen TRAIN/control sample for both "
            "bound model classes. Require identical native input hashes and "
            "hierarchical partition hashes before strict scene-balanced pairing."),
        limitations=[
            "Source equality does not imply checkpoint or native-output equality.",
            "The external CUDA FPS kernel and runtime nondeterminism are not audited.",
            "No expanded semantic sample, terminal PIRS comparison or efficacy result.",
            "The static suite is not native validation or admission evidence."])
    report["evidence"] = [evidence(path) for path in EVIDENCE_PATHS]
    decision = ROOT / "pipeline/decisions/20260916-231350_other.md"
    if decision.is_file():
        report["evidence"].append(evidence(
            "pipeline/decisions/20260916-231350_other.md"))
    (ROOT / REPORT_PATH).write_text(
        json.dumps(report, indent=2) + "\n", encoding="ascii")

    context = json.loads(
        (ROOT / "pipeline/headless/.tick_context.json")
        .read_text(encoding="utf-8"))
    work_path = ROOT / "pipeline/research_work.json"
    work = json.loads(work_path.read_text(encoding="utf-8"))
    due = set(context["research_work"]["due_ids"])
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        additions = [evidence(path) for path in EVIDENCE_PATHS]
        additions.append(evidence(REPORT_PATH))
        if decision.is_file():
            additions.append(evidence(
                "pipeline/decisions/20260916-231350_other.md"))
        candidate["evidence"] = merge_evidence(
            candidate["evidence"] + additions)
        candidate["hierarchical_partition_progress"] = dict(
            report=REPORT_PATH,
            tests_passed=tests_passed,
            native_execution_completed=False,
            scientific_validation_complete=False,
            finding=(
                "Versioned capture now binds entry FPS, hierarchical FPS "
                "geometry, cluster IDs and child maps to exact model/config/"
                "checkpoint identity."))
        candidate["native_capture_blocker"] = blocker
        candidate["next_action"] = (
            "Await terminal PIRS; then retry GPU7 and execute the frozen "
            "TRAIN/control capture for both bound model classes with "
            "--model-class and explicit --config. Require identical native "
            "input and hierarchical partition hashes before strict "
            "scene-balanced paired evaluation; no learned-selection conditioning.")
    work_path.write_text(
        json.dumps(work, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii")
    print(json.dumps(dict(report=REPORT_PATH, tests=tests_passed,
                          changed_due=len(due))))


if __name__ == "__main__":
    main()
