"""Current-lease checks and candidate-first registration for cluster only."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
os.environ.update(PROJECT_ROOT="D:/project",PYTHONDONTWRITEBYTECODE="1",PYTHONIOENCODING="utf-8")
sys.path.insert(0,"C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
ROOT=Path("D:/project/cluster_project")
OUT=Path(__file__).resolve().parent
PRIOR=ROOT/"pipeline/diagnostic_bundles/tick_796c44e9"
TOKEN="99e0a81316784725a58ea871e73d4e11"
CID="m202-train-content-bias-matched-audit"
STAGE="/data/songcl/Project/Cluster_project/pipeline/content_diag_99e0a813"

def guard():
    owner=tick.load(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"]==TOKEN and owner["thread_id"]==os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner["deadline_at"])
    assert tick.digest(ROOT/"pipeline/goal.json")=="42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec"
    return owner

def save(name,value):
    guard();tick.save(OUT/name,value)

def evidence(path):
    return {"path":path.relative_to(ROOT).as_posix(),"sha256":tick.digest(path)}

def run(args,timeout=90):
    return subprocess.run(args,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout)

def ssh(program,host="192.168.1.115",timeout=90):
    result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",
        "-o","ServerAliveInterval=10","-o","ServerAliveCountMax=3","songcl@"+host,
        shlex.join(["/usr/bin/python3","-B","-c",program])],timeout)
    assert result.returncode==0,result.stderr
    return json.loads(result.stdout)

def register():
    guard()
    work=tick.load(ROOT/"pipeline/research_work.json")
    assert not any(c["id"]==CID for c in work["candidates"])
    candidate={"id":CID,"stage":"diagnosis","kind":"TRAIN_mechanistic_diagnostic",
        "hypothesis":"On8scene-disjoint outcome-blind TRAIN scenes, the native aligned point message improves mean fixed-normal-query point IoU compared with a spatially permuted message preserving each recipient superpoint norm. Nonpositive mean refutes only this local premise.",
        "matched_control":"Same captured prefix/query/selection/native ILA+decoder; original bias-retained empty and true-zero controls separate; cyclic point permutation with matched recipient norm, strict native1e-6.",
        "next_action":"Run source/cohort and four CPU fixture controls, freeze8outcome-blind disjoint TRAIN scenes/full identities, then execute8native captures/32suffixes only on live idle authorized GPU under3locks; preserve all failures.",
        "evidence":[evidence(OUT/"content_prereg.md"),evidence(PRIOR/"scale_analysis.json")],
        "preregistered_at":datetime.now(timezone.utc).isoformat(),"failure_scope":"inconclusive"}
    work["candidates"].append(candidate)
    guard();tick.save(ROOT/"pipeline/research_work.json",work)
    print(json.dumps({"registered":CID,"stage":"diagnosis","admissions":0,"training_launches":0}))

if __name__=="__main__":register()
