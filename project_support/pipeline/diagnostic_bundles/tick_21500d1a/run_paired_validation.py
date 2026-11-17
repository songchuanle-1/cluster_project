"""Run bounded frozen post-training evidence capture under the current lease."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
from audit_terminal import guard, save, remote, ROOT, OUT, BASE, tick

owner = guard()
assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 1400
native = tick.load(OUT / "native_equivalence_result.json")
assert native["passed"] and len(native["records"]) == 16
audit = tick.load(OUT / "terminal_observation.json")
checkpoints = tick.load(OUT / "checkpoint_metadata.json")["checkpoints"]
name = BASE + "_hds_canon_r1"
manifest = {"deadline_at": owner["deadline_at"], "root": "/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b",
            "source_hashes": {**audit["source_hashes"], **audit["producer_source_hashes"]},
            "producer_hashes": {filename: tick.digest(OUT / filename) for filename in ("paired_validation.py", "aligned_evidence.py")},
            "conditions": {
                "reference_m95_epoch16": {"model": BASE, "config": "configs/Quard/ctf_hcg_csort/"+BASE+".yaml",
                      "checkpoint": checkpoints["frozen_m95"]["path"], "checkpoint_sha256": checkpoints["frozen_m95"]["sha256"], "epoch": 16},
                "candidate_hds_epoch19": {"model": name, "config": "configs/Quard/ctf_hcg_csort_hds_canon_r1/"+name+".yaml",
                      "checkpoint": checkpoints["best.pth"]["path"], "checkpoint_sha256": checkpoints["best.pth"]["sha256"], "epoch": 19}},
            "expected_expressions": 9508, "analysis_bootstrap_draws": 5000, "analysis_seed": 1999,
            "scope": "Original frozen post-training full ScanRefer VAL paired evidence. Reference is trusted M95epoch16 snapshot, NOT verified historical champion weights. No training, optimizer steps, VAL mechanism selection or new admission."}
save("paired_manifest.json", manifest)
work = tick.load(ROOT / "pipeline/research_work.json")
candidate = next(c for c in work["candidates"] if c["id"] == "m202-paired-native-evidence-producer")
assert candidate["stage"] == "validation"
candidate["native_train_equivalence"] = {"passed": True, "native_forwards": 4, "scenes": 4,
    "expressions": 16, "optimizer_steps": 0, "scope": "Software export equivalence only"}
candidate["next_action"] = "Execute frozen full original VAL evidence capture for existing M95epoch16 reference and HDSepoch19 best; retain full IDs, exact native aggregate/payload controls, scene-clustered paired uncertainty and reference limitations. No model selection or new training."
for filename in ("native_equivalence_result.json", "checkpoint_metadata.json", "paired_eval_prereg.md", "paired_manifest.json", "paired_validation.py"):
    path = OUT / filename
    candidate["evidence"].append({"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)})
guard()
tick.save(ROOT / "pipeline/research_work.json", work)
stage = "/data/songcl/Project/Cluster_project/pipeline/evidence_producer_21500d1a"
for filename in ("paired_eval_prereg.md", "paired_validation.py", "aligned_evidence.py", "paired_manifest.json"):
    response = subprocess.run(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                               str(OUT / filename), "songcl@192.168.1.115:" + stage + "/"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
    assert response.returncode == 0, response.stderr
guard()
command = "source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; " + shlex.join([
    "env", "PYTHONDONTWRITEBYTECODE=1", "python", "-B", stage + "/paired_validation.py"])
args = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
        "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=3", "songcl@192.168.1.115", shlex.join(["bash", "-lc", command])]
lines = []
with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1) as process:
    for line in process.stdout:
        lines.append(line)
        if line.startswith("PAIRED_NATIVE_"):
            print(line.rstrip(), flush=True)
    rc = process.wait(timeout=20)
save("paired_execution_attempt.json", {"observed_at": datetime.now(timezone.utc).isoformat(), "returncode": rc,
     "combined_output": "".join(lines), "scope": manifest["scope"]})
assert rc == 0, "".join(lines)[-4000:]
for filename in ("reference_m95_epoch16.json", "candidate_hds_epoch19.json", "paired_capture_index.json"):
    response = subprocess.run(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                               "songcl@192.168.1.115:" + stage + "/" + filename, str(OUT / filename)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert response.returncode == 0, response.stderr
index = tick.load(OUT / "paired_capture_index.json")
assert index["passed"] and index["optimizer_steps"] == 0
for condition, row in index["conditions"].items():
    assert tick.digest(OUT / (condition + ".json")) == row["sha256"]
print("PAIRED_CAPTURE_PULLED_AND_HASH_VERIFIED", flush=True)
