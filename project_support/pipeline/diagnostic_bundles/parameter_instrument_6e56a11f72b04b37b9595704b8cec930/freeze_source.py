"""Freeze the exact tested function source without executing its native wrapper."""

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

project = Path("D:/project/cluster_project")
bundle = Path(__file__).resolve().parent
owner = tick.load(project / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == "6e56a11f72b04b37b9595704b8cec930"
assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
source = project / "pipeline/diagnostic_bundles/bps_task_2bbb4e0b9a814185a795b2ea2178483f/parameter_transport.py"
frozen = bundle / "tested_parameter_transport.py"
assert not frozen.exists()
expected = tick.load(bundle / "result.json")["source_sha256"]
assert tick.digest(source) == expected
shutil.copyfile(source, frozen)
assert tick.digest(frozen) == expected
work_path = project / "pipeline/research_work.json"
work = tick.load(work_path)
ids = {"m95-native-main-role-weight-precedence", "m95-native-relation-other-sign-conflict",
       "m95-native-secondary-positive-mass"}
for candidate in work["candidates"]:
    if candidate["id"] in ids:
        for path in (frozen, Path(__file__).resolve()):
            candidate["evidence"].append({"path": path.relative_to(project).as_posix(),
                                          "sha256": tick.digest(path)})
tick.save(work_path, work)
print("Exact tested function source frozen and bound; no native execution.")
