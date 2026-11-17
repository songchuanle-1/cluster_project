"""Preserve the actual closure error before releasing the exact owned lease."""

import os
from pathlib import Path
import sys
import json

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

PROJECT = Path("D:/project/cluster_project")
PIPE = PROJECT / "pipeline"
TOKEN = "16d02ebf70a846bdad7f1c4f4d30b0c9"
owner = tick.load(PIPE / "headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
receipt = tick.load(PIPE / "tick_receipts" / (TOKEN + ".json"))
assert receipt["status"] == "INCOMPLETE" and receipt["closure_rc"] == 1
failure = PIPE / "reports" / ("postflight_failure_" + TOKEN + ".md")
work_path = PIPE / "research_work.json"
work = tick.load(work_path)
bps = next(item for item in work["candidates"] if item["id"] == "m95-native-between-pair-support")
for path in (failure, Path(__file__)):
    bps["evidence"].append({"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)})
bps["execution_status"] = "Current16d tick:242nativeforwards+CPUrank;all4stableIDsrealnewdiagnosticsevidence. Actualfinishexit1:Capacity gap remains with executable research:three scalar validation IDs. INCOMPLETE/ownedabortnext;no fake gates/stages/cooldown or deadlinewait;M201trainingcontinues."
tick.save(work_path, work)
notes_path = PIPE / "reports" / ("notes_" + TOKEN + ".json")
notes = tick.load(notes_path)
notes["actions"].append(
    "实际finish返回1：Capacity gap remains with executable research: m95-native-relation-other-sign-conflict,m95-native-main-role-weight-precedence,m95-native-secondary-positive-mass。四个候选新证据均通过哈希校验，但容量缺口/未完研究仍拒绝；执行INCOMPLETE，租约保留，精确abort及释放核实随后执行。"
)
notes["decisions"].append(
    "不重复同一finish失败，不把标量诊断完成冒充新结构准入；原始截止仍14:09:28，无资源阻塞/全路线耗尽/冷却声明。保留具体验收错误并abort；M201训练继续，实际释放/用量只在任务最终报告补充。"
)
tick.save(notes_path, notes)
report = tick.report("cluster_project", TOKEN, str(notes_path))
memory = (PIPE / "codex_memory.md").read_text(encoding="utf-8")
assert len(memory.splitlines()) < 120
for candidate in work["candidates"]:
    if candidate["id"] in (
        "m95-native-between-pair-support", "m95-native-relation-other-sign-conflict",
        "m95-native-main-role-weight-precedence", "m95-native-secondary-positive-mass",
    ):
        assert all(tick.digest(PROJECT / item["path"]) == item["sha256"] for item in candidate["evidence"])
assert tick.digest(PIPE / "headless/.tick_context.json") == owner["context_sha256"]
assert tick.digest(PIPE / "headless/.tick_context_state.next.json") == owner["pending_sha256"]
print(json.dumps({"evidence_checks": "PASS", "bps_evidence_count": len(bps["evidence"]),
                  "report": str(report), "memory_lines": len(memory.splitlines()),
                  "execution_status": "INCOMPLETE_before_abort"}))
