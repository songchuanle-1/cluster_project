"""Read-only MIC project-slot precondition; never prepares or launches work."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "be02b2707ade4647ab24b262de525af2"
PACKET = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    output = HERE / "project_slot_precondition.json"
    assert not output.exists(), "Preserve the prior observation instead of replaying it."
    path = PACKET / "operational/adapter.py"
    packet = read(PACKET / "preparation.json")
    assert sha(path) == packet["new_files"]["operational/adapter.py"]
    assert packet["DRAFT_native"] and packet["DRAFT_operational"]
    assert packet["all10_active_fields_NULL"]
    protected = [
        ROOT / "pipeline/queue.json", ROOT / "pipeline/running.json",
        ROOT / "SERVERS.yaml", ROOT / "pipeline/goal.json",
        ROOT / "pipeline/closure_policy.json", path,
        PACKET / "native/manifest_template.json",
        PACKET / "preparation.json",
    ]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in protected}
    running = read(ROOT / "pipeline/running.json")
    assert running["server-4"]["0"] == "M228-NEC"
    spec = importlib.util.spec_from_file_location("mic_slot_check_only", path)
    adapter_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter_module)
    assert adapter_module.DRAFT_EXECUTION_DISABLED is True

    class NoTransport:
        calls = 0

        def __call__(self, *args, **kwargs):
            self.calls += 1
            raise AssertionError("Transport is forbidden for this local slot check.")

        def run(self, *args, **kwargs):
            return self(*args, **kwargs)

    transport = NoTransport()
    adapter = adapter_module.Adapter(transport=transport)
    try:
        adapter._local_idle(0)
    except adapter_module.Refused as error:
        refusal = str(error)
    else:
        raise AssertionError("Expected the registered NEC project slot to refuse MIC.")
    assert refusal == "Selected GPU has registered running task"
    assert transport.calls == 0
    assert {p.relative_to(ROOT).as_posix(): sha(p) for p in protected} == before
    assert not (PACKET / "operational/adapter_release.json").exists()
    assert not (HERE / "mic_execution").exists()
    evidence = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner": {k: owner[k] for k in (
            "token", "thread_id", "generated_at", "deadline_at",
            "context_sha256", "pending_sha256",
        )},
        "candidate_id": "hierarchy-ancestry-mobius-interaction-composition",
        "experiment_id": "M229-MIC",
        "kind": "resource_check",
        "result": "blocked",
        "actual_call": "reviewed MIC Adapter(transport=NoTransport)._local_idle(0)",
        "refusal": refusal,
        "blocking_task_id": "M228-NEC",
        "blocking_physical_gpu": 0,
        "max_project_tasks_per_gpu": 1,
        "external_overlay_still_authorized": True,
        "adapter": {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)},
        "command": f"python -B -X utf8 {Path(__file__).resolve()}",
        "transport_calls": 0,
        "physical_gpu_occupation_or_memory": "NOT_QUERIED",
        "native": "NOT_RUN",
        "resources": "NOT_RUN",
        "no_active_binding_manifest_lease_request_or_remote_stage": True,
        "protected_files_unchanged": before,
        "scope": "Current registered project-slot precondition only; not a physical-exclusive claim, GPU computation, native attempt or scientific rejection.",
    }
    output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "result": "blocked", "actual_refusal": refusal,
        "transport_calls": 0, "native": "NOT_RUN",
        "evidence": str(output), "sha256": sha(output),
    }))


if __name__ == "__main__":
    main()
