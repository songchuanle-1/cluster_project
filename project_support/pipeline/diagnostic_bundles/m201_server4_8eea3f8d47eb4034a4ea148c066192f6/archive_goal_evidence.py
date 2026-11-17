"""Retain byte-identical historical goal evidence after the user allocation edit."""

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate as m

m.guard()
path = m.PROJECT / "pipeline/goal.json"
raw = path.read_bytes()
current = json.loads(raw)
assert current["constraints"][-1].startswith("[USER-ALLOCATION 2026-10-14]")
original = json.loads(raw)
original["constraints"].pop()
lines = raw.splitlines(keepends=True)
indices = [i for i, line in enumerate(lines) if b'"[USER-ALLOCATION 2026-10-14]' in line]
assert len(indices) == 1
index = indices[0]
assert b"[USER-ALLOCATION 2026-09-21]" in lines[index - 1]
previous = lines[index - 1]
body = previous.rstrip(b"\r\n")
ending = previous[len(body):]
assert body.endswith(b",")
lines[index - 1] = body[:-1] + ending
del lines[index]
historical_bytes = b"".join(lines)
assert json.loads(historical_bytes) == original
expected = "d7296cbb4cfc0742e92ccccc65a17b36513dcd8940c98c90e38801e79f14b21b"
if hashlib.sha256(historical_bytes).hexdigest() != expected:
    # apply_patch can normalize unchanged CRLF lines. Only line endings are
    # searched; a match to the preexisting hash is mandatory before any write.
    bodies = historical_bytes.splitlines()
    begin = bodies.index(b'  "constraints": [')
    end = next(i for i in range(begin + 1, len(bodies)) if bodies[i] == b"  ],")
    affected = list(range(begin + 1, end))
    assert len(affected) == 18
    selected = set(affected)
    prefix = b"\r\n".join(bodies[:begin + 1]) + b"\r\n"
    suffix = b"\r\n".join(bodies[end:]) + b"\r\n"
    found = None
    for mask in range(1 << len(affected)):
        middle = b"".join(bodies[i] + (b"\n" if mask & (1 << j) else b"\r\n")
                           for j, i in enumerate(affected))
        candidate = prefix + middle + suffix
        if hashlib.sha256(candidate).hexdigest() == expected:
            found = candidate
            break
    if found is not None:
        historical_bytes = found
        assert json.loads(historical_bytes) == original
assert hashlib.sha256(historical_bytes).hexdigest() == expected, "Do not invent old evidence"
archive = m.PROJECT / "pipeline/reports/goal_before_server4_migration_20261014.json"
assert not archive.exists()
archive.write_bytes(historical_bytes)
work_path = m.PROJECT / "pipeline/research_work.json"
work = m.tick.load(work_path)
changed = []
for candidate in work["candidates"]:
    for entry in candidate.get("evidence", []):
        if entry.get("path") == "pipeline/goal.json":
            assert entry["sha256"] == expected
            entry["path"] = archive.relative_to(m.PROJECT).as_posix()
            changed.append(candidate["id"])
assert len(changed) == 9
m.tick.save(work_path, work)
assert path.read_bytes() == raw
m.record("historical_goal_archive", {
    "historical_path": archive.relative_to(m.PROJECT).as_posix(), "original_sha256": expected,
    "current_goal_sha256": hashlib.sha256(raw).hexdigest(), "reference_only_candidates": changed,
    "passed_gates_changed": 0, "admission_receipts_changed": 0,
    "earlier_postflight_failure": "Artifact hash mismatch: D:/project/cluster_project/pipeline/goal.json",
    "scope": "Byte-identical old goal verified against existing immutable evidence hash. Only nine old source-fact paths are repointed; no scientific result, gate or current allocation is changed. Not a reconstructed tick snapshot.",
})
print(json.dumps({"historical_goal_sha256": expected, "reference_paths_repaired": len(changed),
                  "current_goal_unchanged": True, "science_gates_unchanged": True}))
