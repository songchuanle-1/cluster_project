"""Fresh-owner read-only observation; no diagnostic or trainer is launched."""
import argparse
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--stage", choices=("rvec_915589b3_gpu0", "rvec_915589b3b_gpu0"))
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_READ_ONLY_NO_SSH"}))
        return
    assert args.stage and sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 120
    binding = {key: owner[key] for key in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256"
    )}
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == binding[key]
    program = next(
        ast.literal_eval(node.value) for node in ast.parse(OLD.read_text(encoding="utf-8")).body
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROGRAM" for t in node.targets)
    )
    assert program.count("rvec_8c4864e1_gpu0") == 1
    program = program.replace("rvec_8c4864e1_gpu0", args.stage)
    program += r"""
additional=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  if proc.stat().st_uid!=1001:continue
  argv=[a.decode(errors='replace') for a in (proc/'cmdline').read_bytes().split(b'\0') if a]
  if any(str(stage) in a or ('tools/train.py' in a and 'Cluster' in a) for a in argv):
   additional.append({'pid':int(proc.name),'argv':argv[:14]})
 except (OSError,RuntimeError):pass
actual_head=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-C',str(root),'rev-parse','HEAD'],text=True,timeout=10).strip()
assert actual_head=='0747f6acec1c61018ec99acf2efa5329c9b3523c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
print(json.dumps({'additional_project_stage_processes':additional,'runtime_root':str(root),'runtime_HEAD':actual_head,'gpu0_contexts':contexts}))
"""
    result_path = HERE / ("stage_release_" + args.stage + ".json")
    assert not result_path.exists(), "Immutable observation already exists; do not replay."
    record = {
        "owner": binding, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "fine-leaf-receiver-conditioned-vector-exchange",
        "remote_stage": "/data/songcl/Project/Cluster_project/pipeline/" + args.stage,
        "current_wrapper_sha256": sha(__file__), "historical_program_container_sha256": sha(OLD),
        "remote_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "source_commit": "0f8cc0f978b38c24e159d3a2d37344f59cc9a0be",
        "physical_gpu": 0, "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c",
        "certainty": "uncertain", "signals_sent": False, "remote_files_written": False,
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
        record["reason"] = "Read-only observation uncertain; no signals or replay."
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
    print(json.dumps({"path": str(result_path), "sha256": sha(result_path), "observations": record["observations"]}))


if __name__ == "__main__":
    main()
