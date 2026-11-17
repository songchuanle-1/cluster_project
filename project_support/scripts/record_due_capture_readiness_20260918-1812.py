import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:/project/cluster_project")
OUTPUT = ROOT / "pipeline/reports/due_capture_readiness_20260918-1812.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = {
    "checked_at": "2026-09-18T18:12:31+08:00",
    "scope": (
        "targeted live capacity and native-progress check; no launch, model "
        "forward, queue mutation, or causal claim"
    ),
    "allocation": {
        "server": "server-6",
        "gpu": 7,
        "gpu_uuid": "GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a",
        "allowed_process_cap": 2,
    },
    "gpu": {
        "memory_used_mib": 62483,
        "memory_total_mib": 81559,
        "memory_free_mib": 19076,
        "utilization_percent": 100,
    },
    "processes": [
        {
            "pid": 1134192,
            "role": "M197-PIRS",
            "used_memory_mib": 19956,
            "command": (
                "python tools/train.py "
                "configs/Quard/pirs/"
                "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs.yaml "
                "--gpu_ids 7 --num_gpus 1"
            ),
        },
        {
            "pid": 3827570,
            "role": "foreign",
            "used_memory_mib": 42488,
            "command": "/home/jiaoh/conda_envs/das_env/bin/python",
        },
    ],
    "native_progress": {
        "log": (
            "/data3/songcl/Project/Cluster_project/Cluster_checkpoints/"
            "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs/"
            "20260916_042843/20260916_042843.log"
        ),
        "epoch": 18,
        "iteration": 1750,
        "iterations_per_epoch": 4686,
        "last_log_time": "2026-09-18 10:12:31",
        "process_alive": True,
    },
    "unblock": {
        "blocked": True,
        "reason": (
            "GPU7 remains at the two-process cap with M197-PIRS and foreign "
            "pid3827570."
        ),
        "retry_after": "2026-09-18T19:15:00+08:00",
        "condition": (
            "M197-PIRS reaches terminal state or GPU7 has fewer than two "
            "processes with sufficient measured free memory."
        ),
    },
    "evidence_inputs": {
        "tick_context": {
            "path": "pipeline/headless/.tick_context.json",
            "sha256": sha(ROOT / "pipeline/headless/.tick_context.json"),
        },
        "control_coverage": {
            "path": "pipeline/reports/referent_control_coverage_20260918-1618.json",
            "sha256": sha(
                ROOT
                / "pipeline/reports/referent_control_coverage_20260918-1618.json"
            ),
        },
    },
}
OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
print(json.dumps({
    "output": str(OUTPUT),
    "sha256": sha(OUTPUT),
}, indent=2))
