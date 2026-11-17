"""Render a fresh hash-bound entry. Not an activation or production approval."""
import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def render_entry(stage, binding, core_bytes, expected_kind):
    """Caller supplies reviewed literals; no env or runtime proof-mode switch."""
    stage = Path(stage)
    assert not stage.exists()
    assert expected_kind in ("cpu-proof", "production")
    assert binding["kind"] == expected_kind
    assert binding["entry"] == str(stage / "bin/python")
    assert binding["stage"] == str(stage)
    assert binding["one_shot_marker"] == str(stage / "train-consumed.json")
    stage.mkdir(mode=0o700)
    (stage / "bin").mkdir(mode=0o700)
    core = stage / "lock_core.py"
    core.write_bytes(core_bytes)
    core.chmod(0o600)
    raw = (json.dumps(binding, sort_keys=True, indent=2) + "\n").encode("utf-8")
    config = stage / "binding.json"
    config.write_bytes(raw)
    config.chmod(0o600)
    # Every security-sensitive path/hash/kind is a literal in this executable.
    # Altered adjacent config/core or another entry directory cannot be selected
    # by a caller environment. -I suppresses Python environment import injection.
    entry = f'''#!/usr/bin/python3 -I
import hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
ENTRY={str(stage / "bin/python")!r}
STAGE={str(stage)!r}
KIND={expected_kind!r}
UID={binding["uid"]!r}
CORE_SHA={digest(core_bytes)!r}
BINDING_SHA={digest(raw)!r}
def secure(path,directory=False):
 s=os.lstat(path)
 assert not stat.S_ISLNK(s.st_mode) and s.st_uid==UID and not(s.st_mode&0o022)
 assert stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)
 return Path(path).read_bytes() if not directory else None
assert Path(__file__).resolve()==Path(ENTRY) and os.getuid()==os.geteuid()==UID
secure(STAGE,True);secure(str(Path(ENTRY).parent),True);secure(ENTRY)
raw=secure(str(Path(STAGE)/"binding.json"))
core=secure(str(Path(STAGE)/"lock_core.py"))
assert hashlib.sha256(raw).hexdigest()==BINDING_SHA
assert hashlib.sha256(core).hexdigest()==CORE_SHA
binding=json.loads(raw)
assert binding["kind"]==KIND and binding["entry"]==ENTRY and binding["stage"]==STAGE
module=importlib.util.module_from_spec(importlib.util.spec_from_loader("psc_fixed_lock_core",loader=None))
module.__file__=str(Path(STAGE)/"lock_core.py")
exec(compile(core,module.__file__,"exec"),module.__dict__)
module.run(binding)
'''
    target = stage / "bin/python"
    target.write_bytes(entry.encode("utf-8"))
    target.chmod(0o755)
    return {
        "stage": str(stage), "entry": str(target), "binding_sha256": digest(raw),
        "core_sha256": digest(core_bytes), "entry_sha256": digest(target.read_bytes()),
        "kind": expected_kind,
    }
