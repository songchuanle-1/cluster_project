"""Stage fixed diagnostic bytes without syncing or modifying the training tree."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from native_registry_geometry_runner_20260920 import runner_manifest
from native_geometry_runtime_20260919 import MODEL_CLASS
from remote_registry_inventory_20260920 import REGISTRY, training_steps


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "pipeline/reports/diagnostic_staging_20260920-0315.json"


def unpack(request):
    rows = request["files"]
    expected_names = {"scripts/" + r["path"] for r in request["producer"]["sources"]}
    expected_names.add(REGISTRY)
    if len(rows) != len(expected_names) or {r["path"] for r in rows} != expected_names:
        raise ValueError("Unexpected diagnostic file set")
    decoded = {}
    for row in rows:
        name = row["path"]
        if "\\" in name or name.startswith("/") or ".." in name.split("/"):
            raise ValueError("Unsafe diagnostic path")
        payload = base64.b64decode(row["base64"], validate=True)
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError("Diagnostic payload hash mismatch")
        decoded[name] = payload
    for row in request["producer"]["sources"]:
        if hashlib.sha256(decoded["scripts/" + row["path"]]).hexdigest() != row["sha256"]:
            raise ValueError("Producer identity differs")
    if hashlib.sha256(decoded[REGISTRY]).hexdigest() != request["expected"]["registry_sha256"]:
        raise ValueError("Registry identity differs")
    return decoded


def publish(root, request):
    """Create a new immutable bundle, never merge into an existing directory."""
    decoded = unpack(request)
    root = Path(root)
    if root.exists() or root.is_symlink():
        raise FileExistsError(root)
    root.mkdir()
    for name, payload in decoded.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(payload)
        path.chmod(0o444)
    manifest = {k: v for k, v in request.items() if k != "files"}
    manifest["files"] = [{k: v for k, v in r.items() if k != "base64"}
                         for r in request["files"]]
    with (root / "manifest.json").open("x", encoding="ascii") as stream:
        json.dump(manifest, stream, indent=2)
    (root / "manifest.json").chmod(0o444)
    for name, payload in decoded.items():
        if (root / name).read_bytes() != payload:
            raise ValueError("Published diagnostic bytes differ")
    return manifest


REMOTE = r'''
import base64, datetime, hashlib, inspect, json, logging, os, pathlib, subprocess, sys, traceback
request = json.loads(REQUEST)
project = pathlib.Path("/data3/songcl/Project/Cluster_project")
root = project / "Cluster"
REGISTRY = request["registry_path"]
HELPERS
result = dict(observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              native_dataset_instantiated=False, native_execution_completed=False,
              physical_bindings_verified=0, scientific_validation_complete=False,
              gpu_allocated=False, training_launch=False)
parent = project / "pipeline/diagnostic_bundles"
if parent.is_symlink() or parent.resolve() != parent:
    raise ValueError("Diagnostic parent symlink")
parent.mkdir(exist_ok=True)
bundle = parent / request["bundle_id"]
manifest = publish(bundle, request)
result.update(bundle=str(bundle), staged_files=manifest["files"],
              producer_sha256=request["producer"]["producer_sha256"])
# Filesystem capability test touches only a fresh sibling scratch directory.
scratch = parent / (request["bundle_id"] + "_scratch")
scratch.mkdir(exist_ok=False)
payload = b"registry diagnostic filesystem capability test\n"
with (scratch / "source").open("xb") as stream:
    stream.write(payload)
    stream.flush()
    os.fsync(stream.fileno())
os.link(scratch / "source", scratch / "published")
try:
    os.link(scratch / "source", scratch / "published")
except FileExistsError:
    collision_rejected = True
else:
    collision_rejected = False
fd = os.open(scratch, os.O_RDONLY | os.O_DIRECTORY)
try:
    os.fsync(fd)
finally:
    os.close(fd)
result["filesystem"] = dict(hardlink_bytes_match=(scratch/"published").read_bytes()==payload,
                            collision_rejected=collision_rejected, directory_fsync=True)
result["gpu"] = subprocess.check_output(["nvidia-smi", "-i", "7",
    "--query-gpu=uuid,memory.total,memory.used,memory.free,utilization.gpu",
    "--format=csv,noheader,nounits"], text=True).strip()
result["gpu_processes"] = subprocess.check_output(["nvidia-smi", "-i", "7",
    "--query-compute-apps=gpu_uuid,pid,used_memory", "--format=csv,noheader,nounits"],
    text=True).strip()
proc = pathlib.Path("/proc/1134192")
if proc.exists():
    command = (proc/"cmdline").read_bytes().replace(b"\0", b" ").decode()
    log = os.readlink(proc/"fd/1")
    result["training"] = dict(pid=1134192, command=command, log=log)
    if request["model"] + "_pirs" in command and request["model"] + "_pirs" in log:
        with open(log, "rb") as stream:
            stream.seek(max(0, os.fstat(stream.fileno()).st_size-18000))
            result["training"]["tail"] = stream.read(18000).decode(errors="replace")
os.environ.update(CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="1")
sys.path[:0] = [str(bundle/"scripts"), str(root), str(root/"framework/lib")]
from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from native_registry_geometry_runner_20260920 import runner_manifest
from referent_registry_binding_20260919 import plan_bindings
config = root/"configs/Quard/ctf_hcg_csort"/(request["model"]+".yaml")
dataset_source = root/"framework/dataset/scannetv2.py"
checkpoint = project/"pipeline/scm_admission_20260914/best.pth"
def binding():
    return dict(producer_sha256=runner_manifest()["producer_sha256"],
        model_source_sha256=model_package_sha256(root, request["model"]),
        config_sha256=file_sha256(config), checkpoint_sha256=file_sha256(checkpoint),
        dataset_source_sha256=file_sha256(dataset_source),
        registry_sha256=file_sha256(bundle/REGISTRY))
result["observed_binding"] = binding()
result["binding_matches"] = result["observed_binding"] == request["expected"]
if not result["binding_matches"]:
    raise ValueError("Observed native binding differs")
data = pathlib.Path("/data3/songcl/data/data_cluster")
annotation = data/"scanrefer/ScanRefer_train_new.json"
result["annotation_sha256"] = file_sha256(annotation)
if result["annotation_sha256"] != request["annotation_sha256"]:
    raise ValueError("Annotation changed")
cache = data/"scanrefer/scene_graphs_new_train.json"
if not cache.is_file():
    raise ValueError("Native constructor would generate absent scene graph cache")
result["scene_graph_cache"] = dict(path=str(cache), sha256=file_sha256(cache))
denied = []
def readonly(event, args):
    reject = event in {"os.remove","os.rename","os.mkdir","os.rmdir","os.link",
                       "os.symlink","os.chmod","os.truncate","subprocess.Popen","os.system"}
    if event == "open":
        path, mode, flags = args
        reject = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
    if reject:
        denied.append(dict(event=event, args=repr(args)[:400]))
        raise PermissionError("Read-only native metadata probe rejected " + event)
sys.addaudithook(readonly)
try:
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(data) + "/"
    result["effective_train_config"] = dict(cfg.data.train)
    native = build_dataset(cfg.data.train, logging.getLogger("metadata_probe"))
    if pathlib.Path(inspect.getfile(type(native))).resolve() != dataset_source:
        raise ValueError("Imported dataset source differs")
    result["native_dataset_instantiated"] = True
    registry = json.loads((bundle/REGISTRY).read_text())
    plan = plan_bindings(registry, request["expected"]["registry_sha256"], native.scene_inputs)
    result["native_metadata_plan"] = plan
    result["metadata_matches_source_plan"] = (
        plan["dataset_metadata_sha256"] == request["dataset_metadata_sha256"]
        and plan["counts"] == {"planned":31})
    result["gpu_initialized"] = torch.cuda.is_initialized()
    if result["gpu_initialized"] or not result["metadata_matches_source_plan"]:
        raise ValueError("Native metadata or CPU-only boundary differs")
except Exception as exc:
    result["metadata_error"] = dict(type=type(exc).__name__, message=str(exc),
                                    traceback=traceback.format_exc()[-6000:])
result["denied_write_events"] = denied
result["final_binding"] = binding()
result["sources_stable"] = result["final_binding"] == result["observed_binding"]
result["annotation_stable"] = file_sha256(annotation) == result["annotation_sha256"]
result["scene_graph_cache_stable"] = file_sha256(cache) == result["scene_graph_cache"]["sha256"]
print(json.dumps(result))
'''


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    prior = json.loads((ROOT / "pipeline/reports/remote_registry_inventory_20260920-0215.json")
                       .read_text(encoding="utf-8"))
    producer = runner_manifest()
    if producer != prior["local_runner_manifest"]:
        raise ValueError("Fixed 14-source closure changed")
    paths = ["scripts/" + r["path"] for r in producer["sources"]] + [REGISTRY]
    config = ROOT / "Cluster/configs/Quard/ctf_hcg_csort" / (MODEL_CLASS + ".yaml")
    expected = dict(producer_sha256=producer["producer_sha256"],
                    model_source_sha256=model_package_sha256(ROOT / "Cluster", MODEL_CLASS),
                    config_sha256=file_sha256(config),
                    dataset_source_sha256=file_sha256(ROOT / "Cluster/framework/dataset/scannetv2.py"),
                    checkpoint_sha256="fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e",
                    registry_sha256=file_sha256(ROOT / REGISTRY))
    request = dict(
        contract="immutable_registry_diagnostic_bundle_v1",
        bundle_id="registry_geometry_20260920_0315_" + producer["producer_sha256"][:12],
        model=MODEL_CLASS, registry_path=REGISTRY, producer=producer, expected=expected,
        annotation_sha256=prior["remote"]["annotation"]["sha256"],
        dataset_metadata_sha256=prior["metadata_plan"]["dataset_metadata_sha256"],
        files=[dict(path=p, sha256=file_sha256(ROOT / p),
                    base64=base64.b64encode((ROOT / p).read_bytes()).decode("ascii"))
               for p in paths])
    parent = ROOT / "pipeline/diagnostic_bundles"
    parent.mkdir(exist_ok=True)
    local_bundle = parent / request["bundle_id"]
    publish(local_bundle, request)
    import inspect
    helpers = inspect.getsource(unpack) + "\n" + inspect.getsource(publish)
    code = REMOTE.replace("HELPERS", "Path = pathlib.Path\n" + helpers)
    code = code.replace("REQUEST", repr(json.dumps(request)), 1)
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "songcl@100.64.3.28",
         "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
        input=code, text=True, capture_output=True, timeout=240)
    if result.returncode:
        remote = dict(error=result.stderr[-7000:], stdout=result.stdout[-3000:],
                      returncode=result.returncode)
    else:
        # Imported native modules may print informational lines before the JSON.
        remote = json.loads(result.stdout.splitlines()[-1])
        if remote.get("training", {}).get("tail"):
            remote["training"]["steps"] = training_steps(remote["training"]["tail"])
    report = dict(contract=request["contract"], local_bundle=str(local_bundle),
                  local_manifest_sha256=file_sha256(local_bundle / "manifest.json"),
                  expected_binding=expected, remote=remote, stderr=result.stderr[-5000:],
                  queue_sha256=file_sha256(ROOT / "pipeline/queue.json"),
                  native_capture_completed=False, captured_pairs=0,
                  missing_binding_pairs=31, admission=False)
    with OUTPUT.open("x", encoding="ascii") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: v for k, v in remote.items()
                      if k not in {"training", "native_metadata_plan", "staged_files"}}))
    print("REPORT", OUTPUT)


if __name__ == "__main__":
    main()
