from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
import sys

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
BUNDLE = P / "manual_ops/20261104_gpu0_overlay/nec_overlay_prepare"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


EXPECTED = load(HERE / "owner_binding.json")


def guard():
    owner = load(P / "headless/.foreground.lockdir/owner.json")
    assert {k: owner.get(k) for k in EXPECTED} == EXPECTED
    assert os.environ["CODEX_THREAD_ID"] == EXPECTED["thread_id"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED["deadline_at"])
    assert sha(P / "headless/.tick_context.json") == EXPECTED["context_sha256"]
    assert sha(P / "headless/.tick_context_state.next.json") == EXPECTED["pending_sha256"]


def save_new(path, value):
    guard()
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    guard()
    peer_path = BUNDLE / "independent_review.json"
    peer = load(peer_path)
    assert peer.get("passed") is True, "Independent port review must pass before release"
    summary = load(BUNDLE / "preparation.json")
    assert summary["owner"] == EXPECTED
    for name, wanted in summary["new_files"].items():
        assert sha(BUNDLE / name) == wanted, name
    native = BUNDLE / "native/preparation.json"
    operation = BUNDLE / "operational/preparation.json"
    template = BUNDLE / "operational/release_template.json"
    release = BUNDLE / "operational/adapter_release.json"
    assert not release.exists()
    assert load(native)["source_commit"] == "6bc36adfe42764aac2209e6600fb3a783e2fa374"
    assert load(native)["runtime_expected_commit"] == "94c4fe61b38f46f321a7ee84236fea70ade04d9b"
    sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        work_path = P / "research_work.json"
        before = load(work_path)
        work = copy.deepcopy(before)
        candidate = next(c for c in work["candidates"]
                         if c["id"] == "hierarchy-coupled-node-edge-state-composition")
        assert candidate["stage"] == "validation" and candidate["native_status"] == "NOT_RUN"
        assert candidate["resource_status"] == "NOT_RUN"
        now = datetime.now(timezone.utc).isoformat()
        candidate.setdefault("execution_preparation_history", []).append(dict(
            recorded_at=now, worker_preparation=copy.deepcopy(candidate["worker_preparation"]),
            execution_adapter=copy.deepcopy(candidate["execution_adapter"]),
            resource_authorization=copy.deepcopy(candidate["resource_authorization"]),
            native_execution_blocker=copy.deepcopy(candidate.get("native_execution_blocker")),
            scope="Original exclusive packets and failed intent preserved; separately reviewed explicit GPU0 overlay/runtime94 packet supersedes only future resource execution metadata."))
        with release.open("xb") as stream:
            stream.write(template.read_bytes())
        assert release.read_bytes() == template.read_bytes()
        candidate["worker_preparation"] = dict(
            status="REVIEWED_GPU0_OVERLAY_RUNTIME94_PACKET_NATIVE_NOT_RUN",
            preparation=ref(native), independent_review=ref(peer_path),
            original_worker_unchanged=True, native_backward_executed=False,
            resource_profile_executed=False, native_backward_passed=None,
            resources_passed=None, active_native_manifest_or_execution_lease_created=False)
        candidate["execution_adapter"] = dict(
            status="REVIEWED_GPU0_OVERLAY_RUNTIME94_RELEASE_NO_BINDING_YET",
            preparation=ref(operation), release=ref(release),
            independent_review=ref(peer_path), live_allowed_gpus=[0],
            selected_native_capability=[0], source_parent_commit=candidate["source_parent_commit"],
            runtime_expected_commit="94c4fe61b38f46f321a7ee84236fea70ade04d9b",
            active_binding_manifest_lease_created=False, transport_executed=False,
            native_execution_tested=False, remote_adapter_execution_tested=False,
            standard_summaries_created=False)
        candidate["resource_authorization"] = ref(P / "authorizations/server4_gpu0_overlay_20261104.json")
        candidate["required_physical_gpu"] = 0
        candidate.pop("native_execution_blocker", None)
        candidate["next_action"] = (
            "Execute reviewed fresh-owner explicitly authorized GPU0 overlay/runtime94 prepare, stage and original paired natural TRAIN2/resources "
            "while the unchanged actual owner deadline permits. Source6bc and local/source-parent4457 remain separate. "
            "No activation replay; actual PASS plus independent result review is required before admission and dispatch.")
        candidate["evidence"].extend([ref(BUNDLE / "preparation.json"), ref(peer_path),
                                      ref(native), ref(operation), ref(release)])
        work["updated_at"] = now
        save_new(HERE / "nec_overlay_packet_registration_intent.json", dict(
            owner=EXPECTED, recorded_at=now, before_candidate=next(
                c for c in before["candidates"] if c["id"] == candidate["id"]),
            before_work_sha256=sha(work_path), release=ref(release), review=ref(peer_path),
            native_or_resources="NOT_RUN"))
        assert load(work_path) == before
        temp = work_path.with_name("research_work.692e522c_nec.tmp")
        with temp.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(work, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        guard()
        os.replace(temp, work_path)
        save_new(HERE / "nec_overlay_packet_registration_result.json", dict(
            owner=EXPECTED, recorded_at=now, work=ref(work_path), release=ref(release),
            peer=ref(peer_path), all_other_candidates_unchanged=True,
            native_or_resources="NOT_RUN"))
        print(json.dumps(dict(status="REVIEWED_PACKET_REGISTERED_NO_EXECUTION",
                              release=ref(release)), ensure_ascii=False))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
