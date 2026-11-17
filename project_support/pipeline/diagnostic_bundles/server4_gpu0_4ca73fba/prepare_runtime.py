from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "runtime/server4_conda_4ca73fba.sh"
TARGET = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
OPTIONS = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "-o", "PasswordAuthentication=no"]


def remote(command, source=None):
    payload = source.encode("utf-8") if source is not None else None
    run = subprocess.run(["ssh"] + OPTIONS + ["server-4", command], input=payload, capture_output=True, timeout=60)
    return {"returncode": run.returncode, "stdout": run.stdout.decode("utf-8", errors="replace"), "stderr": run.stderr.decode("utf-8", errors="replace")}


def main():
    expected = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if remote("hostname")["stdout"].strip() != "dl04-MS-7E06":
        raise RuntimeError("Wrong server identity")
    if remote("test -e " + shlex.quote(TARGET))["returncode"] == 0:
        if remote("sha256sum " + shlex.quote(TARGET))["stdout"].split()[0] != expected:
            raise RuntimeError("Refusing to overwrite an existing different runtime file")
    else:
        made = remote("mkdir -p " + shlex.quote(str(Path(TARGET).parent).replace("\\", "/")))
        if made["returncode"]:
            raise RuntimeError(made["stderr"])
        subprocess.run(["scp"] + OPTIONS + [str(SOURCE), "server-4:" + TARGET], check=True, timeout=60)
    actual = remote("sha256sum " + shlex.quote(TARGET))["stdout"].split()[0]
    if actual != expected:
        raise RuntimeError("Runtime upload hash mismatch")
    command = "import json,sys,torch;print(json.dumps({'executable':sys.executable,'torch':torch.__version__,'cuda':torch.version.cuda,'cuda_initialized':torch.cuda.is_initialized()}))"
    script = "set -eu\nsource " + shlex.quote(TARGET) + "\nconda activate project_cluster\nexport CUDA_VISIBLE_DEVICES=0\npython -B -c " + shlex.quote(command) + "\n"
    checked = remote("bash -s", script)
    result = {"observed_at": datetime.now(timezone.utc).isoformat(), "target": TARGET, "sha256": actual, "probe": checked, "runtime_loaded": checked["returncode"] == 0, "native_forwards": 0, "optimizer_steps": 0, "shared_environment_modified": False, "scope": "Project-only new-process environment wrapper; no dependency/version/source changes or CUDA allocations."}
    output = HERE / "runtime_preparation.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["runtime_loaded"]:
        raise RuntimeError("Scoped runtime verification failed; evidence retained")


if __name__ == "__main__":
    main()
