"""Persist one due resource observation without changing scientific dispositions."""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
TOKEN = "981f368ba8324479a86533a52f2ca5af"
IDS = [
    "m95-native-main-role-weight-precedence",
    "m95-native-relation-other-sign-conflict",
    "m95-native-secondary-positive-mass",
    "m95-native-between-pair-support",
]


def guard():
    owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) -
            datetime.now(timezone.utc)).total_seconds() > 180
    assert tick.digest(PROJECT / "pipeline/goal.json") == (
        "24083b8deaf464c78ad11ac83c00c573d637c0494935ee11e965327e8a2fda2e")
    assert tick.digest(PROJECT / "Cluster/scripts/validate_pdc_20261009.py") == (
        "00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26")


guard()
observation_path = BUNDLE / "resource_observation.json"
observation = tick.load(observation_path)
launch_path = PROJECT / (
    "pipeline/diagnostic_bundles/transport_port_75d7e1ea35634b1fa29749fcf54163c8/"
    "launch_guard_" + TOKEN + ".json")
launch = tick.load(launch_path)
assert launch["token"] == TOKEN and launch["returncode"] == 0
result = tick.load(observation_path)
import json
blocked = json.loads(launch["stdout"])
assert blocked["status"] == "BLOCKED" and blocked["gpu_launches"] == 0
assert result["compute"] == "2634704, 20016"
assert result["locks"]["/tmp/cluster_project_gpu0_m201_migration.lock"] == "held"


def ref(path):
    return {"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)}


references = [ref(observation_path), ref(launch_path)]
work_path = PROJECT / "pipeline/research_work.json"
before_hash = tick.digest(work_path)
work = tick.load(work_path)
retry = (datetime.now().astimezone() + timedelta(minutes=45)).isoformat()
condition = (
    "Fresh pinned server4/GPU0 observation with no NVML compute process and "
    ">=30000MiB idle-equivalent free memory; all original training/diagnostic "
    "flocks truly available. Do not reset GPU, delete locks, kill unknown "
    "owners or assume sudo."
)
for cid in IDS:
    matches = [candidate for candidate in work["candidates"] if candidate["id"] == cid]
    assert len(matches) == 1
    candidate = matches[0]
    assert candidate["stage"] == "blocked"
    assert candidate["blocker_kind"] == "gpu_context_or_lock_not_released"
    assert candidate["required_server"] == "server-4"
    if cid != IDS[-1]:
        assert all(not gate["passed"] for gate in candidate["gates"].values())
    for entry in references:
        assert entry not in candidate["evidence"], "Do not replay the same persistence"
        candidate["evidence"].append(entry)
    candidate.update(
        blocker=(
            "Fresh 2026-10-15T05:11:46+08 observation: GPU0 NVML PID2634704 "
            "uses20016MiB/free11994MiB, exact PID absent; original training "
            "flock held and kernel holder2634697 absent. Frozen guard refused; "
            "cause of residue unknown, no authorized safe cleanup."
        ),
        retry_after=retry, unblock_condition=condition,
        occupation_evidence=ref(observation_path),
        execution_status=(
            "Current981f: due frozen check-only BLOCKED and exact resource/lock "
            "audit unchanged.0GPU/native forwards/optimizer/recovery launches. "
            "Science and old failures unchanged; completed CPU preparations "
            "not repeated."
        ),
    )
    alternative = (
        "Current981f due retry: frozen current-token check-only refused; pinned "
        "GPU0 inventory and exact three flocks audited at05:11:46+08. Prior "
        "non-GPU preparations already complete, not rerun; no reset/signal."
    )
    candidate.setdefault("attempted_alternatives", []).append(alternative)

work["design_cycle"] = {
    "stop_reason": "external_resource_blocked",
    "attempted_ids": IDS,
    "evidence": references,
    "resume_condition": condition,
    "retry_after": retry,
    "scope": (
        "Due retry confirms the same real GPU-context/training-flock block. "
        "No newly independent scientific hypotheses or route exhaustion; "
        "no new admission, training or retrospective gate change."
    ),
}
guard()
assert tick.digest(work_path) == before_hash
tick.save(work_path, work)

memory_path = PROJECT / "pipeline/codex_memory.md"
text = memory_path.read_text(encoding="utf-8")
lines = text.splitlines()
assert lines.count("## Last Tick") == 1
index = lines.index("## Last Tick") + 1
assert lines[index].startswith("- Currentbedfd31f")
lines[index] = (
    "- Current981f368ba8324479a86533a52f2ca5af design05:09:55/"
    "deadline06:09:55+08immutable;due4/budget1/running0. Actual05:11:46 "
    "pinnedserver4/GPU0free11994/used20107/total32607MiB/util0;NVML2634704"
    "20016MiB/exactPIDabsent;trainingflockheld/kernelholder2634697absent,"
    "2diagnosticlocksavailable. Frozencheck-onlyBLOCKED/0GPU. Same4IDs"
    "/sixscalar-gatesfalse/oldFAILs/frozen75d7retained;2newhashedresource"
    "refs/sharedperID/45minretry=" + retry + ". No repeatedCPU/newcandidate"
    "/admission/optimizer/recovery. SameM201stopped_unknown/best"
    ".489848792552948@18/completed26/noimprove8;full642optimizer+scheduler"
    "CPUrestorePASScheckpointSHAf2f6fb53bd3a6388e1bf05e8d7c5099bacf94e5"
    "f81f06d4584d2a1707426d8df/sourcef8457d3b,seed1999/epochs50/max70/"
    "patience10/next27replay/NOmid-epochRNGbitwiseclaim. PriorbedfACTUAL"
    "finish0/PASS/COMPLETE/FINALIZED/lease+pendingabsent04:12:12;resource"
    "notrecheckedthen. Currentexternal_resource_blocked/notrouteexhaustion;"
    "postflightpendingatmemorywrite,actualreceipt/taskresultauthoritative."
    " Noreset/sudo/lockdeletion/foreignsignals/schedulerchange;userPDC"
    "SHAunchanged."
)
assert len(lines) < 120
guard()
memory_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"updated_ids": IDS, "new_shared_evidence": references,
                  "retry_after": retry, "memory_lines": len(lines),
                  "scientific_status": "blocked", "finish": "not yet called"}))
