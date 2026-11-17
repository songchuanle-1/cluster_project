"""CSO private-source native guards. Import is stdlib-only and performs no external action."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess

OWNER = {
    "token": "91c85c4270bd407ba432eca5dbf7d3a8",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T15:11:36.784479+00:00",
    "deadline_at": "2026-11-10T16:11:36.784479+00:00",
    "context_sha256": "d1a82f07e45547ddd21ae1b683c512ebdc507d2918a2e3d29f3042d06c4cfb29",
    "pending_sha256": "f72d8f0311730464227da959d659ce43712b147d50bfba10cdbd70ceaa256985"
}
ROOT = Path("/data/songcl/Project/Cluster_project/Cluster_nsd_20261107")
STAGE = Path(__file__).resolve().parent
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CANDIDATE = NAME + "_cso"
RUNTIME_HEAD = "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"
SOURCE_PARENT = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
SOURCE_COMMIT = "af45707d7b6089f764843337c5f88af285383f88"
GPU_UUID = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
GOAL = "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
RESOURCE_AUTHORIZATION = {"path": "pipeline/authorizations/server4_gpu0_overlay_20261104.json",
                          "sha256": "783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88"}
RESOURCE_MEMORY_POLICY = {"allow_external_overlay": True, "minimum_free_mib_before_launch": 20000,
    "max_project_tasks_per_gpu": 1, "cooperative_lock_kinds": ["training", "diagnostic", "exclusive"],
    "external_contexts": "record_preserve_no_signals",
    "measurement_scope": "authorized_overlay_potentially_contended_not_exclusive"}
MANIFEST = {}
HANDLES = []


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify():
    assert socket.gethostname() == "dl04-MS-7E06" and os.getuid() == os.geteuid() == 1001
    assert STAGE == Path("/data/songcl/Project/Cluster_project/pipeline/cso_91c85c42_gpu0")
    assert MANIFEST["owner"] == OWNER and MANIFEST["runtime_code_commit"] == RUNTIME_HEAD
    assert MANIFEST["candidate_id"] == "fine-leaf-full-covariance-shape-composition"
    assert MANIFEST["goal_sha256"] == GOAL
    assert MANIFEST["physical_gpu"] == 0 and MANIFEST["gpu_uuid"] == GPU_UUID
    assert MANIFEST["resource_authorization"] == RESOURCE_AUTHORIZATION
    assert MANIFEST["resource_memory_policy"] == RESOURCE_MEMORY_POLICY
    environment_path = STAGE / "environment_binding.json"
    assert sha(environment_path) == MANIFEST["environment_binding_sha256"]
    environment = json.loads(environment_path.read_text())
    assert environment["owner"] == OWNER and environment["selected_arm"] == "activated_native"
    assert environment["actual_import_passed"] is True and environment["cuda_initialized_after"] is False
    assert environment["base_conda_source"] == "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
    assert sha(environment["base_conda_source"]) == environment["base_conda_sha256"] == "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
    import site
    import sys
    assert not sys.flags.isolated and site.ENABLE_USER_SITE is True
    assert environment["user_site_directory"] in sys.path
    assert sha(environment["compatible_extension_path"]) == environment["compatible_extension_sha256"] == "ef0daa5ccf7fe471a5d73528762f209ba6d2dd89a6c3b50c6371eb9e0edebcfe"
    assert str(Path(sys.executable)) == environment["python_path"] and sha(sys.executable) == environment["python_sha256"]
    version_path = STAGE / "source_binding.json"
    assert sha(version_path) == MANIFEST["source_binding_sha256"]
    version = json.loads(version_path.read_text())
    assert version["candidate_id"] == MANIFEST["candidate_id"]
    assert version["source_parent_commit"] == SOURCE_PARENT
    assert version["experiment_id"] == MANIFEST["experiment_id"]
    assert version["source_snapshot_sha256"] == MANIFEST["source_snapshot_sha256"]
    assert version["runtime_original_parent_commit"] == RUNTIME_HEAD
    proof = version["source_version_proof"]
    assert proof["owner"] == OWNER and proof["source_parent_commit"] == version["source_parent_commit"] == SOURCE_PARENT
    assert proof["runtime_original_parent_commit"] == RUNTIME_HEAD
    assert proof["source_commit"] == version["source_commit"]
    assert proof["source_files_exact9"] == version["source_files"]
    assert sha(STAGE / "source_version.json") == version["source_snapshot_sha256"]
    assert version["source_commit"] == SOURCE_COMMIT, "Require retained exact CSO source commit"
    assert version["source_commit"] == MANIFEST["code_commit"] and len(version["source_files"]) == 9
    assert version["candidate_source_hashes"] == MANIFEST["candidate_source_hashes"]
    assert version["candidate_config_sha256"] == MANIFEST["candidate_config_sha256"]
    for name, expected in MANIFEST["candidate_source_hashes"].items():
        assert Path(name).name == name and sha(STAGE / "candidate_model" / name) == expected, name
    assert len(MANIFEST["candidate_source_hashes"]) == 8
    assert sha(STAGE / "candidate.yaml") == MANIFEST["candidate_config_sha256"]
    assets = MANIFEST["assets"]
    for name, expected in assets["source_hashes"].items():
        assert sha(ROOT / "framework/model/Quard_model" / NAME / name) == expected, name
    for key, path_key in (("config", "config_path"), ("annotation", "annotation_path"),
                          ("checkpoint", "checkpoint"), ("pretrain", "pretrain")):
        assert sha(assets[path_key]) == assets[key + "_sha256"], key
    assert sha(ROOT / "framework/dataset/scannetv2.py") == assets["dataset_source_sha256"]
    assert sha(ROOT / "tools/train.py") == assets["native_train_source_sha256"]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null")
    actual = subprocess.check_output(["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                                     "-C", str(ROOT), "rev-parse", "--verify", "HEAD"],
                                    text=True, env=env, timeout=15).strip()
    assert actual == RUNTIME_HEAD, "No runtime checkout/source synchronization is permitted"
    for name, expected in MANIFEST["diagnostic_files"].items():
        path = (STAGE / name).resolve()
        assert path.is_relative_to(STAGE.resolve()) and sha(path) == expected, name


def observe(require_usable=False):
    assert socket.gethostname() == "dl04-MS-7E06"
    row = subprocess.check_output(["nvidia-smi", "-i", "0",
        "--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    fields = [part.strip() for part in row.split(",")]
    assert len(fields) == 5 and fields[:2] == ["0", GPU_UUID]
    used, total, utilization = map(int, fields[2:])
    assert 0 <= used <= total
    contexts = subprocess.check_output(["nvidia-smi", "-i", "0",
        "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
        text=True, timeout=10).strip()
    external = []
    for line in contexts.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if parts and parts[0].isdigit() and int(parts[0]) != os.getpid():
            external.append({"pid": int(parts[0]), "used_memory_mib": parts[1]})
    free = total - used
    usable = free >= 20000
    if require_usable:
        assert usable, "Actual free GPU0 memory below 20000 MiB; external tasks remain untouched"
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "gpu": row, "contexts": contexts,
            "external_contexts": external, "memory_used_mib": used, "memory_total_mib": total,
            "memory_free_mib": free, "utilization_percent": utilization,
            "usable_under_current_overlay_policy": usable,
            "resource_authorization": RESOURCE_AUTHORIZATION, "resource_memory_policy": RESOURCE_MEMORY_POLICY,
            "cooperative_project_locks_held": len(HANDLES),
            "measurement_scope": RESOURCE_MEMORY_POLICY["measurement_scope"], "exclusive_measurement_claimed": False}


def acquire(lease_path):
    import fcntl
    import signal
    import stat
    assert not HANDLES and not MANIFEST
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert str(Path(lease_path).resolve()) == str(STAGE / "execution_lease.json")
    MANIFEST.update(json.loads((STAGE / "native_manifest.json").read_text()))
    lease = json.loads(Path(lease_path).read_text())
    assert lease["owner"] == OWNER and lease["thread_id"] == OWNER["thread_id"]
    assert lease["native_manifest_sha256"] == sha(STAGE / "native_manifest.json")
    assert lease["physical_gpu"] == 0 and lease["gpu_uuid"] == GPU_UUID
    assert lease["allowed_gpus"] == [0] and lease["project"] == "cluster_project"
    assert lease["resource_authorization"] == RESOURCE_AUTHORIZATION
    assert lease["resource_memory_policy"] == RESOURCE_MEMORY_POLICY
    assert lease["source_binding_sha256"] == MANIFEST["source_binding_sha256"]
    generated, deadline = map(datetime.fromisoformat, (OWNER["generated_at"], OWNER["deadline_at"]))
    now = datetime.now(timezone.utc)
    assert generated <= now < deadline and 0 < (deadline - generated).total_seconds() <= 3600
    remaining = (deadline - now).total_seconds()
    assert 300 < remaining <= 3600, "Require fresh current-owner lease with original 300-second guard"
    # Cap1 covers every same-user Cluster_project trainer, regardless of root or argv spelling.
    # It preserves M235 and every existing job; no Torch import or CUDA init has occurred.
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid != 1001:
                continue
            argv = [part.decode(errors="replace") for part in (proc / "cmdline").read_bytes().split(b"\0") if part]
            trainer = any(arg == "tools/train.py" or arg.endswith("/tools/train.py") for arg in argv)
            cwd = os.readlink(proc / "cwd")
            same_project = cwd == str(ROOT.parent) or cwd.startswith(str(ROOT.parent) + "/")
            assert not (trainer and same_project), "Existing Cluster_project trainer (including M235) occupies cap1; preserve and refuse"
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    before = observe(True)
    try:
        expected_locks = {"training": (66308, 92537152), "diagnostic": (66308, 92537153), "exclusive": (66308, 92537154)}
        identities = []
        for kind in ("training", "diagnostic", "exclusive"):
            lock_path = "/tmp/cluster_project_gpu0_" + kind + ".lock"
            descriptor = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
            handle = os.fdopen(descriptor, "r+b")
            try:
                opened, named = os.fstat(handle.fileno()), os.lstat(lock_path)
                assert stat.S_ISREG(opened.st_mode) and stat.S_ISREG(named.st_mode)
                assert (opened.st_dev, opened.st_ino) == expected_locks[kind]
                assert (named.st_dev, named.st_ino) == expected_locks[kind]
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                again = os.lstat(lock_path)
                assert (again.st_dev, again.st_ino) == expected_locks[kind]
            except BaseException:
                handle.close()
                raise
            HANDLES.append(handle)
            identities.append({"kind": kind, "path": lock_path, "device": opened.st_dev, "inode": opened.st_ino,
                               "opened_existing_NOFOLLOW_no_create": True, "nonblocking_acquired": True})
        for item in identities:
            named = os.lstat(item["path"])
            assert (named.st_dev, named.st_ino) == (item["device"], item["inode"])
        before["original_lock_identities"] = identities
        before["post_acquisition_observation"] = observe(True)
        verify()
        os.environ.update(CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES=GPU_UUID,
            PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
            TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="1")
        signal.alarm(min(600, int(remaining) - 150))
        return before
    except BaseException:
        release()
        raise


def release():
    for handle in reversed(HANDLES):
        handle.close()
    HANDLES.clear()


def fingerprint(torch, value):
    h = hashlib.sha256()
    def feed(item):
        if torch.is_tensor(item):
            item = item.detach().cpu().contiguous()
            h.update(str((str(item.dtype), tuple(item.shape))).encode())
            h.update(item.numpy().tobytes())
        elif isinstance(item, dict):
            for key in sorted(item):
                h.update(str(key).encode())
                feed(item[key])
        elif isinstance(item, (tuple, list)):
            for part in item:
                feed(part)
        else:
            h.update(repr(item).encode())
    feed(value)
    return h.hexdigest()


def save(name, value):
    assert Path(name).name == name
    value.update(observed_at=datetime.now(timezone.utc).isoformat(),
        resource_authorization=RESOURCE_AUTHORIZATION, resource_memory_policy=RESOURCE_MEMORY_POLICY,
        measurement_scope=RESOURCE_MEMORY_POLICY["measurement_scope"], exclusive_measurement_claimed=False)
    with (STAGE / name).open("x", encoding="utf8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
