"""Real TRAIN-data diagnostic carrier, v2; default NOP.

No local/remote launch is authorized by this source. A missing prerequisite
blocks before importing Torch. Supply only supervisor-owned anonymous FDs.
"""
import argparse
import datetime as dt
import faulthandler
import functools
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
import traceback

OWNER = {
    "token": "4ecb5020c4c54abeb26dc874ed90080e",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T01:06:58.009358+00:00",
    "deadline_at": "2026-11-10T02:06:58.009358+00:00",
    "context_sha256": "a143a825802aa28c5db3b61c93314f0b2d764e02ed0cb7008d88c8e6bc280f4d",
    "pending_sha256": "71bc1ed72a827fe476a5e8492671d879e0d24bec5b16a3bd674f3022994ea08d",
}
SOURCE_COMMIT = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
RUNTIME = Path("/data/songcl/Project/Cluster_project/Cluster_nsd_20261107")
PREFIX = Path("/home/songcl/.conda/envs/project_cluster")
DATA = Path("/home/songcl/data/data")
CONFIG_REL = "configs/Quard/ctf_hcg_csort_rvec/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec.yaml"
CONSUMED_BATCHES = 10
EVENT_BYTES = 2 * 1024 * 1024
EVENT_COUNT = 8192
INSTALLED_SOURCE_PINS = {
    "lib/python3.10/site-packages/torch/utils/data/dataloader.py":
        "fbd260c9587fadb2f81dc255b080356261df3a6827272c07f11ab1ac20276ef0",
    "lib/python3.10/site-packages/torch/utils/data/_utils/worker.py":
        "d3652cf902df501a6e824659b5a07941db9b689834a2acd18dabf16f2e0633e8",
    "lib/python3.10/multiprocessing/util.py":
        "027d6642308f741f94d44fc79c23e4d1a1c275159823720ccb05b0a8e705450a",
    "lib/python3.10/multiprocessing/process.py":
        "9a5f6ca49fb78452678bed74f9b09491c688571f9f09edb97758933294356513",
    "lib/python3.10/multiprocessing/popen_fork.py":
        "0a09db57e7fab7061c01a61778feea6e2b6bb02ccbc150332f2960b05258ef95",
}
SOURCE_PINS = {
    "framework/dataset/scannetv2.py": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
    "framework/dataset/__init__.py": "eb3f092f427ec70c62adfa5c7e4586335fbc925ea76d175ef33387f9fa4da33c",
    "framework/__init__.py": "08a6daec10d4fb5e2599c9fe90d54001f06520c7e2119e8a92e17cc628f2b662",
}
TORCH = NP = LOG = PACKET = None
ACTIVE = None
STOP = None
CAPTURED = []
STARTING_LOADER = False
ITERATOR = None
LOADER = None
FDS = {}
SAFE_STATUS_FD = None
FORKING_RECORD = None
SIGNALS_SENT = []
HELPER_COUNT = 0
ORIGINAL_POPEN = subprocess.Popen
IPV6_SOCKET = None
IPV6_BIND_COUNT = 0
IPV6_SOURCE_IDENTITY = None


class Blocked(RuntimeError):
    pass


def require(condition, reason):
    if not condition:
        raise Blocked(reason)


def digest(path, cap=2 * 1024 * 1024):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= cap, "PIN_FILE_MISSING_OR_BYTE_CAP:" + str(path))
    with path.open("rb") as stream:
        return hashlib.sha256(stream.read(cap + 1)).hexdigest()


def identity(pid=None):
    pid = os.getpid() if pid is None else pid
    try:
        text = Path("/proc/%d/stat" % pid).read_text()
        fields = text.rsplit(")", 1)[1].split()
        return {"pid": pid, "start_ticks": fields[19], "ppid": int(fields[1]),
                "pgrp": int(fields[2]), "uid": Path("/proc/%d" % pid).stat().st_uid}
    except (FileNotFoundError, ProcessLookupError):
        return {"pid": pid, "start_ticks": None, "absent": True}


def cpu_assert():
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CUDA_MASK_NOT_EMPTY")
    if TORCH is not None:
        require(not TORCH.cuda.is_initialized(), "CUDA_ALREADY_INITIALIZED")


def checkpoint():
    cpu_assert()
    require(time.monotonic() < STOP, "SOFT_TIME_BUDGET_NO_NEW_NATIVE_BOUNDARY")
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(OWNER["deadline_at"]),
            "CURRENT_LEASE_EXPIRED")


