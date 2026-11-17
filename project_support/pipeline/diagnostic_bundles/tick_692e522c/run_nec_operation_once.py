from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
LAUNCHER = P / "manual_ops/20261104_gpu0_overlay/nec_overlay_prepare/operational/run_nec_operation.py"
EXPECTED = json.loads((HERE / "owner_binding.json").read_text(encoding="utf-8"))


def guard():
    owner = json.loads((P / "headless/.foreground.lockdir/owner.json").read_text(encoding="utf-8"))
    assert {k: owner.get(k) for k in EXPECTED} == EXPECTED
    assert os.environ["CODEX_THREAD_ID"] == EXPECTED["thread_id"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED["deadline_at"])
    for name, key in (("headless/.tick_context.json", "context_sha256"),
                      ("headless/.tick_context_state.next.json", "pending_sha256")):
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == EXPECTED[key]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("probe", "prepare", "stage", "run", "status", "reconcile"))
    parser.add_argument("--mode", choices=("smoke", "resources"))
    parser.add_argument("--target", choices=("champion", "candidate"))
    parser.add_argument("--request-id")
    args = parser.parse_args()
    guard()
    label = args.operation
    command = [sys.executable, "-B", "-X", "utf8", str(LAUNCHER),
               "--execute-root", "--operation", args.operation]
    if args.operation == "run":
        assert args.mode and args.target
        command += ["--mode", args.mode, "--target", args.target]
        label += "_" + args.mode + "_" + args.target
    if args.request_id:
        command += ["--request-id", args.request_id]
        label += "_" + args.request_id
    output = HERE / ("nec_" + label + "_call.json")
    assert not output.exists(), "This call was already recorded; reconcile the exact request."
    started = datetime.now(timezone.utc).isoformat()
    process = subprocess.run(command, capture_output=True, text=True,
                             encoding="utf-8", timeout=1120)
    record = dict(owner=EXPECTED, started_at=started,
                  recorded_at=datetime.now(timezone.utc).isoformat(),
                  command=command, launcher_sha256=hashlib.sha256(LAUNCHER.read_bytes()).hexdigest(),
                  returncode=process.returncode, stdout=process.stdout, stderr=process.stderr)
    if process.returncode == 0:
        try:
            record["result"] = json.loads(process.stdout)
        except ValueError:
            record["unparsed_success_output"] = True
    # Keep the actual result even if a command exhausted the owner window.
    with output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(dict(operation=label, returncode=process.returncode,
                          path=output.relative_to(ROOT).as_posix(),
                          sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                          stderr_tail=process.stderr[-2000:] if process.returncode else ""),
                     ensure_ascii=False))
    sys.exit(process.returncode)


if __name__ == "__main__":
    main()
