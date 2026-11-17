"""Read-only current-tick native provenance and GPU7 release audit."""
import datetime
import hashlib
import json
from pathlib import Path
import socket
import subprocess

ROOT = Path("/data3/songcl/Project/Cluster_project/pipeline")


def run(args):
    process = subprocess.run(args, capture_output=True, text=True, check=False)
    return {"returncode": process.returncode, "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip()}


def main():
    rows = []
    for name in ("query_anchor_native_20261012", "fps_identity_native_20261012"):
        path = ROOT / (name + ".json")
        source = ROOT / (name + ".py")
        data = json.loads(path.read_text())
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        rows.append({
            "result": path.name,
            "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source": source.name, "source_sha256": source_hash,
            "declared_source_sha256": data["script_sha256"],
            "source_matches": data["script_sha256"] == source_hash})
    original = ROOT / "query_anchor_native_20261012_adapter_failure.py"
    original_sha = hashlib.sha256(original.read_bytes()).hexdigest()
    assert original_sha == "0c6919a0d5a703b6e95af64af4f97e5a1a355e19da618e45e908531c02d5ba86"
    result = {
        "remote_observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "rows": rows,
        "original_adapter_failure_source_sha256": original_sha,
        "gpu7": run(["nvidia-smi", "-i", "7", "--query-gpu=timestamp,uuid,"
                     "utilization.gpu,memory.used,memory.total",
                     "--format=csv,noheader,nounits"]),
        "gpu7_compute_processes": run([
            "nvidia-smi", "-i", "7", "--query-compute-apps=gpu_uuid,pid,"
            "process_name,used_memory", "--format=csv,noheader,nounits"]),
        "diagnostic_lock": run([
            "flock", "-n", "/tmp/cluster_project_gpu7_slot2_diagnostic.lock", "true"]),
        "admissions": 0, "launches": 0,
    }
    output = ROOT / "tick_evidence_audit_20261012_0309.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
