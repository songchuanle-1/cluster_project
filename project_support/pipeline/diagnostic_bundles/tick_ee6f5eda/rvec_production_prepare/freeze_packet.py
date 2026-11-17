"""Default NOP. Pin genuine current read-only verification; no external action."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
OLD = ROOT / "pipeline/diagnostic_bundles/tick_558ef1ee/rvec_production_prepare"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if not args.freeze:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_GIT_TORCH_GPU_OR_MUTATION"}))
        return
    assert not (HERE / "FROZEN.json").exists(), "Never modify an existing frozen packet"
    owner = read(TICK / "current_owner_binding.json")
    actual_owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: actual_owner[key] for key in owner} == owner
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    path = TICK / "source_verify_execution/verify_actual.json"
    proof = read(path)
    assert proof["owner"] == owner and proof["passed"] is True and proof["certainty"] == "terminal"
    assert proof["kind"] == "CURRENT_READONLY_VERIFICATION_REUSE_OLD_SYNC_NOT_NEW_SYNC"
    source = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
    assert proof["source_commit"] == source and proof["runtime_code_commit"] == source
    assert proof["source_verified"] is True and proof["canonical_source_integrity_current"] is True
    assert proof["source_integrity_before_after"] is True and proof["new_sync_performed"] is False
    assert proof["Git_mutations"] is False and proof["training_started"] is False and proof["GPU_compute"] is False
    assert proof["main_index_user28_r0nine_preserved"] is True and proof["lifecycle_unchanged"] is True
    assert proof["old_558_stage_reconciled"] is True
    previous = read(OLD / "FROZEN.json")
    assert sha(OLD / "FROZEN.json") == "ba2efe4cfa45a5978f46a8c45ff6bf21591927dfc0a171b282512d968d6e0bb5"
    assert all(sha(OLD / name) == expected for name, expected in previous["files"].items())
    assert proof["historical_sync"]["owner"] == previous["owner"]
    assert proof["historical_sync"]["not_relabelled_current_owner"] is True
    for name in ("lock_core.py", "entry_factory.py", "source_resolver.py"):
        assert (HERE / name).read_bytes() == (OLD / name).read_bytes()
    verification_sha = sha(path)
    fields = {
        "controller_sha256": "production_controller.py", "transport_sha256": "run_setup_once.py",
        "resolver_sha256": "source_resolver.py", "dispatch_sha256": "dispatch_rvec_once.py",
        "switch_sha256": "switch_rvec_pointer.py", "guard_sha256": "packet_runtime.py"}
    contract = read(HERE / "independent_review_contract.json")
    contract.update(current_verification_sha256=verification_sha,
                    **{field: sha(HERE / name) for field, name in fields.items()})
    save(HERE / "independent_review_contract.json", contract)
    status = read(HERE / "PREPARATION_STATUS.json")
    status.update(status="FROZEN_PENDING_GENUINE_CURRENT_DELTA_PEER_AND_ROOT_SETUP",
                  current_verification_sha256=verification_sha,
                  current_verification_kind=proof["kind"], new_sync_performed=False)
    save(HERE / "PREPARATION_STATUS.json", status)
    anchors = dict(previous["anchors"])
    anchors.pop("current_preflight", None)
    new_paths = {
        "accepted_prior_packet": OLD / "FROZEN.json",
        "accepted_prior_source_review": OLD.parent / "operational_review/rve_production_source_independent_review.json",
        "historical_prior_CPU_collect": OLD.parent / "rvec_setup_execution/collect_actual.json",
        "historical_prior_CPU_review": OLD.parent / "operational_review/rvec_collect_actual_independent_review.json",
        "historical_actual_sync": OLD.parent / "rvec_deployment_execution/sync_result.json",
        "current_verification": path,
        "current_verification_packet": TICK / "source_verify_prepare/FROZEN.json",
        "current_verification_binding": TICK / "source_verify_prepare/owner_binding.json"}
    anchors.update({name: {"path": str(value), "sha256": sha(value)} for name, value in new_paths.items()})
    frozen = dict(previous)
    frozen.update(
        owner=owner, recorded_at=datetime.now(timezone.utc).isoformat(),
        producer_stage="/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prepare_ee6f5eda",
        production_stage="/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_ee6f5eda",
        current_verification_sha256=verification_sha, current_verification_kind=proof["kind"],
        historical_sync_owner_preserved=True, new_sync_performed=False,
        files={entry.name: sha(entry) for entry in sorted(HERE.iterdir())
               if entry.is_file() and entry.name != "FROZEN.json"},
        anchors=anchors, **{field: sha(HERE / name) for field, name in fields.items()},
        status="FROZEN_CURRENT_BINDING_PENDING_GENUINE_DELTA_PEER_AND_ROOT_SETUP",
        reuse_delta_sha256=sha(HERE / "reuse_delta.json"),
        source_delta_sha256=sha(HERE / "source_delta.diff"),
        actual_CPU_setup_render_switch_dispatch="PENDING_FRESH_CURRENT_ROOT_ACTIONS")
    save(HERE / "FROZEN.json", frozen)
    print(json.dumps({
        "FROZEN_sha256": sha(HERE / "FROZEN.json"),
        "current_verification_sha256": verification_sha,
        **{field: sha(HERE / name) for field, name in fields.items()},
        "source_commit": source, "new_sync_performed": False}))


if __name__ == "__main__":
    main()