class Events:
    def __init__(self, fd):
        self.fd, self.bytes, self.seq = fd, 0, 0

    def write(self, stage, **fields):
        self.seq += 1
        row = {"seq": self.seq, "monotonic_ns": time.monotonic_ns(),
               "pid": os.getpid(), "stage": stage, **fields}
        raw = (json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n").encode()
        require(len(raw) <= 16384, "SINGLE_EVENT_BYTE_CAP")
        require(self.seq <= EVENT_COUNT and self.bytes + len(raw) <= EVENT_BYTES,
                "EVENT_EVIDENCE_CAP_NO_FURTHER_NATIVE_WORK")
        written = os.write(self.fd, raw)
        require(written == len(raw), "SHORT_EVENT_WRITE")
        self.bytes += written


def meta(value, depth=0):
    if TORCH is not None and isinstance(value, TORCH.Tensor):
        return {"type": "Tensor", "shape": list(value.shape), "dtype": str(value.dtype),
                "device": str(value.device), "contiguous": value.is_contiguous()}
    if NP is not None and isinstance(value, NP.ndarray):
        return {"type": "ndarray", "shape": list(value.shape), "dtype": str(value.dtype),
                "contiguous": bool(value.flags.c_contiguous)}
    if isinstance(value, str):
        return {"type": "str", "length": len(value)}
    if isinstance(value, (int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return {"type": type(value).__name__, "len": len(value),
                "items": [meta(v, depth + 1) for v in value[:6]] if depth < 1 else None}
    if isinstance(value, dict):
        return {"type": "dict", "len": len(value), "keys": list(value)[:24]}
    return {"type": type(value).__name__}


def rng_digest():
    # State getters are observational; no draw, seed, restore or data mutation.
    state = NP.random.get_state()
    return {
        "python": hashlib.sha256(repr(random.getstate()).encode()).hexdigest(),
        "numpy": hashlib.sha256(state[1].tobytes() + repr((state[0], state[2:])).encode()).hexdigest(),
        "torch_cpu": hashlib.sha256(TORCH.get_rng_state().numpy().tobytes()).hexdigest(),
    }


def group_identity(dataset, index):
    rows = dataset.scene_inputs[index]
    return {"dataset_index": int(index), "scene_ids": [str(row["scene_id"]) for row in rows],
            "ann_ids": [str(row["ann_id"]) for row in rows]}


def stage_wrapper(original, stage, skip_self=False):
    @functools.wraps(original)
    def observed(*args, **kwargs):
        checkpoint()
        selected = args[1:] if skip_self else args
        LOG.write(stage + ".enter", sample=ACTIVE, inputs=meta(selected), kwarg_names=list(kwargs))
        try:
            result = original(*args, **kwargs)
        except BaseException as exc:
            LOG.write(stage + ".exception", sample=ACTIVE, error_type=type(exc).__name__,
                      error=str(exc)[:400])
            raise
        cpu_assert()
        LOG.write(stage + ".exit", sample=ACTIVE, output=meta(result))
        return result
    return observed


def stat_fingerprint(path):
    path = Path(path).resolve(strict=True)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode), "DATA_NOT_REGULAR")
    return {"path": str(path), "dev": info.st_dev, "ino": info.st_ino,
            "bytes": info.st_size, "mtime_ns": info.st_mtime_ns}


def verify_data_file(path):
    record = stat_fingerprint(path)
    target = Path(record["path"])
    train_root = (DATA / "scannetv2/train").resolve(strict=True)
    clip_root = (DATA / "clip_feat").resolve(strict=True)
    require(ACTIVE is not None and ACTIVE.get("scene_ids"), "DATA_LOAD_OUTSIDE_ORIGINAL_GETITEM")
    scenes = set(ACTIVE["scene_ids"])
    if target.parent == train_root and target.name.endswith("_refer.pth"):
        # The exact original __getitem__ selects the first sorted filename
        # containing the scene ID; do not replace that algorithm.
        selected = ACTIVE.get("original_selected_train_path")
        require(selected == record["path"] and any(scene in str(target) for scene in scenes),
                "TRAIN_FILE_DIFFERS_FROM_ORIGINAL_SELECTION")
    else:
        require(target.parent == clip_root and target.suffix == ".pth" and target.stem in scenes,
                "LOAD_OUTSIDE_NATIVE_TRAIN_OR_CLIP_ROOT")
    LOG.write("torch_load.file_identity", sample=ACTIVE, file=record)
    return record


def install_write_and_network_guard(packet):
    approved_fds = set(FDS.values())
    ipc = Path(packet["owned_ipc_directory"]).resolve(strict=True)
    ipc_stat = ipc.stat()
    require(ipc_stat.st_uid == os.getuid() and stat.S_ISDIR(ipc_stat.st_mode) and
            ipc_stat.st_mode & 0o077 == 0, "IPC_DIRECTORY_IDENTITY")
    require(str(ipc).startswith("/tmp/m234_trace_4ecb5020_"), "IPC_DIRECTORY_SCOPE")
    require(os.environ.get("TMPDIR") == str(ipc), "OWNED_IPC_TMPDIR_MISMATCH")

    def owned_path(value):
        if not isinstance(value, (str, bytes, os.PathLike)):
            return False
        try:
            return Path(os.fsdecode(value)).resolve().is_relative_to(ipc)
        except (ValueError, OSError):
            return False

    def audit(event, args):
        global HELPER_COUNT, IPV6_SOCKET, IPV6_BIND_COUNT
        if event == "open":
            path, mode, flags = args
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT |
                                                    os.O_TRUNC | os.O_APPEND))
            if writing:
                null_ok = False
                if isinstance(path, (str, bytes)) and os.fsdecode(path) == "/dev/null":
                    info = os.lstat("/dev/null")
                    null_ok = (stat.S_ISCHR(info.st_mode) and info.st_rdev == os.makedev(1, 3) and
                               isinstance(flags, int) and not flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND))
                require(null_ok or (isinstance(path, int) and path in approved_fds) or owned_path(path),
                        "PERSISTENT_WRITE_DENIED:" + str(path)[:200])
        elif event in {"os.mkdir", "os.remove", "os.rmdir", "os.unlink", "os.chmod", "os.truncate"}:
            require(owned_path(args[0]), "PERSISTENT_MUTATION_DENIED:" + event)
        elif event in {"os.rename", "os.replace", "os.link", "os.symlink"}:
            require(owned_path(args[0]) and owned_path(args[1]), "PERSISTENT_MUTATION_DENIED:" + event)
        elif event == "socket.__new__":
            if args[1] != socket.AF_UNIX:
                policy = packet["local_ipv6_probe_policy"]
                caller = any(row.filename == policy["path"] and row.name == "_has_ipv6"
                             for row in traceback.extract_stack(limit=14))
                require(caller and IPV6_SOCKET is None and IPV6_BIND_COUNT == 0 and
                        args[1] == socket.AF_INET6 and args[2] == socket.SOCK_STREAM and args[3] == 0,
                        "NON_UNIX_SOCKET_OUTSIDE_AUTHENTIC_IPV6_PROBE_DENIED")
                verify_ipv6_policy(policy)
                IPV6_SOCKET = args[0]
        elif event in {"socket.connect", "socket.bind"}:
            connection, address = args
            if event == "socket.bind" and connection is IPV6_SOCKET:
                policy = packet["local_ipv6_probe_policy"]
                caller = any(row.filename == policy["path"] and row.name == "_has_ipv6"
                             for row in traceback.extract_stack(limit=14))
                require(caller and IPV6_BIND_COUNT == 0 and address == ("::1", 0) and
                        connection.family == socket.AF_INET6 and connection.type == socket.SOCK_STREAM and
                        connection.proto == 0 and connection.fileno() >= 0, "EXACT_LOCAL_IPV6_BIND_ONLY")
                verify_ipv6_policy(policy)
                IPV6_BIND_COUNT += 1
                LOG.write("allowed_loopback_ipv6_capability_bind", address=list(address),
                          family=int(connection.family), socket_type=int(connection.type),
                          protocol=connection.proto, source_sha256=policy["sha256"],
                          source_identity=IPV6_SOURCE_IDENTITY, listen_connect_send_DNS_allowed=False)
            else:
                require(connection.family == socket.AF_UNIX and owned_path(address),
                        "SOCKET_OUTSIDE_OWN_IPC_DENIED")
        elif event in {"socket.listen", "socket.send", "socket.sendall", "socket.sendto", "socket.sendmsg"}:
            require(args[0].family == socket.AF_UNIX, "EXTERNAL_NETWORK_LISTEN_OR_SEND_DENIED")
        elif event == "subprocess.Popen":
            executable, argv, cwd, environment = args
            policy = packet["readonly_helper_policy"]
            authentic = any(row.filename == policy["platform_path"] and row.name == "from_subprocess"
                            for row in traceback.extract_stack(limit=14))
            require(executable == "uname" and isinstance(argv, (list, tuple)) and
                    list(argv) == ["uname", "-p"] and cwd is None and environment is None and
                    authentic and HELPER_COUNT == 0, "UNAPPROVED_SUBPROCESS_DENIED")
            verify_readonly_uname(policy)
            HELPER_COUNT += 1
            LOG.write("readonly_helper.allowed", argv=["uname", "-p"], source="authenticated_platform.from_subprocess")
        elif event in {"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr",
                       "os.system", "os.posix_spawn", "os.exec"}:
            raise Blocked("NETWORK_OR_EXEC_DENIED:" + event)
        elif event in {"os.kill", "os.killpg"}:
            raise Blocked("PROCESS_SIGNAL_DENIED")
        elif event == "import" and args[0].startswith(("framework.model", "tools.train")):
            raise Blocked("MODEL_OR_TRAIN_IMPORT_DENIED")
    sys.addaudithook(audit)


