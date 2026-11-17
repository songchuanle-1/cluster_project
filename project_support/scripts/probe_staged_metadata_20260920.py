"""CPU-only constructor check against an already staged diagnostic bundle."""
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "pipeline/reports/staged_native_metadata_20260920-0315.json"
REMOTE = r'''
import datetime, hashlib, inspect, json, logging, os, pathlib, sys, traceback
project = pathlib.Path("/data3/songcl/Project/Cluster_project")
root = project/"Cluster"
bundle = project/"pipeline/diagnostic_bundles/registry_geometry_20260920_0315_88b51c997a74"
manifest = json.loads((bundle/"manifest.json").read_text())
scratch = bundle.parent/(bundle.name+"_metadata_scratch")
scratch.mkdir(exist_ok=False)
os.environ.update(CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
    TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="1", TMPDIR=str(scratch),
    XDG_CACHE_HOME=str(scratch/"cache"), TORCH_HOME=str(scratch/"torch"))
sys.path[:0] = [str(bundle/"scripts"), str(root), str(root/"framework/lib")]
from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from native_registry_geometry_runner_20260920 import runner_manifest
from referent_registry_binding_20260919 import plan_bindings
model = manifest["model"]
config = root/"configs/Quard/ctf_hcg_csort"/(model+".yaml")
source = root/"framework/dataset/scannetv2.py"
checkpoint = project/"pipeline/scm_admission_20260914/best.pth"
registry = bundle/manifest["registry_path"]
data = pathlib.Path("/data3/songcl/data/data_cluster")
annotation = data/"scanrefer/ScanRefer_train_new.json"
cache = data/"scanrefer/scene_graphs_new_train.json"
def binding():
    return dict(producer_sha256=runner_manifest()["producer_sha256"],
        model_source_sha256=model_package_sha256(root, model),
        config_sha256=file_sha256(config), checkpoint_sha256=file_sha256(checkpoint),
        dataset_source_sha256=file_sha256(source), registry_sha256=file_sha256(registry))
before = binding()
if before != manifest["expected"] or not cache.is_file():
    raise ValueError("Native inputs differ or cache absent")
before_data = {str(p):file_sha256(p) for p in (annotation,cache)}
if before_data[str(annotation)] != manifest["annotation_sha256"]:
    raise ValueError("Annotation changed")
for row in manifest["files"]:
    if file_sha256(bundle/row["path"]) != row["sha256"]:
        raise ValueError("Staged file changed")
result = dict(observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    bundle=str(bundle), scratch=str(scratch), observed_binding=before,
    native_dataset_instantiated=False, physical_bindings_verified=0,
    native_capture_completed=False, scientific_validation_complete=False,
    annotation_and_cache_before=before_data)
denied = []
def inside(path, dir_fd=None):
    if isinstance(path, int):
        path = os.readlink("/proc/self/fd/" + str(path))
    path = pathlib.Path(os.fsdecode(path))
    if dir_fd is not None and dir_fd >= 0 and not path.is_absolute():
        path = pathlib.Path(os.readlink("/proc/self/fd/" + str(dir_fd)))/path
    return path.resolve().is_relative_to(scratch)
def audit(event, args):
    reject = False
    if event == "open":
        path, mode, flags = args
        write = (isinstance(mode,str) and any(c in mode for c in "wax+")) or (
            isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
        reject = write and path != "/dev/null" and not inside(path)
    elif event in {"os.remove","os.rmdir","os.mkdir","os.chmod"}:
        index = 2 if event in {"os.mkdir","os.chmod"} else 1
        dir_fd = args[index] if len(args)>index else None
        reject = not inside(args[0],dir_fd)
    elif event in {"os.rename","os.link","os.symlink","os.truncate","subprocess.Popen","os.system"}:
        reject = True
    if reject:
        denied.append(dict(event=event,args=repr(args)[:500]))
        raise PermissionError("Native metadata probe rejected "+event)
sys.addaudithook(audit)
try:
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(data)+"/"
    result["effective_train_config"] = dict(cfg.data.train)
    native = build_dataset(cfg.data.train, logging.getLogger("native_metadata"))
    if pathlib.Path(inspect.getfile(type(native))).resolve() != source:
        raise ValueError("Imported dataset differs")
    result["native_dataset_instantiated"] = True
    plan = plan_bindings(json.loads(registry.read_text()),
                         before["registry_sha256"], native.scene_inputs)
    result["native_metadata_plan"] = plan
    result["metadata_matches_source_plan"] = (
        plan["dataset_metadata_sha256"] == manifest["dataset_metadata_sha256"]
        and plan["counts"] == {"planned":31})
    result["gpu_initialized"] = torch.cuda.is_initialized()
    result["torch_version"] = torch.__version__
    if result["gpu_initialized"] or not result["metadata_matches_source_plan"]:
        raise ValueError("CPU-only or metadata boundary differs")
except Exception as exc:
    result["error"] = dict(type=type(exc).__name__,message=str(exc),
                           traceback=traceback.format_exc()[-6000:])
result["denied_events"] = denied
result["final_binding"] = binding()
result["sources_stable"] = result["final_binding"] == before
result["annotation_and_cache_stable"] = all(
    file_sha256(pathlib.Path(p)) == sha for p,sha in before_data.items())
result["training_launch"] = False
print(json.dumps(result))
'''


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "songcl@100.64.3.28",
         "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
        input=REMOTE, text=True, capture_output=True, timeout=240)
    if result.returncode:
        report = dict(returncode=result.returncode, stdout=result.stdout[-3000:],
                      stderr=result.stderr[-6000:])
    else:
        report = json.loads(result.stdout.splitlines()[-1])
        report["stderr"] = result.stderr[-6000:]
    with OUTPUT.open("x", encoding="ascii") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k:v for k,v in report.items() if k != "native_metadata_plan"}))


if __name__ == "__main__":
    main()
