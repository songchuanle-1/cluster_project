"""Fresh-owner read-only reconciliation of the expired RVE diagnostic."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "915589b3154c4c3c99b1db658f610a1f"
OLD = ROOT / "pipeline/diagnostic_bundles/tick_8c4864e1/observe_native_release_once.py"
assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 300
binding = {key: owner[key] for key in (
    "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256"
)}
for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
    assert hashlib.sha256((ROOT / "pipeline/headless" / name).read_bytes()).hexdigest() == binding[key]
program = next(
    ast.literal_eval(node.value)
    for node in ast.parse(OLD.read_text(encoding="utf-8")).body
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROGRAM" for t in node.targets)
)
# The previous owner's executable wrapper is never run. Only its read-only
# remote program is reused, explicitly targeting that previous stage.
extra = r"""
other_project_processes=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  if proc.stat().st_uid!=1001:continue
  argv=[a.decode(errors='replace') for a in (proc/'cmdline').read_bytes().split(b'\0') if a]
  if any(str(stage) in a or ('tools/train.py' in a and 'Cluster' in a) for a in argv):
   other_project_processes.append({'pid':int(proc.name),'ppid':int((proc/'stat').read_text().split(') ',1)[1].split()[1]),'argv':argv[:14]})
 except (OSError,RuntimeError,ValueError):pass
actual_head=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-C',str(root),'rev-parse','HEAD'],text=True,timeout=10).strip()
assert actual_head=='0747f6acec1c61018ec99acf2efa5329c9b3523c'
print(json.dumps({'additional_project_stage_processes':other_project_processes,'runtime_root':str(root),'runtime_HEAD':actual_head}))
"""
program += extra
result_path = HERE / "previous_native_reconciliation_actual.json"
assert not result_path.exists()
record = {
    "owner": binding,
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "candidate_id": "fine-leaf-receiver-conditioned-vector-exchange",
    "purpose": "RECONCILE_PREVIOUS_TERMINAL_STAGE_ONLY",
    "historical_wrapper_sha256": hashlib.sha256(OLD.read_bytes()).hexdigest(),
    "current_wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "remote_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    "historical_remote_stage": "/data/songcl/Project/Cluster_project/pipeline/rvec_8c4864e1_gpu0",
    "source_commit": "0f8cc0f978b38c24e159d3a2d37344f59cc9a0be",
    "physical_gpu": 0,
    "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c",
    "certainty": "uncertain",
}
process = subprocess.Popen([
    "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
    "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
    "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -",
], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding="utf-8", errors="replace")
try:
    stdout, stderr = process.communicate(program, timeout=35)
except subprocess.TimeoutExpired:
    record["reason"] = "Read-only observation uncertain; no signals or retry."
else:
    record.update(certainty="terminal", returncode=process.returncode, stderr=stderr[:3000])
    try:
        record["observations"] = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    except json.JSONDecodeError:
        record["stdout_excerpt"] = stdout[:2000]
with result_path.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
assert record.get("returncode") == 0 and len(record.get("observations", [])) == 2
print(json.dumps({
    "path": str(result_path), "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
    "observations": record["observations"],
}))
