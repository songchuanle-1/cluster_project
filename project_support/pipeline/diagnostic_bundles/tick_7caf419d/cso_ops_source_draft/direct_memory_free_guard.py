"""NOT_APPROVED source draft. Running this file always performs a NOP.

Future reviewed native_runtime.observe and production prelaunch/marker callers
may invoke require_direct_free_memory after their original identity/lock guards.
This file is not wired into any deployment, entry, launcher or native test.
"""
import json
import subprocess


class ResourceRefused(RuntimeError):
    pass


def require_direct_free_memory():
    """Future native observation/prelaunch/locked marker guard; no signals."""
    argv = ["/usr/bin/nvidia-smi", "-i", "0",
            "--query-gpu=index,uuid,memory.free,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits"]
    child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    try:
        stdout, stderr = child.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        raise ResourceRefused("Uncertain resource query; preserve child PID " +
                              str(child.pid) + "; no signal or retry")
    if child.returncode:
        raise ResourceRefused("Resource query failed; no launch or marker consumption")
    fields = [part.strip() for part in stdout.decode("utf-8").strip().split(",")]
    if len(fields) != 6 or fields[:2] != ["0", "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]:
        raise ResourceRefused("Physical GPU0 identity or resource row mismatch")
    free_mib = int(fields[2])
    if free_mib < 20000:
        raise ResourceRefused("Direct memory.free below unchanged 20000 MiB gate")
    return {"index": 0, "uuid": fields[1], "memory_free_mib": free_mib,
            "memory_used_mib": int(fields[3]), "memory_total_mib": int(fields[4]),
            "utilization_percent": int(fields[5]),
            "memory_free_queried_directly": True}


if __name__ == "__main__":
    print(json.dumps({"status": "DEFAULT_NOP_NOT_APPROVED_SOURCE_DRAFT",
                      "resource_query_performed": False,
                      "deployment_or_training_authorized": False}))
