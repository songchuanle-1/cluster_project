"""Read-only replay of M196 metric counting and canonical parser regression."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
skill = Path.home()/".codex/skills/songcl_research_pipeline"
sys.path.insert(0, str(skill))
os.environ["PROJECT_ROOT"] = str(root.parent)
spec = importlib.util.spec_from_file_location("pipeline_monitor", skill/"pipeline_monitor.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
log = root/"pipeline/reports/M196_native_terminal_20260916.log"
text = log.read_text(encoding="utf-8")
exact = [float(v) for v in re.findall(r"mIoU : ([0-9.]+)", text)]
rounded = [float(v) for v in re.findall(r"\bmIOU: ([0-9]+\.[0-9]+)", text)]
contaminated = [float(v) for v in re.findall(r"mIOU: ([0-9]+\.[0-9]+)", text)]


def count(values):
    best = max(values)
    return dict(records=len(values), best=best, best_index=values.index(best),
                no_improve=len(values)-values.index(best)-1)


assert count(exact)["no_improve"] == 5
assert count(rounded)["no_improve"] == 5
assert count(contaminated)["no_improve"] == 11
with patch.object(monitor, "ssh", side_effect=["", "\n".join(map(str, exact))]):
    result = monitor.parse_miou_from_logs(["native"], "host", "user")
    assert result == (exact, max(exact), 5)
with patch.object(monitor, "ssh", side_effect=["", "", "\n".join(map(str, rounded))]) as remote:
    result = monitor.parse_miou_from_logs(["stdout"], "host", "user")
    assert result == (rounded, max(rounded), 5)
    fallback_command = remote.call_args_list[2].args[2]
    assert r"\bmIOU:" in fallback_command
assert not monitor.should_early_stop({"patience": 10}, {}, 5, 23, 50)
assert monitor.should_early_stop({"patience": 10}, {}, 11, 23, 50)
result = dict(exact=count(exact), rounded=count(rounded),
    unbounded_substring=count(contaminated), canonical_parser_regressions_pass=True,
    scope="Archived logger static replay,not actual07:01 invocation provenance. "
          "Unbounded substring reproduces11 by matching spmIOU as well;current "
          "canonical source uses word boundary and returns5. No kill,restart, "
          "queue edit or policy change.",
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (log, Path(__file__), skill/"pipeline_monitor.py")})
out = root/"pipeline/reports/M196_monitor_replay_20260916.json"
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
