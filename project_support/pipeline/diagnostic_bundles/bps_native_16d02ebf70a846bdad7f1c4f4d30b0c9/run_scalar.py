"""One authorized scalar diagnostic; no model, configuration or queue edits."""

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
REMOTE = "/data3/songcl/Project/Cluster_project/pipeline/diagnostics/bps_native_" + TOKEN
RUNNER = "/data3/songcl/Project/Cluster_project/pipeline/diagnostics/bps_population_f8bdf4cb21774bf2af11f959fa12d89a/native_capture.py"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST]
owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() >= 720
assert not (BUNDLE / "scalar_execution.json").exists(), "Never replay the diagnostic"
record = {"token": TOKEN, "started_at": datetime.now().astimezone().isoformat(),
          "script_sha256": tick.digest(BUNDLE / "scalar_checkpoint.py")}
try:
    copied = subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
         str(BUNDLE / "scalar_checkpoint.py"), HOST + ":" + REMOTE + "/"],
        text=True, encoding="utf-8", capture_output=True, timeout=30,
    )
    record["upload"] = {"returncode": copied.returncode, "stderr": copied.stderr}
    copied.check_returncode()
    result = subprocess.run(
        SSH + ["timeout", "--signal=TERM", "--kill-after=15s", "600",
               "/home/songcl/miniconda3/envs/project_cluster/bin/python", "-B",
               REMOTE + "/scalar_checkpoint.py", "--runner", RUNNER,
               "--output", REMOTE + "/scalar_result.json", "--token", TOKEN],
        text=True, encoding="utf-8", capture_output=True, timeout=650,
    )
    record.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
except BaseException as exc:
    record.update(returncode=None, error_type=type(exc).__name__, error=str(exc))
finally:
    assert tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")["token"] == TOKEN
    record["recorded_at"] = datetime.now().astimezone().isoformat()
    tick.save(BUNDLE / "scalar_execution.json", record)
    pulled = subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
         HOST + ":" + REMOTE + "/scalar_result.json", str(BUNDLE / "scalar_result.json")],
        text=True, encoding="utf-8", capture_output=True, timeout=30,
    )
    tick.save(BUNDLE / "scalar_pull.json", {"returncode": pulled.returncode, "stderr": pulled.stderr})
    print(json.dumps({"execution": record, "pull_returncode": pulled.returncode}, indent=2))
