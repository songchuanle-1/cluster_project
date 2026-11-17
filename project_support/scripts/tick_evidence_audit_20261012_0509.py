"""Read-only source/result provenance and native diagnostic release audit."""
import datetime
import hashlib
import json
from pathlib import Path
import socket
import subprocess

ROOT = Path("/data3/songcl/Project/Cluster_project/pipeline")


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return {"returncode": result.returncode, "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()}


def main():
    rows = []
    for name in ("scale_alias_native_20261012_0509",
                 "support_orth_native_20261012_0509"):
        path = ROOT / (name + ".json")
        source = ROOT / (name + ".py")
        result = json.loads(path.read_text())
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        rows.append({
            "result": path.name,
            "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source": source.name, "source_sha256": actual,
            "declared_source_sha256": result["script_sha256"],
            "source_matches": actual == result["script_sha256"]})
    assert all(r["source_matches"] for r in rows)
    result = {
        "remote_observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "rows": rows,
        "gpu7": run(["nvidia-smi", "-i", "7", "--query-gpu=timestamp,uuid,"
                     "utilization.gpu,memory.used,memory.total",
                     "--format=csv,noheader,nounits"]),
        "gpu7_compute_processes": run([
            "nvidia-smi", "-i", "7", "--query-compute-apps=gpu_uuid,pid,"
            "process_name,used_memory", "--format=csv,noheader,nounits"]),
        "diagnostic_lock": run([
            "flock", "-n", "/tmp/cluster_project_gpu7_slot2_diagnostic.lock", "true"]),
        "admissions": 0, "launches": 0}
    output = ROOT / "tick_evidence_audit_20261012_0509.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
