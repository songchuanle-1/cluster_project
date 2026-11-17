"""Opt-in, fail-closed research receipts and non-destructive deployment."""
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import tick_efficiency
import source_integrity
import experiment_first
import cluster_resume

REQUIRED_GATES = ("diagnosis", "controls", "native_backward", "resources",
                  "independence", "constraints")
OPTIONAL_GATES = ("derivation", "literature")
# Keep the complete receipt vocabulary for compatibility with existing
# receipt generators and historical receipts.
GATES = REQUIRED_GATES + OPTIONAL_GATES
STAGES = ("diagnosis", "design", "implementation", "validation", "admission",
          "deployment", "training", "complete", "rejected", "blocked")


def read(path, default=None):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default


def enabled(project):
    return read(Path(project) / "pipeline/closure_policy.json", {}).get("enabled") is True


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def artifact(project, entry):
    path = (Path(project) / entry["path"]).resolve()
    if not path.is_relative_to(Path(project).resolve()) or not path.is_file():
        raise ValueError("Missing or out-of-project artifact")
    if digest(path) != entry["sha256"]:
        raise ValueError("Artifact hash mismatch: " + str(path))
    return path


def frozen_legacy_candidates(project):
    """Grandfather unchanged terminal records, never new or edited evidence."""
    root = Path(project)
    policy = read(root / "pipeline/closure_policy.json", {})
    legacy = policy.get("legacy_terminal_snapshot")
    if not legacy:
        return {}
    if root.name != "AdaRES_project":
        raise ValueError("Legacy snapshot is restricted to AdaRES")
    snapshot = (root / legacy["path"]).resolve()
    if not snapshot.is_relative_to(root.resolve()) or not snapshot.is_file():
        raise ValueError("Legacy snapshot missing or outside project")
    if digest(snapshot) != legacy["sha256"]:
        raise ValueError("Legacy snapshot hash mismatch")
    records = read(snapshot, {}).get("research_work", {}).get("candidates", [])
    if len({record["id"] for record in records}) != len(records):
        raise ValueError("Legacy snapshot has duplicate candidates")
    return {record["id"]: record for record in records
            if record.get("stage") in ("closed", "rejected")}


def pending(project):
    data = read(Path(project) / "pipeline/research_work.json", {"candidates": []})
    return [c for c in data["candidates"]
            if c.get("stage") not in ("training", "complete", "rejected", "closed")]


def exclusive_gpu_slot_available(candidate, servers, active_tasks):
    """Queue opening only; the native runner must confirm live idle ownership."""
    name = candidate.get("required_server")
    server = next((item for item in servers if item.get("name") == name), None)
    if not server or server.get("max_tasks_per_gpu", 1) != 1:
        return False
    allowed = {str(gpu) for gpu in server.get("allowed_gpus", [])}
    relevant = [task for task in active_tasks if task.get("server") == name]
    if any(task.get("gpu") is None or str(task["gpu"]) not in allowed
           for task in relevant):
        return False
    occupied = {str(task["gpu"]) for task in relevant}
    return bool(allowed - occupied)