def verify_ipv6_policy(policy):
    global IPV6_SOURCE_IDENTITY
    path = Path(policy["path"])
    require(str(path) == str(PREFIX / "lib/python3.10/site-packages/urllib3/util/connection.py") and
            path.resolve(strict=True) == path and
            policy.get("address") == ["::1", 0] and policy.get("maximum_binds") == 1,
            "AUTHENTIC_LOCAL_IPV6_POLICY_REQUIRED")
    info = path.stat()
    current = [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns]
    require(digest(path, 262144) == policy["sha256"], "URLLIB3_IPV6_SOURCE_HASH")
    if policy.get("identity") is not None:
        require(current == policy["identity"], "URLLIB3_IPV6_SOURCE_IDENTITY_CHANGED")
    if IPV6_SOURCE_IDENTITY is None:
        IPV6_SOURCE_IDENTITY = current
    else:
        require(current == IPV6_SOURCE_IDENTITY, "URLLIB3_IPV6_SOURCE_CHANGED_DURING_IMPORT")


def verify_readonly_uname(policy):
    path = Path(policy["path"])
    require(str(path) == "/usr/bin/uname" and path.resolve() == path, "EXACT_UNAME_PATH")
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022 and
            [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns] == policy["identity"],
            "AUTHENTIC_UNAME_IDENTITY")
    require(shutil.which("uname") is not None and Path(shutil.which("uname")).resolve() == path and
            digest(path, 1024 * 1024) == policy["sha256"] and
            digest(policy["platform_path"]) == policy["platform_sha256"], "UNAME_OR_PLATFORM_SOURCE_HASH")


class ObservedReadonlyPopen(ORIGINAL_POPEN):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.diagnostic_identity = identity(self.pid)
        self.diagnostic_pidfd = None
        if hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"):
            try:
                self.diagnostic_pidfd = os.pidfd_open(self.pid, 0)
            except ProcessLookupError:
                pass
        LOG.write("readonly_helper.started", identity=self.diagnostic_identity, argv=["uname", "-p"])

    def communicate(self, input=None, timeout=None):
        try:
            result = super().communicate(input=input, timeout=5 if timeout is None else min(timeout, 5))
        except subprocess.TimeoutExpired:
            if self.diagnostic_pidfd is None:
                LOG.write("readonly_helper.uncertain", identity=self.diagnostic_identity,
                          reason="NO_PIDFD_NO_SIGNAL_NO_RETRY")
                os._exit(6)  # Avoid subprocess.run's implicit numeric-PID kill.
            record = {"identity": self.diagnostic_identity, "pidfd": self.diagnostic_pidfd,
                      "fork_pid": self.pid}
            for signum in (signal.SIGTERM, signal.SIGKILL):
                own_signal(record, signum)
                try:
                    self.wait(timeout=2)
                    break
                except subprocess.TimeoutExpired:
                    continue
            if self.returncode is None:
                LOG.write("readonly_helper.uncertain", identity=self.diagnostic_identity)
                os._exit(6)
            raise Blocked("READONLY_UNAME_HELPER_TIMEOUT_BOUNDED_OWN_CLEANUP")
        LOG.write("readonly_helper.terminal", identity=self.diagnostic_identity, returncode=self.returncode)
        return result


