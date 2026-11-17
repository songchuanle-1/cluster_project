"""Host-side execution guard and child-side checks; not authorization.

The guard requires an externally acquired slot lease, fresh host/capacity
observations and hashed dependency, asset and isolation evidence. It freezes
those observations into one write-once driver context. The child rechecks the
pinned receipt before and during PreIdentityHandoff collection.

This proves that concrete external checks were supplied to the boundary. It is
not a sandbox, reservation, dependency/ABI proof, native execution permit or
scientific admission.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re

from cpu_diagnostic_bootstrap_20260920 import (
    observe_runtime, validate_host_runtime,
)
from pinned_diagnostic_imports_20260920 import checked_digest, digest, regular_bytes
from saved_physical_location_20260920 import check_server4_capacity


SERVER = "server-4"
RECEIPT_CONTRACT = "server4-execution-receipt-v1"
DRIVER_CONTEXT_CONTRACT = "server4-production-driver-context-v1"
MAX_RECEIPT_AGE_SECONDS = 300
FALSE_CLAIM_KEYS = frozenset({
    "admission", "training_launch", "native_execution_authorized",
    "native_execution_verified", "scientific_validation_complete",
    "native_backward_verified", "resources_verified",
})
REQUEST_KEYS = frozenset({
    "executable", "executable_sha256", "bundle", "manifest_sha256",
    "handoff_path", "handoff_sha256", "driver_module", "driver_entry",
    "context_path", "context_sha256", "output", "timeout", "max_output_bytes",
})
DRIVER_KEYS = frozenset({
    "contract", "expected_executable", "gpu", "required_memory_mib",
    "capacity", "runtime", "execution_receipt",
})
RECEIPT_KEYS = frozenset({
    "contract", "prepared_at", "server", "gpu", "gpu_uuid",
    "executable_sha256", "runtime", "capacity", "slot", "dependencies",
    "assets", "isolation",
})


def _strict_json(raw):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Nonfinite JSON value: " + value)

    if isinstance(raw, bytes):
        raw = raw.decode("ascii")
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def _finite(value, label):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Finite " + label + " required")
    return value


def _canonical_posix(value, label):
    if (not isinstance(value, str) or not value.startswith("/")
            or str(PurePosixPath(value)) != value or "\\" in value
            or ".." in PurePosixPath(value).parts):
        raise ValueError("Canonical absolute POSIX " + label + " required")
    return value


def _full_uuid(value):
    if (not isinstance(value, str) or not re.fullmatch(
            r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
            value)):
        raise ValueError("Full physical GPU UUID required")
    return value


def _checked_regular(path, sha256):
    path = Path(path)
    if (not path.is_absolute() or path.is_symlink()
            or any(parent.is_symlink() for parent in path.parents)
            or not path.is_file() or path.stat().st_nlink != 1):
        raise ValueError("Canonical regular non-hardlinked evidence file required")
    expected = checked_digest(sha256)
    if digest(regular_bytes(path)) != expected:
        raise ValueError("Evidence file hash differs")
    return expected


def _evidence(label, callback):
    if not callable(callback):
        raise ValueError("External " + label + " verifier required")
    row = callback()
    if (not isinstance(row, dict) or set(row) != {"path", "sha256"}
            or not isinstance(row["path"], str)):
        raise ValueError(label + " verifier must return one hashed evidence row")
    _checked_regular(row["path"], row["sha256"])
    return copy.deepcopy(row)


def _verify_evidence(row, label):
    if (not isinstance(row, dict) or set(row) != {"path", "sha256"}
            or not isinstance(row["path"], str)):
        raise ValueError("Invalid " + label + " evidence")
    _checked_regular(row["path"], row["sha256"])


def _validate_slot_proof(proof):
    if (not isinstance(proof, dict)
            or set(proof) != {"owner_pid", "token", "server", "gpu"}
            or type(proof["owner_pid"]) is not int or proof["owner_pid"] <= 0
            or not isinstance(proof["token"], str) or len(proof["token"]) != 64
            or any(char not in "0123456789abcdef" for char in proof["token"])
            or proof["server"] != SERVER or type(proof["gpu"]) is not int
            or proof["gpu"] not in (0, 1)):
        raise ValueError("Invalid external slot lease proof")
    return copy.deepcopy(proof)


def _reject_positive_claims(document):
    if isinstance(document, dict):
        for key, value in document.items():
            if key in FALSE_CLAIM_KEYS and value is True:
                raise ValueError("Execution guard cannot claim: " + key)
            _reject_positive_claims(value)
    elif isinstance(document, list):
        for value in document:
            _reject_positive_claims(value)


class ProductionExecutionGuard:
    """Context-managed external validator for the pinned handoff launcher."""

    def __init__(
            self, *, expected_executable, expected_executable_sha256, gpu,
            expected_gpu_uuid, required_memory_mib, acquire_slot,
            observe_capacity, verify_dependencies, verify_assets,
            verify_isolation, runtime_observer=observe_runtime,
            host_validator=validate_host_runtime,
            capacity_validator=check_server4_capacity, clock=None):
        self.expected_executable = _canonical_posix(
            expected_executable, "executable")
        self.expected_executable_sha256 = checked_digest(
            expected_executable_sha256)
        if type(gpu) is not int or gpu not in (0, 1):
            raise ValueError("Only server-4 GPU0/1")
        self.gpu = gpu
        self.expected_gpu_uuid = _full_uuid(expected_gpu_uuid)
        self.required_memory_mib = _finite(
            required_memory_mib, "required memory")
        if self.required_memory_mib <= 0:
            raise ValueError("Positive required memory required")
        if (not callable(acquire_slot) or not callable(observe_capacity)
                or not callable(verify_dependencies)
                or not callable(verify_assets) or not callable(verify_isolation)
                or not callable(runtime_observer) or not callable(host_validator)
                or not callable(capacity_validator)):
            raise ValueError("External guard callbacks required")
        import time
        self.acquire_slot = acquire_slot
        self.observe_capacity = observe_capacity
        self.verify_dependencies = verify_dependencies
        self.verify_assets = verify_assets
        self.verify_isolation = verify_isolation
        self.runtime_observer = runtime_observer
        self.host_validator = host_validator
        self.capacity_validator = capacity_validator
        self.clock = clock or time.time
        self.lease = None
        self.receipt = None
        self.context_path = None
        self.context_sha256 = None
        self.context_document = None

    def __enter__(self):
        if self.lease is not None:
            raise ValueError("Execution guard is single-use")
        lease = self.acquire_slot(SERVER, self.gpu)
        try:
            if (not hasattr(lease, "assert_held")
                    or not callable(lease.assert_held)
                    or not hasattr(lease, "release")
                    or not callable(lease.release)
                    or lease.assert_held() is not True):
                raise ValueError("External callable slot lease required")
            runtime = copy.deepcopy(self.runtime_observer())
            self.host_validator(runtime, self.expected_executable)
            if runtime.get("cuda_visible_devices") != self.expected_gpu_uuid:
                raise ValueError("Child runtime must expose the expected physical UUID")
            now = _finite(self.clock(), "preparation time")
            capacity = copy.deepcopy(self.observe_capacity(self.gpu))
            self.capacity_validator(
                SERVER, self.gpu, copy.deepcopy(capacity), now,
                self.required_memory_mib, True)
            if capacity.get("gpu_uuid") != self.expected_gpu_uuid:
                raise ValueError("Capacity observation UUID differs")
            dependencies = _evidence(
                "dependency", self.verify_dependencies)
            assets = _evidence("asset", self.verify_assets)
            isolation = _evidence("isolation", self.verify_isolation)
            slot = _validate_slot_proof(getattr(lease, "proof", None))
            if (slot["owner_pid"] != os.getpid()
                    or slot["server"] != SERVER or slot["gpu"] != self.gpu):
                raise ValueError("Slot lease is not owned by this guard process")
            if lease.assert_held() is not True:
                raise ValueError("Held slot was lost before context creation")
            self.receipt = {
                "contract": RECEIPT_CONTRACT,
                "prepared_at": now,
                "server": SERVER,
                "gpu": self.gpu,
                "gpu_uuid": self.expected_gpu_uuid,
                "executable_sha256": self.expected_executable_sha256,
                "runtime": runtime,
                "capacity": capacity,
                "slot": slot,
                "dependencies": dependencies,
                "assets": assets,
                "isolation": isolation,
            }
            _validate_receipt(self.receipt)
            _reject_positive_claims(self.receipt)
            self.lease = lease
            return self
        except BaseException:
            try:
                lease.release()
            finally:
                self.lease = None
            raise

    def __exit__(self, exc_type, exc, traceback):
        lease, self.lease = self.lease, None
        if lease is not None:
            lease.release()
        return False

    def write_context(self, path):
        """Freeze the validated receipt into a fresh JSON launch context."""
        if self.lease is None or self.receipt is None:
            raise ValueError("Active execution guard required")
        path = Path(path).absolute()
        if (path.is_symlink() or any(parent.is_symlink() for parent in path.parents)
                or not path.parent.is_dir()):
            raise ValueError("Canonical fresh context path required")
        if path.exists():
            raise FileExistsError(path)
        document = {
            "contract": DRIVER_CONTEXT_CONTRACT,
            "expected_executable": self.expected_executable,
            "gpu": self.gpu,
            "required_memory_mib": self.required_memory_mib,
            "capacity": copy.deepcopy(self.receipt["capacity"]),
            "runtime": copy.deepcopy(self.receipt["runtime"]),
            "execution_receipt": copy.deepcopy(self.receipt),
        }
        validate_driver_context(document)
        raw = json.dumps(
            document, sort_keys=True, separators=(",", ":"),
            allow_nan=False).encode("ascii")
        descriptor = os.open(
            path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        self.context_path = path
        self.context_sha256 = hashlib.sha256(raw).hexdigest()
        self.context_document = document
        return path, self.context_sha256

    def _refresh(self, request):
        if self.lease is None or self.receipt is None:
            raise ValueError("Active execution guard required")
        now = _finite(self.clock(), "validation time")
        prepared = self.receipt["prepared_at"]
        if not 0 <= now - prepared <= MAX_RECEIPT_AGE_SECONDS:
            raise ValueError("Execution receipt is stale")
        if self.lease.assert_held() is not True:
            raise ValueError("Held slot was lost before launch")
        runtime = copy.deepcopy(self.runtime_observer())
        self.host_validator(runtime, self.expected_executable)
        if runtime != self.receipt["runtime"]:
            raise ValueError("Host runtime changed after preparation")
        capacity = copy.deepcopy(self.observe_capacity(self.gpu))
        self.capacity_validator(
            SERVER, self.gpu, copy.deepcopy(capacity), now,
            self.required_memory_mib, True)
        if capacity.get("gpu_uuid") != self.expected_gpu_uuid:
            raise ValueError("Capacity observation UUID changed")
        dependencies = _evidence(
            "dependency", self.verify_dependencies)
        assets = _evidence("asset", self.verify_assets)
        isolation = _evidence("isolation", self.verify_isolation)
        if (dependencies != self.receipt["dependencies"]
                or assets != self.receipt["assets"]
                or isolation != self.receipt["isolation"]):
            raise ValueError("External evidence changed after preparation")
        if (self.context_path is None
                or str(Path(request["context_path"]).absolute()) != str(self.context_path)
                or request["context_sha256"] != self.context_sha256):
            raise ValueError("Frozen launch context differs")
        raw = regular_bytes(self.context_path)
        if (hashlib.sha256(raw).hexdigest() != self.context_sha256
                or _strict_json(raw) != self.context_document):
            raise ValueError("Frozen launch context changed")
        if (request["executable"] != self.expected_executable
                or request["executable_sha256"] != self.expected_executable_sha256):
            raise ValueError("Launch executable differs from validated executable")
        if self.lease.assert_held() is not True:
            raise ValueError("Held slot was lost after validation")
        return None

    def __call__(self, request):
        if not isinstance(request, dict) or set(request) != REQUEST_KEYS:
            raise ValueError("Exact launcher request required")
        return self._refresh(copy.deepcopy(request))


def _validate_runtime_shape(runtime):
    if (not isinstance(runtime, dict)
            or runtime.get("platform") != "Linux"
            or not isinstance(runtime.get("addresses"), list)
            or not isinstance(runtime.get("paths"), dict)
            or not isinstance(runtime.get("cuda_visible_devices"), str)):
        raise ValueError("Invalid frozen runtime observation")
    return copy.deepcopy(runtime)


def _validate_capacity_shape(capacity, gpu, gpu_uuid):
    required = {
        "server", "gpu", "gpu_uuid", "observed_at", "memory_total_mib",
        "memory_used_mib", "utilization_percent", "process_count",
    }
    if (not isinstance(capacity, dict) or set(capacity) != required
            or capacity["server"] != SERVER or capacity["gpu"] != gpu
            or (gpu_uuid is not None and capacity["gpu_uuid"] != gpu_uuid)):
        raise ValueError("Invalid frozen capacity observation")
    _finite(capacity["observed_at"], "capacity observation time")
    return copy.deepcopy(capacity)


def _validate_receipt(receipt):
    if (not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS
            or receipt.get("contract") != RECEIPT_CONTRACT
            or receipt.get("server") != SERVER
            or type(receipt.get("gpu")) is not int
            or receipt["gpu"] not in (0, 1)):
        raise ValueError("Invalid execution receipt schema")
    _finite(receipt.get("prepared_at"), "execution receipt time")
    _full_uuid(receipt.get("gpu_uuid"))
    checked_digest(receipt.get("executable_sha256"))
    _validate_runtime_shape(receipt.get("runtime"))
    _validate_capacity_shape(
        receipt.get("capacity"), receipt["gpu"], receipt["gpu_uuid"])
    _validate_slot_proof(receipt.get("slot"))
    for label in ("dependencies", "assets", "isolation"):
        _verify_evidence(receipt.get(label), label)
    _reject_positive_claims(receipt)
    return copy.deepcopy(receipt)


def validate_driver_context(document):
    """Static and evidence checks performed before the pinned child starts."""
    if (not isinstance(document, dict) or set(document) != DRIVER_KEYS
            or document.get("contract") != DRIVER_CONTEXT_CONTRACT):
        raise ValueError("Invalid production driver context")
    executable = _canonical_posix(
        document.get("expected_executable"), "expected executable")
    gpu = document.get("gpu")
    if type(gpu) is not int or gpu not in (0, 1):
        raise ValueError("Only server-4 GPU0/1")
    memory = _finite(document.get("required_memory_mib"), "required memory")
    if memory <= 0:
        raise ValueError("Positive required memory required")
    capacity = _validate_capacity_shape(document.get("capacity"), gpu, None)
    gpu_uuid = capacity["gpu_uuid"]
    runtime = _validate_runtime_shape(document.get("runtime"))
    receipt = _validate_receipt(document.get("execution_receipt"))
    if (receipt["gpu"] != gpu or receipt["gpu_uuid"] != gpu_uuid
            or receipt["runtime"] != runtime or receipt["capacity"] != capacity):
        raise ValueError("Driver context duplicates differ")
    _reject_positive_claims(document)
    return dict(
        contract=DRIVER_CONTEXT_CONTRACT,
        expected_executable=executable, gpu=gpu, required_memory_mib=memory,
        gpu_uuid=gpu_uuid, receipt=receipt)


def _parent_pid():
    return os.getppid()


def make_child_checks(document, *, runtime_observer=None, parent_pid=None,
                      clock=None):
    """Build exact True-returning callbacks after validating frozen evidence."""
    import time
    config = validate_driver_context(copy.deepcopy(document))
    receipt = config["receipt"]
    runtime_observer = runtime_observer or observe_runtime
    parent_pid = parent_pid or _parent_pid
    clock = clock or time.time

    def verify_current(server, gpu):
        if server != SERVER or type(gpu) is not int or gpu != config["gpu"]:
            raise ValueError("Only the pinned server-4 GPU0/1 slot")
        now = _finite(clock(), "child validation time")
        if not 0 <= now - receipt["prepared_at"] <= MAX_RECEIPT_AGE_SECONDS:
            raise ValueError("Execution receipt is stale in child")
        if parent_pid() != receipt["slot"]["owner_pid"]:
            raise ValueError("Child parent differs from slot lease owner")
        runtime = copy.deepcopy(runtime_observer())
        if runtime != receipt["runtime"]:
            raise ValueError("Child host runtime differs from receipt")
        if runtime.get("cuda_visible_devices") != config["gpu_uuid"]:
            raise ValueError("Child CUDA visibility differs from receipt")
        for label in ("dependencies", "assets", "isolation"):
            _verify_evidence(receipt[label], label)

    def slot_check(server, gpu):
        verify_current(server, gpu)
        return True

    def execution_check(server, gpu):
        verify_current(server, gpu)
        return True

    return slot_check, execution_check
