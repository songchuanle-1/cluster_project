"""Independent bounded current-owner helper review; no real result normalization."""
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
from contextlib import redirect_stdout
import ast
import hashlib
import importlib.util
import io
import json
import os
import runpy
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
TICK = Path(__file__).resolve().parent
OLD = TICK.parent / "tick_eb827823"
KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
CHECKS = []
EXPECTED = {
    "nsd_result_prepare": "ffe2f9a3e3a6122ae037be44711fa5f7397ef82eabc7dceb7e4cd66e921ea8a6",
    "nsd_path_production_prepare": "e7c6a8c55730dfdcf1cb5d3fd35f041f2ebbc445c76a0bee97b01691bfa2549d",
    "nsd_path_production_transport": "3f71abfc5d2222d52a161eeb81c13363f3bf5f32edfd27792145b6ff2653c5ec",
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def ref(p): return {"path": Path(p).relative_to(ROOT).as_posix(), "sha256": sha(p)}
def check(n, value):
    CHECKS.append({"name": n, "passed": bool(value)})
    assert value, n
def forbidden(*a, **k): raise AssertionError("SSH/process/model execution forbidden")
def import_file(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
def literal(p, name):
    for n in ast.parse(p.read_text(encoding="utf-8")).body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return ast.literal_eval(n.value)
    raise KeyError(name)
def refuses(n, operation):
    try:
        operation()
    except (AssertionError, ValueError):
        check(n, True)
    else:
        check(n, False)


def main():
    check("actual_reviewer_child", os.environ.get("CODEX_THREAD_ID") == "01a1a5a9-7056-7c92-bc3b-ca205451add4")
    check("bytecode_disabled", sys.dont_write_bytecode and os.environ.get("PYTHONDONTWRITEBYTECODE") == "1")
    original_owner = read(OLD / "nsd_current_activation/current_binding.json")["owner"]
    raw_owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {k: raw_owner[k] for k in KEYS}
    check("current_root_owner_exact", owner["token"] == "f74f3603193a426097a8dc288fd05fde"
          and owner["thread_id"] == "01a159c5-29ab-7a22-ba7f-e79174757253")
    check("current_context_pending_hashes", sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
          and sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"])
    def port(text):
        for k in KEYS:
            if original_owner[k] != owner[k]:
                text = text.replace(original_owner[k], owner[k])
        return text.replace("eb827823", "f74f3603")
    for name, expected in EXPECTED.items():
        folder = TICK / name
        frozen = read(folder / "FROZEN.json")
        check(name + "_exact_FROZEN_anchor", sha(folder / "FROZEN.json") == expected)
        check(name + "_current_owner_provenance", frozen["owner_provenance_only"] == owner)
        check(name + "_author_distinct_stopped", frozen["author_thread_id"] != os.environ["CODEX_THREAD_ID"]
              and frozen["author_will_not_write_further"] is True)
        check(name + "_complete_frozen_graph", all(sha(folder / n) == h for n, h in frozen["files"].items()))
        producer = frozen["producer_FROZEN"]
        producer_path = ROOT / producer["path"]
        check(name + "_producer_frozen_graph", sha(producer_path) == producer["sha256"] and all(
            sha(producer_path.parent / n) == h for n, h in read(producer_path).get("files", read(producer_path).get("files_sha256", {})).items()))
        review = frozen["producer_review"]
        review_path = ROOT / review["path"]
        check(name + "_prior_independent_review_PASS", sha(review_path) == review["sha256"] and read(review_path)["passed"] is True)
        check(name + "_no_real_native_or_resource_claim", frozen["native"] == frozen["resources"] == "NOT_RUN"
              and frozen["actual_execution_material_created"] is False)
        for p in folder.glob("*.py"):
            compile(p.read_bytes(), str(p), "exec")
        check(name + "_Python_compiles_without_importing_models", True)
    normalizer = TICK / "nsd_result_prepare/normalize_nsd_actual_results.py"
    controller = TICK / "nsd_path_production_prepare/production_controller.py"
    transport = TICK / "nsd_path_production_transport/run_controller_once.py"
    check("normalizer_entire_algorithm_byte_exact_after_two_metadata_ports",
          normalizer.read_text(encoding="utf-8") == port((OLD / "nsd_result_prepare/normalize_nsd_actual_results.py").read_text(encoding="utf-8")))
    check("controller_entire_algorithm_byte_exact_after_owner_path_ports",
          controller.read_text(encoding="utf-8") == port((OLD / "nsd_path_production_prepare/production_controller.py").read_text(encoding="utf-8")))
    prior_packet_sha = sha(OLD / "nsd_path_production_prepare/FROZEN.json")
    check("transport_entire_algorithm_byte_exact_after_owner_path_and_FROZEN_ports",
          transport.read_text(encoding="utf-8") == port((OLD / "nsd_path_production_transport/run_controller_once.py").read_text(encoding="utf-8")).replace(prior_packet_sha, EXPECTED["nsd_path_production_prepare"]))
    for n in ("lock_core.py", "entry_factory.py"):
        check(n + "_proved_core_byte_exact", (controller.parent / n).read_bytes() == (OLD / "nsd_path_production_prepare" / n).read_bytes())
    check("controller_owner_six_fields_literal_exact", literal(controller, "EXPECTED_OWNER") == owner)
    check("transport_owner_six_fields_literal_exact", literal(transport, "EXPECTED_OWNER") == owner)
    check("transport_disabled_REVIEW_SHA_NULL", literal(transport, "DRAFT_EXECUTION_DISABLED") is True and literal(transport, "REVIEW_SHA") is None)
    check("transport_controller_FROZEN_anchor_exact", literal(transport, "FROZEN_SHA") == EXPECTED["nsd_path_production_prepare"])
    for name in ("collect_request.draft.json", "render_request.draft.json", "activation_receipt.draft.json"):
        p = controller.parent / name
        prior = json.loads(port((OLD / "nsd_path_production_prepare" / name).read_text(encoding="utf-8")))
        if "files" in prior:
            prior["files"]["production_controller.py"] = sha(controller)
        check(name + "_only_approved_owner_path_controller_hash_changes", read(p) == prior)
        check(name + "_current_owner", read(p)["owner"] == owner)
    production_prep = read(controller.parent / "preparation.json")
    check("production_source9_and_proof_unchanged",
          production_prep["source_files_exact9"] == read(OLD / "nsd_path_production_prepare/preparation.json")["source_files_exact9"]
          and production_prep["source_proof"] == read(OLD / "nsd_path_production_prepare/preparation.json")["source_proof"])
    nprep = read(normalizer.parent / "preparation.json")
    check("normalizer_current_native_preparation_anchor", nprep["owner"] == owner
          and sha(ROOT / nprep["current_native_preparation"]["path"]) == nprep["current_native_preparation"]["sha256"]
          == "1561c98a81d8a0ba07bc769bd51c939c7c54a5c7eed5bf2d8cc921d5ed22be31")
    with patch.object(subprocess, "run", forbidden), patch.object(subprocess, "Popen", forbidden), patch.object(subprocess, "check_output", forbidden):
        n = import_file("independent_current_NSD_normalizer", normalizer)
        check("normalizer_literal_identity_source_runtime_current_tick", n.TOKEN == owner["token"]
              and n.CID == "hierarchy-native-spatial-dirichlet-composition"
              and n.SOURCE == "f6257de79148581334ee495e6e2d60ccb525457c"
              and n.PARENT == "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
              and n.TICK == TICK and n.NATIVE == TICK / "nsd_current_activation/native")
        check("normalizer_original_four_arms", n.PAIRS == (("smoke", "champion"), ("smoke", "candidate"), ("resources", "champion"), ("resources", "candidate")))
        refuses("actual_child_normalizer_guard_refuses_without_spoof", n.guard)
        for mode, target in n.PAIRS:
            fixture = {"candidate_id": "hierarchy-native-spatial-dirichlet-composition", "code_commit": n.SOURCE,
                "experiment_id": "M232-NSD", "goal_sha256": n.GOAL, "mode": mode, "target": target,
                "config": "configs/Quard/ctf_hcg_csort_nsd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd.yaml",
                "model_package": "framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort" + ("_nsd" if target == "candidate" else "")}
            n.validate_external_arm_identity(fixture, mode, target)
            check("synthetic_external_NSD_identity_accept_" + mode + "_" + target, True)
            refuses("synthetic_PSC_identity_reject_" + mode + "_" + target,
                    lambda f=fixture, m=mode, t=target: n.validate_external_arm_identity({**f, "candidate_id": "hierarchy-native-position-feature-cross-scatter-composition"}, m, t))
        tr = import_file("independent_current_NSD_transport", transport)
        refuses("actual_disabled_transport_guard_refuses_before_any_IO", tr.guard)
        with patch.object(sys, "argv", [str(transport)]), redirect_stdout(io.StringIO()) as output:
            runpy.run_path(str(transport), run_name="__main__")
        check("actual_transport_default_NOP", "DEFAULT_NOP" in json.loads(output.getvalue())["status"])
    check("no_Torch_or_model_import", "torch" not in sys.modules)
    check("no_actual_normalization_output", not n.OUTPUT.exists() and not list(normalizer.parent.glob("results_*")))
    count_record = read(transport.parent / "software_validation.json")
    check("author_transport_count_discrepancy_harmless_all_entries_pass", count_record["check_count"] == 40
          and len(count_record["checks"]) == 41 and all(x["passed"] is True for x in count_record["checks"]))
    check("reviewed_freezes_unchanged_after_tests", all(sha(TICK / name / "FROZEN.json") == h for name, h in EXPECTED.items()))
    result = {"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": "INDEPENDENT_CURRENT_OWNER_HELPERS_SOFTWARE_REVIEW_PASS_ONLY",
        "passed": True, "reviewer_thread_id": os.environ["CODEX_THREAD_ID"], "owner": owner,
        "check_count": len(CHECKS), "checks": CHECKS,
        "frozen_inputs": [ref(TICK / n / "FROZEN.json") for n in EXPECTED],
        "scope": "Fresh metadata/identity/hash graph review only. Exact original algorithms and proved cores reused with prior independent reviews; no old mechanism/CPU suites rerun.",
        "nonblocking_observations": [{"path": ref(transport.parent / "software_validation.json"),
            "declared_check_count": 40, "actual_listed_check_count": 41,
            "interpretation": "Stale summary count only; 41 listed successful software checks. Frozen record preserved, not silently corrected."}],
        "native": "NOT_RUN", "resources": "NOT_RUN", "actual_results_normalized": False,
        "production_transport_still_disabled_REVIEW_SHA_NULL": True,
        "real_collect_render_install_or_training_launch": False,
        "no_automatic_root_release_or_activation_granted": True,
        "root_guard_spoofed": False, "GPU_SSH_model_execution": False,
        "package_or_shared_ledger_modified": False}
    p = TICK / "nsd_helpers_independent_review.json"
    with p.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({"review": ref(p), "passed": True, "check_count": len(CHECKS)}))


if __name__ == "__main__":
    main()