def worker_init(worker_id):
    global LOG, ACTIVE
    # Installed _worker_loop must prove native signal handlers precede this call.
    target_fd = FDS["event_worker_%d" % worker_id]
    if LOG is None or LOG.fd != target_fd:
        LOG = Events(target_fd)
    ACTIVE = None
    faulthandler.enable(file=FDS["fault_worker_%d" % worker_id], all_threads=True)
    checkpoint()
    LOG.write("worker.init", identity=identity(), worker_id=worker_id,
              torch_initial_seed=TORCH.initial_seed(), rng=rng_digest(),
              start_method=TORCH.multiprocessing.get_start_method(),
              torch_num_threads=TORCH.get_num_threads(),
              process_threads=len(list(Path("/proc/self/task").iterdir())),
              cuda_initialized=TORCH.cuda.is_initialized())


class FiniteBatchPrefix:
    """Exactly ten batches from original BatchSampler; no eleventh next()."""
    def __init__(self, original, dataset):
        self.original, self.dataset = original, dataset
        self.scheduled = []

    def __len__(self):
        return CONSUMED_BATCHES

    def __iter__(self):
        source = iter(self.original)
        for batch_id in range(CONSUMED_BATCHES):
            checkpoint()
            indices = next(source)
            require(len(indices) == 2, "ORIGINAL_SAMPLER_BATCH_SIZE")
            groups = [group_identity(self.dataset, index) for index in indices]
            self.scheduled.append(list(indices))
            LOG.write("sampler.schedule", batch_id=batch_id, groups=groups)
            yield indices


def install_observers(dataset_module, dataset):
    cls = type(dataset)
    original_getitem = cls.__getitem__

    @functools.wraps(original_getitem)
    def getitem(self, index):
        global ACTIVE
        checkpoint()
        previous = ACTIVE
        ACTIVE = group_identity(self, index)
        first_scene = ACTIVE["scene_ids"][0]
        selected = next((fn for fn in self.sp_filenames if first_scene in fn), None)
        ACTIVE["original_selected_train_path"] = (
            str(Path(selected).resolve(strict=True)) if selected is not None else None)
        LOG.write("getitem.enter", sample=ACTIVE, rng=rng_digest())
        try:
            result = original_getitem(self, index)
            LOG.write("getitem.exit", sample=ACTIVE, rng=rng_digest(), output=meta(result))
            return result
        except BaseException as exc:
            LOG.write("getitem.exception", sample=ACTIVE, error_type=type(exc).__name__,
                      error=str(exc)[:400])
            raise
        finally:
            ACTIVE = previous
    cls.__getitem__ = getitem

    for name in ("load", "_torch_load_compat", "transform_train", "data_aug",
                 "elastic", "sample_rdn", "get_sp_label", "get_ref_mask",
                 "_get_token_positive_map_by_parse"):
        setattr(cls, name, stage_wrapper(getattr(cls, name), "dataset." + name, True))
    original_load = TORCH.load

    @functools.wraps(original_load)
    def load(*args, **kwargs):
        require(args and isinstance(args[0], (str, os.PathLike)), "TORCH_LOAD_REQUIRES_APPROVED_PATH")
        before = verify_data_file(args[0])
        result = stage_wrapper(original_load, "torch_load")(*args, **kwargs)
        require(stat_fingerprint(args[0]) == before, "DATA_FILE_CHANGED_DURING_LOAD")
        return result
    TORCH.load = load
    dataset.tokenizer.batch_encode_plus = stage_wrapper(
        dataset.tokenizer.batch_encode_plus, "tokenizer.batch_encode_plus")
    dataset_module.torch_scatter.scatter_mean = stage_wrapper(
        dataset_module.torch_scatter.scatter_mean, "torch_scatter.scatter_mean")
    original_collate = cls.collate_fn

    @functools.wraps(original_collate)
    def collate(self, batch):
        global ACTIVE
        previous = ACTIVE
        ACTIVE = {"collate_groups": [{"ann_ids": [str(v) for v in item[0]],
                                     "scene_id": str(item[1]), "coord": meta(item[2])} for item in batch]}
        try:
            return stage_wrapper(original_collate, "collate", True)(self, batch)
        finally:
            ACTIVE = previous
    cls.collate_fn = collate
    original_voxel = dataset_module.pointgroup_ops.voxelization_idx

    @functools.wraps(original_voxel)
    def voxel(coords, batch_size, mode):
        checkpoint()
        require(coords.device.type == "cpu", "VOXEL_COORDS_NOT_CPU")
        endpoints = [coords[0, 0].item(), coords[-1, 0].item()] if (
            coords.ndim == 2 and coords.shape[0] > 0 and coords.shape[1] > 0) else None
        LOG.write("voxel.contract", sample=ACTIVE, coords=meta(coords),
                  batch_size=batch_size, mode=mode,
                  first_last_batch_values=endpoints,
                  bounds_scope="Endpoints only; batch labels constructed by original collate. No extra full reduction.")
        return stage_wrapper(original_voxel, "pointgroup.voxelization_idx")(coords, batch_size, mode)
    dataset_module.pointgroup_ops.voxelization_idx = voxel


