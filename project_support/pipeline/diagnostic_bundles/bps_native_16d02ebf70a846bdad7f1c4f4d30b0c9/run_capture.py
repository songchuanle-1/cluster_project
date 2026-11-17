"""Run one bounded remote diagnostic and preserve all returned execution evidence."""

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
OLD = BASE + "/bps_population_f8bdf4cb21774bf2af11f959fa12d89a"
REMOTE = BASE + "/bps_native_" + TOKEN
OUTPUT = REMOTE + "/v3"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST]


def guard():
    owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    seconds = (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds()
    assert seconds >= 720, "Insufficient immutable tick time for600sec execution+120sec closure"
    return owner


guard()
prereg = PROJECT / "pipeline/designs/bps_native_buffer_adapter_prereg_20261014_1312.md"
work_path = PROJECT / "pipeline/research_work.json"
work = tick.load(work_path)
candidate = next(item for item in work["candidates"] if item["id"] == "m95-native-between-pair-support")
assert candidate["stage"] == "training"
for path in (prereg, BUNDLE / "native_capture_v3.py", Path(__file__)):
    ref = {"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)}
    assert not any(ref == old for old in candidate["evidence"]), "Do not replay this launch"
    candidate["evidence"].append(ref)
tick.save(work_path, work)
setup = f"""
from pathlib import Path
import subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='das'
line=subprocess.check_output(['nvidia-smi','-i','7','--query-gpu=uuid,memory.free','--format=csv,noheader,nounits'],text=True).strip()
assert line.split(',')[0].strip()=='GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a'
assert int(line.split(',')[1])>=32768
base=Path('{BASE}').resolve(); output=Path('{OUTPUT}').resolve()
assert base in output.parents
output.mkdir(parents=True,exist_ok=False)
print(line)
"""
record = {
    "token": TOKEN, "started_at": datetime.now().astimezone().isoformat(),
    "adapter_sha256": tick.digest(BUNDLE / "native_capture_v3.py"),
    "prereg_sha256": tick.digest(prereg), "remote_directory": REMOTE,
}
try:
    setup_result = subprocess.run(SSH + ["python3", "-"], input=setup, text=True,
                                  encoding="utf-8", capture_output=True, timeout=30)
    record["setup"] = {"returncode": setup_result.returncode,
                       "stdout": setup_result.stdout, "stderr": setup_result.stderr}
    setup_result.check_returncode()
    copy = subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
         str(BUNDLE / "native_capture_v3.py"), HOST + ":" + REMOTE + "/"],
        text=True, encoding="utf-8", capture_output=True, timeout=30,
    )
    record["upload"] = {"returncode": copy.returncode, "stderr": copy.stderr}
    copy.check_returncode()
    guard()
    command = [
        "timeout", "--signal=TERM", "--kill-after=15s", "600",
        "/home/songcl/miniconda3/envs/project_cluster/bin/python", "-B",
        REMOTE + "/native_capture_v3.py",
        "--runner", OLD + "/native_capture.py",
        "--code-root", "/data3/songcl/Project/Cluster_project/Cluster",
        "--config", "configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml",
        "--checkpoint", OLD + "/checkpoint_snapshot.pth",
        "--source-manifest", OLD + "/source_manifest.json",
        "--population", OLD + "/result.json",
        "--output", OUTPUT + "/result.json", "--token", TOKEN,
    ]
    execution = subprocess.run(SSH + command, text=True, encoding="utf-8",
                               capture_output=True, timeout=650)
    record.update(returncode=execution.returncode, stdout=execution.stdout, stderr=execution.stderr)
except BaseException as exc:
    record.update(returncode=None, error_type=type(exc).__name__, error=str(exc))
finally:
    record["recorded_at"] = datetime.now().astimezone().isoformat()
    owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    tick.save(BUNDLE / "execution.json", record)
    pulled = {}
    for name in ("result.json", "adapter_audit.json"):
        copy = subprocess.run(
            ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
             HOST + ":" + OUTPUT + "/" + name, str(BUNDLE / name)],
            text=True, encoding="utf-8", capture_output=True, timeout=30,
        )
        pulled[name] = {"returncode": copy.returncode, "stderr": copy.stderr}
    tick.save(BUNDLE / "pull_execution.json", pulled)
    print(json.dumps({"execution": record, "pulls": pulled}, ensure_ascii=False, indent=2))
