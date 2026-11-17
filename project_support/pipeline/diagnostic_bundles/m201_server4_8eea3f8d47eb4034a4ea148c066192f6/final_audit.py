"""Final migration observation and honest tick disposition, without relaunch."""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate as m

m.guard(120)
launch = m.tick.load(m.BUNDLE / "launch_retry.json")
result = json.loads(m.remote(m.TARGET, f"""
import datetime,json,os,pathlib,re,subprocess
pid={launch['pid']!r};p=pathlib.Path('/proc')/str(pid)
assert p.exists() and (p/'stat').read_text().split()[2]!='Z'
assert os.readlink(p/'cwd')=={m.ROOT!r}
args=(p/'cmdline').read_bytes().split(b'\\0')
assert {m.CONFIG.encode()!r} in args and b'--resume' in args
log=pathlib.Path({launch['log']!r})
with log.open('rb') as f:
    f.seek(max(0,log.stat().st_size-16000));text=f.read().decode(errors='replace')
assert 'Traceback (most recent call last)' not in text and 'CUDA out of memory' not in text
steps=re.findall(r'Train\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)
assert steps and int(steps[-1][0])==9 and int(steps[-1][2])>199
print(json.dumps({{'remote_time':datetime.datetime.now().astimezone().isoformat(),'pid':pid,
 'latest_step':steps[-1],'gpu':subprocess.check_output(['nvidia-smi','-i','0',
 '--query-gpu=uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
 'compute':subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory',
 '--format=csv,noheader,nounits'],text=True).strip(),'no_crash_in_bounded_tail':True}}))
""", timeout=20))
m.record("final_training_audit", result)
postflight = {
    "attempts": [
        {"result": "INCOMPLETE", "reason": "Artifact hash mismatch: D:/project/cluster_project/pipeline/goal.json"},
        {"result": "INCOMPLETE", "reason": "Artifact hash mismatch: D:/project/cluster_project/pipeline/goal.json",
         "note": "Archive reconstruction first failed; subsequent finish ran unintentionally after the failed shell stage; no claim of progress."},
        {"result": "INCOMPLETE", "reason": "Unfinished candidate made no durable progress",
         "repair_since_previous": "Old goal recovered byte-identically to preexisting SHA; only nine source-fact reference paths repaired."},
    ],
    "final_reason": "Unfinished candidate made no durable progress",
    "scope": "Explicit user migration prioritized; three due scalar IDs have no new diagnostic this tick. Native migration readiness is not their scientific progress. Training migration success and research tick INCOMPLETE are separate.",
}
m.record("postflight_attempts", postflight)
work_path = m.PROJECT / "pipeline/research_work.json"
work = m.tick.load(work_path)
candidate = next(c for c in work["candidates"] if c["id"] == "m95-native-between-pair-support")
for name in ("archive_goal_evidence.py", "historical_goal_archive.json", "final_audit.py",
             "final_training_audit.json", "postflight_attempts.json"):
    p = m.BUNDLE / name
    candidate["evidence"].append({"path": p.relative_to(m.PROJECT).as_posix(), "sha256": m.tick.digest(p)})
m.tick.save(work_path, work)
notes_path = m.PROJECT / "pipeline/reports" / ("notes_" + m.TOKEN + ".json")
notes = m.tick.load(notes_path)
notes["actions"].append(
    "旧goal因混合换行被编辑器正规化，首次原哈希复原失败；随后仅搜索约束行换行，精确命中原d7296cbb4cfc0742e92ccccc65a17b36513dcd8940c98c90e38801e79f14b21b并归档。九条旧源事实只换证据路径，旧hash/科学门槛/准入收据/当前goal保持；不是重建tick快照或新科学进展。"
)
notes["actions"].append(
    "实际finish仍exit1/INCOMPLETE：Unfinished candidate made no durable progress。三scalar本轮未测试，不能把迁移就绪伪装为诊断进展；不造假stage/blocked/cooldown、不修改快照或等待截止。训练迁移已验证，tick将按精确token abort保留证据并核实释放；释放结果及收据在任务报告补充。"
)
notes["actions"].append(
    "最终原生训练核验：" + result["remote_time"] + "，server4 GPU0/PID" + str(result["pid"]) +
    "，Train" + "/".join(result["latest_step"][:2]) + "步骤" + "/".join(result["latest_step"][2:]) +
    "；GPU实测 " + result["gpu"] + "，无新崩溃。"
)
m.tick.save(notes_path, notes)
print(json.dumps(result))