def install_process_capture(worker_loop):
    global FORKING_RECORD
    import multiprocessing.process
    base = multiprocessing.process.BaseProcess
    original_start = base.start
    original_fork = os.fork
    names = list(inspect.signature(worker_loop).parameters)
    require(names == ["dataset_kind", "dataset", "index_queue", "data_queue", "done_event",
                      "auto_collation", "collate_fn", "drop_last", "base_seed", "init_fn",
                      "worker_id", "num_workers", "persistent_workers", "shared_seed"],
            "INSTALLED_WORKER_SIGNATURE")

    def fork():
        global LOG, ACTIVE
        record = FORKING_RECORD
        require(STARTING_LOADER and record is not None, "UNREVIEWED_PYTHON_FORK")
        # Defer cooperative timeout/SIGCHLD exceptions until child ownership is
        # retained. Restore the exact inherited mask in both branches.
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGUSR1, signal.SIGCHLD})
        try:
            pid = original_fork()  # Call once, unchanged.
            if pid:
                record["fork_pid"] = pid
                if hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"):
                    try:
                        record["pidfd"] = os.pidfd_open(pid, 0)
                    except ProcessLookupError:
                        pass
                record["identity"] = identity(pid)
                LOG.write("worker.fork_captured", worker_id=record["worker_id"],
                          identity=record["identity"], pidfd_available=record["pidfd"] is not None)
            else:
                LOG = Events(FDS["event_worker_%d" % record["worker_id"]])
                ACTIVE = None
                faulthandler.enable(file=FDS["fault_worker_%d" % record["worker_id"]], all_threads=True)
                LOG.write("worker.after_fork_before_bootstrap", worker_id=record["worker_id"],
                          identity=identity())
            return pid
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    os.fork = fork

    @functools.wraps(original_start)
    def start(process, *args, **kwargs):
        global FORKING_RECORD
        require(STARTING_LOADER and process._target is worker_loop,
                "UNREVIEWED_PROCESS_CREATION")
        require(len(CAPTURED) < 4, "FOUR_WORKER_PROCESS_BOUND")
        params = dict(zip(names, process._args))
        require({"index_queue", "done_event", "worker_id"}.issubset(params),
                "PARTIAL_START_CAPTURE_FIELDS_UNAVAILABLE")
        record = {"process": process, "index_queue": params["index_queue"],
                  "done_event": params["done_event"], "worker_id": params["worker_id"],
                  "fork_pid": None, "pidfd": None, "identity": None}
        CAPTURED.append(record)  # Capture all references before original start.
        FORKING_RECORD = record
        try:
            return original_start(process, *args, **kwargs)
        finally:
            FORKING_RECORD = None
            LOG.write("worker.process_start_observed", worker_id=record["worker_id"],
                      identity=record["identity"], started_pid_known=process.pid is not None)
    base.start = start

    iterator_type = TORCH.utils.data.dataloader._MultiProcessingDataLoaderIter
    original_iterator_init = iterator_type.__init__

    @functools.wraps(original_iterator_init)
    def iterator_init(iterator, loader):
        global ITERATOR
        # Retain the object before its installed constructor can create any
        # worker. A raised constructor must not immediately run __del__.
        ITERATOR = iterator
        completed = False
        try:
            original_iterator_init(iterator, loader)
            completed = True
        finally:
            if not completed:
                iterator._shutdown = True
    iterator_type.__init__ = iterator_init


def wait_own_record(record):
    process = record["process"]
    if process.pid is not None:
        process.join(timeout=0)
        return process.exitcode
    pid = record.get("fork_pid")
    if pid is not None:
        if "partial_exitcode" not in record:
            try:
                found, status = os.waitpid(pid, os.WNOHANG)
                if found:
                    record["partial_exitcode"] = os.waitstatus_to_exitcode(status)
            except ChildProcessError:
                record["wait_uncertain"] = True
        return record.get("partial_exitcode")
    return "NOT_STARTED"


def own_signal(record, signum):
    require(record.get("pidfd") is not None and record.get("identity") and
            record["identity"].get("start_ticks"), "UNKNOWN_WORKER_IDENTITY_NO_SIGNAL")
    # A pidfd binds the process even if its numeric PID later disappears.
    now = identity(record["fork_pid"])
    require(now.get("start_ticks") == record["identity"]["start_ticks"] and
            now.get("uid") == 1001 and now.get("ppid") == os.getpid(),
            "WORKER_OWNERSHIP_CHANGED_NO_SIGNAL")
    try:
        signal.pidfd_send_signal(record["pidfd"], signum)
        observation = {"identity": record["identity"], "signal": int(signum),
                       "method": "pidfd_send_signal", "reason": "OWN_DIAGNOSTIC_BOUNDED_CLEANUP"}
        SIGNALS_SENT.append(observation)
        LOG.write("worker.cleanup_signal", **observation)
    except ProcessLookupError:
        pass


def cooperative_cleanup(seconds):
    # Installed pinned source proves done_event + None; no destructor fallback.
    if ITERATOR is not None:
        ITERATOR._shutdown = True
        require(getattr(ITERATOR, "_pin_memory_thread", None) is None,
                "UNREVIEWED_PIN_MEMORY_THREAD")
    # Diagnostic work has stopped. Keep installed failure notifications from
    # interrupting owned cleanup; the supervisor independently observes pidfds.
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    signal.signal(signal.SIGUSR1, lambda signum, frame: None)
    for record in CAPTURED:
        record["done_event"].set()
    for record in CAPTURED:
        queue = record["index_queue"]
        queue.cancel_join_thread()
        queue.put_nowait(None)
    def wait_for(duration):
        until = time.monotonic() + duration
        while time.monotonic() < until:
            pending = [record for record in CAPTURED if wait_own_record(record) is None]
            if not pending:
                return []
            time.sleep(min(0.025, max(0, until - time.monotonic())))
        return [record for record in CAPTURED if wait_own_record(record) is None]
    pending = wait_for(seconds)
    for signum, duration in ((signal.SIGTERM, 2), (signal.SIGKILL, 2)):
        for record in pending:
            if record.get("pidfd") is not None and (record.get("identity") or {}).get("start_ticks"):
                own_signal(record, signum)
        pending = wait_for(duration)
        if not pending:
            break
    fates = [{"worker_id": record["worker_id"], "identity": record["identity"],
              "exitcode": wait_own_record(record),
              "certainty": ("not_started" if wait_own_record(record) == "NOT_STARTED" else
                            "terminal" if wait_own_record(record) is not None else "uncertain"),
              "current_identity": identity(record["fork_pid"]) if record["fork_pid"] else None,
              "partial_start": record["process"].pid is None,
              "pidfd_captured": record["pidfd"] is not None}
             for record in CAPTURED]
    if ITERATOR is not None and getattr(ITERATOR, "_worker_pids_set", False):
        TORCH.utils.data._utils.signal_handling._remove_worker_pids(id(ITERATOR))
        ITERATOR._worker_pids_set = False
    return fates


