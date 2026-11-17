"""Verify cluster legacy delegation and real read-only metric extraction."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
skill = Path.home() / ".codex/skills/songcl_research_pipeline"
legacy = root.parent / ".agents/skills/songcl_research_pipeline/pipeline_monitor.py"
os.environ["PROJECT_ROOT"] = str(root.parent)
sys.path.insert(0, str(skill))
spec = importlib.util.spec_from_file_location("canonical_monitor", skill / "pipeline_monitor.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
tree = ast.parse(legacy.read_text(encoding="utf-8"))
guard = next(n for n in tree.body if isinstance(n, ast.If)
             and "cluster_project" in ast.unparse(n.test))
code = compile(ast.Module(body=[guard], type_ignores=[]), str(legacy), "exec")
with patch.object(sys, "argv", [str(legacy), "cluster_project", "--read-only"]), \
     patch.object(subprocess, "call", return_value=23) as call:
    try:
        exec(code, dict(__name__="__main__", __file__=str(legacy),
                        sys=sys, subprocess=subprocess))
    except SystemExit as exc:
        assert exc.code == 23
    else:
        raise AssertionError("Legacy dispatch continued after canonical delegation")
    assert call.call_args.args[0] == [
        sys.executable, str(skill / "pipeline_monitor.py"), "cluster_project", "--read-only"]
with patch.object(sys, "argv", [str(legacy), "lighttext_project"]), \
     patch.object(subprocess, "call") as call:
    exec(code, dict(__name__="__main__", __file__=str(legacy),
                    sys=sys, subprocess=subprocess))
    call.assert_not_called()
with patch.object(sys, "argv", [str(legacy), "cluster_project"]), \
     patch.object(Path, "is_file", return_value=False), \
     patch.object(subprocess, "call") as call:
    try:
        exec(code, dict(__name__="__main__", __file__=str(legacy),
                        sys=sys, subprocess=subprocess))
    except SystemExit as exc:
        assert "refusing" in str(exc)
    else:
        raise AssertionError("Missing canonical runtime must fail closed")
    call.assert_not_called()
entry = json.loads((root / "pipeline/experiments/M196-CTF-HCG-CSORT-BCA.json").read_text())
values, best, no_improve = monitor.parse_miou_from_logs(
    [entry["log"]], "192.168.1.137", "songcl")
assert len(values) == 22 and best == .480 and no_improve == 5
tracked = [root / "pipeline/queue.json", root / "pipeline/running.json",
           root / "pipeline/experiments.csv"]


def digest():
    files = [*tracked, *(root / "pipeline/decisions").glob("*.md"),
             *(root / "pipeline/experiments").glob("*.json")]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


before = digest()
proc = subprocess.run([sys.executable, str(legacy), "cluster_project", "--read-only"],
                      capture_output=True, encoding="utf-8", errors="replace", timeout=120)
assert proc.returncode == 0, proc.stderr
assert before == digest(), "Read-only path mutated experiment/queue/decision state"
result = dict(checks_passed=5, remote_log=entry["log"], records=len(values),
              best=best, no_improve=no_improve, readonly_stdout=proc.stdout,
              readonly_state_unchanged=True,
              historical_caller_proven=False,
              sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [Path(__file__), legacy, skill / "pipeline_monitor.py"]})
(root / "pipeline/reports/monitor_entrypoint_20260916.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
