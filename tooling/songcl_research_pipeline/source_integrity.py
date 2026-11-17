"""Read-only deployment checks; a commit label does not identify live files."""
import hashlib
import json
from pathlib import PurePosixPath
import shlex
import subprocess


SOURCE_SUFFIXES = {".py", ".pyi", ".yaml", ".yml", ".json", ".toml", ".ini",
                   ".cfg", ".sh", ".c", ".cpp", ".cu", ".h", ".hpp", ".so"}


def remote_python(server, program):
    prefix = ""
    executable = server.get("python") or "python3"
    if server.get("conda_source") and server.get("conda_env"):
        prefix = (f"source {shlex.quote(server['conda_source'])} && "
                  f"conda activate {shlex.quote(server['conda_env'])} && ")
        executable = "python"
    return prefix + shlex.quote(executable) + " -B -c " + shlex.quote(program)


def checked_probe(server, program, ssh):
    output = ssh(server["host"], server["user"], remote_python(server, program))
    try:
        result = json.loads(output)
    except (ValueError, TypeError):
        raise ValueError("Source integrity observation unavailable") from None
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise ValueError("Source integrity mismatch; preserve files and reconcile tested source")


def verify_git(server, commit, mappings, ssh):
    program = f"""
import json,pathlib,subprocess
root=pathlib.Path({server['remote_code_root']!r}).resolve()
def within_root(path):
    try:path.resolve().relative_to(root)
    except ValueError:return False
    return True
def git(*args):
    return subprocess.check_output(['git','-C',str(root),*args])
assert git('rev-parse','HEAD').decode().strip()=={commit!r}
changed=git('diff','--name-only','-z','--ignore-submodules=none','HEAD').split(b'\\0')
untracked=git('ls-files','--others','--exclude-standard','-z').split(b'\\0')
bad=[]
for raw in changed:
    if not raw: continue
    name=raw.decode('utf-8')
    path=root/name
    if (path.suffix not in {sorted(SOURCE_SUFFIXES)!r} and not path.is_dir()
            and name not in ('.gitmodules','requirements.txt','Dockerfile')):continue
    if ({mappings!r} and name.startswith('configs/')
            and path.suffix in ('.yaml','.yml') and path.is_file()
            and within_root(path)):
        import yaml
        def adapt(value):
            if isinstance(value,dict):return {{k:adapt(v) for k,v in value.items()}}
            if isinstance(value,list):return [adapt(v) for v in value]
            if isinstance(value,str):
                for old,new in {mappings!r}:value=value.replace(old,new)
            return value
        original=yaml.safe_load(git('show','HEAD:'+name).decode('utf-8'))
        if yaml.safe_load(path.read_text())==adapt(original):continue
    bad.append(name)
for raw in untracked:
    if raw and pathlib.PurePosixPath(raw.decode('utf-8')).suffix in {sorted(SOURCE_SUFFIXES)!r}:
        bad.append(raw.decode('utf-8'))
assert git('rev-parse','HEAD').decode().strip()=={commit!r}
print(json.dumps({{'ok':not bad,'paths':bad[:6]}}))
"""
    checked_probe(server, program, ssh)


def marker_manifest(code, commit):
    tree = subprocess.check_output(
        ["git", "-C", str(code), "ls-tree", "-r", "-z", commit + ":AdaRES"],
        timeout=120)
    records = []
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        header, raw_name = entry.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        name = raw_name.decode("utf-8")
        path = PurePosixPath(name)
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        if kind != "blob" or mode not in ("100644", "100755") or ".." in path.parts:
            raise ValueError("Source integrity manifest contains unsupported source entry")
        records.append((name, oid))
    if not records:
        raise ValueError("Source integrity manifest is empty")
    return records


def verify_marker(code, commit, server, ssh):
    # Keep SSH arguments bounded on Windows without uploading a manifest.
    records = marker_manifest(code, commit)
    checked_records = []
    for name, oid in records:
        yaml_digest = None
        suffix = PurePosixPath(name).suffix
        if suffix in ('.yaml', '.yml', '.py', '.pyi'):
            original = subprocess.check_output(
                ['git', '-C', str(code), 'show', commit + ':AdaRES/' + name], timeout=120)
            if suffix in ('.py', '.pyi'):
                canonical = original.replace(b'\r\n', b'\n')
            else:
                import yaml
                decoded = yaml.safe_load(original)
                canonical = json.dumps(decoded, sort_keys=True,
                                       separators=(',', ':')).encode('utf-8')
            yaml_digest = hashlib.sha256(canonical).hexdigest()
            mappings = server.get('runtime_path_mappings', [])
            if suffix in ('.yaml', '.yml') and mappings:
                def adapt(value):
                    if isinstance(value, dict):
                        return {key: adapt(item) for key, item in value.items()}
                    if isinstance(value, list):
                        return [adapt(item) for item in value]
                    if isinstance(value, str):
                        for mapping in mappings:
                            old, new = mapping['source'], mapping['target']
                            if not old.startswith('/') or not new.startswith('/'):
                                raise ValueError('Runtime mapping must bind absolute paths')
                            if value == old or value.startswith(old.rstrip('/') + '/'):
                                value = new.rstrip('/') + value[len(old.rstrip('/')):]
                    return value
                adapted = json.dumps(adapt(decoded), sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')
                yaml_digest = [yaml_digest, hashlib.sha256(adapted).hexdigest()]
        checked_records.append((name, oid, yaml_digest))
    chunks, chunk = [], []
    for record in checked_records:
        if chunk and len(json.dumps(chunk + [record])) > 6000:
            chunks.append(chunk)
            chunk = []
        chunk.append(record)
    if chunk:
        chunks.append(chunk)
    for batch in chunks:
        program = f"""
import hashlib,json,pathlib
root=pathlib.Path({server['remote_code_root']!r}).resolve()
def within_root(path):
    try:path.resolve().relative_to(root)
    except ValueError:return False
    return True
assert (root/'.codex_source_commit').read_text().strip()=={commit!r}
bad=[]
for name,expected,yaml_digest in {batch!r}:
    path=root/name
    if not path.is_file() or not within_root(path):
        bad.append(name);continue
    data=path.read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\\0'+data).hexdigest()
    if actual!=expected:
        if yaml_digest is None:
            bad.append(name);continue
        if path.suffix in ('.py','.pyi'):
            canonical=data.replace(b'\\r\\n',b'\\n')
        else:
            import yaml
            canonical=json.dumps(yaml.safe_load(data),sort_keys=True,separators=(',',':')).encode('utf-8')
        expected_digests=yaml_digest if isinstance(yaml_digest,list) else [yaml_digest]
        if hashlib.sha256(canonical).hexdigest() not in expected_digests:bad.append(name)
print(json.dumps({{'ok':not bad,'paths':bad[:6]}}))
"""
        checked_probe(server, program, ssh)
