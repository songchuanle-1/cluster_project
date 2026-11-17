"""Relocated saved-item loading; caller owns native execution and coordination."""
from collections import Counter
import copy
import math
from pathlib import PurePosixPath
import re

from frozen_capture_contract_20260916 import fingerprint
from saved_replay_migration_20260920 import (
    DESTINATION_DATA, SOURCE_DATA, build_contract, checked_hash, mapped_path,
    verify_destination_artifacts,
)


class SavedPhysicalLocation:
    """Keep original reports immutable and resolve only verified storage paths."""

    def __init__(self, contract, physical, prior, inspect, source_check):
        expected = build_contract(physical, prior)
        if any(contract.get(key) != value for key, value in expected.items()):
            raise ValueError("Migration contract differs from original evidence")
        self.contract = copy.deepcopy(expected)
        self.physical = copy.deepcopy(physical)
        self.inspect = inspect
        self.source_check = source_check
        self.locations = {
            PurePosixPath(row["source"]).name: row["destination"]
            for row in expected["artifact_transfers"]
        }

    def verify(self):
        if self.source_check() != self.contract["original_binding"]:
            raise ValueError("Current native source binding differs")
        verify_destination_artifacts(self.contract, self.inspect)
        seen = set()
        for row in self.contract["data_verification"]:
            path = mapped_path(row["source"], SOURCE_DATA, DESTINATION_DATA)
            if row["destination"] != path or path in seen:
                raise ValueError("Data location differs")
            seen.add(path)
            actual = self.inspect(path)
            if (actual.get("regular_file") is not True
                    or actual.get("symlink") is not False
                    or actual.get("parent_chain_verified") is not True
                    or actual.get("sha256") != checked_hash(row["sha256"])):
                raise ValueError("Destination data bytes/path not verified")
        return dict(artifact_count=3, data_count=len(seen),
                    native_execution_authorized=False)

    def validate_denominator(self, joins, registry_pair_ids):
        rows = joins["dispositions"]
        expected_ids = list(registry_pair_ids)
        row_ids = [row["pair_id"] for row in rows]
        bound_ids = [row["pair_id"] for row in rows if row["status"] == "bound"]
        bindings = [row["pair_id"] for row in joins["bindings"]]
        if (len(expected_ids) != 31 or len(set(expected_ids)) != 31
                or type(joins["requested"]) is not int or joins["requested"] != 31
                or len(row_ids) != 31 or len(set(row_ids)) != 31
                or set(row_ids) != set(expected_ids)
                or dict(Counter(row["status"] for row in rows))
                != self.contract["bundle_binding_counts"]
                or joins["counts"] != self.contract["bundle_binding_counts"]
                or len(bindings) != 4 or len(set(bindings)) != 4
                or set(bindings) != set(bound_ids)
                or set(bound_ids) != set(self.contract["physical_pair_ids"])):
            raise ValueError("Full31 registry denominator or physical identities differ")
        observed = self.contract["original_binding"]
        source = {k: v for k, v in observed.items()
                  if k not in ("dataset_source_sha256", "registry_sha256")}
        if (joins["source_binding"] != source
                or joins["dataset_source_sha256"] != observed["dataset_source_sha256"]
                or joins["registry_sha256"] != observed["registry_sha256"]):
            raise ValueError("Full registry source differs")
        payload = {k: v for k, v in joins.items() if k != "payload_sha256"}
        if fingerprint(payload) != joins["payload_sha256"]:
            raise ValueError("Full registry fingerprint differs")

    def load_items(self, exporter, registry_pair_ids, read_json, load):
        """Verify relocated bytes before loading; no collation/model or resampling."""
        self.verify()
        joins = read_json(self.locations["physical_bindings.json"])
        self.validate_denominator(joins, registry_pair_ids)
        observed = self.contract["original_binding"]
        source = {k: v for k, v in observed.items()
                  if k not in ("dataset_source_sha256", "registry_sha256")}
        if (exporter.source_binding != source
                or exporter.dataset_source_sha256 != observed["dataset_source_sha256"]
                or exporter.plan["registry_sha256"] != observed["registry_sha256"]):
            raise ValueError("Exporter source differs")
        prepared = []
        for row in self.physical["items"]:
            index = row["dataset_index"]
            payload = load(self.locations["item_%d.pth" % index])
            if (type(payload["dataset_index"]) is not int
                    or payload["dataset_index"] != index
                    or payload["source_binding"] != source
                    or fingerprint(payload["item"]) != row["native_input_sha256"]
                    or len(payload["axes"]) != row["expressions"]):
                raise ValueError("Saved item identity/input differs")
            before = fingerprint(payload)
            exporter.export_item(index, payload["item"], payload["axes"])
            if fingerprint(payload) != before:
                raise ValueError("Exporter mutated saved item")
            prepared.append((payload, before))
        if exporter.manifest() != joins:
            raise ValueError("Reconstructed full physical bindings differ")
        self.verify()
        return prepared, joins


