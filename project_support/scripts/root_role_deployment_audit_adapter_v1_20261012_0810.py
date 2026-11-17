"""Read-only deployed source/config/actual train progress evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import yaml

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
STAGE = PIPE / "tmr_validation_20261012_0810"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    static = json.loads((STAGE / "root_role_static_v2_20261012_0810.json").read_text())
    package = ROOT / "framework/model/Quard_model" / NAME
    files = []
    for record in static["files"]:
        actual = sha(package / record["filename"])
        assert actual == record["sha256"]
        files.append(dict(record, deployed_sha256=actual))
    original = yaml.safe_load((STAGE / (NAME + ".yaml")).read_text())
    config = ROOT / "configs/Quard/ctf_hcg_csort_tmr" / (NAME + ".yaml")
    deployed = yaml.safe_load(config.read_text())
    mappings = [
        ("/home/songcl/data/data", "/data3/songcl/data/data_cluster"),
        ("/home/songcl/3dres/project/cluster_project/Checkpoints",
         "/data3/songcl/Project/Cluster_project/Checkpoints"),
    ]

    def adapt(value):
        if isinstance(value, dict):
            return {key: adapt(item) for key, item in value.items()}
        if isinstance(value, list):
            return [adapt(item) for item in value]
        if isinstance(value, str):
            for before, after in mappings:
                value = value.replace(before, after)
        return value

    assert deployed == adapt(original)
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    assert commit == "810f3067b22692f2cdc1b096b4b7d5931bacd238"
    pid = int((ROOT / "logs" / (".pid_" + NAME)).read_text())
    process = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\x00", b" ").decode()
    assert NAME in process and "tools/train.py" in process
    logs = sorted((ROOT / "logs").glob("train_" + NAME + "_*.log"),
                  key=lambda path: path.stat().st_mtime)
    log = logs[-1]
    tail = log.read_bytes()[-24000:].decode("utf-8", errors="replace")
    steps = [list(map(int, match)) for match in re.findall(
        r"Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+", tail)]
    assert len({tuple(value) for value in steps}) >= 2 and max(value[1] for value in steps) > 0
    gpu = subprocess.check_output([
        "nvidia-smi", "-i", "7", "--query-gpu=uuid,utilization.gpu,memory.used,memory.total",
        "--format=csv,noheader,nounits"], text=True).strip()
    result = {
        "contract": "tmr_postlaunch_source_progress_audit_v1",
        "remote_observed_at": datetime.now(timezone.utc).isoformat(),
        "code_commit": commit, "files": files,
        "candidate_config_path_only_adapted": True,
        "config_sha256": sha(config), "original_config_sha256": sha(STAGE / (NAME + ".yaml")),
        "pid": pid, "process": process, "log": str(log), "training_steps_tail": steps,
        "last_training_lines": [line for line in tail.splitlines() if "Train[" in line][-2:],
        "gpu7": gpu, "trained_validation_metric": None,
        "limitations": "Actual native progress, not final efficacy; remote/local clocks reported separately.",
    }
    output = PIPE / "root_role_deployment_audit_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
