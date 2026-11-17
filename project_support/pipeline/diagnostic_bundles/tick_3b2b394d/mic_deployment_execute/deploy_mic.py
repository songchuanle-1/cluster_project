"""Root-only MIC ff/runtime/switch. Default NOP. Never queues or launches training."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import json
import os
import shlex
import subprocess
import sys
import uuid

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
CODE = ROOT / "Cluster"
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"
SOURCE = "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
BASE = "6bc36adfe42764aac2209e6600fb3a783e2fa374"
CID = "hierarchy-ancestry-mobius-interaction-composition"
CONFIG = "configs/Quard/ctf_hcg_csort_mic/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mic.yaml"
OLD_ROOT = "/data/songcl/Project/Cluster_project/Cluster_nec_20261104"
NEW_ROOT = "/data/songcl/Project/Cluster_project/Cluster_mic_20261105"
SO_REL = "framework/lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so"
SO_SHA = "c86f516858d480e2583a437deb598279bc626e74975a060b17d75bf03f630033"
SSH = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8"]
DEST = "songcl@192.168.1.115"
EXPECTED = {
    "token": "3b2b394d2fa242b19bbf4fef5ea11c67",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-05T13:07:08.623175+00:00",
    "deadline_at": "2026-11-05T14:07:08.623175+00:00",
    "context_sha256": "fe48ed24dba1c4e039abbf0c098ace6ec43bad7c5c91b3def914f40e492dc065",
    "pending_sha256": "8a63b7b374f3cd520c81f28baae4a09b5f9266b53b45eafd4f65e40893922d77",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def ref(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT.resolve())
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard(seconds=0):
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {k: owner.get(k) for k in EXPECTED} == EXPECTED, "Actual owner changed"
    assert os.environ.get("CODEX_THREAD_ID") == EXPECTED["thread_id"]
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    now = datetime.now(timezone.utc)
    assert (datetime.fromisoformat(EXPECTED["deadline_at"]) - now).total_seconds() > seconds
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == EXPECTED["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == EXPECTED["pending_sha256"]
    assert read(ROOT / "pipeline/execution_mode.json") == {"mode": "foreground", "target_thread_id": EXPECTED["thread_id"]}


def save(path, obj):
    guard()
    path = Path(path).resolve()
    assert path.is_relative_to(HERE.resolve()) or path == (TICK / "mic_runtime_deployment.json").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def command(args, timeout=60):
    guard()
    return subprocess.check_output(args, text=True, encoding="utf-8", timeout=timeout,
                                   env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_LFS_SKIP_SMUDGE="1"))


def git(*args):
    guard()
    return subprocess.check_output([GIT, "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(CODE), *args],
                                   env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0"))


def protected():
    baseline = read(TICK / "protected_assets_before.json")
    assert len(baseline["files"]) == 28
    assert git("status", "--porcelain=v1", "--untracked-files=all", "-z").hex() == baseline["status_hex"]
    assert not git("diff", "--cached", "--name-only", "-z")
    for group in ("files", "WFC_source_paths", "LFT_source_paths"):
        for path, digest in baseline[group].items():
            assert sha(CODE / path) == digest, path
    return baseline


def lifecycle():
    baseline = read(TICK / "protected_assets_before.json")
    names = set(baseline["protected_ledgers"]) | {
        "queue.json", "running.json", "experiments.csv", "research_work.json", "codex_memory.md",
        "goal.json", "closure_policy.json", "execution_mode.json", "admissions/M229-MIC.json",
    }
    return {n: sha(ROOT / "pipeline" / n) for n in names if (ROOT / "pipeline" / n).is_file()}


def gates(receipt_path, review_path):
    guard()
    receipt_path = Path(receipt_path).resolve()
    review_path = Path(review_path).resolve()
    assert receipt_path.is_relative_to(ROOT.resolve()) and review_path.is_relative_to(ROOT.resolve())
    resource_path = ROOT / "pipeline/authorizations/server4_gpu0_overlay_20261104.json"
    assert sha(resource_path) == "783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88"
    resource = read(resource_path)
    assert resource["allowed_gpus"] == [0] and resource["allow_external_overlay"] is True
    assert resource["task_memory_mb"] == 20000 and resource["max_project_tasks_per_gpu"] == 1
    receipt = read(receipt_path)
    identity = {"id": "M229-MIC", "candidate_id": CID, "code_commit": SOURCE, "config": CONFIG,
                "goal_sha256": "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"}
    assert all(receipt.get(k) == v for k, v in identity.items())
    assert receipt["profile"] == "experiment_first"
    assert sha(ROOT / "pipeline/goal.json") == identity["goal_sha256"]
    review = read(review_path)
    assert review.get("candidate_id") == CID and review.get("code_commit") == SOURCE
    assert review.get("material_concerns", review.get("blocking_issues")) == []
    assert review.get("passed") is True or review.get("resources_passed") is True
    sys.path.insert(0, str(SKILL))
    import closure
    task = {"id": "M229-MIC", "candidate_id": CID, "config": CONFIG, "code_commit": SOURCE,
            "admission_receipt": ref(receipt_path)["path"], "profile": "experiment_first",
            "requires_exclusive_ownership": False}
    closure.admission(ROOT, task)
    for gate in ("native_backward", "resources", "independence", "constraints"):
        value = receipt["gates"][gate]
        assert value["passed"] is True and value["evidence"]
        for item in value["evidence"]:
            path = (ROOT / item["path"]).resolve()
            assert path.is_relative_to(ROOT.resolve()) and sha(path) == item["sha256"]
    version = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_version_prepare/isolated_source_version.json"
    assert sha(version) == "f5e94bfb0b4c45674f3acc9ed315dac543f8ee8064bf09dda7d4fe5897e4ee8d"
    proof = read(version)
    assert proof["code_commit"] == SOURCE and proof["parent_commit"] == BASE
    paths = proof["frozen_source_files"]
    assert len(paths) == 9
    return paths, {"receipt": ref(receipt_path), "actual_independent_review": ref(review_path), "source_version": ref(version)}


def ff(paths, inputs):
    guard(150)
    assert not (HERE / "ff_intent.json").exists(), "Prior ff intent: inspect/reconcile; never replay"
    baseline = protected()
    assert baseline["head"] == BASE and git("rev-parse", "HEAD").decode().strip() == BASE
    assert git("show", "-s", "--format=%P", SOURCE).decode().strip() == BASE
    assert set(git("diff-tree", "--no-commit-id", "--name-status", "-r", SOURCE).decode().splitlines()) == {"A\t" + p for p in paths}
    entries = lambda commit: {r.split(b"\t", 1)[1]: r.split(b"\t", 1)[0]
                              for r in git("ls-tree", "-r", "-z", commit).split(b"\0") if r}
    old_tree, next_tree = entries(BASE), entries(SOURCE)
    assert all(next_tree.get(k) == v for k, v in old_tree.items())
    old_index = {r.split(b"\t", 1)[1]: r.split(b"\t", 1)[0] for r in git("ls-files", "--stage", "-z").split(b"\0") if r}
    for p, digest in paths.items():
        assert not (CODE / p).exists() and hashlib.sha256(git("show", SOURCE + ":" + p)).hexdigest() == digest
        assert git("ls-tree", SOURCE, "--", p).decode().split()[0] == "100644"
    before = lifecycle()
    save(HERE / "ff_intent.json", {"owner": EXPECTED, "base": BASE, "source": SOURCE, "inputs": inputs, "paths": paths,
                                   "protected_before": before, "script": ref(__file__)})
    hooks = HERE / "empty_hooks"
    hooks.mkdir(exist_ok=False)
    args = [GIT, "--no-optional-locks", "-C", str(CODE), "-c", "merge.autoStash=false",
            "-c", "core.autocrlf=false", "-c", "core.eol=lf", "-c", "core.hooksPath=" + str(hooks),
            "merge", "--ff-only", SOURCE]
    guard(120)
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=120,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_LFS_SKIP_SMUDGE="1"))
    save(HERE / "ff_command.json", {"command": args, "returncode": result.returncode,
                                   "stdout": result.stdout, "stderr": result.stderr})
    assert result.returncode == 0, "Inspect exact ff state; no reset/stash/clean/retry"
    assert git("rev-parse", "HEAD").decode().strip() == SOURCE
    protected()
    assert lifecycle() == before and all(sha(CODE / p) == h for p, h in paths.items())
    new_index = {r.split(b"\t", 1)[1]: r.split(b"\t", 1)[0] for r in git("ls-files", "--stage", "-z").split(b"\0") if r}
    assert all(new_index.get(k) == v for k, v in old_index.items())
    save(HERE / "ff_result.json", {"owner": EXPECTED, "local_head": SOURCE, "source_verified": True,
                                   "exact9_additions": True, "prior_tree_and_index_entries_preserved": True,
                                   "user28_and_WFC_LFT_preserved": True, "inputs": inputs})


REMOTE = r'''
import socket
assert socket.gethostname()=="dl04-MS-7E06"
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,sys,yaml
def guard():
    assert datetime.now(timezone.utc)<datetime.fromisoformat(P["owner"]["deadline_at"])
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()
def git(root,*args):
    guard()
    return subprocess.check_output(["git","--no-optional-locks","-c","core.fsmonitor=false","-C",str(root),*args])
def snapshot(root,commit):
    assert git(root,"rev-parse","HEAD").decode().strip()==commit
    hashes={}
    for raw in git(root,"ls-files","-z").split(b"\0"):
        if not raw:continue
        name=raw.decode()
        if Path(name).suffix in {".py",".pyi",".yaml",".yml",".json",".toml",".ini",".cfg",".sh",".c",".cpp",".cu",".h",".hpp",".so"}:
            path=Path(root)/name
            hashes[name]={"sha256":sha(path),"symlink":os.readlink(path) if path.is_symlink() else None}
    return {"head":commit,"status_hex":git(root,"status","--porcelain=v1","--untracked-files=all","-z").hex(),
            "source_file_count":len(hashes),"source_digest":hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()}
guard()
root=Path(P["new_root"]);current=Path(P["current_root"])
assert not root.exists(),"Runtime target exists: inspect; never overwrite/replay"
before={r:snapshot(r,c) for r,c in P["old_roots"].items()}
original=current/P["extension_rel"];assert sha(original)==P["extension_sha"]
bundle=Path(P["bundle"]);assert sha(bundle)==P["bundle_sha256"]
git(current,"fetch","--no-tags","--no-write-fetch-head",str(bundle),P["bundle_ref"])
git(current,"worktree","add","--detach",str(root),P["source"])
assert git(root,"rev-parse","HEAD").decode().strip()==P["source"]
target=root/P["extension_rel"];assert not target.exists()
target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
assert sha(target)==P["extension_sha"] and git(root,"check-ignore",P["extension_rel"]).strip()
for name,digest in P["source_paths"].items():assert sha(root/name)==digest,name
m=P["manifest"];config=root/m["config"];original_config=yaml.safe_load(config.read_text())
def adapt(value):
    if isinstance(value,dict):return {k:adapt(v) for k,v in value.items()}
    if isinstance(value,list):return [adapt(v) for v in value]
    if isinstance(value,str):
        for old,new in P["mappings"]:value=value.replace(old,new)
    return value
deployed=adapt(original_config);config.write_text(yaml.safe_dump(deployed,sort_keys=False))
assert yaml.safe_load(config.read_text())==adapt(yaml.safe_load(git(root,"show","HEAD:"+m["config"]).decode()))
assets=m["assets"]
assert sha(root/"tools/train.py")==assets["native_train_source_sha256"]
assert sha(root/"framework/dataset/scannetv2.py")==assets["dataset_source_sha256"]
for key,path in [("annotation",assets["annotation_path"]),("pretrain",assets["pretrain"]),("checkpoint",assets["checkpoint"])]:
    assert sha(path)==assets[key+"_sha256"],key
assert Path(deployed["model"]["data_root"]).is_dir() and Path(deployed["train"]["pretrain"]).is_file()
assert sys.version_info[:2]==(3,10) and os.environ.get("CONDA_DEFAULT_ENV")=="project_cluster"
after={r:snapshot(r,c) for r,c in P["old_roots"].items()}
assert before==after and sha(original)==P["extension_sha"]
guard()
print(json.dumps({"recorded_at":datetime.now(timezone.utc).isoformat(),"owner":P["owner"],
    "runtime_root":str(root),"runtime_code_commit":P["source"],"source_verified":True,
    "old_roots_preserved":True,"old_roots_before":before,"old_roots_after":after,
    "python":sys.version,"conda_environment":os.environ.get("CONDA_DEFAULT_ENV"),
    "compiled_extension":{"path":str(target),"sha256":sha(target)},
    "original_yaml_sha256":m["candidate_config_sha256"],"deployed_yaml_sha256":sha(config),
    "YAML_mapping_verified":True,"yaml_mappings":P["mappings"],"signals_sent":False,
    "training_started":False,"GPU_computation":False,"SERVERS_changed":False}))
'''


def runtime(paths, inputs):
    guard(240)
    assert (HERE / "ff_result.json").is_file()
    ff_proof = read(HERE / "ff_result.json")
    assert ff_proof["local_head"] == SOURCE and ff_proof["owner"] == EXPECTED and ff_proof["inputs"] == inputs
    assert not (HERE / "runtime_intent.json").exists(), "Prior runtime intent: inspect/reconcile; never replay"
    assert not (TICK / "mic_runtime_deployment.json").exists()
    assert git("rev-parse", "HEAD").decode().strip() == SOURCE
    protected()
    import yaml
    server = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    assert server["host"] == "192.168.1.115" and server["user"] == "songcl" and server["expected_hostname"] == "dl04-MS-7E06"
    assert server["allowed_gpus"] == [0] and server["remote_code_root"] == OLD_ROOT
    assert server["max_tasks_per_gpu"] == 1 and server["allow_external_overlay"] is True and server["task_memory_mb"] == 20000
    assert str(server["expected_gpu_uuids"].get("0", server["expected_gpu_uuids"].get(0))) == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
    manifest = read(TICK / "mic_execution/native_manifest.json")
    assert manifest["code_commit"] == SOURCE and manifest["runtime_code_commit"] == BASE and manifest["config"] == CONFIG
    assert manifest["candidate_config_sha256"] == paths[CONFIG]
    before = lifecycle()
    assert command(["ssh", *SSH, DEST, "hostname"], 20).strip() == "dl04-MS-7E06"
    tag = EXPECTED["token"][:8] + "_" + uuid.uuid4().hex[:12]
    private = HERE / ("bundle_" + tag)
    private.mkdir(exist_ok=False)
    bare = private / "objects.git"
    command([GIT, "init", "--bare", str(bare)])
    bundle_ref = "refs/heads/mic-runtime-" + tag
    command([GIT, "--git-dir", str(bare), "fetch", "--no-tags", "--no-write-fetch-head",
             str(CODE), SOURCE + ":" + bundle_ref])
    bundle = private / ("mic_" + tag + ".bundle")
    command([GIT, "--git-dir", str(bare), "bundle", "create", str(bundle), bundle_ref, "^" + BASE])
    remote_bundle = "/data/songcl/Project/Cluster_project/pipeline/runtime/mic_" + tag + ".bundle"
    mappings = [(v["source"], server[v["server_key"]].rstrip("/"))
                for v in read(ROOT / "pipeline/closure_policy.json")["path_mappings"]]
    params = {"owner": EXPECTED, "source": SOURCE, "current_root": OLD_ROOT, "new_root": NEW_ROOT,
              "old_roots": {OLD_ROOT: BASE,
                  "/data/songcl/Project/Cluster_project/Cluster_resume_wfc_20261104": "94c4fe61b38f46f321a7ee84236fea70ade04d9b",
                  "/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1": "4457a46f9075f61e83340aa0f0af87d5bf4e986c"},
              "bundle": remote_bundle, "bundle_sha256": sha(bundle), "bundle_ref": bundle_ref,
              "source_paths": paths, "manifest": manifest, "extension_rel": SO_REL, "extension_sha": SO_SHA,
              "mappings": mappings}
    save(HERE / "runtime_intent.json", {"owner": EXPECTED, "params": params, "inputs": inputs, "script": ref(__file__)})
    command(["scp", *SSH, str(bundle), DEST + ":" + remote_bundle], 90)
    activation = "source " + shlex.quote(server["conda_source"]) + " && conda activate " + shlex.quote(server["conda_env"]) + " && PYTHONDONTWRITEBYTECODE=1 python -B -"
    guard(180)
    run = subprocess.run(["ssh", *SSH, DEST, activation], input="P=" + repr(params) + "\n" + REMOTE,
                         capture_output=True, text=True, encoding="utf-8", timeout=150)
    save(HERE / "runtime_command.json", {"returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
                                        "intent": ref(HERE / "runtime_intent.json")})
    assert run.returncode == 0, "Inspect remote worktree and original intent; no replay/cleanup"
    observation = json.loads(run.stdout)
    assert observation["runtime_root"] == NEW_ROOT and observation["runtime_code_commit"] == SOURCE
    assert observation["source_verified"] and observation["old_roots_preserved"]
    protected()
    assert lifecycle() == before
    save(TICK / "mic_runtime_deployment.json", {
        **observation, "local_head": SOURCE, "inputs": inputs,
        "actual_ff": ref(HERE / "ff_result.json"), "runtime_command": ref(HERE / "runtime_command.json"),
        "receipt": inputs["receipt"], "source_paths": paths,
        "SERVERS_changed": False, "admission_created": False, "training_started": False})


def switch(inputs):
    guard(60)
    assert not (HERE / "switch_intent.json").exists(), "Prior switch intent: inspect/reconcile; never replay"
    proof = read(TICK / "mic_runtime_deployment.json")
    assert proof["owner"] == EXPECTED and proof["local_head"] == SOURCE
    assert proof["runtime_root"] == NEW_ROOT and proof["runtime_code_commit"] == SOURCE
    assert proof["source_verified"] and proof["old_roots_preserved"] and proof["YAML_mapping_verified"]
    protected()
    assert git("rev-parse", "HEAD").decode().strip() == SOURCE
    import yaml
    path = ROOT / "SERVERS.yaml"
    original = path.read_bytes()
    text = original.decode("utf-8")
    before = yaml.safe_load(text)
    server = before["servers"]["server-4"]
    assert server["remote_code_root"] == OLD_ROOT and server["allowed_gpus"] == [0]
    assert server["max_tasks_per_gpu"] == 1 and server["allow_external_overlay"] is True and server["task_memory_mb"] == 20000
    assert server["host"] == "192.168.1.115" and server["user"] == "songcl" and server["expected_hostname"] == "dl04-MS-7E06"
    assert str(server["expected_gpu_uuids"].get("0", server["expected_gpu_uuids"].get(0))) == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
    assert text.count(OLD_ROOT) == 1, "Only the exact unique code-root scalar may change"
    changed = text.replace(OLD_ROOT, NEW_ROOT, 1)
    expected = copy.deepcopy(before)
    expected["servers"]["server-4"]["remote_code_root"] = NEW_ROOT
    assert yaml.safe_load(changed) == expected
    ledgers = lifecycle()
    save(HERE / "switch_intent.json", {"owner": EXPECTED, "SERVERS_before_sha256": hashlib.sha256(original).hexdigest(),
                                      "runtime_proof": ref(TICK / "mic_runtime_deployment.json"), "inputs": inputs})
    temp = ROOT / ("SERVERS.yaml.mic_" + EXPECTED["token"][:8] + ".tmp")
    guard()
    with temp.open("xb") as f:
        f.write(changed.encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
    assert path.read_bytes() == original
    guard()
    os.replace(temp, path)
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == expected
    assert lifecycle() == ledgers
    protected()
    save(HERE / "switch_result.json", {"recorded_at": datetime.now(timezone.utc).isoformat(), "owner": EXPECTED,
                                       "runtime_root": NEW_ROOT, "runtime_code_commit": SOURCE,
                                       "SERVERS_before_sha256": hashlib.sha256(original).hexdigest(),
                                       "SERVERS_after_sha256": sha(path), "only_remote_code_root_changed": True,
                                       "allocation_holds_scheduler_other_servers_preserved": True,
                                       "runtime_proof": ref(TICK / "mic_runtime_deployment.json"),
                                       "queue_changed": False, "training_started": False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--phase", choices=["ff", "runtime", "switch", "all"], default="all")
    parser.add_argument("--receipt", default=str(ROOT / "pipeline/admissions/M229-MIC.json"))
    parser.add_argument("--review", default=str(TICK / "mic_actual_independent_review.json"))
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_FF_RUNTIME_SWITCH_OR_LAUNCH", "source": SOURCE,
                          "base": BASE, "new_root": NEW_ROOT, "phase": args.phase}))
        return
    guard()
    paths, inputs = gates(Path(args.receipt), Path(args.review))
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        assert gates(Path(args.receipt), Path(args.review))[1] == inputs
        if args.phase in ("ff", "all"):
            assert gates(Path(args.receipt), Path(args.review))[1] == inputs
            ff(paths, inputs)
        if args.phase in ("runtime", "all"):
            assert gates(Path(args.receipt), Path(args.review))[1] == inputs
            runtime(paths, inputs)
        if args.phase in ("switch", "all"):
            assert gates(Path(args.receipt), Path(args.review))[1] == inputs
            switch(inputs)
        print(json.dumps({"status": "DEPLOYMENT_PHASE_COMPLETED_NO_QUEUE_OR_LAUNCH", "phase": args.phase,
                          "runtime_proof": ref(TICK / "mic_runtime_deployment.json") if (TICK / "mic_runtime_deployment.json").exists() else None}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