def check_server4_capacity(server, gpu, observation, now, required_memory_mib,
                           coordinated_slot):
    """Check an observation, not a reservation or authorization to launch."""
    if (server != "server-4" or type(gpu) is not int or gpu not in (0, 1)
            or observation.get("server") != server
            or type(observation.get("gpu")) is not int
            or observation["gpu"] != gpu or coordinated_slot is not True):
        raise ValueError("Coordinated server-4 GPU0/1 slot required")
    values = [now, required_memory_mib] + [
        observation.get(k) for k in
        ("observed_at", "memory_total_mib", "memory_used_mib", "utilization_percent")]
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError("Finite capacity measurements required")
    measured, total, used, util = values[2:]
    if (not 0 <= now - measured <= 60 or total <= 0 or not 0 <= used <= total
            or not 0 <= util <= 100 or required_memory_mib <= 0
            or type(observation.get("process_count")) is not int
            or observation["process_count"] != 0
            or used >= 1024 or util >= 10 or total - used < required_memory_mib):
        raise ValueError("Fresh idle GPU with measured sufficient memory required")
    return dict(server=server, gpu=gpu, coordinated_slot=True,
                process_cap_reached=False, measured_memory_sufficient=True,
                observation=copy.deepcopy(observation), native_execution_authorized=False)


