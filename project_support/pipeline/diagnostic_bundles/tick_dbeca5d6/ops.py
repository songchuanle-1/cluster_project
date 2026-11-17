"""Current-lease cluster-only research helpers; no old tick token reuse."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

ROOT=Path("D:/project/cluster_project")
OUT=Path(__file__).resolve().parent
TOKEN="dbeca5d649a941c0bd7ed8b54e38dd08"
CID="fle-self-neighbor-content-separation"
NAME="model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1"
REMOTE_ROOT="/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b"
STAGE="/data/songcl/Project/Cluster_project/pipeline/fle_content_dbeca5d6"


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


def run(args,timeout=90,**kwargs):
    return subprocess.run(args,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout,**kwargs)


def ssh(program,host="192.168.1.115",timeout=90,python="/usr/bin/python3"):
    result=run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10","songcl@"+host,
        shlex.join([python,"-B","-c",program])],timeout)
    assert result.returncode==0,result.stderr
    return json.loads(result.stdout)


def register():
    owner=guard();work=tick.load(ROOT/"pipeline/research_work.json")
    assert not any(c["id"]==CID for c in work["candidates"])
    work["candidates"].append({"id":CID,"stage":"diagnosis","kind":"trained_point_path_diagnostic",
        "hypothesis":"At an outcome-blind time-selected frozen M203 last checkpoint, nonself fine-message spatial content affects final masks beyond the unchanged recipient-self term and matched nonself message norm. Positive task benefit is a separate uncertain readout,not presumed from graph activity.",
        "matched_control":"Decompose actual per-head fine output into exact self term plus nonself term; hold self unchanged and spatially permute only nonself terms within fine leaves with recipient norms preserved. Same captured native prefix/query/selection and ILA+decoder; identity/permutation/zero/tie controls before native use.",
        "next_action":"First verify decomposition/intervention on CPU analytic fixtures and the exact admitted FLE operator;freeze TRAIN cohort,checkpoint policy and native runner. Recheck both authorized slots before any CUDA;never share occupied slots or change ongoing training.",
        "evidence":[evidence(OUT/"diagnostic_prereg.md"),evidence(ROOT/"pipeline/diagnostic_bundles/tick_0571f421/native_result.json")],
        "preregistered_at":datetime.now(timezone.utc).isoformat(),"failure_scope":"inconclusive",
        "wake_paths":["pipeline/experiments/M203-FLE.json","pipeline/queue.json","SERVERS.yaml"]})
    guard();tick.save(ROOT/"pipeline/research_work.json",work)
    print(json.dumps({"registered":CID,"stage":"diagnosis","new_training_models":0,"admissions":0,"snapshot_at":owner["created_at"] if "created_at" in owner else None}))


if __name__=="__main__":register()