def check_guarded_files():
    require(PACKET.get("guarded_files"), "CONSTRUCTOR_GUARDED_FILE_IDENTITIES_REQUIRED")
    for row in PACKET["guarded_files"]:
        path = Path(row["path"])
        info = path.stat()
        require(str(path.resolve(strict=True)) == row["resolved"] and
                [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns] == row["identity"],
                "CONSTRUCTOR_ASSET_IDENTITY_CHANGED:" + str(path))


def validate_packet(packet):
    require(packet.get("owner") == OWNER, "EXACT_CURRENT_OWNER_REQUIRED")
    require(packet.get("execution_authorized") is True, "PREPARATION_ONLY_NOT_AUTHORIZED")
    require(packet.get("status") == "READY_AFTER_ACTUAL_CONSTRUCTOR_AND_PEER_REVIEW", "UNVERIFIED_PREREQUISITES")
    require(packet.get("carrier_sha256") == digest(__file__), "CARRIER_SOURCE_HASH")
    require(os.name == "posix" and sys.version_info[:2] == (3, 10), "PROJECT_LINUX_PYTHON310_REQUIRED")
    require(Path(sys.executable).resolve() == PREFIX / "bin/python3.10", "ORDINARY_INTERPRETER_REQUIRED")
    require(Path.cwd().resolve() == RUNTIME and os.getuid() == os.geteuid() == 1001,
            "RUNTIME_OR_UID_IDENTITY")
    require(os.environ.get("PYTHONDONTWRITEBYTECODE") == "1" and sys.dont_write_bytecode,
            "BYTECODE_DISABLED_REQUIRED")
    require(os.environ.get("TOKENIZERS_PARALLELISM") == "false", "TOKENIZER_ENV_REQUIRED")
    require(os.environ.get("HF_HUB_OFFLINE") == "1" and os.environ.get("TRANSFORMERS_OFFLINE") == "1",
            "OFFLINE_REQUIRED")
    require(len(packet.get("constructor_actual_sha256", "")) == 64 and
            packet.get("constructor_status") == "CONSTRUCTOR_AND_CACHE_COVERAGE_PASS",
            "ACTUAL_IMPORT_AND_FULL_CACHE_COVERAGE_REQUIRED")
    require(len(packet.get("peer_review_sha256", "")) == 64, "FINAL_SOURCE_AND_SUPERVISOR_PEER_REVIEW_REQUIRED")
    require(packet.get("capacity_admitted") is True and packet.get("capacity_observation_sha256"),
            "CURRENT_CPU_RAM_SHARING_CAPACITY_ADMISSION_REQUIRED")
    require(15 <= packet.get("soft_work_seconds", 0) <= 120, "SOFT_WORK_BOUND")
    require(1 <= packet.get("cooperative_shutdown_seconds", 0) <= 10, "SHUTDOWN_BOUND")
    require(packet.get("consumed_batches") == CONSUMED_BATCHES and packet.get("scheduled_batches") == 10,
            "FINITE_WORK_DECLARATION")
    require(packet.get("historical_source_commit") == SOURCE_COMMIT, "HISTORICAL_SOURCE_BINDING")
    for rel, expected in SOURCE_PINS.items():
        require(digest(RUNTIME / rel) == expected, "ADMITTED_SOURCE_HASH:" + rel)
    for rel, expected in INSTALLED_SOURCE_PINS.items():
        require(digest(PREFIX / rel) == expected, "PINNED_INSTALLED_LIFECYCLE_CHANGED:" + rel)
    require(digest(RUNTIME / CONFIG_REL) ==
            "6807c2528dde696409dd2dc1102f9873d5b7b2d28b223338adcd22ec3ac07a26",
            "RENDERED_PRODUCTION_YAML_CHANGED")
    for pin in packet["file_hash_pins"]:
        require(digest(pin["path"], pin["byte_cap"]) == pin["sha256"], "PIN_MISMATCH:" + pin["path"])
    require(packet.get("import_paths") and all(
        Path(path).is_relative_to(RUNTIME) for path in packet["import_paths"]), "APPROVED_IMPORT_PATHS")
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(OWNER["deadline_at"]),
            "LEASE_EXPIRED_BEFORE_IMPORT")
    cpu_assert()


