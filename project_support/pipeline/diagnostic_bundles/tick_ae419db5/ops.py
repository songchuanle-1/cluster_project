"""Single-project foreground guard and lossless-reindexing audit registration."""
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
import yaml
ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
TOKEN = "ae419db58cbc4de4a44771efc6019a00"
THREAD = "01a04987-fdbe-7301-b2f0-f9b6ab60f74c"
GOAL = "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
CID = "hierarchy-native-superpoint-relabeling-audit"
SSH = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10"]

def now():
    return datetime.now(timezone.utc).isoformat()

def guard(seconds=0):
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > seconds
    assert tick.digest(ROOT / "pipeline/goal.json") == GOAL
    cfg = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    assert cfg["host"] == "192.168.1.115" and cfg["expected_hostname"] == "dl04-MS-7E06"
    assert cfg["allowed_gpus"] == [0, 1] and cfg["max_tasks_per_gpu"] == 1
    return owner, cfg

def evidence(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)}

def save(name, value):
    guard()
    path = OUT / name
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return path

def remote(code, timeout=120, conda=False):
    _, cfg = guard()
    code = "import socket\nassert socket.gethostname()=='dl04-MS-7E06'\n" + code
    command = shlex.join(["python" if conda else "/usr/bin/python3", "-B", "-c", code])
    if conda:
        command = shlex.join(["bash", "-lc", "source " + shlex.quote(cfg["conda_source"]) + " && conda activate " + shlex.quote(cfg["conda_env"]) + " && " + command])
    process = subprocess.run(["ssh", *SSH, cfg["user"] + "@" + cfg["host"], command], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    assert process.returncode == 0, process.stderr[-6000:]
    return json.loads(process.stdout)

def register():
    guard(600)
    source = ROOT / "Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/hier_postprocess.py"
    assert tick.digest(source) == "7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f"
    protocol = save("relabeling_protocol.json", {
        "preregistered_at": now(), "token": TOKEN, "candidate_id": CID, "goal_sha256": GOAL,
        "hypothesis": "Native multiscale partitioning should preserve physical point-group membership under lossless superpoint row relabeling after undoing the permutation. Recompute FPS/partitions rather than merely permuting fixed maps; distinguish changed cluster labels from changed physical co-membership.",
        "source": evidence(source),
        "matched_control": "Exact permutation-plus-inverse of physical coordinates/features/IDs; identity native partition replay; compare physical co-membership independent of arbitrary cluster label numbering. Source/seed evidence alone is not a final mask effect.",
        "first_test": "Audit the exact installed native FPS starting-index rule and a source-bound physical-row relabeling witness; capture outcome-blind native TRAIN geometry before requesting any CUDA. No reimplementation of the native FPS engine.",
        "cohort": "First four large TRAIN scenes from the prior frozen lexical census: scene0000_00,scene0001_00,scene0002_00,scene0003_00; unchanged native augmentation/seed1999. Geometry first, no VAL/test mechanism selection.",
        "distinction": "Not prior fixed-membership FLE rigid-transform audit, conditional message permutation, or batch-minimum cardinality intervention. This audit recomputes geometric hierarchy under equivalent physical row labels with unchanged support size.",
        "decision": "A changed first physical seed is only a source-level risk witness. Need native hierarchy co-membership/readback and fixed-query task controls before any point-feature deficit/admission claim; no model change, canonical-seed repair or training from an audit.",
        "limits": "Original1e-6 numerical gates, bans, data/seed/schedule and resource permissions unchanged. Do not reopen FLE/HDS/routing or label a numerical source observation an innovation.",
    })
    work = tick.load(ROOT / "pipeline/research_work.json")
    assert not any(row["id"] == CID for row in work["candidates"])
    work["candidates"].append({"id": CID, "stage": "diagnosis", "created_at": now(),
        "hypothesis": tick.load(protocol)["hypothesis"], "matched_control": tick.load(protocol)["matched_control"],
        "next_action": "Run the frozen source-bound FPS identity/relabeling witness and capture exact native TRAIN geometry; then execute the original native hierarchy permutation control only on a verified idle authorized GPU with exclusive locks.",
        "scientific_admission": False, "evidence": [evidence(protocol)]})
    guard()
    tick.save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({"registered": CID, "stage": "diagnosis", "protocol": evidence(protocol)}))

if __name__ == "__main__":
    register()
