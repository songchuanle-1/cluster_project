"""One previously preregistered failing readout under the new owning lease."""
import copy
from datetime import datetime, timezone
import shlex
import shutil
from ops import (guard, save, run, ssh, advance, evidence, tick, OUT, PREV,
                 RUNTIME, TOKEN, THREAD, STAGE, HOST, SSH)

owner = guard(380)
identity = ssh('import json\nprint(json.dumps({"hostname":socket.gethostname()}))')
save("identity.json", identity)
local = OUT / "channel_failure"
local.mkdir(exist_ok=False)
for source, name in [
        (RUNTIME, "native_runtime.py"),
        (PREV / "native_channel_null.py", "channel_template.py"),
        (PREV / "native_channel_failure.py", "native_channel_failure.py")]:
    shutil.copyfile(source, local / name)
manifest = copy.deepcopy(tick.load(PREV / "channel_null/native_manifest.json"))
stage = STAGE + "/channel_failure"
manifest.update(stage=stage,
                failure_preregistration=evidence(PREV / "channel_failure_prereg.md"),
                original_failure=evidence(
                    PREV / "channel_null/native_channel_null_result.json"),
                actual_readout={"expression": 0, "point": 728,
                                "rule": "last valid point; frozen original failure"})
manifest["diagnostic_files"] = {
    name: tick.digest(local / name)
    for name in ("native_runtime.py", "channel_template.py",
                 "native_channel_failure.py")}
save("channel_failure/native_manifest.json", manifest)
save("channel_failure/execution_lease.json", {
    "project": "cluster_project", "thread_id": THREAD, "token": TOKEN,
    "deadline_at": owner["deadline_at"],
    "native_manifest_sha256": tick.digest(local / "native_manifest.json")})
advance([PREV / "channel_failure_prereg.md", local / "native_manifest.json",
         local / "native_channel_failure.py", OUT / "run_channel_failure.py"],
        next_action="Execute exactly the original expression0/lastvalid diagnostic; "
                    "retain strict1e-6 and original failure, record arithmetic residuals.")
ssh("from pathlib import Path\nimport json\nPath(" + repr(stage) +
    ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
uploaded = run(["scp", *SSH,
                *[str(local / name) for name in
                  (*manifest["diagnostic_files"], "native_manifest.json",
                   "execution_lease.json")],
                "songcl@" + HOST + ":" + stage + "/"])
assert uploaded.returncode == 0, uploaded.stderr
guard(340)
command = ("source /data/songcl/Project/Cluster_project/pipeline/runtime/"
           "server4_conda_4ca73fba.sh && conda activate project_cluster && python -B " +
           shlex.quote(stage + "/native_channel_failure.py") +
           " --lease " + shlex.quote(stage + "/execution_lease.json"))
remaining = (datetime.fromisoformat(owner["deadline_at"]) -
             datetime.now(timezone.utc)).total_seconds()
result = run(["ssh", *SSH, "songcl@" + HOST,
              shlex.join(["bash", "-lc", command])],
             min(450, int(remaining) - 120))
save("channel_failure_execution.json", {
    "returncode": result.returncode, "stdout": result.stdout,
    "stderr": result.stderr, "finished_at": datetime.now(timezone.utc).isoformat()})
fetched = run(["scp", *SSH, "songcl@" + HOST + ":" + stage +
               "/native_channel_failure_result.json",
               str(local / "native_channel_failure_result.json")])
assert fetched.returncode == 0, fetched.stderr
value = tick.load(local / "native_channel_failure_result.json")
advance([local / "native_channel_failure_result.json",
         OUT / "channel_failure_execution.json"], failure_scope="inconclusive",
        gate_result="Original failed null gate retained. One fixed-readout follow-up "
                    "strict_null_gate_passed=" +
                    str(value.get("strict_null_gate_passed", "UNKNOWN")) +
                    ". Not efficacy/admission or a revision of original failure.")
print({key: item for key, item in value.items() if key not in ("before", "after")})