def revision_digest(revision):
    return hashlib.sha256(json.dumps(revision, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def candidate_progress(candidate):
    return {"stage": candidate.get("stage"),
            "evidence_sha256": revision_digest(candidate.get("evidence", []))}


def changed_candidate_ids(context, candidates):
    work = context.get("research_work", {})
    previous = work.get("progress_baselines")
    if previous is None:
        previous = {c["id"]: candidate_progress(c) for c in work.get("candidates", [])}
    return {c["id"] for c in candidates if previous.get(c["id"]) != candidate_progress(c)}


def scoped_revision_limit(root, candidate, default, previous=None):
    entry = candidate.get("implementation_revision_authorization")
    if not entry:
        return default
    authorization = read(artifact(root, entry), {})
    history = candidate.get("revision_history", [])
    preserved = bool(
        previous and previous.get("id") == candidate.get("id")
        and previous.get("stage") == candidate.get("stage")
        and previous.get("implementation_revision_authorization") == entry
        and previous.get("revision_history") == history
        and history and all(isinstance(r, dict) and r.get("result") in
                            ("passed", "failed", "inconclusive") for r in history))
    base = authorization.get("base_revision_count")
    if not isinstance(base, int) or isinstance(base, bool) or base < 0:
        raise ValueError("Invalid candidate-scoped implementation revision authorization")
    owner = read(Path(root) / "pipeline/execution_mode.json", {}).get("target_thread_id")
    if (authorization.get("scope") != "implementation_revision"
            or authorization.get("authorization_granted") is not True
            or authorization.get("candidate_id") != candidate.get("id")
            or authorization.get("additional_revisions") != 1
            or not authorization.get("human_reply")
            or not authorization.get("owner_thread_id")
            or not re.fullmatch(r"[0-9a-f]{64}", str(authorization.get("goal_sha256", "")))
            or authorization.get("base_revision_history_sha256") != revision_digest(history[:base])
            or (not preserved and (
                base != default or not owner or authorization.get("owner_thread_id") != owner
                or authorization["goal_sha256"] != digest(Path(root) / "pipeline/goal.json")))):
        raise ValueError("Invalid candidate-scoped implementation revision authorization")
    # An unchanged completed record is history, not permission for another operation.
    return base + 1


def validate_reopening(root, candidate, previous):
    if (previous and previous.get("stage") in ("rejected", "closed")
            and candidate.get("stage") != previous.get("stage")):
        authorization = candidate.get("reopen_authorization")
        if not authorization:
            raise ValueError("Historical rejection needs explicit reopen authorization")
        artifact(root, authorization)


def validate_revisions(root, candidate, previous=None):
    """Revision evidence is append-only; this does not certify scientific merit."""
    history = candidate.get("revision_history", [])
    old = (previous or {}).get("revision_history", [])
    if not isinstance(history, list) or len(history) < len(old):
        raise ValueError("Implementation revision history was removed")
    validate_reopening(root, candidate, previous)
    if not history:
        return
    limit = read(Path(root) / "pipeline/goal.json", {}).get(
        "pipeline_policy", {}).get("max_implementation_revisions", 2)
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
        raise ValueError("Invalid implementation revision budget")
    limit = scoped_revision_limit(root, candidate, limit, previous)
    if len(history) > limit:
        raise ValueError("Implementation revision budget exceeded")
    if previous:
        if any(candidate.get(k) != previous.get(k) for k in ("hypothesis", "hypothesis_id")):
            raise ValueError("Implementation revision changed the core hypothesis")
        if previous.get("failure_scope") == "hypothesis" and len(history) > len(old):
            raise ValueError("A falsified hypothesis cannot receive another local revision")
    mutable = {"result", "evidence", "result_evidence"}
    for index, revision in enumerate(history):
        if not isinstance(revision, dict):
            raise ValueError("Invalid implementation revision record")
        if revision.get("revision") != index + 1:
            raise ValueError("Implementation revision numbers must be consecutive")
        if revision.get("failure_scope") not in ("implementation", "inconclusive"):
            raise ValueError("A falsified hypothesis is not an implementation revision")
        if not all(revision.get(k) for k in (
                "reason", "change", "prediction", "failure_evidence", "preregistered_at")):
            raise ValueError("Implementation revision lacks a frozen test or failure evidence")
        try:
            registered = datetime.fromisoformat(revision["preregistered_at"])
            if registered.tzinfo is None or registered > datetime.now(timezone.utc):
                raise ValueError()
        except (TypeError, ValueError):
            raise ValueError("Implementation revision needs a valid preregistered_at") from None
        for entry in revision["failure_evidence"]:
            artifact(root, entry)
        result = revision.get("result")
        if result not in ("pending", "passed", "failed", "inconclusive"):
            raise ValueError("Invalid implementation revision result")
        if index and history[index - 1].get("result") == "pending":
            raise ValueError("Resolve the preceding revision before another attempt")
        evidence = revision.get("evidence", [])
        outputs = revision.get("result_evidence", evidence)
        if not isinstance(evidence, list) or not isinstance(outputs, list):
            raise ValueError("Implementation revision evidence must be a list")
        if result != "pending" or "result_evidence" in revision:
            if result != "pending" and not outputs:
                raise ValueError("Implementation revision result lacks evidence")
            # Frozen source/protocol inputs can precede registration; test outputs cannot.
            for entry in evidence:
                artifact(root, entry)
            for entry in outputs:
                if entry not in evidence:
                    raise ValueError("Implementation revision result evidence is not in the evidence archive")
                if artifact(root, entry).stat().st_mtime < registered.timestamp():
                    raise ValueError("Implementation revision cannot reuse pre-registration results")
        if index < len(old):
            earlier = old[index]
            if ({k: v for k, v in revision.items() if k not in mutable}
                    != {k: v for k, v in earlier.items() if k not in mutable}):
                raise ValueError("Implementation revision protocol was rewritten")
            if earlier.get("result") != "pending" and revision != earlier:
                raise ValueError("Completed implementation revision was rewritten")
            if earlier.get("result") == "pending":
                for field in ("evidence", "result_evidence"):
                    if not all(entry in revision.get(field, []) for entry in earlier.get(field, [])):
                        raise ValueError("Implementation revision evidence was removed")


def admission(project, task, *, completed=False):
    """Evidence is human/agent-reviewed; hashes prove identity, not scientific truth."""
    if completed and (task.get("status") not in ("done_complete", "done_earlystop")
                      or task.get("launch_verified") is not True):
        raise ValueError("Completed admission lacks successful terminal state or verified launch")
    if not task.get("admission_receipt"):
        raise ValueError("Missing admission receipt")
    receipt_path = (Path(project) / task["admission_receipt"]).resolve()
    if not receipt_path.is_relative_to(Path(project).resolve()):
        raise ValueError("Admission receipt outside project")
    receipt = read(receipt_path, {})
    if receipt.get("id") != task["id"] or receipt.get("config") != task["config"]:
        raise ValueError("Missing or mismatched admission receipt")
    commit = receipt.get("code_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or commit != task.get("code_commit"):
        raise ValueError("Admission commit mismatch")
    if receipt.get("goal_sha256") != digest(Path(project) / "pipeline/goal.json"):
        raise ValueError("Goal changed since admission")
    profile = receipt.get("profile", "legacy")
    if profile not in ("legacy", "experiment_first"):
        raise ValueError("Unknown admission profile")
    gates = REQUIRED_GATES
    if profile == "experiment_first":
        policy = experiment_first.effective(project)
        if not policy or receipt.get("authorization") != policy["authorization"]:
            raise ValueError("Experiment-first admission is not authorized for this tick")
        experiment_first.validate_smoke(project, receipt)
        gates = experiment_first.GATES
    for name in gates:
        gate = receipt.get("gates", {}).get(name, {})
        if gate.get("passed") is not True or not gate.get("evidence"):
            raise ValueError("Incomplete admission gate: " + name)
        for evidence in gate["evidence"]:
            artifact(project, evidence)
    artifact(project, receipt["decision"])
    candidates = read(Path(project) / "pipeline/research_work.json", {}).get("candidates", [])
    matches = [c for c in candidates
               if c.get("experiment_id", c.get("id")) == task["id"]
               or c.get("id") == receipt.get("candidate_id")]
    if len(matches) > 1:
        raise ValueError("Ambiguous admission candidate")
    if matches:
        candidate = matches[0]
        context = bound_foreground_context(project) or {}
        work = context.get("research_work", {})
        previous = work.get("revision_baselines", {}).get(candidate["id"])
        if previous is None:
            previous = next((c for c in work.get("candidates", [])
                             if c["id"] == candidate["id"]), None)
        validate_reopening(project, candidate, previous)
        stages = ("validation", "admission", "deployment", "training")
        if completed:
            stages += ("complete",)
        if candidate.get("stage") not in stages:
            raise ValueError("Admission receipt does not bind a current passed candidate stage")
    if matches and matches[0].get("revision_history"):
        candidate = matches[0]
        validate_revisions(project, candidate)
        revision = candidate["revision_history"][-1]
        if (revision.get("result") != "passed"
                or receipt.get("candidate_id") != candidate["id"]
                or receipt.get("implementation_revision_sha256") != revision_digest(revision)):
            raise ValueError("Admission receipt does not bind the current passed implementation revision")
    elif receipt.get("implementation_revision_sha256"):
        raise ValueError("Admission receipt refers to a missing implementation revision")
    return receipt


def git(code, *args):
    return subprocess.check_output(["git", "-C", str(code), *args],
                                   text=True, timeout=120).strip()


def validate_adares_server(project, server):
    """Keep the original server, or verify the user's scoped server-1 grant."""
    if Path(project).name != 'AdaRES_project':
        raise ValueError('AdaRES runtime restricted to its authorized project')
    if server.get('name') == 'server-2':
        return
    if server.get('name') != 'server-1' or server.get('host') != '192.168.1.175':
        raise ValueError('AdaRES runtime server is not authorized')
    grant = read(Path(project) / (server.get('resource_authorization') or '__missing__'), {})
    if not (grant.get('authorization_granted') is True
            and grant.get('project') == 'AdaRES_project'
            and grant.get('server') == 'server-1'
            and grant.get('host') == server['host']
            and grant.get('allowed_gpus') == server.get('allowed_gpus') == [0]
            and grant.get('expected_hostname') == server.get('expected_hostname') == 'dl02-MS-7B73'
            and server.get('max_tasks_per_gpu') == 1):
        raise ValueError('AdaRES server-1 requires its exact scoped resource grant')


def safe_sync(project, code, server, ssh):
    """Never stash, clean, reset, auto-commit, or overwrite a diverged checkout."""
    commit = git(code, "rev-parse", "HEAD")
    root = server["remote_code_root"]
    qroot = shlex.quote(root)
    policy = read(Path(project) / "pipeline/closure_policy.json", {})
    if policy.get("sync_strategy") == "adares_additive_marker":
        if Path(project).name != "AdaRES_project":
            raise ValueError("AdaRES marker sync cannot be used by another project")
        script = Path(project) / "scripts/sync.sh"
        validate_adares_server(project, server)
        if not script.is_file():
            raise ValueError("AdaRES additive sync script/server unavailable")
        marker = ssh(server["host"], server["user"],
                     f"cat {shlex.quote(root + '/.codex_source_commit')}").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", marker):
            raise ValueError("Remote source marker unavailable")
        source_integrity.verify_marker(code, marker, server, ssh)
        if marker != commit:
            from pipeline_monitor import bash_executable
            result = subprocess.run(
                [bash_executable(), str(script), server["name"]],
                cwd=str(project), capture_output=True, text=True, timeout=180)
            if result.returncode:
                raise ValueError("AdaRES additive sync failed: " + result.stderr[-300:])
        verified = ssh(server["host"], server["user"],
                       f"cat {shlex.quote(root + '/.codex_source_commit')}").strip()
        if verified != commit:
            raise ValueError("Remote source marker did not match admitted HEAD")
        if marker != commit:
            source_integrity.verify_marker(code, commit, server, ssh)
        return True
    remote = ssh(server["host"], server["user"], f"git -C {qroot} rev-parse HEAD").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", remote):
        raise ValueError("Remote source identity unavailable")
    mappings = [(item["source"], server[item["server_key"]].rstrip("/"))
                for item in policy.get("path_mappings", [])]
    source_integrity.verify_git(server, remote, mappings, ssh)
    if remote != commit:
        if not re.fullmatch(r"[0-9a-f]{40}", remote):
            raise ValueError("Remote source identity unavailable")
        ref = "refs/heads/codex-admitted-" + commit[:12]
        target = f'{server["user"]}@{server["host"]}:{root}'
        git(code, "push", target, f"{commit}:{ref}")
        ssh(server["host"], server["user"],
            f"git -C {qroot} -c merge.autoStash=false merge --ff-only {ref}")
    if ssh(server["host"], server["user"], f"git -C {qroot} rev-parse HEAD").strip() != commit:
        raise ValueError("Remote fast-forward verification failed")
    if remote != commit:
        source_integrity.verify_git(server, commit, mappings, ssh)
    return True


def safe_launch(project, server, task, gpu, ssh):
    """Return PID and unique log; never invoke legacy remote_train.sh."""
    root = server["remote_code_root"]
    config = task["config"]
    isolated = task.get("isolated_runtime") is not None
    if isolated:
        from isolated_runtime import runtime_server
        from pipeline_monitor import load_servers
        expected = runtime_server(project, load_servers(project)[task["server"]], task)
        if (server["remote_code_root"] != expected["remote_code_root"]
                or server["conda_source"] != expected["conda_source"] or str(gpu) != "1"):
            raise ValueError("Isolated launch differs from the admitted human runtime scope")
    if not re.fullmatch(r"[0-9]+", str(gpu)):
        raise ValueError("Only single GPU launch is supported")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = f"{root}/logs/train_{Path(config).stem}_{timestamp}.log"
    # Only this candidate's deployment paths are transformed.
    policy = read(Path(project) / "pipeline/closure_policy.json", {})
    resume = cluster_resume.requested(project, task)
    contract = None
    if resume:
        # Recheck admission and source at launch, including direct callers.
        admission(project, task)
        from pipeline_monitor import find_local_code_dir
        contract = cluster_resume.verify_source(
            project, find_local_code_dir(project), server, task, gpu, ssh)
    if policy.get("launcher") == "multiview_hydra":
        return launch_multiview(server, task, gpu, log, ssh)
    if policy.get("launcher") == "adares_native":
        return launch_adares(project, server, task, gpu, log, ssh)
    local = policy["path_mappings"]
    mappings = [(item["source"], server[item["server_key"]].rstrip("/")) for item in local]
    config_write = "" if resume else "p.write_text(yaml.safe_dump(c,sort_keys=False))"
    config_read = "yaml.safe_load(p.read_text())" if resume else "adapt(yaml.safe_load(p.read_text()))"
    resume_args = ["--resume", contract["resume_from"]] if resume else []
    checkpoint_check = cluster_resume.checkpoint_check(contract) if resume else ""
    program = f"""
import json,os,pathlib,subprocess,sys,yaml
root=pathlib.Path({root!r})
cfg={config!r}
p=(root/cfg).resolve()
try:
    p.relative_to(root.resolve())
except ValueError:
    raise RuntimeError("Candidate config outside remote code root")
assert p.is_file()
for cmdfile in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
    try: cmd=cmdfile.read_bytes().split(b'\\0')
    except OSError: continue
    if b'tools/train.py' in cmd and cfg.encode() in cmd:
        raise RuntimeError('Candidate already running; reconcile before retry')
def adapt(x):
    if isinstance(x,dict): return {{k:adapt(v) for k,v in x.items()}}
    if isinstance(x,list): return [adapt(v) for v in x]
    if isinstance(x,str):
        for a,b in {mappings!r}: x=x.replace(a,b)
    return x
c={config_read}
assert pathlib.Path(c['model']['data_root']).is_dir()
assert pathlib.Path(c['train']['pretrain']).is_file()
{config_write}
env=os.environ.copy()
if {isolated!r}:env['PYTHONDONTWRITEBYTECODE']='1'
env['PYTHONPATH']=str(root)+':'+str(root/'framework/lib')+':'+env.get('PYTHONPATH','')
pyver='.'.join(str(value) for value in sys.version_info[:2])
env['LD_LIBRARY_PATH']=(env['CONDA_PREFIX']+'/lib:'+env['CONDA_PREFIX']+
    '/lib/python'+pyver+'/site-packages/torch/lib:'+env.get('LD_LIBRARY_PATH',''))
# Bugfix 2026-09-16: torch_shm_manager needs a writable temp dir for DataLoader
# worker sockets. On server-6 the root filesystem (and therefore /tmp) reached 100%
# full, so every launch died with "could not generate a random directory for manager
# socket". Prefer a project-local temp dir on the data volume when one is writable,
# and keep the inherited TMPDIR otherwise.
# Honor a configured short IPC path; deep deployment paths can exceed AF_UNIX limits.
_td=pathlib.Path(env.get('TMPDIR') or str(pathlib.Path(root).parent/'pipeline/tmp'))
try:
    _td.mkdir(parents=True,exist_ok=True)
except OSError:
    _td=None
if _td is not None and os.access(str(_td),os.W_OK):
    env['TMPDIR']=str(_td)
{checkpoint_check}
(root/'logs').mkdir(exist_ok=True)
with open({log!r},'ab',buffering=0) as out:
    proc=subprocess.Popen({(['python', '-B'] if isolated else ['python'])!r}+['tools/train.py',cfg,'--gpu_ids',{str(gpu)!r},'--num_gpus','1']+{resume_args!r},
        cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
(root/'logs'/('.pid_'+pathlib.Path(cfg).stem)).write_text(str(proc.pid))
print(json.dumps(dict(pid=proc.pid,log={log!r})))
"""
    python_command = "PYTHONDONTWRITEBYTECODE=1 python -B" if isolated else "python"
    cmd = (f"source {shlex.quote(server['conda_source'])} && "
           f"conda activate {shlex.quote(server['conda_env'])} && {python_command} -c {shlex.quote(program)}")
    result = json.loads(ssh(server["host"], server["user"], cmd))
    if not isinstance(result.get("pid"), int) or result.get("log") != log:
        raise ValueError("Invalid launch response; reconcile remote before retry")
    return result


def launch_adares(project, server, task, gpu, log, ssh):
    """Launch the project-native single-GPU environment after marker verification."""
    validate_adares_server(project, server)
    root = server["remote_code_root"]
    config = task["config"]
    if not re.fullmatch(r"configs_song/model_paper5/[A-Za-z0-9_]+\.yaml", config):
        raise ValueError("Invalid AdaRES config")
    if str(gpu) not in {"0", "1"}:
        raise ValueError("AdaRES GPU outside authorized pair")
    if (server.get('allowed_gpus') is not None
            and str(gpu) not in {str(value) for value in server['allowed_gpus']}):
        raise ValueError('AdaRES GPU not in the current server whitelist')
    program = f"""
import json,os,pathlib,subprocess
root=pathlib.Path({root!r}).resolve()
cfg={config!r}
p=(root/cfg).resolve()
try: p.relative_to(root)
except ValueError: raise RuntimeError('Candidate config outside remote root')
assert p.is_file()
assert (root/'tools/train.py').is_file()
assert (root/'.codex_source_commit').read_text().strip()=={task['code_commit']!r}
expected_hostname={server.get('expected_hostname')!r}
if expected_hostname:
    assert subprocess.check_output(['hostname']).decode().strip()==expected_hostname
for item in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
    try: args=item.read_bytes().split(b'\\0')
    except OSError: continue
    if b'tools/train.py' in args and cfg.encode() in args:
        raise RuntimeError('Candidate already running; reconcile before retry')
env=os.environ.copy()
env['PYTHONPATH']=':'.join([str(root),str(root/'ipdn/lib'),
    {server['site_packages']!r},{server['pointnet_egg']!r}])
env['PYTHONDONTWRITEBYTECODE']='1'
if {server.get('runtime_library_path', '')!r}:
    env['LD_LIBRARY_PATH']={server.get('runtime_library_path', '')!r}+':'+env.get('LD_LIBRARY_PATH','')
if {server.get('runtime_path_mappings', [])!r}:
    import yaml
    def adapt(value):
        if isinstance(value,dict):return {{key:adapt(item) for key,item in value.items()}}
        if isinstance(value,list):return [adapt(item) for item in value]
        if isinstance(value,str):
            for mapping in {server.get('runtime_path_mappings', [])!r}:
                old,new=mapping['source'].rstrip('/'),mapping['target'].rstrip('/')
                if value==old or value.startswith(old+'/'):value=new+value[len(old):]
        return value
    original=yaml.safe_load(p.read_text())
    mapped=adapt(original)
    assert pathlib.Path(mapped['train']['pretrain']).is_file()
    assert pathlib.Path(mapped['data']['train']['data_root']).is_dir()
    p.write_text(yaml.safe_dump(mapped,sort_keys=False))
(root/'logs').mkdir(exist_ok=True)
with open({log!r},'ab',buffering=0) as out:
    proc=subprocess.Popen([{server['python']!r},'-B','-S','tools/train.py',cfg,
        '--num_gpus','1','--gpu_ids',{str(gpu)!r}],
        cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,
        start_new_session=True)
(root/'logs'/('.pid_'+p.stem)).write_text(str(proc.pid))
print(json.dumps(dict(pid=proc.pid,log={log!r})))
"""
    cmd = f"{shlex.quote(server['python'])} -c {shlex.quote(program)}"
    result = json.loads(ssh(server["host"], server["user"], cmd))
    if not isinstance(result.get("pid"), int) or result.get("log") != log:
        raise ValueError("Invalid AdaRES launch response; reconcile remote before retry")
    return result


def multiview_program(root, config, gpu, log):
    """Keep Hydra defaults and package directives intact; no YAML rewriting."""
    if not re.fullmatch(r"configs/train/[A-Za-z0-9_]+\.yaml", config):
        raise ValueError("Invalid multiview config")
    if not re.fullmatch(r"[0-9]+", str(gpu)):
        raise ValueError("Invalid GPU")
    override = "train=" + Path(config).stem
    return f"""
import json,os,pathlib,subprocess,sys
root=pathlib.Path({root!r}).resolve()
config=root/{config!r}
assert config.is_file() and config.resolve().is_relative_to(root)
assert (root/'scripts/train_mvggt.py').is_file()
for item in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
    try: args=item.read_bytes().split(b'\\0')
    except OSError: continue
    if b'scripts/train_mvggt.py' in args and {override.encode()!r} in args:
        raise RuntimeError('Candidate already running; reconcile before retry')
env=os.environ.copy()
env['MVGGT_GPU']={str(gpu)!r}
env.pop('CUDA_VISIBLE_DEVICES',None)
env['PYTHONDONTWRITEBYTECODE']='1'
(root/'logs').mkdir(exist_ok=True)
with open({log!r},'ab',buffering=0) as out:
    proc=subprocess.Popen([sys.executable,'-m','accelerate.commands.launch',
        '--num_processes=1','scripts/train_mvggt.py',{override!r}],
        cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,
        start_new_session=True)
print(json.dumps(dict(pid=proc.pid,log={log!r})))
"""


def launch_multiview(server, task, gpu, log, ssh):
    program = multiview_program(server["remote_code_root"], task["config"], gpu, log)
    cmd = (f"source {shlex.quote(server['conda_source'])} && "
           f"conda activate {shlex.quote(server['conda_env'])} && python -c {shlex.quote(program)}")
    result = json.loads(ssh(server["host"], server["user"], cmd))
    if not isinstance(result.get("pid"), int) or result.get("log") != log:
        raise ValueError("Invalid launch response; reconcile remote before retry")
    return result


def steps(text):
    pattern = (r"Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+"
               r"|Epoch:\s*\[(\d+)\]\s*\[\s*(\d+)/\d+\]")
    return [tuple(int(v) for v in match if v) for match in re.findall(pattern, text)]


def verify_progress(server, task, ssh, wait_s=90):
    deadline = time.monotonic() + wait_s
    while True:
        cmd = (f"if kill -0 {int(task['pid'])} 2>/dev/null; then "
               f"tail -c 24000 {shlex.quote(task['log'])}; else echo __DEAD__; fi")
        text = ssh(server["host"], server["user"], cmd)
        if "__DEAD__" in text or any(x in text for x in ("Traceback", "CUDA out of memory", "RuntimeError")):
            return False
        if len(set(steps(text))) >= 2 and max(s for _, s in steps(text)) > 0:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(3)


def validate_pending_limit(context, candidates, queue, root=None):
    reserve = context.get("research_work", {})
    limit = reserve.get("pending_limit")
    if limit is None:
        return
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
        raise ValueError("Invalid pending candidate limit")
    queued = [t for group in queue.get("gpu_queues", {}).values() for t in group]
    states = context.get("queue", {}).get("dependency_states", {})
    if reserve.get("pending_scope") == "actionable" and root is not None:
        from pipeline_monitor import dependency_states
        dependencies = {d for t in queued for d in (t.get("depends_on") or [])}
        states = dependency_states(root, queue, dependencies)
    current = tick_efficiency.pending_ids(
        candidates, queued, actionable_only=reserve.get("pending_scope") == "actionable",
        states=states)
    previous = set(reserve.get("pending_ids", []))
    if len(current) > limit and current - previous:
        raise ValueError("Pending candidate limit exceeded; advance or resolve existing work")


def new_tick_experiments(root, context):
    known = context.get("queue", {}).get("known_experiment_ids")
    if known is None:
        return {}
    known = set(known)
    added = {}
    for path in (Path(root) / "pipeline/experiments").glob("*.json"):
        record = read(path, {})
        # Match the lifecycle inventory's declared ID, not a legacy filename alias.
        tid = str(record.get("id") or path.stem).strip() if isinstance(record, dict) else path.stem
        if tid in known:
            continue
        if tid in added:
            raise ValueError("Duplicate archived experiment identity: " + tid)
        added[tid] = path
    return added


def tick_admission_delta(root, context, queue):
    """Inventory admission changes without granting scientific or launch approval."""
    snapshot = context.get("queue", {})
    if "recorded_ids" not in snapshot or "candidate_budget" not in snapshot:
        return None  # Old snapshots cannot establish a budget-met early close.
    budget = snapshot["candidate_budget"]
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("Invalid tick admission budget")
    recorded = set(snapshot["recorded_ids"])
    active = {"waiting", "claiming", "running"}
    old_active = snapshot.get("monitored_active_tasks", snapshot.get("active_tasks"))
    active_ids = ({t.get("id") or t.get("exp_id") for t in old_active}
                  if old_active is not None else recorded)
    added, seen = {}, set()
    for server, tasks in queue.get("gpu_queues", {}).items():
        for task in tasks:
            tid = task.get("id") or task.get("exp_id")
            if not tid or tid in seen:
                raise ValueError("Missing or duplicate queue experiment identity")
            seen.add(tid)
            if tid not in recorded or ((task.get("status") or task.get("state")) in active
                                       and tid not in active_ids):
                added[tid] = (server, task)
    spent = set(added)
    # Archiving a short run must not erase its consumption of this tick's budget.
    spent.update(new_tick_experiments(root, context))
    if len(spent) > budget:
        raise ValueError("Tick admission budget exceeded")
    authorized = ({s["name"] for s in snapshot["servers"]}
                  if "servers" in snapshot else set(queue.get("gpu_queues", {})))
    for server, task in added.values():
        if server not in authorized:
            raise ValueError("New admission is not on an authorized dispatch server")
    return budget, added


def validate_tick_admissions(root, context, queue):
    """Credit only receipt-backed admissions; existing dispatch is not new admission."""
    delta = tick_admission_delta(root, context, queue)
    if delta is None:
        return False
    budget, added = delta
    archives = new_tick_experiments(root, context)
    for tid in archives:
        journal = Path(root) / "pipeline/archive_pending" / (
            hashlib.sha256(tid.encode("utf-8")).hexdigest() + ".json")
        if journal.exists():
            raise ValueError("Current tick archival is incomplete: " + tid)
    credited = 0
    for server, task in added.values():
        status = task.get("status") or task.get("state")
        admission(root, task, completed=status in ("done_complete", "done_earlystop"))
        if status in ("claiming", "running") and task.get("launch_verified") is not True:
            raise ValueError("Training launch still requires progress verification: " + task["id"])
        if status in ("waiting", "claiming", "running") or (
                status in ("done_complete", "done_earlystop")
                and task.get("launch_verified") is True):
            credited += 1
    snapshot = context.get("queue", {})
    authorized = ({s["name"] for s in snapshot["servers"]}
                  if "servers" in snapshot else set(queue.get("gpu_queues", {})))
    for tid, path in archives.items():
        if tid in added:
            continue
        task = read(path, {})
        if not isinstance(task, dict) or task.get("id") != tid:
            raise ValueError("Invalid archived experiment identity")
        if task.get("status") not in ("done_complete", "done_earlystop"):
            continue
        if not re.fullmatch(r"[0-9a-f]{32}", str(task.get("archive_id", ""))):
            raise ValueError("Missing completed archive identity: " + tid)
        if task.get("server") not in authorized:
            raise ValueError("Archived admission is not on an authorized dispatch server")
        admission(root, task, completed=True)
        credited += 1
    return budget > 0 and credited == budget


def bound_foreground_context(root):
    """Return only a snapshot sealed by the current foreground lease."""
    headless = Path(root) / "pipeline/headless"
    owner = read(headless / ".foreground.lockdir/owner.json", {})
    expected = owner.get("context_sha256")
    if not expected:
        return None
    path = headless / ".tick_context.json"
    if not path.is_file() or digest(path) != expected:
        raise ValueError("Foreground dispatch snapshot missing or changed")
    return read(path)


def validate_foreground_dispatch_budget(root, queue, task):
    """Enforce an owned tick's bound before sync/launch, never during fresh preflight."""
    context = bound_foreground_context(root)
    if context is None:
        return
    snapshot = context.get("queue", {})
    previous = snapshot.get("monitored_active_tasks", snapshot.get("active_tasks"))
    if previous is not None and any(
            (t.get("id") or t.get("exp_id")) == task.get("id") for t in previous):
        return  # Existing queued training may proceed even if new admissions are blocked.
    tick_admission_delta(root, context, queue)


def validate_tick_handoff(context, work, quota_met):
    """Allow bounded carryover, never missing evidence or unchanged whole-tick work."""
    handoff = work.get("tick_handoff", {})
    # Old handoffs remain history; they never authorize this tick's deferral.
    if handoff.get("tick_started_at") != context["generated_at"]:
        return set()
    ids = handoff.get("candidate_ids")
    if (not isinstance(ids, list) or not ids or any(not isinstance(cid, str) for cid in ids)
            or len(set(ids)) != len(ids) or not handoff.get("resume_condition")):
        raise ValueError("Invalid current tick handoff")
    reason = handoff.get("reason")
    if reason == "admission_budget_met":
        allowed = quota_met
    elif reason == "tick_deadline_near":
        deadline = context.get("deadline_at")
        end = datetime.fromisoformat(deadline) if deadline else None
        allowed = bool(end and end.tzinfo and
                       (end - datetime.now(timezone.utc)).total_seconds() <= 180)
    else:
        allowed = False
    if not allowed:
        raise ValueError("Tick handoff has no satisfied admission budget or near deadline")
    candidates = work.get("candidates", [])
    changed = changed_candidate_ids(context, candidates)
    if not changed:
        raise ValueError("Tick handoff cannot replace actual candidate progress")
    previous_ids = {c["id"] for c in context.get("research_work", {}).get("candidates", [])}
    unchanged = {c["id"] for c in candidates if c["id"] in previous_ids and c["id"] not in changed
                 and c.get("stage") in ("diagnosis", "design", "implementation",
                                       "validation", "admission", "deployment")}
    if set(ids) != unchanged:
        raise ValueError("Tick handoff must name exactly the preserved unchanged executable candidates")
    return set(ids)


def postflight(project):
    root = Path(project)
    context = read(root / "pipeline/headless/.tick_context.json")
    preflight = context["preflight"]
    # check_goal.py uses 0/1/4 for phase status, not preflight failure.
    if preflight.get("monitor_rc", 1) != 0 or preflight.get("goal_rc") not in (0, 1, 4):
        raise ValueError("Preflight failed")
    since = datetime.fromisoformat(context["generated_at"]).timestamp()
    reports = [p for p in (root / "pipeline/reports").glob("summary_*.md")
               if p.stat().st_mtime >= since]
    if not reports:
        raise ValueError("Missing current tick report")
    text = max(reports, key=lambda p: p.stat().st_mtime).read_text(encoding="utf-8")
    if not all(re.search(rf"^##\s+{n}[.\s]", text, re.M) for n in range(6)):
        raise ValueError("Incomplete six-section report")
    if context["mode"] != "steady" and "<!-- RESEARCH_NOTES_PENDING -->" in text:
        raise ValueError("Research report still lacks this tick's action/decision notes")
    queue = read(root / "pipeline/queue.json", {"gpu_queues": {}})
    reserve = context.get("research_work", {})
    if context["mode"] == "design" and reserve.get("reserve_only"):
        original_ids = set(context.get("queue", {}).get("recorded_ids", []))
        if any(task.get("id") not in original_ids
               for group in queue["gpu_queues"].values() for task in group):
            raise ValueError("Reserve-only research cannot add queue entries or launch training")
    for tasks in queue["gpu_queues"].values():
        for task in tasks:
            if (task.get("launch_verification") == "pending_progress"
                    and task.get("status") in ("waiting", "claiming", "running")):
                raise ValueError("Training launch still requires progress verification: " + task["id"])
    quota_met = validate_tick_admissions(root, context, queue)
    if context["mode"] == "steady":
        if reserve.get("pending_limit") is not None:
            current_work = read(root / "pipeline/research_work.json", {})
            validate_pending_limit(context, current_work.get("candidates", []), queue, root)
        return
    memory = root / "pipeline/codex_memory.md"
    content = memory.read_text(encoding="utf-8")
    required = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                "Closed Or Failed Directions", "Running And Queue", "Open Questions And Risks", "Last Tick")
    if memory.stat().st_mtime < since or len(content.splitlines()) >= 200 or not all(
            "## " + name in content for name in required):
        raise ValueError("Memory snapshot missing/stale/invalid")
    work = read(root / "pipeline/research_work.json", {})
    candidates = work.get("candidates", [])
    if context["mode"] == "design" and not candidates:
        raise ValueError("Design tick has no durable candidate disposition")
    simple = context.get("experiment_first", {}).get("enabled") is True
    deferred_ids = set() if simple else validate_tick_handoff(context, work, quota_met)
    validate_work(root, context, candidates, queue, deferred_ids=deferred_ids)
    validate_pending_limit(context, candidates, queue, root)
    if simple:
        experiment_first.validate_outcome(root, context, candidates, queue)
        return
    if context["mode"] == "design" and (
            context.get("queue", {}).get("candidate_budget", 0) > 0
            or reserve.get("reserve_only")):
        previous = {item["id"]: item for item in
                    context.get("research_work", {}).get("candidates", [])}
        changed_ids = changed_candidate_ids(context, candidates)
        progressed = bool(changed_ids)
        if not progressed:
            raise ValueError(
                "Capacity-gap design made no durable candidate progress; "
                "create a stable diagnosis candidate and run its next test before stopping")
        if quota_met:
            return
        if reserve.get("reserve_only"):
            known = reserve.get("progress_baselines", previous)
            created = [c for c in candidates if c["id"] not in known]
            if len(created) > reserve.get("reserve_budget", 0):
                raise ValueError("Research reserve creation budget exceeded")
            return
        if read(root / "pipeline/goal.json", {}).get("pipeline_policy", {}).get(
                "research_on_capacity_gap") is True:
            whitelisted = {server["name"] for server in
                           context["queue"].get("servers", [])} if context["queue"].get(
                               "servers") else set(queue["gpu_queues"])
            active = sum(task.get("status") in ("running", "claiming", "waiting")
                         for server, group in queue["gpu_queues"].items()
                         if server in whitelisted for task in group)
            capacity = context["queue"].get("target_active", 0)
            if active < capacity:
                active_research = [
                    item for item in candidates
                    if item.get("stage") in ("diagnosis", "design", "implementation",
                                             "validation", "admission", "deployment")
                ]
                deadline = context.get("deadline_at")
                remaining = ((datetime.fromisoformat(deadline) -
                              datetime.now(datetime.fromisoformat(deadline).tzinfo)
                              ).total_seconds() if deadline else float("inf"))
                if active_research:
                    if remaining > 180:
                        raise ValueError(
                            "Capacity gap remains with executable research: "
                            + ",".join(item["id"] for item in active_research))
                    # Integrity checks have already run. Only further research
                    # may be deferred at the deadline, not evidence validation.
                    return
                cycle = work.get("design_cycle", {})
                if cycle.get("stop_reason") not in (
                        "independent_routes_exhausted", "external_resource_blocked",
                        "tick_deadline_near", "goal_phase_hold", "no_information_gain"):
                    raise ValueError(
                        "Capacity gap remains: continue an executable candidate "
                        "(including a newly created diagnosis candidate) or document "
                        "a valid design-cycle stop reason")
                if not cycle.get("attempted_ids") or not cycle.get("resume_condition"):
                    raise ValueError("Incomplete design-cycle stop disposition")
                if not changed_ids.intersection(cycle["attempted_ids"]):
                    raise ValueError("Design-cycle stop must cite this tick's candidate progress")
                for entry in cycle.get("evidence", []):
                    artifact(root, entry)
                if not cycle.get("evidence"):
                    raise ValueError("Design-cycle stop lacks hashed evidence")
                if (cycle["stop_reason"] == "no_information_gain" or
                        (cycle["stop_reason"] == "independent_routes_exhausted" and remaining > 180)):
                    validate_early_stop(root, context, candidates, cycle)
                if cycle["stop_reason"] == "tick_deadline_near":
                    if not deadline:
                        raise ValueError("Tick deadline stop lacks scheduler deadline")
                    if remaining > 180:
                        raise ValueError("Tick deadline is not near")
                if cycle["stop_reason"] == "external_resource_blocked" and not any(
                        item.get("stage") == "blocked" and item.get("blocker") and
                        item.get("retry_after") and item.get("unblock_condition")
                        for item in candidates):
                    raise ValueError("External resource stop lacks blocked candidate")


def validate_early_stop(root, context, candidates, cycle):
    """Evidence allows early termination, never admission or fake rejection."""
    if not cycle.get("no_gain_reason") or not cycle.get("resume_condition"):
        raise ValueError("Early stop needs no_gain_reason and resume_condition")
    try:
        retry = datetime.fromisoformat(cycle["retry_after"])
        now = datetime.now(timezone.utc)
        delay = (retry - now).total_seconds()
        if retry.tzinfo is None or not 0 < delay <= 4 * 3600:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise ValueError("Early stop needs a future retry_after within four hours") from None
    active = ("diagnosis", "design", "implementation", "validation", "admission", "deployment")
    if any(c.get("stage") in active for c in candidates):
        raise ValueError("Early stop cannot abandon executable research")
    changed_ids = changed_candidate_ids(context, candidates)
    current = {c["id"]: c for c in candidates}
    results = cycle.get("attempt_results", [])
    if len({r.get("candidate_id") for r in results}) < 2 or len({
            r.get("hypothesis_id") for r in results if r.get("hypothesis_id")}) < 2:
        raise ValueError("Early stop needs two independently tested routes")
    since = datetime.fromisoformat(context["generated_at"]).timestamp()
    for result in results:
        cid = result.get("candidate_id")
        candidate = current.get(cid, {})
        if cid not in cycle.get("attempted_ids", []) or candidate.get("stage") not in ("rejected", "blocked"):
            raise ValueError("Early stop tests need durable rejected/blocked dispositions")
        if cid not in changed_ids:
            raise ValueError("Early stop cannot recycle unchanged candidate evidence")
        if not all(result.get(k) for k in ("hypothesis_id", "test", "result", "evidence")):
            raise ValueError("Early stop test result is incomplete")
        for entry in result["evidence"]:
            if artifact(root, entry).stat().st_mtime < since:
                raise ValueError("Early stop requires evidence produced in this tick")


def validate_work(root, context, candidates, queue, deferred_ids=()):
    """Validate durable evidence regardless of capacity or remaining tick time."""
    seen = set()
    legacy = frozen_legacy_candidates(root)
    old_by_id = {c["id"]: c for c in context.get("research_work", {}).get("candidates", [])}
    revision_baselines = context.get("research_work", {}).get("revision_baselines", {})
    old_by_id.update(revision_baselines)
    revised_ids = {cid for cid, c in revision_baselines.items() if c.get("revision_history")}
    if revised_ids - {c["id"] for c in candidates}:
        raise ValueError("Implementation revision history was removed")
    for candidate in candidates:
        historical = candidate["id"] in legacy and candidate == legacy[candidate["id"]]
        if (candidate["id"] in seen
                or candidate.get("stage") not in STAGES + ("closed",)
                or (candidate.get("stage") == "closed" and not historical)):
            raise ValueError("Duplicate candidate or invalid stage")
        seen.add(candidate["id"])
        if not candidate.get("next_action") or not candidate.get("evidence"):
            raise ValueError("Missing actionable disposition/evidence")
        if not historical:
            for evidence in candidate["evidence"]:
                artifact(root, evidence)
        validate_revisions(root, candidate, old_by_id.get(candidate["id"]))
        if candidate["stage"] == "blocked":
            if not all(candidate.get(k) for k in (
                    "blocker", "retry_after", "unblock_condition")):
                raise ValueError("Blocked candidate needs retry and unblock condition")
            try:
                retry = datetime.fromisoformat(candidate["retry_after"])
            except (ValueError, TypeError):
                raise ValueError("Blocked candidate needs valid retry_after") from None
            if retry.tzinfo is None or retry.utcoffset() is None:
                raise ValueError("Blocked candidate needs timezone-aware retry_after")
            if candidate.get("blocker_kind") == "exclusive_gpu_slot":
                queue_state = context.get("queue", {})
                server = next((item for item in queue_state.get("servers", [])
                               if item.get("name") == candidate.get("required_server")),
                              None)
                if not server or server.get("max_tasks_per_gpu", 1) != 1:
                    raise ValueError("Blocked GPU candidate lacks authorized single-task server")
                if exclusive_gpu_slot_available(
                        candidate, queue_state.get("servers", []),
                        queue_state.get("active_tasks", [])):
                    # A queue opening is not proof of physical GPU idleness:
                    # foreign processes and graphics workloads are outside it.
                    import gpu_occupation
                    try:
                        gpu_occupation.validate_block(root, context, candidate, server, queue)
                    except ValueError as error:
                        raise ValueError("Blocked GPU candidate has a queue opening without "
                                         "valid live occupation evidence: " + str(error)) from None
    old = context.get("research_work", {}).get("candidates", [])
    for previous in old:
        current = next((c for c in candidates if c["id"] == previous["id"]), None)
        if current is None:
            raise ValueError("Unfinished candidate silently removed")
        if current["id"] in legacy and current == legacy[current["id"]]:
            continue
        # Timestamp-only edits or reworded next_action do not constitute progress.
        if (current.get("stage") == previous.get("stage")
                and current.get("evidence") == previous.get("evidence")
                and current["stage"] not in ("blocked", "complete", "rejected")
                and not context.get("experiment_first", {}).get("enabled")
                and current["id"] not in deferred_ids):
            raise ValueError("Unfinished candidate made no durable progress; "
                             "a budget/deadline carryover needs a valid current tick_handoff")
    for current in candidates:
        if current["stage"] == "training":
            tasks = [t for group in queue["gpu_queues"].values() for t in group
                     if t.get("id") == current.get("experiment_id", current["id"])]
            if len(tasks) != 1 or not tasks[0].get("launch_verified"):
                raise ValueError("Training disposition lacks verified launch")


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--require-enabled", action="store_true")
    args = parser.parse_args(argv)
    project = Path(os.environ.get("PROJECT_ROOT", "D:/project")) / args.project
    try:
        if not enabled(project):
            print("CLOSURE_NOT_ENABLED: no postflight validation performed")
            return 2 if args.require_enabled else 0
        postflight(project)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print("CLOSURE_INCOMPLETE:", exc)
        return 1
    print("CLOSURE_POSTFLIGHT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
