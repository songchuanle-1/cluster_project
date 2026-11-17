"""Capture one reviewed operation without printing raw training or owner state."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/project/cluster_project")
TOKEN = "2bcb30da1bcc4f67a6193b8413cec6ec"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["probe", "prepare", "stage", "run", "status", "reconcile"])
    parser.add_argument("--mode", choices=["smoke", "resources"])
    parser.add_argument("--target", choices=["candidate", "champion"])
    parser.add_argument("--request-id")
    args = parser.parse_args()
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text(encoding="utf-8"))
    assert owner["token"] == TOKEN
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    name = args.operation
    if args.operation == "run":
        assert args.mode and args.target
        name += "_" + args.mode + "_" + args.target
    elif args.operation in ("status", "reconcile"):
        name += "_" + datetime.now(timezone.utc).strftime("%H%M%S_%f")
    out = HERE / (name + "_capture.stdout.json")
    err = HERE / (name + "_capture.stderr.txt")
    audit = HERE / (name + "_capture.json")
    assert not any(path.exists() for path in (out, err, audit)), "Never replay; reconcile the original operation."
    command = [sys.executable, "-B", "-X", "utf8",
               str(HERE / "nde_crash_operational_active/run_nde_operation.py"),
               "--execute-root", "--operation", args.operation]
    if args.mode:
        command += ["--mode", args.mode]
    if args.target:
        command += ["--target", args.target]
    if args.request_id:
        command += ["--request-id", args.request_id]
    started = datetime.now(timezone.utc).isoformat()
    with out.open("xb") as stdout, err.open("xb") as stderr:
        process = subprocess.run(command, stdout=stdout, stderr=stderr)
    summary = {"operation": args.operation, "mode": args.mode, "target": args.target,
               "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
               "returncode": process.returncode, "command": command,
               "stdout_bytes": out.stat().st_size, "stderr_bytes": err.stat().st_size}
    try:
        value = json.loads(out.read_bytes())
        result = value.get("result", {})
        summary["result_keys"] = list(result) if isinstance(result, dict) else []
        if isinstance(result, dict):
            summary.update({key: result[key] for key in ("certainty", "returncode", "pid", "verified") if key in result})
            measured = result.get("result") or {}
            if isinstance(measured, dict):
                summary["actual"] = {key: measured.get(key) for key in
                    ("execution_completed", "optimizer_steps", "losses", "native_smoke_checks_passed",
                     "peak_allocated_bytes", "median_ms", "p90_ms")}
                profile = measured.get("profile") or {}
                summary["profile"] = {key: profile.get(key) for key in ("flops_g", "within10G")}
    except (ValueError, OSError):
        summary["stdout_json_parsed"] = False
    if process.returncode:
        summary["stderr_tail"] = err.read_bytes()[-1400:].decode("utf-8", errors="replace")
    with audit.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "command"}, ensure_ascii=False))
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
