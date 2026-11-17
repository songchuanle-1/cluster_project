"""Root-controlled NSD production observation/render only; never launch/train.

Run only from a new reviewed remote producer stage with a fresh explicit request.
This file does not deploy source, alter YAML/SERVERS/queue, obtain GPU resources,
signal processes, remove locks/markers, or invoke the training entry.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import stat
import subprocess
import sys
from types import ModuleType


EXPECTED_OWNER = {'token': 'ec4597142e314aa7a0478bac13e26402', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-08T13:10:13.081564+00:00', 'deadline_at': '2026-11-08T14:10:13.081564+00:00', 'context_sha256': 'ca7d223211d13359f25e920276d637ff4ba3b31a5e55c67981f2f626c48e653f', 'pending_sha256': '92367a4ba1deb25a852d7a9719a34156543ed92dd223562473812002928482aa'}
OWNER = 'ec4597142e314aa7a0478bac13e26402'
OWNER_THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
OWNER_DEADLINE = '2026-11-08T14:10:13.081564+00:00'
PROJECT = Path("/data/songcl/Project/Cluster_project")
PRODUCER = PROJECT / 'pipeline/runtime/nde_path_prepare_ec459714'
PRODUCTION = PROJECT / 'pipeline/runtime/nde_path_prod_ec459714'
RUNTIME = PROJECT / "Cluster_nsd_20261107"
COMMIT = '0747f6acec1c61018ec99acf2efa5329c9b3523c'
CONFIG = 'configs/Quard/ctf_hcg_csort_nde/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde.yaml'
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
PREFIX = "/home/songcl/.conda/envs/project_cluster"
BASE = PROJECT / "pipeline/runtime/server4_conda_4ca73fba.sh"
BASE_SHA = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
CORE_SHA = "c0857d0b79da396da73c4dbefd60a81ce35f9fb3839b76441328a22183e988b3"
FACTORY_SHA = "0a8ed26bd62327314de89f4228b53c8c633fdd73e4e1867d674df94b24d073dd"
PROOF_REVIEW_SHA = "ce4d57c001c6dd4a7c2ea1491563c56fc7a7c4ab4371cc2aedae663b73fcac82"
EXACT_ARGS = ["tools/train.py", CONFIG, "--gpu_ids", "0", "--num_gpus", "1"]
LOCK_PATHS = ["/tmp/cluster_project_gpu0_" + label + ".lock"
              for label in ("training", "diagnostic", "exclusive")]
MAPPINGS = [
    ["/home/songcl/data/data", "/home/songcl/data/data"],
    ["/home/songcl/3dres/project/cluster_project/Checkpoints",
     "/data/songcl/Project/Cluster_project/Cluster_checkpoints"],
]
EXPECTED_SOURCES = {'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/__init__.py': '327bf439ad68108b0493d337a2097dc83626e71af869b2536408232f197eda62', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/backbone.py': '1eb4ac3483961e708c23b0abad396c181dbf38c56fcca559d88b9622af46bafd', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/dec.py': 'ec21d503979fd95c87fa63280948b8a5e9b9f300383a99a53038eb081440ad54', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/hier_postprocess.py': '2f802153fba7483c84cdb8b778108e0edadc44c83d4b2e266094d84a0b315ac5', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/loss.py': 'c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/network.py': '5a77eb852b3c6e5de2804d80a2c7a16504f1fd8a57aa94dc6045d9f35587625d', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/sample_model.py': 'b22319d5c3958a9a893cb6c2134dd7e124778610aba7e8b9c90647560c806999', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/distribution_embedding.py': '4acbbc28748425d37959a5edb6dcbb68f9a61859d693a9222c14ac96e38a877f'}
GIT_ENV = {
    "PATH": "/usr/bin:/bin", "GIT_OPTIONAL_LOCKS": "0",
    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_CONFIG_GLOBAL": "/dev/null", "LANG": "C",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def save_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def run(argv, *, env=None):
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, env=env)
    try:
        stdout, stderr = process.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Uncertain CPU child; preserve PID " + str(process.pid))
    if process.returncode:
        raise RuntimeError("Read/CPU command failed: " + stderr[-1500:])
    return stdout


def regular(path):
    metadata = os.lstat(path)
    assert stat.S_ISREG(metadata.st_mode) and metadata.st_uid == 1001
    assert metadata.st_nlink == 1 and not stat.S_ISLNK(metadata.st_mode)
    return metadata


def guard(request):
    assert sys.flags.isolated and sys.dont_write_bytecode
    assert socket.gethostname() == "dl04-MS-7E06"
    assert os.getuid() == os.geteuid() == 1001
    assert Path(__file__).resolve().parent == PRODUCER
    metadata = os.lstat(PRODUCER)
    assert stat.S_ISDIR(metadata.st_mode) and metadata.st_uid == 1001
    assert stat.S_IMODE(metadata.st_mode) == 0o700
    owner = request["owner"]
    assert owner == EXPECTED_OWNER
    assert owner["token"] == OWNER and owner["thread_id"] == OWNER_THREAD
    assert owner["deadline_at"] == OWNER_DEADLINE
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert request["kind"] == "NDE_PRODUCTION_PATH_PREPARATION"
    assert request["execution_authorized"] is True
    assert request["training_launch_authorized"] is False
    assert request["cpu_proof_independent_review_sha256"] == PROOF_REVIEW_SHA
    assert request["path_mappings"] == MAPPINGS
    for filename in ("production_controller.py", "lock_core.py", "entry_factory.py"):
        regular(PRODUCER / filename)
        assert sha(PRODUCER / filename) == request["files"][filename]
    assert sha(PRODUCER / "lock_core.py") == CORE_SHA
    assert sha(PRODUCER / "entry_factory.py") == FACTORY_SHA
    assert sha(BASE) == BASE_SHA


def git(*args):
    return run(["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                "-C", str(RUNTIME), *args], env=GIT_ENV)


def observe(request):
    guard(request)
    assert RUNTIME.is_dir() and RUNTIME.resolve() == RUNTIME
    assert git("rev-parse", "--verify", "HEAD").strip() == COMMIT
    hashes = {}
    for relative, expected in EXPECTED_SOURCES.items():
        filename = RUNTIME / relative
        assert filename.resolve() == filename and filename.is_relative_to(RUNTIME)
        regular(filename)
        hashes[relative] = sha(filename)
        assert hashes[relative] == expected
    train = RUNTIME / "tools/train.py"
    regular(train)
    tracked_train = git("show", COMMIT + ":tools/train.py").encode("utf-8")
    assert train.read_bytes() == tracked_train
    config = RUNTIME / CONFIG
    regular(config)
    original = git("show", COMMIT + ":" + CONFIG).encode("utf-8")
    assert digest(original) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    # Compute exactly canonical safe_launch's deterministic adaptation without
    # writing YAML. The same original conda PyYAML serializes the same object.
    preview_program = r'''
import base64,hashlib,json,sys,yaml
raw=base64.b64decode(sys.argv[1]);mappings=json.loads(sys.argv[2])
def adapt(x):
 if isinstance(x,dict):return {k:adapt(v) for k,v in x.items()}
 if isinstance(x,list):return [adapt(v) for v in x]
 if isinstance(x,str):
  for a,b in mappings:x=x.replace(a,b)
 return x
c=adapt(yaml.safe_load(raw.decode("utf-8")))
out=yaml.safe_dump(c,sort_keys=False).encode("utf-8")
print(json.dumps({"sha256":hashlib.sha256(out).hexdigest(),
                 "bytes_base64":base64.b64encode(out).decode("ascii")}))
'''
    preview = json.loads(run(
        [PYTHON, "-I", "-B", "-c", preview_program,
         base64.b64encode(original).decode("ascii"), json.dumps(MAPPINGS)]))
    adapted = base64.b64decode(preview["bytes_base64"], validate=True)
    assert digest(adapted) == preview["sha256"]
    assert config.read_bytes() in (original, adapted), "Unexpected runtime YAML edit"
    real_python = Path(PYTHON).resolve(strict=True)
    assert real_python.is_file() and os.access(PYTHON, os.X_OK)
    locks = []
    for filename in LOCK_PATHS:
        metadata = regular(filename)  # Read metadata only; no lock acquisition.
        locks.append({"path": filename, "dev": metadata.st_dev, "ino": metadata.st_ino})
    guard(request)
    return {
        "owner": request["owner"], "hostname": socket.gethostname(), "uid": os.getuid(),
        "runtime_root": str(RUNTIME), "source_commit": COMMIT,
        "source_files": hashes, "tools_train_sha256": sha(train),
        "runtime_config_current_sha256": sha(config),
        "runtime_config_canonical_preview": preview,
        "python": PYTHON, "python_realpath": str(real_python),
        "python_sha256": sha(real_python), "conda_prefix": PREFIX,
        "original_conda_source": str(BASE), "original_conda_source_sha256": sha(BASE),
        "lock_files": locks, "core_sha256": CORE_SHA, "factory_sha256": FACTORY_SHA,
        "production_stage": str(PRODUCTION), "kind": "actual_CPU_observation_only",
        "GPU_occupancy_or_resource_PASS": False,
    }


def embedded_evidence(item):
    raw = base64.b64decode(item["bytes_base64"], validate=True)
    assert digest(raw) == item["sha256"]
    return json.loads(raw)


def shim_source(entry_sha):
    return f'''#!/usr/bin/env bash
_nsd_owner_deadline_guard() {{
 /usr/bin/python3 -I -B -c {shlex.quote("from datetime import datetime,timezone;assert datetime.now(timezone.utc)<datetime.fromisoformat(" + repr(OWNER_DEADLINE) + ")")}
}}
_nsd_owner_deadline_guard || return 126
read -r _nsd_base_sha _ < <(/usr/bin/sha256sum -- {shlex.quote(str(BASE))})
[[ "$_nsd_base_sha" == {shlex.quote(BASE_SHA)} ]] || return 126
source {shlex.quote(str(BASE))} || return "$?"
declare -F __conda_activate >/dev/null || return 126
_nsd_bin={shlex.quote(str(PRODUCTION / "bin"))}
[[ -x "$_nsd_bin/python" && ! -L "$_nsd_bin/python" ]] || return 126
read -r _nsd_entry_sha _ < <(/usr/bin/sha256sum -- "$_nsd_bin/python")
[[ "$_nsd_entry_sha" == {shlex.quote(entry_sha)} ]] || return 126
_nsd_prepend_python() {{
 [[ "${{CONDA_PREFIX:-}}" == {shlex.quote(PREFIX)} ]] || return 126
 unset -f python 2>/dev/null || return 126
 unalias python 2>/dev/null || :
 export PATH="$_nsd_bin:$PATH"
 hash -r
 [[ "$(type -P python)" == "$_nsd_bin/python" && "$(type -t python)" == file ]] || return 126
}}
conda() {{
 [[ "$#" == 2 && "$1" == activate && "$2" == project_cluster ]] || return 126
 _nsd_owner_deadline_guard || return 126
 __conda_activate "$@" || return "$?"
 _nsd_prepend_python
}}
return 0
'''


def render(request):
    guard(request)
    prior_path = PRODUCER / "actual_observation.json"
    regular(prior_path)
    assert sha(prior_path) == request["actual_observation_sha256"]
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    current = observe(request)
    assert current == prior, "Actual production facts changed; do not install/replay"
    receipt = embedded_evidence(request["admission_receipt"])
    assert receipt["id"] == "M233-NDE" and receipt["config"] == CONFIG
    assert receipt["code_commit"] == COMMIT
    assert receipt["candidate_id"] == "hierarchy-native-distribution-embedding-composition"
    assert receipt["goal_sha256"] == "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
    assert receipt["profile"] == "experiment_first"
    decision = receipt["decision"]
    assert isinstance(decision, dict)
    assert decision["path"].startswith("pipeline/decisions/")
    assert len(decision["sha256"]) == 64
    for name in ("native_backward", "resources", "independence", "constraints"):
        assert receipt["gates"][name]["passed"] is True
    activation = embedded_evidence(request["activation_receipt"])
    assert activation["decision"] == "ALLOW_PRODUCTION_PATH_RENDER"
    assert activation["owner"] == request["owner"]
    assert activation["actual_observation_sha256"] == request["actual_observation_sha256"]
    assert activation["admission_receipt_sha256"] == request["admission_receipt"]["sha256"]
    assert activation["training_launch_authorized"] is False
    assert not PRODUCTION.exists(), "Existing stage must reconcile, never overwrite"
    factory = ModuleType("nsd_fixed_factory")
    raw_factory = (PRODUCER / "entry_factory.py").read_bytes()
    exec(compile(raw_factory, str(PRODUCER / "entry_factory.py"), "exec"), factory.__dict__)
    binding = {
        "kind": "production", "hostname": "dl04-MS-7E06", "uid": 1001,
        "runtime_root": str(RUNTIME), "source_commit": COMMIT,
        "conda_prefix": PREFIX, "python": PYTHON,
        "python_realpath": current["python_realpath"],
        "python_sha256": current["python_sha256"],
        "runtime_config_sha256": current["runtime_config_canonical_preview"]["sha256"],
        "activation_receipt_sha256": request["activation_receipt"]["sha256"],
        "physical_gpu": 0,
        "expected_gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c",
        "max_project_tasks": 1, "required_free_memory_mib": 20000,
        "resource_values_are_contract_not_current_GPU_observation": True,
        "source_files": current["source_files"], "argv": EXACT_ARGS,
        "lock_files": current["lock_files"], "stage": str(PRODUCTION),
        "entry": str(PRODUCTION / "bin/python"),
        "one_shot_marker": str(PRODUCTION / "train-consumed.json"),
    }
    artifact = factory.render_entry(
        PRODUCTION, binding, (PRODUCER / "lock_core.py").read_bytes(), "production")
    shim = PRODUCTION / "conda_source.sh"
    with shim.open("x", encoding="utf-8") as stream:
        stream.write(shim_source(artifact["entry_sha256"]))
    shim.chmod(0o600)
    # Real conda/path/interpreter CPU verification only. This cannot invoke
    # tools/train.py, open three locks, or consume the one-shot marker.
    normal = "import json,os,sys;print(json.dumps({'python':sys.executable,'prefix':os.environ.get('CONDA_PREFIX'),'pid':os.getpid()}))"
    prefix = ("source " + shlex.quote(str(shim)) +
              " && conda activate project_cluster && ")
    resolved = run(["/bin/bash", "-c", prefix +
                    'printf "%s\\n" "$(type -t python)" "$(type -P python)"'])
    assert resolved.splitlines() == ["file", binding["entry"]]
    diagnostic = json.loads(run(["/bin/bash", "-c", prefix +
                                "python -B -c " + shlex.quote(normal)]))
    assert Path(diagnostic["python"]).resolve() == Path(PYTHON).resolve()
    assert diagnostic["prefix"] == PREFIX
    assert not Path(binding["one_shot_marker"]).exists()
    guard(request)
    result = {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": request["owner"],
        "kind": "PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED",
        "binding": binding, "artifact": artifact, "shim": str(shim),
        "shim_sha256": sha(shim), "diagnostic": diagnostic,
        "actual_conda_PATH_resolution": resolved.splitlines(),
        "files": {p.relative_to(PRODUCTION).as_posix(): sha(p)
                  for p in PRODUCTION.rglob("*") if p.is_file()},
        "training_launch_or_GPU_use": False, "one_shot_consumed": False,
        "independent_production_review": "PENDING_ROOT_PEER_REVIEW",
    }
    save_new(PRODUCER / "production_render_result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("collect", "render"))
    parser.add_argument("--request", required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args()
    request_path = Path(args.request).resolve()
    assert request_path.parent == PRODUCER
    regular(request_path)
    assert sha(request_path) == args.request_sha256
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["action"] == args.action
    guard(request)
    if args.action == "collect":
        result = observe(request)
        save_new(PRODUCER / "actual_observation.json", result)
    else:
        result = render(request)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
