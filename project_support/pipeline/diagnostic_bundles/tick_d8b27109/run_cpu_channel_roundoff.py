"""CPU-only diagnostic while both authorized GPU slots are occupied."""
from datetime import datetime, timezone
import shlex
from ops import (guard, save, run, ssh, advance, evidence, tick, OUT, PREV,
                 STAGE, HOST, SSH)

guard(180)
identity = ssh('import json\nprint(json.dumps({"hostname":socket.gethostname()}))')
stage = STAGE + "/cpu_channel_roundoff"
local = OUT / "cpu_channel_roundoff"
local.mkdir(exist_ok=False)
original = tick.load(PREV / "channel_null/native_manifest.json")
manifest = {"prefix_source": original["prefix_source"],
            "original_failure": evidence(PREV / "channel_null/native_channel_null_result.json"),
            "preregistration": evidence(OUT / "cpu_channel_roundoff_prereg.md"),
            "script_sha256": tick.digest(OUT / "cpu_channel_roundoff.py"),
            "fixed_readout": {"expression": 0, "point": 728}}
save("cpu_channel_roundoff/cpu_manifest.json", manifest)
advance([OUT / "cpu_channel_roundoff_prereg.md", OUT / "cpu_channel_roundoff.py",
         local / "cpu_manifest.json"],
        next_action="Run the fixed CPU float32/float64 arithmetic references without CUDA; "
                    "not a replacement for the still-unrun GPU failure measurement.")
ssh("from pathlib import Path\nimport json\nPath(" + repr(stage) +
    ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
result = run(["scp", *SSH, str(OUT / "cpu_channel_roundoff.py"),
              str(local / "cpu_manifest.json"), "songcl@" + HOST + ":" + stage + "/"])
assert result.returncode == 0, result.stderr
command = ("source /data/songcl/Project/Cluster_project/pipeline/runtime/"
           "server4_conda_4ca73fba.sh && conda activate project_cluster && "
           "CUDA_VISIBLE_DEVICES='' python -B " + shlex.quote(stage + "/cpu_channel_roundoff.py") +
           " --root " + shlex.quote(stage))
result = run(["ssh", *SSH, "songcl@" + HOST, shlex.join(["bash", "-lc", command])], 120)
save("cpu_channel_roundoff_execution.json", {
    "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
    "observed_at": datetime.now(timezone.utc).isoformat()})
assert result.returncode == 0, result.stderr
result = run(["scp", *SSH, "songcl@" + HOST + ":" + stage +
              "/cpu_channel_roundoff_result.json", str(local / "cpu_channel_roundoff_result.json")])
assert result.returncode == 0, result.stderr
value = tick.load(local / "cpu_channel_roundoff_result.json")
advance([local / "cpu_channel_roundoff_result.json", OUT / "cpu_channel_roundoff_execution.json"],
        failure_scope="inconclusive",
        gate_result="CPU arithmetic references measured; original native null failure remains, "
                    "exact original GPU amplitude still UNKNOWN; no gate/admission/efficacy claim.")
print(value)
