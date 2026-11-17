"""Capture one guarded PSC operation without displaying native CR logs."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
ACT = HERE / "psc_current_activation"
args = sys.argv[1:]
assert args and args[0] in ("prepare", "stage", "run", "status", "reconcile")
operation = args[0]
if operation == "run":
    assert len(args) == 3 and args[1] in ("smoke", "resources") and args[2] in ("champion", "candidate")
    label = "_".join(args)
else:
    assert len(args) == 1
    label = operation
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == "d20ca92f1b654e24ba9cf29f634307b7" and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
command = [sys.executable, "-B", "-X", "utf8", str(ACT / "run_psc_operation.py"),
           "--execute-root", "--operation", operation]
if operation == "run":
    command += ["--mode", args[1], "--target", args[2]]
stdout = HERE / ("psc_" + label + "_stdout.json")
stderr = HERE / ("psc_" + label + "_stderr.txt")
metadata = HERE / ("psc_" + label + "_capture.json")
assert not stdout.exists() and not stderr.exists() and not metadata.exists(), "Capture exists: reconcile, never replay"
with stdout.open("xb") as out, stderr.open("xb") as err:
    result = subprocess.run(command, stdout=out, stderr=err, timeout=940 if operation == "run" else 300)
record = {
    "recorded_at": datetime.now(timezone.utc).isoformat(), "command": command,
    "returncode": result.returncode,
    "stdout": {"path": stdout.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(stdout.read_bytes()).hexdigest(), "bytes": stdout.stat().st_size},
    "stderr": {"path": stderr.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(stderr.read_bytes()).hexdigest(), "bytes": stderr.stat().st_size},
}
with metadata.open("x", encoding="utf8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
summary = {"operation": label, "returncode": result.returncode, "capture": str(metadata)}
if result.returncode == 0:
    value = json.loads(stdout.read_text(encoding="utf8"))
    body = value.get("result", {})
    if isinstance(body, dict):
        summary.update({k: body[k] for k in ("certainty", "verified", "returncode") if k in body})
        native = body.get("result")
        if isinstance(native, dict):
            summary["native"] = {k: native[k] for k in (
                "mode", "target", "execution_completed", "losses",
                "native_data_loaded", "backward_finite", "intended_path_observed",
            ) if k in native}
            steps = native.get("steps")
            summary["native"]["step_count"] = len(steps) if isinstance(steps, list) else steps
    summary["protected_source_and_lifecycle_unchanged"] = value.get("protected_source_and_lifecycle_unchanged")
else:
    summary["stderr_tail"] = stderr.read_text(encoding="utf8", errors="replace")[-1600:]
print(json.dumps(summary, ensure_ascii=False))
raise SystemExit(result.returncode)
