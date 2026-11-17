"""Explicit root-only preparation of a new NEC Git worktree; never launches training."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shlex
import subprocess
import uuid

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
P = ROOT / "pipeline"
COMMIT = "6bc36adfe42764aac2209e6600fb3a783e2fa374"
PARENT = "4457a46f9075f61e83340aa0f0af87d5bf4e986c"
NEW_ROOT = "/data/songcl/Project/Cluster_project/Cluster_nec_20261104"
OLD_ROOTS = {
    "/data/songcl/Project/Cluster_project/Cluster_resume_wfc_20261104": "94c4fe61b38f46f321a7ee84236fea70ade04d9b",
    "/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1": PARENT,
}
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"
SSH_OPTIONS = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8"]
DEST = "songcl@192.168.1.115"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


OWNER = read(HERE / "owner_binding.json")


def guard(minimum=0):
    owner = read(P / "headless/.foreground.lockdir/owner.json")
    assert all(owner.get(k) == v for k, v in OWNER.items()), "Owner changed"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > minimum
    assert sha(P / "headless/.tick_context.json") == OWNER["context_sha256"]
    assert sha(P / "headless/.tick_context_state.next.json") == OWNER["pending_sha256"]


def run(command, **kwargs):
    guard()
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=kwargs.pop("timeout", 120), **kwargs)
    if result.returncode:
        raise RuntimeError(f"Command failed rc={result.returncode}: {command[:4]!r}\n{result.stderr[-3000:]}")
    return result.stdout


REMOTE = r'''
import socket
assert socket.gethostname() == "dl04-MS-7E06"
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, shutil, subprocess, yaml
def guard():
    assert datetime.now(timezone.utc) < datetime.fromisoformat(PARAMS["owner"]["deadline_at"])
def git(root,*args):
    guard()
    return subprocess.check_output(["git","--no-optional-locks","-c","core.fsmonitor=false","-C",str(root),*args])
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()
def snapshot(root,head):
    root=Path(root)
    assert git(root,"rev-parse","HEAD").decode().strip()==head
    files={}
    suffixes={".py",".pyi",".yaml",".yml",".json",".toml",".ini",".cfg",".sh",".c",".cpp",".cu",".h",".hpp",".so"}
    for raw in git(root,"ls-files","-z").split(b"\0"):
        if not raw:continue
        name=raw.decode()
        if Path(name).suffix in suffixes:
            path=root/name
            files[name]={"sha256":sha(path),"symlink":os.readlink(path) if path.is_symlink() else None}
    return dict(head=head,status_hex=git(root,"status","--porcelain=v1","--untracked-files=all","-z").hex(),source_hashes=files)
guard()
root=Path(PARAMS["new_root"])
assert not root.exists(), "New runtime already exists: inspect it; never overwrite/replay"
before={r:snapshot(r,h) for r,h in PARAMS["old_roots"].items()}
current=Path(PARAMS["current_root"])
bundle=Path(PARAMS["bundle"])
assert bundle.is_file() and sha(bundle)==PARAMS["bundle_sha256"]
guard()
git(current,"fetch","--no-tags","--no-write-fetch-head",str(bundle),PARAMS["bundle_ref"])
assert git(current,"cat-file","-t",PARAMS["commit"]).decode().strip()=="commit"
guard()
git(current,"worktree","add","--detach",str(root),PARAMS["commit"])
assert git(root,"rev-parse","HEAD").decode().strip()==PARAMS["commit"]
extension=PARAMS["extension"]
original=Path(extension["path"])
assert sha(original)==extension["sha256"]
relative=original.relative_to(current)
target=root/relative
assert not target.exists()
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(original,target)
assert sha(target)==extension["sha256"]
assert git(root,"check-ignore",str(relative)).strip(), "Extension must remain ignored"
manifest=PARAMS["manifest"]
model=root/"framework/model/Quard_model"/manifest["candidate_name"]
verified={}
for name,want in manifest["candidate_source_hashes"].items():
    path=model/name
    assert sha(path)==want,name
    verified[str(path.relative_to(root))]=want
config=root/manifest["config"]
assert sha(config)==manifest["candidate_config_sha256"]
original_config=yaml.safe_load(config.read_text())
def adapt(value):
    if isinstance(value,dict):return {k:adapt(v) for k,v in value.items()}
    if isinstance(value,list):return [adapt(v) for v in value]
    if isinstance(value,str):
        for a,b in PARAMS["mappings"]:value=value.replace(a,b)
    return value
deployed=adapt(original_config)
config.write_text(yaml.safe_dump(deployed,sort_keys=False))
assert yaml.safe_load(config.read_text())==adapt(yaml.safe_load(git(root,"show","HEAD:"+manifest["config"]).decode()))
assets=manifest["assets"]
assert sha(root/"tools/train.py")==assets["native_train_source_sha256"]
assert sha(root/"framework/dataset/scannetv2.py")==assets["dataset_source_sha256"]
assert Path(deployed["model"]["data_root"]).is_dir()
assert Path(deployed["train"]["pretrain"]).is_file()
for path,want in [(assets["annotation_path"],assets["annotation_sha256"]),(assets["pretrain"],assets["pretrain_sha256"])]:
    assert sha(path)==want,path
import sys
assert sys.version_info[:2]==(3,10)
assert os.environ.get("CONDA_DEFAULT_ENV")=="project_cluster"
after={r:snapshot(r,h) for r,h in PARAMS["old_roots"].items()}
assert before==after, "Protected old-root source/head/status changed"
guard()
print(json.dumps(dict(owner=PARAMS["owner"],observed_at=datetime.now(timezone.utc).isoformat(),
    hostname=socket.gethostname(),remote_code_root=str(root),code_commit=PARAMS["commit"],
    protected_old_roots_before=before,protected_old_roots_after=after,old_roots_unchanged=True,
    candidate_source_hashes=verified,candidate_original_yaml_sha256=manifest["candidate_config_sha256"],
    deployed_yaml_sha256=sha(config),only_existing_yaml_path_mappings_applied=True,
    compiled_extension=dict(path=str(target),sha256=sha(target)),python=sys.version,
    conda_environment=os.environ.get("CONDA_DEFAULT_ENV"),data_inputs_verified=True,
    new_root_status_hex=git(root,"status","--porcelain=v1","--untracked-files=all","-z").hex(),
    bundle_path=str(bundle),bundle_sha256=sha(bundle),training_started=False,GPU_computation=False,
    signals_sent=False,SERVERS_changed=False)))
'''


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP", "remote_code_root": NEW_ROOT, "training_started": False}))
        return
    guard(180)
    import yaml
    server = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    assert server["host"] == "192.168.1.115" and server["user"] == "songcl"
    assert server["expected_hostname"] == "dl04-MS-7E06" and server["allowed_gpus"] == [0]
    assert server["remote_code_root"] in OLD_ROOTS
    manifest_path = HERE / "nec_execution/native_manifest.json"
    manifest = read(manifest_path)
    assert manifest["code_commit"] == COMMIT and manifest["current_token"] == OWNER["token"]
    assert run([GIT, "--no-optional-locks", "-C", str(ROOT / "Cluster"), "rev-parse", "HEAD"]).strip() == COMMIT
    intent = HERE / "nec_runtime_prepare_intent.json"
    assert not intent.exists(), "Prior runtime preparation intent exists: inspect, never replay"
    assert not (HERE / "nec_runtime_preparation.json").exists()
    assert run(["ssh", *SSH_OPTIONS, DEST, "hostname"], timeout=20).strip() == "dl04-MS-7E06"
    tag = OWNER["token"][:8] + "_" + uuid.uuid4().hex[:12]
    private = HERE / ("runtime_bundle_" + tag)
    private.mkdir(exist_ok=False)
    bare = private / "objects.git"
    run([GIT, "init", "--bare", str(bare)])
    bundle_ref = "refs/heads/nec-runtime-" + tag
    run([GIT, "--git-dir", str(bare), "fetch", "--no-tags", "--no-write-fetch-head",
         str(ROOT / "Cluster"), COMMIT + ":" + bundle_ref])
    bundle = private / ("nec_" + tag + ".bundle")
    run([GIT, "--git-dir", str(bare), "bundle", "create", str(bundle), bundle_ref, "^" + PARENT])
    remote_bundle = "/data/songcl/Project/Cluster_project/pipeline/runtime/nec_" + tag + ".bundle"
    params = dict(owner=OWNER,commit=COMMIT,new_root=NEW_ROOT,old_roots=OLD_ROOTS,
                  current_root=server["remote_code_root"],bundle=remote_bundle,
                  bundle_sha256=sha(bundle),bundle_ref=bundle_ref,manifest=manifest,
                  extension=read(P / "manual_ops/20261104_wfc_gpu0_start/runtime_preparation_and_checkpoint.json")["data"]["compiled_extension"],
                  mappings=[(x["source"],server[x["server_key"]].rstrip("/")) for x in read(P / "closure_policy.json")["path_mappings"]])
    guard(120)
    with intent.open("x", encoding="utf-8") as stream:
        json.dump(dict(owner=OWNER,params=params,helper_sha256=sha(__file__),manifest_sha256=sha(manifest_path)),
                  stream, ensure_ascii=False, indent=2)
    run(["scp", *SSH_OPTIONS, str(bundle), DEST + ":" + remote_bundle], timeout=90)
    activation = "source " + shlex.quote(server["conda_source"]) + " && conda activate " + shlex.quote(server["conda_env"]) + " && PYTHONDONTWRITEBYTECODE=1 python -B -"
    result = subprocess.run(["ssh", *SSH_OPTIONS, DEST, activation],
                            input="PARAMS=" + repr(params) + "\n" + REMOTE,
                            capture_output=True,text=True,encoding="utf-8",timeout=150)
    record = dict(owner=OWNER,recorded_at=datetime.now(timezone.utc).isoformat(),returncode=result.returncode,
                  stderr=result.stderr,stdout=result.stdout,helper_sha256=sha(__file__),intent_sha256=sha(intent))
    if result.returncode == 0:
        record["observation"] = json.loads(result.stdout)
    guard()
    output = HERE / "nec_runtime_preparation.json"
    with output.open("x",encoding="utf-8") as stream:
        json.dump(record,stream,ensure_ascii=False,indent=2,allow_nan=False)
    assert result.returncode == 0, result.stderr[-3000:]
    print(json.dumps(dict(status="RUNTIME_PREPARED_NO_TRAINING",evidence=str(output),sha256=sha(output),
                          remote_code_root=NEW_ROOT,code_commit=COMMIT,SERVERS_changed=False)))


if __name__ == "__main__":
    main()
