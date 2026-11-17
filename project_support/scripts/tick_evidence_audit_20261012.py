"""Read-only remote provenance and post-diagnostic occupation audit."""
import datetime
import hashlib
import json
from pathlib import Path
import socket
import subprocess

ROOT = Path("/data3/songcl/Project/Cluster_project/pipeline")
NAMES = [
    "relation_schema_audit_20261012",
    "relation_witness_audit_20261012",
    "relation_witness_control_20261012",
    "caption_equivalence_audit_20261012",
    "caption_equivalence_native_20261012",
    "caption_equivalence_operator_20261012",
]


def command(args):
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    return {"returncode": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def main():
    rows = []
    for name in NAMES:
        result_path = ROOT / (name + ".json")
        source_path = ROOT / (name + ".py")
        result = json.loads(result_path.read_text())
        source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        rows.append({
            "result": result_path.name,
            "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "source": source_path.name, "source_sha256": source_hash,
            "declared_source_sha256": result.get("script_sha256"),
            "source_matches": result.get("script_sha256") == source_hash,
        })
    audit = {
        "remote_observed_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "scope": "Read-only server-6 GPU7 and this tick's diagnostic evidence",
        "rows": rows,
        "gpu7": command(["nvidia-smi", "-i", "7", "--query-gpu=timestamp,uuid,"
                         "utilization.gpu,memory.used,memory.total",
                         "--format=csv,noheader,nounits"]),
        "compute_processes": command([
            "nvidia-smi", "-i", "7", "--query-compute-apps=gpu_uuid,pid,"
            "process_name,used_memory", "--format=csv,noheader,nounits"]),
        "diagnostic_lock": command([
            "flock", "-n", "/tmp/cluster_project_gpu7_slot2_diagnostic.lock",
            "true"]),
        "admission": False, "launches": 0,
    }
    (ROOT / "tick_evidence_audit_20261012.json").write_text(
        json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
