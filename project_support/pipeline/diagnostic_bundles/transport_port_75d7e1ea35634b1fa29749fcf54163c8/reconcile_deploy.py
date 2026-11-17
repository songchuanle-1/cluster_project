"""Resume the verified partial asset, preserving the failed deployment."""

import hashlib
import json
import subprocess

import stage

stage.guard(420)
checkpoint = stage.ASSETS / "checkpoint_snapshot.pth"
remote_checkpoint = stage.REMOTE + "/assets/checkpoint_snapshot.pth"
probe = json.loads(stage.remote(f"""
import hashlib,json,pathlib,subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
p=pathlib.Path({remote_checkpoint!r});before=p.stat();h=hashlib.sha256()
with p.open('rb') as stream:
    for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
after=p.stat()
assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
print(json.dumps({{'bytes':before.st_size,'mtime_ns':before.st_mtime_ns,'sha256':h.hexdigest()}}))
""", timeout=60))
assert 0 < probe["bytes"] <= checkpoint.stat().st_size
hasher = hashlib.sha256()
with checkpoint.open("rb") as stream:
    remaining = probe["bytes"]
    while remaining:
        block = stream.read(min(8 * 1024**2, remaining))
        assert block
        hasher.update(block)
        remaining -= len(block)
assert hasher.hexdigest() == probe["sha256"]
stage.save("partial_prefix_verified", probe)
batch = f'reput "{checkpoint.as_posix()}" "{remote_checkpoint}"\nquit\n'
result = subprocess.run(
    ["sftp", *stage.OPTS, "-b", "-", "server-4"],
    input=batch, text=True, encoding="utf-8", capture_output=True, timeout=180,
)
stage.save("resume_transfer", {"returncode": result.returncode,
                             "stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:]})
assert result.returncode == 0, result.stderr
for name in ("runtime.py", "native_adapter.py", "cpu_prepare.py", "assets_manifest.json", "ast_audit.json"):
    stage.command(["scp", *stage.OPTS, str(stage.BUNDLE / name), "server-4:" + stage.REMOTE + "/"])
rows = stage.tick.load(stage.BUNDLE / "assets_manifest.json")["assets"]
result = json.loads(stage.remote(f"""
import hashlib,json,pathlib
root=pathlib.Path({stage.REMOTE!r});expected={rows!r}
for name,row in expected.items():
    p=root/'assets'/name;h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
    assert h.hexdigest()==row['sha256'],name
    assert p.stat().st_size==row['bytes'],name
print(json.dumps({{'assets_verified':len(expected),'checkpoint_verified':True,
                  'resumed_bytes':{checkpoint.stat().st_size - probe["bytes"]},
                  'prior_failure_retained':True}}))
""", timeout=60))
stage.save("deployment_reconciled", result)
print(json.dumps(result))
