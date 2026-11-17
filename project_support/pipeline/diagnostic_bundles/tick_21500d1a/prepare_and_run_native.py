"""Transport the SAME frozen exporter test to the now-idle authorized target."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import shutil
import subprocess

from audit_terminal import guard, save, remote, ROOT, OUT, BASE, tick

owner = guard()
assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 600
prior = ROOT / "pipeline/diagnostic_bundles/evidence_producer_86290288"
assert tick.digest(prior / "native_equivalence.py") == "75e2dbaa572c13404bc9c9c6c29207b5f307c2fffa1af487085067091b636657"
audit = tick.load(OUT / "terminal_observation.json")
assert not audit["exact_training_pids"] and audit["gpu0"]["compute_contexts"] == ""
assert all(value == "acquired_and_released" for value in audit["locks"].values())
source = (prior / "native_equivalence.py").read_text(encoding="utf-8")
changes = [
    ('CUDA_VISIBLE_DEVICES="1"', 'CUDA_VISIBLE_DEVICES="0"'),
    ('"sysu311-MS-7C59"', '"dl04-MS-7E06"'),
    ('manifest["physical_gpu"] == 1', 'manifest["physical_gpu"] == 0'),
    ('"pipeline/server3_fallback_abdff23d"', '"pipeline/evidence_producer_21500d1a"'),
    ('"-i", "1"', '"-i", "0"'),
    ('["1", manifest["gpu_uuid"]]', '["0", manifest["gpu_uuid"]]'),
    ('"/sdc1/songcl/IPDN/data/"', '"/home/songcl/data/data/"'),
    ('        import torch\n', '        from tools import train as native_train\n        import torch\n'),
    ('    deadline = datetime.fromisoformat(args.deadline)\n',
     '    deadline = datetime.fromisoformat(args.deadline)\n    assert (deadline - datetime.now(timezone.utc)).total_seconds() > 360\n')]
review = []
for old, new in changes:
    count = source.count(old)
    assert count > 0, old
    review.append({"old": old, "new": new, "count": count})
    source = source.replace(old, new)
runner = OUT / "native_equivalence_server4.py"
runner.write_text(source, encoding="utf-8", newline="\n")
for name in ("aligned_evidence.py", "test_aligned_evidence.py"):
    shutil.copyfile(prior / name, OUT / name)
    assert tick.digest(OUT / name) == tick.digest(prior / name)
for name in ("aligned_evidence.py", "test_aligned_evidence.py", runner.name):
    compile((OUT / name).read_text(encoding="utf-8"), name, "exec")
manifest = copy.deepcopy(tick.load(prior / "native_manifest.json"))
manifest.update(hostname="dl04-MS-7E06", root="/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b",
                checkpoint=audit["frozen_m95"]["path"], physical_gpu=0,
                gpu_uuid="GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c",
                source_hashes=audit["producer_source_hashes"], lifetime_locks=list(audit["locks"]),
                native_test_status="PENDING: now-idle authorized target; original4TRAINgroups/seed/control unchanged",
                producer_hashes={name: tick.digest(OUT / name) for name in ("aligned_evidence.py", "test_aligned_evidence.py", runner.name)})
assert manifest["checkpoint_sha256"] == audit["frozen_m95"]["sha256"]
save("native_manifest_server4.json", manifest)
save("transport_adaptation_review.json", {"changes": review, "original_runner_sha256": tick.digest(prior / "native_equivalence.py"),
     "target_runner_sha256": tick.digest(runner), "original_cpu_controls": "13passed, cached from prior tick; not rerun/countable this tick",
     "source_frozen": True, "seed_groups_controls_unchanged": True, "static_compile_files": 3,
     "scope": "Path/GPU/runtime trusted-loader/deadline transport only, not a model revision or scientific gate change"})
work = tick.load(ROOT / "pipeline/research_work.json")
candidate = next(c for c in work["candidates"] if c["id"] == "m202-paired-native-evidence-producer")
assert candidate["stage"] == "blocked"
candidate["previous_resource_block"] = {key: candidate[key] for key in ("blocker_kind", "required_server", "blocker", "retry_after", "unblock_condition")}
candidate["stage"] = "validation"
candidate["next_action"] = "Execute SAME frozen4TRAINgroup exporter equivalence on newly verified idle server4GPU0; preserve failed attempts, all payload/float32 controls and native source hashes."
for key in ("blocker_kind", "required_server", "blocker", "retry_after", "unblock_condition"):
    candidate.pop(key, None)
for name in ("native_manifest_server4.json", "transport_adaptation_review.json"):
    p = OUT / name
    candidate["evidence"].append({"path": p.relative_to(ROOT).as_posix(), "sha256": tick.digest(p)})
guard()
tick.save(ROOT / "pipeline/research_work.json", work)
stage = "/data/songcl/Project/Cluster_project/pipeline/evidence_producer_21500d1a"
remote("192.168.1.115", "umask 077; mkdir -p " + shlex.quote(stage))
files = [str(OUT / name) for name in ("aligned_evidence.py", "test_aligned_evidence.py", runner.name, "native_manifest_server4.json")]
response = subprocess.run(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                           *files, "songcl@192.168.1.115:" + stage + "/"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
assert response.returncode == 0, response.stderr
guard()
command = "source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; " + shlex.join([
    "env", "PYTHONDONTWRITEBYTECODE=1", "python", "-B", stage + "/" + runner.name,
    "--manifest", stage + "/native_manifest_server4.json", "--deadline", owner["deadline_at"], "--output", stage + "/native_equivalence_result.json"])
response = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "songcl@192.168.1.115",
                           shlex.join(["bash", "-lc", command])], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=360)
save("native_execution_attempt.json", {"observed_at": datetime.now(timezone.utc).isoformat(), "returncode": response.returncode,
     "stdout": response.stdout, "stderr": response.stderr, "scope": "Actual SAME exporter native test on server4GPU0; no optimizer or model edits"})
assert response.returncode == 0, response.stderr[-3000:]
markers = [line for line in response.stdout.splitlines() if line.startswith("NATIVE_EVIDENCE_RESULT=")]
assert len(markers) == 1
result = json.loads(markers[0].split("=", 1)[1])
assert result["passed"] and result["native_forwards"] == 4 and result["optimizer_steps"] == 0
local_result = OUT / "native_equivalence_result.json"
response = subprocess.run(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                           "songcl@192.168.1.115:" + stage + "/native_equivalence_result.json", str(local_result)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
assert response.returncode == 0, response.stderr
full = tick.load(local_result)
assert full["passed"] and len(full["records"]) == 16 and full["unique_scenes"] == 4
print(json.dumps({key: full[key] for key in ("passed", "native_forwards", "optimizer_steps", "unique_scenes", "native_mean", "exported_mean", "peak_allocated_bytes")}, indent=2))
