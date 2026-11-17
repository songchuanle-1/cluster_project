"""Keep the actual queue-versus-live-occupation mismatch before safe abort."""
from datetime import datetime, timezone
import os
from pathlib import Path
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
TOKEN = "d7dee0a18225465284ff88f668cfc050"
owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
receipt = tick.load(ROOT / "pipeline/tick_receipts" / (TOKEN + ".json"))
assert receipt["status"] == "INCOMPLETE" and receipt["closure_rc"] == 1
assert receipt["context_committed"] is False and receipt["lease_release"] == "retained"
failure = {"recorded_at": datetime.now(timezone.utc).isoformat(), "token": TOKEN,
           "finish_returncode": 1,
           "actual_stdout": ["CLOSURE_INCOMPLETE: Blocked GPU candidate has a queue opening",
                             "POSTFLIGHT FAILED: lease retained; continue this tick or explicitly abort"],
           "actual_resource_evidence": "resources_d7dee0a1.json",
           "cause": "Preferred server3 has no managed queue task but live NVML PID1453 occupies GPU1. Existing exclusive_gpu_slot_available/validate_work only considers managed queue opening; it rejects this real externally occupied slot.",
           "scientific_status": "CPU13controls PASS; native equivalence UNRUN; SAME M202 remains training with verified step growth",
           "decision": "Do not falsify queue, required_server, blocker_kind, deadline, science gates or shared checker. No equivalent repeated finish. Preserve evidence and original blockers, then abort this exact owned lease.",
           "next_native_test_guard": "Reverify live authorized idle GPU and all lifetime locks/asset hashes; only launch the frozen300second diagnostic when at least360seconds remain in its newly acquired foreground lease.",
           "executed_gpu_diagnostics": 0, "model_revisions": 0, "new_training_launches": 0}
path = OUT / "postflight_mismatch_d7dee0a1.json"
tick.save(path, failure)
work = tick.load(ROOT / "pipeline/research_work.json")
candidate = next(c for c in work["candidates"] if c["id"] == "m202-paired-native-evidence-producer")
assert candidate["stage"] == "blocked" and candidate["blocker_kind"] == "exclusive_gpu_slot"
candidate["evidence"].append({"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)})
candidate["execution_status"] = "INCOMPLETE: actual finish rejected queue opening despite real NVML occupation; CPU13controls PASS/native UNRUN. Preserve honest resource block; abort owned lease without interrupting SAME M202."
tick.save(ROOT / "pipeline/research_work.json", work)
notes_path = OUT / "notes_d7dee0a1.json"
notes = tick.load(notes_path)
notes["actions"].append("实际finish返回1：Blocked GPU candidate has a queue opening；校验仅看项目队列空位，未接受server3实时外部占用。收据INCOMPLETE、context未提交、当时租约仍保留。本轮不得称完成；失败输出及资源证据已留档，不重复相同finish，随后以本轮原令牌abort并核实释放。")
notes["decisions"].append("本轮执行结果为未完成，不是模型或13项CPU测试失败；原生等价性仍未执行。保留真实required_server=server-3/exclusive_gpu_slot，不把外部GPU任务登记为本项目任务，也不修改共享校验器或放宽科学准入。后续GPU空闲时续做同一诊断，冻结300秒runner至少预留360秒新租约时间。")
tick.save(notes_path, notes)
memory_path = ROOT / "pipeline/codex_memory.md"
memory = memory_path.read_text(encoding="utf-8")
memory = memory.replace("Execution recorded BEFORE postflight; require actual finish PASS and absent matching lease,otherwise preserve evidence/abort and report incomplete.",
    "Actual finish returned1: Blocked GPU candidate has a queue opening. Receipt INCOMPLETE/context not committed/lease retained at validation. Honest live external occupation is not accepted by queue-only validator; preserve evidence and abort owned token,verify release. This tick is NOT complete.")
memory += "- Actual postflight mismatch evidence: pipeline/diagnostic_bundles/evidence_producer_86290288/postflight_mismatch_d7dee0a1.json. No repeated unchanged finish/shared-checker patch. Native300second runner requires at least360seconds in a fresh lease before launch.\n"
assert len(memory.splitlines()) < 120
memory_path.write_text(memory, encoding="utf-8")
print("Actual INCOMPLETE disposition preserved; abort and lease-release verification remain required.")
