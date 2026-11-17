import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "-o", "PasswordAuthentication=no", "server-4"]
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"


def remote(command, source=None):
    run = subprocess.run(SSH + [command], input=source, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return {"returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr}


def main():
    result = {"started_at": datetime.now(timezone.utc).isoformat(), "server": "server-4", "physical_gpu": 0}
    result["identity"] = remote("hostname")
    if result["identity"]["returncode"] or result["identity"]["stdout"].strip() != "dl04-MS-7E06":
        raise RuntimeError("Pinned server-4 identity did not match")
    result["inventory"] = remote("nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu,driver_version --format=csv,noheader,nounits")
    result["gpus"] = [dict(zip(["index", "uuid", "name", "total_mib", "used_mib", "free_mib", "utilization_percent", "driver"], [c.strip() for c in row])) for row in csv.reader(io.StringIO(result["inventory"]["stdout"])) if row]
    result["gpu0_processes"] = remote("nvidia-smi -i 0 --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv,noheader,nounits")
    source = r'''
import datetime, fcntl, importlib.metadata as metadata, json, sys
from pathlib import Path
paths = {"conda_source": "/home/dl04/anaconda3/etc/profile.d/conda.sh", "python": "/home/songcl/.conda/envs/project_cluster/bin/python", "code_root": "/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b", "data_root": "/home/songcl/data/data/", "work_dir": "/data/songcl/Project/Cluster_project/Cluster_checkpoints"}
locks, handles = [], []
try:
    for path in ("/tmp/cluster_project_gpu0_m201_migration.lock", "/tmp/cluster_project_gpu0_exclusive.lock", "/tmp/cluster_project_gpu0_parameter_transport.lock"):
        try:
            handle = open(path, "rb")
        except FileNotFoundError:
            locks.append({"path": path, "status": "absent_not_created"})
            continue
        handles.append(handle)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locks.append({"path": path, "status": "acquired_for_probe"})
        except BlockingIOError:
            locks.append({"path": path, "status": "held_by_existing_owner"})
    versions = {}
    for name in ("torch", "numpy", "transformers", "spconv-cu128", "spconv-cu124", "spconv-cu120"):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    result = {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "python": sys.version.split()[0], "executable": sys.executable, "paths": {k: {"path": v, "exists": Path(v).exists()} for k, v in paths.items()}, "versions": versions, "flocks": locks}
finally:
    for handle in reversed(handles):
        handle.close()
result["probe_flocks_released"] = True
print(json.dumps(result))
'''
    result["metadata_command"] = remote("PYTHONDONTWRITEBYTECODE=1 " + shlex.quote(PYTHON) + " -B -", source)
    result["metadata"] = json.loads(result["metadata_command"]["stdout"]) if result["metadata_command"]["returncode"] == 0 else None
    code = "import json,sys,torch;print(json.dumps({'python':sys.version.split()[0],'torch':torch.__version__,'torch_cuda':torch.version.cuda,'cuda_initialized':torch.cuda.is_initialized()}))"
    result["torch_import_command"] = remote("CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 " + shlex.quote(PYTHON) + " -B -c " + shlex.quote(code))
    result["observed_at"] = datetime.now(timezone.utc).isoformat()
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["scope"] = {"cuda_allocations": 0, "native_forwards": 0, "optimizer_steps": 0, "gpu1_computation": 0, "foreign_process_signals": 0, "lock_deletions": 0, "remote_file_writes": 0, "limitations": "Placement/occupation/existing-lock/import checks only, not native readiness or admission. Initial nonexistent interpreter and failed stdin import are retained in task outputs; this probes the located interpreter without stdin-dependent import."}
    output = HERE / "resource_probe.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(output), "observed_at": result["observed_at"], "gpus": result["gpus"], "metadata": result["metadata"], "torch_import": result["torch_import_command"], "result_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