def validate_gpu_runtime(runtime, expected_executable, device, *, gpu, capacity,
                         now, required_memory_mib, coordinated_slot):
    """Validate trusted observations only; no probe, reservation or native gate.

    The isolated child must expose one full UUID, not an ambiguous ordinal.
    Host NVML/nvidia-smi and child CUDA observations must independently agree.
    Callers remain responsible for producing those observations and holding the
    slot, verifying sources/assets/ABI, and synchronization/model teardown.
    """
    from cpu_diagnostic_bootstrap_20260920 import validate_host_runtime

    validate_host_runtime(runtime, expected_executable)
    checked = check_server4_capacity(
        "server-4", gpu, capacity, now, required_memory_mib, coordinated_slot)
    uuid = device.get("physical_uuid")
    if (not isinstance(uuid, str) or not re.fullmatch(
            r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", uuid)):
        raise ValueError("Full physical GPU UUID required")
    if (device.get("server") != "server-4"
            or type(device.get("physical_index")) is not int
            or device["physical_index"] != gpu
            or capacity.get("gpu_uuid") != uuid
            or runtime.get("cuda_visible_devices") != uuid
            or device.get("logical_uuid") != uuid
            or type(device.get("logical_device_count")) is not int
            or device["logical_device_count"] != 1
            or type(device.get("current_logical_device")) is not int
            or device["current_logical_device"] != 0
            or device.get("cuda_available") is not True):
        raise ValueError("Physical allocation and sole logical0 UUID must agree")
    measured = device.get("observed_at")
    if (type(measured) not in (int, float) or not math.isfinite(measured)
            or not 0 <= now - measured <= 60):
        raise ValueError("Fresh GPU identity observation required")
    return dict(
        server="server-4", physical_gpu=gpu, gpu_uuid=uuid, logical_device=0,
        runtime_observation_validated=True, device_mapping_validated=True,
        capacity=checked, native_execution_authorized=False,
        native_dependencies_verified=False, source_assets_verified=False,
        native_backward_verified=False, admission=False)


def parse_gpu_inventory(xml, *, gpu, expected_uuid, observed_at):
    """Parse one selected nvidia-smi XML inventory, never infer logical CUDA."""
    import xml.etree.ElementTree as ET

    if (type(gpu) is not int or gpu not in (0, 1)
            or not isinstance(expected_uuid, str) or not re.fullmatch(
                r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
                expected_uuid)
            or type(observed_at) not in (int, float)
            or not math.isfinite(observed_at) or observed_at < 0):
        raise ValueError("Explicit physical GPU0/1, full UUID and finite time required")
    if (not isinstance(xml, str) or len(xml.encode("utf-8")) > 1024 * 1024
            or "<!ENTITY" in xml.upper() or "[" in xml):
        raise ValueError("Bounded XML without internal DTD/entities required")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as error:
        raise ValueError("Malformed GPU XML") from error
    devices = root.findall("gpu")
    if root.tag != "nvidia_smi_log" or len(devices) != 1:
        raise ValueError("Exactly one selected physical GPU required")
    selected = devices[0]

    def one(parent, path):
        nodes = parent.findall(path)
        if len(nodes) != 1:
            raise ValueError("Missing or duplicate inventory field: " + path)
        return nodes[0]

    def text(parent, path):
        node = one(parent, path)
        if len(node) or not node.text or not node.text.strip():
            raise ValueError("Unobserved inventory field: " + path)
        return node.text.strip()

    def quantity(parent, path, unit):
        value = text(parent, path)
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?) " + re.escape(unit), value)
        if not match:
            raise ValueError("Unsupported inventory measurement: " + path)
        number = float(match[1])
        if not math.isfinite(number):
            raise ValueError("Nonfinite inventory measurement")
        return number

    if text(selected, "uuid") != expected_uuid:
        raise ValueError("Selected physical index and expected UUID differ")
    memory = one(selected, "fb_memory_usage")
    total = quantity(memory, "total", "MiB")
    used = quantity(memory, "used", "MiB")
    util = quantity(one(selected, "utilization"), "gpu_util", "%")
    if total <= 0 or not 0 <= used <= total or not 0 <= util <= 100:
        raise ValueError("Out-of-range inventory measurements")
    processes = one(selected, "processes")
    if (processes.text or "").strip():
        raise ValueError("Unsupported process inventory")
    pids = []
    for row in processes:
        if row.tag != "process_info" or (row.tail or "").strip():
            raise ValueError("Unknown process inventory entry")
        value = text(row, "pid")
        if not re.fullmatch(r"[1-9][0-9]*", value):
            raise ValueError("Invalid process ID")
        pids.append(int(value))
    if len(set(pids)) != len(pids):
        raise ValueError("Duplicate process inventory")
    return dict(
        server="server-4", gpu=gpu, gpu_uuid=expected_uuid,
        observed_at=observed_at, memory_total_mib=total, memory_used_mib=used,
        utilization_percent=util, process_count=len(pids), process_ids=pids,
        native_execution_authorized=False)


def collect_gpu_inventory(expected_executable, gpu, expected_uuid, *,
                          nvidia_smi, nvidia_smi_sha256):
    """Read-only host collector for an already verified fresh GPU child.

    No model/CUDA imports, reservation or CLI. The caller must independently
    attest the executable, hold the slot and later observe the child's logical
    CUDA identity. XML schema/unsupported measurements fail closed.
    """
    import time
    import hashlib
    from pathlib import Path
    from bounded_collation_process_20260921 import bounded_process
    from cpu_diagnostic_bootstrap_20260920 import (
        CODE_ROOT, observe_runtime, validate_host_runtime,
    )
    from frozen_capture_contract_20260916 import file_sha256

    runtime = observe_runtime()
    validate_host_runtime(runtime, expected_executable)
    if (type(gpu) is not int or gpu not in (0, 1)
            or not isinstance(expected_uuid, str) or not re.fullmatch(
                r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
                expected_uuid)
            or runtime.get("cuda_visible_devices") != expected_uuid):
        raise ValueError("GPU child must expose exactly the expected physical UUID")
    if (not isinstance(nvidia_smi, str) or not nvidia_smi.startswith("/")
            or str(PurePosixPath(nvidia_smi)) != nvidia_smi
            or "\\" in nvidia_smi or ".." in PurePosixPath(nvidia_smi).parts):
        raise ValueError("Explicit canonical nvidia-smi executable required")
    expected_hash = checked_hash(nvidia_smi_sha256)
    executable = Path(nvidia_smi)

    def verify():
        if (not executable.is_file() or executable.is_symlink()
                or any(p.is_symlink() for p in executable.parents)
                or file_sha256(executable) != expected_hash):
            raise ValueError("nvidia-smi bytes/path differ from independent attestation")

    verify()
    started = time.time()
    completed = bounded_process(
        [nvidia_smi, "-q", "-x", "-i", str(gpu)], CODE_ROOT,
        timeout=10, max_output_bytes=1024 * 1024)
    if completed.returncode != 0 or completed.stderr.strip():
        raise ValueError("GPU inventory command failed or emitted diagnostics")
    verify()
    after = observe_runtime()
    if after != runtime:
        raise ValueError("Host runtime changed during inventory")
    finished = time.time()
    if not 0 <= finished - started <= 15:
        raise ValueError("GPU inventory time window invalid")
    capacity = parse_gpu_inventory(
        completed.stdout, gpu=gpu, expected_uuid=expected_uuid,
        observed_at=started)
    return dict(
        runtime=runtime, capacity=capacity, nvidia_smi_sha256=expected_hash,
        inventory_xml_sha256=hashlib.sha256(
            completed.stdout.encode("utf-8")).hexdigest(),
        collection_finished_at=finished, logical_device_observed=False,
        native_execution_authorized=False, admission=False)


def collect_logical_gpu_identity(expected_executable, *, gpu, capacity,
                                 required_memory_mib, coordinated_slot,
                                 dependency_loader):
    """Observe child CUDA only after a trusted pinned-dependency/ABI loader.

    dependency_loader must verify and return the actual torch module without
    allocating a model or initializing CUDA. It is a caller-owned trust boundary,
    not a production verifier supplied here. The caller holds the GPU slot and
    bounds the entire child lifetime; CUDA initialization can block and allocate
    a context. The capacity observation must precede that initialization.
    """
    import time
    from cpu_diagnostic_bootstrap_20260920 import observe_runtime, validate_host_runtime

    runtime = copy.deepcopy(observe_runtime())
    validate_host_runtime(runtime, expected_executable)
    capacity = copy.deepcopy(capacity)
    started = time.time()
    check_server4_capacity(
        "server-4", gpu, capacity, started, required_memory_mib, coordinated_slot)
    physical_uuid = capacity.get("gpu_uuid")
    if (not isinstance(physical_uuid, str) or not re.fullmatch(
            r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
            physical_uuid)
            or runtime.get("cuda_visible_devices") != physical_uuid
            or not callable(dependency_loader)):
        raise ValueError("Independent full physical UUID and trusted loader required")

    torch = dependency_loader()
    if observe_runtime() != runtime:
        raise ValueError("Runtime changed during dependency verification")
    if (not isinstance(torch.version.cuda, str) or not torch.version.cuda
            or torch.version.hip is not None):
        raise ValueError("Verified NVIDIA CUDA build required")
    cuda = torch.cuda
    if cuda.is_initialized() is not False:
        raise ValueError("Fresh child required before CUDA identity observation")
    available = cuda.is_available()
    if available is not True:
        raise ValueError("CUDA unavailable")
    count = cuda.device_count()
    if type(count) is not int or count != 1:
        raise ValueError("Exactly one logical CUDA device required")
    current = cuda.current_device()
    if type(current) is not int or current != 0:
        raise ValueError("Current logical CUDA device must be zero")
    raw_uuid = str(cuda.get_device_properties(0).uuid)
    # PyTorch v2.7.1 CUuuid.__str__ returns the bare 8-4-4-4-12 UUID.
    if not re.fullmatch(
            r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", raw_uuid):
        raise ValueError("Unsupported or missing CUDA UUID representation")
    logical_uuid = "GPU-" + raw_uuid
    finished = time.time()
    if (type(finished) not in (int, float) or not math.isfinite(finished)
            or not 0 <= finished - started <= 60):
        raise ValueError("Logical identity observation time window invalid")
    if observe_runtime() != runtime:
        raise ValueError("Runtime changed during CUDA observation")
    device = dict(
        server="server-4", physical_index=gpu, physical_uuid=physical_uuid,
        logical_uuid=logical_uuid, logical_device_count=count,
        current_logical_device=current, cuda_available=available,
        observed_at=started)
    validation = validate_gpu_runtime(
        runtime, expected_executable, device, gpu=gpu, capacity=capacity,
        now=finished, required_memory_mib=required_memory_mib,
        coordinated_slot=coordinated_slot)
    return dict(
        runtime=runtime, device=device, validation=validation,
        collection_finished_at=finished, logical_device_observed=True,
        capacity_observed_before_cuda=True, native_execution_authorized=False,
        native_dependencies_verified=False, native_backward_verified=False,
        admission=False)
