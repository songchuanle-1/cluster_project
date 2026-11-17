"""Run the fixed native-bank diagnostic inside the current foreground lease."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

TOKEN = "16d02ebf70a846bdad7f1c4f4d30b0c9"
PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
HOST = "songcl@100.64.3.28"
BASE = "/data3/songcl/Project/Cluster_project/pipeline/diagnostics"
REMOTE = BASE + "/bps_native_" + TOKEN
OLD = BASE + "/bps_population_f8bdf4cb21774bf2af11f959fa12d89a"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST]
owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() >= 720
assert not (BUNDLE / "bank_execution.json").exists(), "Do not replay a recorded attempt"
record = {"token": TOKEN, "started_at": datetime.now().astimezone().isoformat()}
try:
    setup = subprocess.run(SSH + ["mkdir", REMOTE + "/bank"], capture_output=True, text=True, timeout=30)
    setup.check_returncode()
    copied = subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
         str(BUNDLE / "query_bank_capture.py"), HOST + ":" + REMOTE + "/"],
        capture_output=True, text=True, timeout=30,
    )
    copied.check_returncode()
    result = subprocess.run(SSH + [
        "timeout", "--signal=TERM", "--kill-after=15s", "600",
        "/home/songcl/miniconda3/envs/project_cluster/bin/python", "-B",
        REMOTE + "/query_bank_capture.py", "--adapter", REMOTE + "/native_capture_v3.py",
        "--runner", OLD + "/native_capture.py",
        "--code-root", "/data3/songcl/Project/Cluster_project/Cluster",
        "--config", "configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml",
        "--checkpoint", OLD + "/checkpoint_snapshot.pth",
        "--source-manifest", OLD + "/source_manifest.json",
        "--population", OLD + "/result.json",
        "--output", REMOTE + "/bank/native_result.json", "--token", TOKEN,
    ], capture_output=True, text=True, encoding="utf-8", timeout=650)
    record.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
except BaseException as exc:
    record.update(returncode=None, error_type=type(exc).__name__, error=str(exc))
finally:
    assert tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")["token"] == TOKEN
    record["recorded_at"] = datetime.now().astimezone().isoformat()
    tick.save(BUNDLE / "bank_execution.json", record)
    pulls = {}
    for remote_name, local_name in (
        ("native_result.json", "bank_native_result.json"),
        ("bank_result.json", "bank_result.json"),
        ("adapter_audit.json", "bank_adapter_audit.json"),
    ):
        copied = subprocess.run(
            ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
             HOST + ":" + REMOTE + "/bank/" + remote_name, str(BUNDLE / local_name)],
            capture_output=True, text=True, timeout=30,
        )
        pulls[remote_name] = {"returncode": copied.returncode, "stderr": copied.stderr}
    tick.save(BUNDLE / "bank_pull.json", pulls)
    print(json.dumps({"execution": record, "pulls": pulls}, indent=2))
