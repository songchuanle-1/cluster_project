"""Run and archive one bounded remote diagnostic under the exact owned lease."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import json

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

parser = argparse.ArgumentParser()
parser.add_argument("--label", choices=("task_head", "mask_direction"), required=True)
args = parser.parse_args()
TOKEN = "2bbb4e0b9a814185a795b2ea2178483f"
PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
HOST = "songcl@100.64.3.28"
BASE = "/data3/songcl/Project/Cluster_project/pipeline/diagnostics"
REMOTE = BASE + "/bps_task_" + TOKEN
OLD = BASE + "/bps_population_f8bdf4cb21774bf2af11f959fa12d89a"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST]
owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() >= 720
execution_path = BUNDLE / (args.label + "_execution.json")
assert not execution_path.exists(), "Never replay a recorded attempt"
script = BUNDLE / (args.label + ".py")
record = {"token": TOKEN, "label": args.label, "started_at": datetime.now().astimezone().isoformat(),
          "script_sha256": tick.digest(script)}
try:
    setup_code = f"""
from pathlib import Path
import subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='das'
line=subprocess.check_output(['nvidia-smi','-i','7','--query-gpu=uuid,memory.free','--format=csv,noheader,nounits'],text=True).strip()
assert line.split(',')[0].strip()=='GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a'
assert int(line.split(',')[1])>=32768
base=Path('{BASE}').resolve();p=Path('{REMOTE}').resolve();assert base in p.parents
p.mkdir(exist_ok=True)
print(line)
"""
    setup = subprocess.run(SSH + ["python3", "-"], input=setup_code, text=True,
                           capture_output=True, timeout=30)
    record["setup"] = {"returncode": setup.returncode, "stdout": setup.stdout, "stderr": setup.stderr}
    setup.check_returncode()
    copied = subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", str(script), HOST + ":" + REMOTE + "/"],
        text=True, capture_output=True, timeout=30,
    )
    copied.check_returncode()
    execution = subprocess.run(SSH + [
        "timeout", "--signal=TERM", "--kill-after=15s", "600",
        "/home/songcl/miniconda3/envs/project_cluster/bin/python", "-B",
        REMOTE + "/" + script.name, "--runner", OLD + "/native_capture.py",
        "--output", REMOTE + "/" + args.label + "_result.json", "--token", TOKEN,
    ], text=True, encoding="utf-8", capture_output=True, timeout=650)
    record.update(returncode=execution.returncode, stdout=execution.stdout, stderr=execution.stderr)
except BaseException as exc:
    record.update(returncode=None, error_type=type(exc).__name__, error=str(exc))
finally:
    assert tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")["token"] == TOKEN
    record["recorded_at"] = datetime.now().astimezone().isoformat()
    tick.save(execution_path, record)
    result_name = args.label + "_result.json"
    pulled = subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
         HOST + ":" + REMOTE + "/" + result_name, str(BUNDLE / result_name)],
        text=True, capture_output=True, timeout=30,
    )
    tick.save(BUNDLE / (args.label + "_pull.json"), {"returncode": pulled.returncode, "stderr": pulled.stderr})
    print(json.dumps({"execution": record, "pull_returncode": pulled.returncode}, indent=2))
