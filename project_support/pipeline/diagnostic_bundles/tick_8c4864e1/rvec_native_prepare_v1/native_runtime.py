"""RVE native guards. Import is stdlib-only and performs no external action."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess

OWNER = {"token": "8c4864e1a36e4f3883b3d301cfc39069", "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
         "generated_at": "2026-11-08T23:07:37.192344+00:00", "deadline_at": "2026-11-09T00:07:37.192344+00:00",
         "context_sha256": "1355b39f8a8e1e3014fc9a88c859829961fe5440fb90d5c44bead5b2ff6b0643",
         "pending_sha256": "899db4c29a4d1a8412badfd2344695d0e357c1adfd050a2e78f3850c48a30ed2"}
ROOT = Path("/data/songcl/Project/Cluster_project/Cluster_nsd_20261107")
STAGE = Path(__file__).resolve().parent
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CANDIDATE = NAME + "_rvec"
RUNTIME_HEAD = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
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
    assert STAGE == Path("/data/songcl/Project/Cluster_project/pipeline/rvec_8c4864e1_gpu0")
    assert MANIFEST["owner"] == OWNER and MANIFEST["runtime_code_commit"] == RUNTIME_HEAD
    assert MANIFEST["candidate_id"] == "fine-leaf-receiver-conditioned-vector-exchange"
    assert MANIFEST["experiment_id"] == "M234-RVE" and MANIFEST["goal_sha256"] == GOAL
    assert MANIFEST["physical_gpu"] == 0 and MANIFEST["gpu_uuid"] == GPU_UUID
    assert MANIFEST["resource_authorization"] == RESOURCE_AUTHORIZATION
    assert MANIFEST["resource_memory_policy"] == RESOURCE_MEMORY_POLICY
    version_path = STAGE / "source_binding.json"
    assert sha(version_path) == MANIFEST["source_binding_sha256"]
    version = json.loads(version_path.read_text())
    assert version["candidate_id"] == MANIFEST["candidate_id"]
    assert version["source_parent_commit"] == RUNTIME_HEAD
    assert re.fullmatch(r"[0-9a-f]{40}", version["source_commit"])
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
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid == 1001 and (proc / "cwd").resolve() == ROOT:
                argv = (proc / "cmdline").read_bytes().split(b"\0")
                assert b"tools/train.py" not in argv, "Existing same-root project trainer is preserved"
        except (OSError, RuntimeError):
            pass
    before = observe(True)
    try:
        for kind in ("training", "diagnostic", "exclusive"):
            handle = open("/tmp/cluster_project_gpu0_" + kind + ".lock", "a+b")
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BaseException:
                handle.close()
                raise
            HANDLES.append(handle)
        observe(True)
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