def execute(packet, fds):
    global TORCH, NP, LOG, PACKET, FDS, STOP, STARTING_LOADER, ITERATOR, LOADER, SAFE_STATUS_FD
    PACKET, FDS = packet, fds
    outcome = {"owner": OWNER, "kind": "REAL_TRAIN_DATASET_CPU_STAGE_TRACE",
               "root_cause": "UNKNOWN", "historical_crash_reproduced": False,
               "training_repair_verified": False, "signals_sent": False,
               "automatic_retry": False, "consumed_batches": 0}
    code = 2
    try:
        # Anonymous descriptors are created and retained by a separate reviewed
        # system-Python supervisor; project Python does not need memfd_create.
        expected_names = {"status", "event_parent", "fault_parent"} | {
            "%s_worker_%d" % (kind, i) for kind in ("event", "fault") for i in range(4)}
        require(set(fds) == expected_names and len(set(fds.values())) == 11, "EXACT_DISTINCT_OUTPUT_FDS")
        for fd in fds.values():
            target = os.readlink("/proc/self/fd/%d" % fd)
            require(target.startswith("/memfd:") and stat.S_ISREG(os.fstat(fd).st_mode),
                    "ONLY_SUPERVISOR_ANONYMOUS_MEMFD_OUTPUTS")
        SAFE_STATUS_FD = fds["status"]
        validate_packet(packet)
        check_guarded_files()
        LOG = Events(fds["event_parent"])
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        faulthandler.enable(file=fds["fault_parent"], all_threads=True)
        def cooperative_cancel(signum, frame):
            raise Blocked("SUPERVISOR_REQUESTED_COOPERATIVE_STOP")
        signal.signal(signal.SIGUSR1, cooperative_cancel)
        STOP = time.monotonic() + packet["soft_work_seconds"]
        verify_readonly_uname(packet["readonly_helper_policy"])
        verify_ipv6_policy(packet["local_ipv6_probe_policy"])
        subprocess.Popen = ObservedReadonlyPopen
        install_write_and_network_guard(packet)
        for path in reversed(packet["import_paths"]):
            sys.path.insert(0, path)
        import torch
        import numpy
        TORCH, NP = torch, numpy
        checkpoint()
        TORCH.multiprocessing.set_sharing_strategy("file_system")
        import gorilla
        import framework.dataset as dataset_module
        from torch.utils.data._utils.worker import _worker_loop
        cpu_assert()
        require(TORCH.__version__ == "2.8.0+cu128", "EXPECTED_INSTALLED_TORCH_VERSION")
        expected_origins = packet.get("expected_module_origins")
        require(expected_origins, "ACTUAL_CONSTRUCTOR_MODULE_ORIGINS_REQUIRED")
        for name, expected in expected_origins.items():
            require(expected is not None and getattr(sys.modules.get(name), "__file__", None) == expected,
                    "CONSTRUCTOR_IMPORT_ORIGIN_CHANGED:" + name)
        require(digest(RUNTIME / "framework/lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so",
                       128 * 1024 * 1024) ==
                "c86f516858d480e2583a437deb598279bc626e74975a060b17d75bf03f630033",
                "ADMITTED_POINTGROUP_BINARY_CHANGED")
        LOG.write("imports.complete", identity=identity(), torch=TORCH.__version__,
                  sharing_strategy=TORCH.multiprocessing.get_sharing_strategy(),
                  cuda_initialized=TORCH.cuda.is_initialized())
        cfg = gorilla.Config.fromfile(str(RUNTIME / CONFIG_REL))
        require(cfg.train.seed == 1999, "ORIGINAL_SEED")
        require(dict(cfg.dataloader.train) == {
            "batch_size": 2, "num_workers": 4, "persistent_workers": True}, "ORIGINAL_LOADER_YAML")
        train_cfg = cfg.data.train
        require(train_cfg.type == "scannetv2_sample_graph_edge" and train_cfg.dataset == "scanrefer" and
                train_cfg.prefix == "train" and train_cfg.training is True and train_cfg.mode == 4 and
                train_cfg.aug is True and train_cfg.with_elastic is True and train_cfg.lang_num_max == 4 and
                train_cfg.voxel_cfg.max_npoint == 2500000, "ORIGINAL_TRAIN_DATASET_YAML")
        cache_path = DATA / "scanrefer/scene_graphs_new_train.json"
        require(cache_path.is_file(), "CACHE_ABSENT_NO_FALLBACK")
        # Reuse the constructor's hash-bound file identities; no cache or PTH
        # rehash/inventory. Preserve the original constructor and deny fallback.
        original_graphs = dataset_module.ScanNetDataset_sample_graph_edge.load_scene_graphs
        def guarded_graphs(self):
            require(cache_path.is_file(), "GRAPH_CACHE_ABSENT_NO_FALLBACK")
            check_guarded_files()
            result = original_graphs(self)
            check_guarded_files()
            return result
        dataset_module.ScanNetDataset_sample_graph_edge.load_scene_graphs = guarded_graphs
        class DatasetLogger:
            def info(self, message):
                LOG.write("dataset.constructor.info", message=str(message)[:400])
        gorilla.set_random_seed(1999)
        checkpoint()
        dataset = dataset_module.build_dataset(train_cfg, DatasetLogger())
        missing_cache_entries = []
        for row in dataset.scanrefer:
            scene, ann = str(row["scene_id"]), str(int(row["ann_id"]))
            if scene not in dataset.scene_graphs or ann not in dataset.scene_graphs[scene]:
                missing_cache_entries.append([scene, ann])
                if len(missing_cache_entries) == 8:
                    break
        require(not missing_cache_entries, "INCOMPLETE_GRAPH_CACHE_NO_WORKERS:" +
                json.dumps(missing_cache_entries))
        LOG.write("dataset.ready", groups=len(dataset), rng=rng_digest())
        install_observers(sys.modules[type(dataset).__module__], dataset)
        LOADER = dataset_module.build_dataloader(dataset, dist=False, **cfg.dataloader.train)
        require(LOADER.batch_size == 2 and LOADER.num_workers == 4 and LOADER.persistent_workers and
                LOADER.drop_last and LOADER.pin_memory and LOADER.worker_init_fn is None and
                LOADER.prefetch_factor == 2 and LOADER.timeout == 0,
                "EFFECTIVE_ORIGINAL_LOADER_DEFAULTS")
        require(TORCH.multiprocessing.get_start_method() == "fork", "ACTUAL_DEFAULT_START_METHOD_NOT_FORK")
        prefix = FiniteBatchPrefix(LOADER.batch_sampler, dataset)
        object.__setattr__(LOADER, "batch_sampler", prefix)
        LOADER.worker_init_fn = worker_init
        install_process_capture(_worker_loop)
        LOG.write("loader.plan", batch_size=2, num_workers=4, persistent_workers=True,
                  prefetch_factor=2, scheduled_batch_cap=10, consumed_batch_goal=10,
                  sampler_scope="Finite prefix of original RandomSampler/BatchSampler order; no historical RNG replay.")
        STARTING_LOADER = True
        try:
            ITERATOR = iter(LOADER)
        finally:
            STARTING_LOADER = False
        require(getattr(ITERATOR, "_pin_memory", None) is False and
                getattr(ITERATOR, "_pin_memory_thread", None) is None, "CPU_PIN_MEMORY_THREAD_MUST_BE_ABSENT")
        for batch_id in range(CONSUMED_BATCHES):
            checkpoint()
            batch = next(ITERATOR)  # Native loader timeout is unchanged; outer
            # supervisor must preserve uncertainty on a hang, never auto-kill.
            cpu_assert()
            outcome["consumed_batches"] += 1
            LOG.write("parent.batch_consumed", batch_id=batch_id,
                      scan_ids=batch["scan_ids"], ann_ids=batch["ann_ids"],
                      voxel=meta(batch["voxel_coords"]), v2p=meta(batch["v2p_map"]))
            del batch
        require(len(prefix.scheduled) == 10, "SCHEDULED_BATCH_ACCOUNTING")
        try:
            next(ITERATOR)
            raise Blocked("FINITE_PREFIX_PRODUCED_ELEVENTH_BATCH")
        except StopIteration:
            pass
        outcome.update(status="OBSERVED_FINITE_REAL_DATA_TRACE", scheduled_batches=10,
                       scheduled_samples=20, prefetch_additional_batches=0,
                       worker_execution_scope="All scheduled work bounded by finite10batch prefix.")
        code = 0
    except BaseException as exc:
        outcome.update(status="BLOCKED_OR_DIAGNOSTIC_FAILURE", error_type=type(exc).__name__,
                       error=str(exc)[:700])
    finally:
        # No Python exit/destructors while an owned worker may still be live.
        try:
            if CAPTURED:
                outcome["worker_fates"] = cooperative_cleanup(packet.get("cooperative_shutdown_seconds", 1))
                if any(row["certainty"] == "uncertain" for row in outcome["worker_fates"]):
                    outcome["status"] = "OWNED_WORKER_UNCERTAIN_NO_SIGNAL_NO_RETRY"
                    code = 3
                elif any(row["certainty"] == "terminal" and row["exitcode"] != 0
                         for row in outcome["worker_fates"]):
                    outcome["status"] = "OWNED_WORKER_TERMINAL_FAILURE"
                    code = 5
            if TORCH is not None:
                check_guarded_files()
            outcome["carrier_identity"] = identity()
            outcome["signals_sent"] = bool(SIGNALS_SENT)
            outcome["signal_observations"] = SIGNALS_SENT
            outcome["ipv6_loopback_capability_binds"] = IPV6_BIND_COUNT
            outcome["ipv6_policy_source_identity"] = IPV6_SOURCE_IDENTITY
            outcome["cuda_initialized"] = TORCH.cuda.is_initialized() if TORCH is not None else False
            if TORCH is not None:
                outcome["sharing_strategy_observed"] = TORCH.multiprocessing.get_sharing_strategy()
                outcome["carrier_max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                shared = os.statvfs("/dev/shm")
                outcome["sharing_capacity_after"] = {
                    "available_bytes": shared.f_bavail * shared.f_frsize,
                    "total_bytes": shared.f_blocks * shared.f_frsize}
            outcome["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            raw = (json.dumps(outcome, ensure_ascii=True) + "\n").encode()
            require(len(raw) <= 65536, "STATUS_BYTE_CAP")
            if SAFE_STATUS_FD is not None:
                os.write(SAFE_STATUS_FD, raw)
        except BaseException as cleanup_error:
            emergency = {"status": "CLEANUP_UNCERTAIN_NO_SIGNALS", "error_type": type(cleanup_error).__name__,
                         "error": str(cleanup_error)[:300],
                         "workers": [record.get("identity") for record in CAPTURED]}
            try:
                if SAFE_STATUS_FD is not None:
                    os.write(SAFE_STATUS_FD, (json.dumps(emergency) + "\n").encode())
            except BaseException:
                pass
            code = 4
        os._exit(code)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-reviewed", action="store_true")
    parser.add_argument("--packet-fd", type=int)
    parser.add_argument("--fds-json")
    args = parser.parse_args()
    if not args.execute_reviewed:
        print(json.dumps({"status": "DEFAULT_NOP_PREPARATION_ONLY", "Torch_imported": False,
                          "dataset_read": False, "workers_started": False}))
        return
    require(args.packet_fd is not None and args.fds_json, "SUPERVISOR_PACKET_AND_ANONYMOUS_FDS_REQUIRED")
    # Bounded metadata input, no executable code or deserialization of samples.
    raw = os.read(args.packet_fd, 1024 * 1024 + 1)
    require(len(raw) <= 1024 * 1024, "PACKET_BYTE_CAP")
    execute(json.loads(raw), json.loads(args.fds_json))


if __name__ == "__main__":
    main()
