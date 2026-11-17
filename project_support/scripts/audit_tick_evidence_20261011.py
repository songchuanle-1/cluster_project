"""Verify remote artifacts and capture only the authorized GPU's final state."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
sys.path.insert(0, str(SKILL))
import foreground_tick as fg

TOKEN = "b395a8b5064a4b6a810cc2285c82c890"
REMOTE = "/data3/songcl/Project/Cluster_project/pipeline"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "songcl@100.64.3.28"]
FILES = ["padding_equivalence_result_20261011.json", "joint_selector_result_20261011.json",
         "joint_selector_population_20261011.json", "joint_selector_backward_20261011.json",
         "joint_selector_equivalence_20261011.json"]


def main():
    owner = fg.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    artifacts = []
    for name in FILES:
        path = ROOT / "pipeline/reports" / name
        if not path.exists():
            subprocess.run(["scp", "-q", "-o", "BatchMode=yes",
                            f"songcl@100.64.3.28:{REMOTE}/{name}", str(path)],
                           check=True, timeout=60)
        local = hashlib.sha256(path.read_bytes()).hexdigest()
        remote = subprocess.check_output(SSH + [f"sha256sum '{REMOTE}/{name}'"],
                                         text=True, timeout=20).split()[0]
        assert remote == local
        artifacts.append({"path": path.relative_to(ROOT).as_posix(), "sha256": local,
                          "remote_local_verified": True})
    info = subprocess.check_output(
        SSH + ["nvidia-smi -i 7 --query-gpu=timestamp,uuid,utilization.gpu,memory.used,memory.total --format=csv,noheader"],
        text=True, timeout=20).strip()
    processes = subprocess.check_output(
        SSH + ["nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name --format=csv,noheader"],
        text=True, timeout=20)
    uuid = "GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a"
    gpu7 = [row for row in processes.splitlines() if row.startswith(uuid + ",")]
    assert uuid in info and not gpu7
    lock_check = subprocess.run(
        SSH + ["flock -n /tmp/cluster_project_gpu7_slot2_diagnostic.lock true"], timeout=20)
    assert lock_check.returncode == 0
    record = {"observed_at": datetime.now().astimezone().isoformat(),
              "server": "server-6", "gpu": 7, "gpu_csv": info,
              "gpu7_compute_processes": gpu7, "diagnostic_lock_available": True,
              "artifacts": artifacts, "all_remote_local_sha256_match": True}
    fg.save(ROOT / "pipeline/reports/tick_evidence_audit_20261011.json", record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
