"""Owning foreground lease and immutable diagnostic evidence helpers."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1",
                  PYTHONIOENCODING="utf-8")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
PREV = ROOT / "pipeline/diagnostic_bundles/tick_ed0d2b32"
RUNTIME = ROOT / "pipeline/diagnostic_bundles/tick_ce9bc689/trace_m95_1/native_runtime.py"
TOKEN = "d8b27109653f45b1918e4b3a823398be"
THREAD = "01a04987-fdbe-7301-b2f0-f9b6ab60f74c"
GOAL = "42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec"
CID = "hierarchical-nonlocal-channel-rank-audit"
STAGE = "/data/songcl/Project/Cluster_project/pipeline/native_channel_d8b27109"
HOST = "192.168.1.115"
SSH = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
       "-o", "ConnectTimeout=10"]


def guard(seconds=0):
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == THREAD == os.environ["CODEX_THREAD_ID"]
    remaining = (datetime.fromisoformat(owner["deadline_at"]) -
                 datetime.now(timezone.utc)).total_seconds()
    assert remaining > seconds, (remaining, seconds)
    assert tick.digest(ROOT / "pipeline/goal.json") == GOAL
    assert tick.load(ROOT / "pipeline/execution_mode.json") == {
        "mode": "foreground", "target_thread_id": THREAD}
    return owner


def save(name, value):
    guard()
    with (OUT / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def evidence(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)}


def advance(paths, candidate_id=CID, **updates):
    guard()
    work = tick.load(ROOT / "pipeline/research_work.json")
    candidate = next(c for c in work["candidates"] if c["id"] == candidate_id)
    candidate.update(updates)
    known = {(e["path"], e["sha256"]) for e in candidate["evidence"]}
    for path in paths:
        item = evidence(path)
        if (item["path"], item["sha256"]) not in known:
            candidate["evidence"].append(item)
    guard()
    tick.save(ROOT / "pipeline/research_work.json", work)


def run(args, timeout=90):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def ssh(program, timeout=90):
    guard()
    program = ('import socket\nassert socket.gethostname()=="dl04-MS-7E06"\n' +
               program)
    result = run(["ssh", *SSH, "songcl@" + HOST,
                  shlex.join(["/usr/bin/python3", "-B", "-c", program])], timeout)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)
