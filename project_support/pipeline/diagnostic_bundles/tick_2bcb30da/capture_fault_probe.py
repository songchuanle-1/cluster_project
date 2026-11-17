"""Execute the single independently reviewed fault probe and capture bounded UI output."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "2bcb30da1bcc4f67a6193b8413cec6ec"
OP = HERE / "nde_crash_probe_bound_operation"
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_bytes())
assert owner["token"] == TOKEN
assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() >= 1020
review = HERE / "nde_crash_actual_binding_independent_review.json"
value = json.loads(review.read_bytes())
assert value["passed"] is True
assert not (HERE / "nde_root_crash_probe_intent.json").exists()
assert not (HERE / "nde_crash_probe_execution").exists()
release = OP / "operation_release.json"
assert not release.exists()
with release.open("xb") as stream:
    stream.write((OP / "release_template.json").read_bytes())
out = HERE / "crash_probe_capture.stdout.json"
err = HERE / "crash_probe_capture.stderr.txt"
audit = HERE / "crash_probe_capture.json"
assert not any(path.exists() for path in (out, err, audit))
command = [sys.executable, "-B", "-X", "utf8", str(OP / "run_crash_probe_operation.py"),
           "--execute-root", "--operation", "run"]
started = datetime.now(timezone.utc).isoformat()
with out.open("xb") as stdout, err.open("xb") as stderr:
    process = subprocess.run(command, stdout=stdout, stderr=stderr)
result = {"command": command, "returncode": process.returncode, "started_at": started,
          "finished_at": datetime.now(timezone.utc).isoformat(),
          "stdout_bytes": out.stat().st_size, "stderr_bytes": err.stat().st_size,
          "review_sha256": hashlib.sha256(review.read_bytes()).hexdigest(),
          "fault_localization_only": True, "admission_evidence": False}
try:
    raw = json.loads(out.read_bytes())
    execution = raw.get("result") or {}
    result.update(status=raw.get("status"), certainty=execution.get("certainty"),
                  diagnostic_returncode=execution.get("returncode"),
                  pid=execution.get("pid"), result_keys=list(execution))
except ValueError:
    result["stdout_json_parsed"] = False
if process.returncode:
    result["stderr_tail"] = err.read_bytes()[-1200:].decode("utf-8", errors="replace")
with audit.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write("\n")
print(json.dumps({key: value for key, value in result.items() if key != "command"}, ensure_ascii=False))
raise SystemExit(process.returncode)
