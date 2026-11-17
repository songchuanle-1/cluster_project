"""Resume two original TRAIN item observations without loading a model or CUDA."""
import json
from pathlib import Path
import subprocess

from frozen_capture_contract_20260916 import file_sha256
from probe_staged_metadata_20260920 import REMOTE as METADATA_REMOTE
from remote_registry_inventory_20260920 import training_steps


ROOT = Path(__file__).resolve().parents[1]
TAG = "20260920-0415-retry"
OUTPUT = ROOT / ("pipeline/reports/physical_items_" + TAG + ".json")
PRIOR = ROOT / "pipeline/reports/staged_native_metadata_20260920-0315.json"

OBSERVE = r'''
capacity = dict(status="Not re-queried: first attempt queried once but failed before saving output",
                gpu_execution_authorized=False)
proc = pathlib.Path("/proc/1134192")
training = dict(pid=1134192, exists=proc.exists())
if proc.exists():
    command = (proc/"cmdline").read_bytes().replace(b"\0",b" ").decode()
    log = os.readlink(proc/"fd/1")
    training.update(command=command, log=log)
    if model+"_pirs" not in command or model+"_pirs" not in log:
        raise ValueError("Training process/log identity changed")
    with open(log,"rb") as stream:
        stream.seek(max(0,os.fstat(stream.fileno()).st_size-18000))
        training["tail"] = stream.read(18000).decode(errors="replace")
result.update(capacity=capacity, training=training, gpu_query_count=0,
              manifest_sha256=file_sha256(bundle/"manifest.json"))
result["local_manifest_sha256"] = request["manifest_sha256"]
result["manifest_parsed_matches"] = manifest == request["manifest"]
result["manifest_lf_matches"] = result["manifest_sha256"] == request["manifest_lf_sha256"]
if not result["manifest_parsed_matches"] or not result["manifest_lf_matches"]:
    raise ValueError("Immutable manifest changed")
if before_data != request["annotation_and_cache_before"]:
    raise ValueError("Annotation/cache changed since native metadata observation")
'''

PHYSICAL = r'''
    import random
    import numpy as np
    from frozen_capture_contract_20260916 import fingerprint
    from native_registry_geometry_runner_20260920 import RegistryDataset
    random.seed(1999)
    np.random.seed(1999)
    torch.manual_seed(1999)
    source_binding = {k:v for k,v in before.items()
                      if k not in ("dataset_source_sha256","registry_sha256")}
    observed = RegistryDataset(native, scratch.name, json.loads(registry.read_text()),
        before["registry_sha256"], source_binding, before["dataset_source_sha256"])
    result["requested_item_indices"] = list(observed.indices[:2])
    result["items"] = []
    result["artifacts"] = []
    result["input_files"] = []
    def save_json(name, value):
        path = scratch/name
        with path.open("x",encoding="ascii") as stream:
            json.dump(value,stream,indent=2,allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        result["artifacts"].append(dict(path=str(path),sha256=file_sha256(path),
                                        bytes=path.stat().st_size))
    def layout(value):
        if torch.is_tensor(value):
            return dict(type="tensor",dtype=str(value.dtype),shape=list(value.shape),
                        device=str(value.device),contiguous=value.is_contiguous())
        if isinstance(value,(tuple,list)):
            return dict(type=type(value).__name__,length=len(value),
                        children=[layout(x) for x in value[:4]])
        return dict(type=type(value).__name__)
    for index in observed.indices[:2]:
        scene = native.scene_inputs[index][0]["scene_id"]
        paths = [pathlib.Path(next(p for p in native.sp_filenames if scene in p)),
                 data/"clip_feat"/(scene+".pth")]
        inputs = {str(p):file_sha256(p) for p in paths}
        item, axes = observed[index]
        if torch.cuda.is_initialized():
            raise ValueError("CPU-only boundary violated")
        digest = fingerprint(item)
        path = scratch/("item_%d.pth" % index)
        with path.open("xb") as stream:
            torch.save(dict(item=item,axes=axes,dataset_index=index,
                            source_binding=source_binding),stream)
            stream.flush()
            os.fsync(stream.fileno())
        if digest != fingerprint(item):
            raise ValueError("Serialization mutated item")
        if any(file_sha256(pathlib.Path(p)) != sha for p,sha in inputs.items()):
            raise ValueError("Input scene/CLIP changed")
        result["input_files"].extend(dict(path=p,sha256=sha,stable=True)
                                     for p,sha in inputs.items())
        result["items"].append(dict(dataset_index=index,scene=scene,
            native_input_sha256=digest,expressions=len(axes),
            superpoints=len(axes[0]["original_superpoint_ids"]),
            sampled_points=len(axes[0]["sample_inverse"]),
            layout=[layout(v) for v in item],
            transient_observers_removed=all(name not in vars(native)
                for name in ("transform_train","get_sp_label"))))
        result["artifacts"].append(dict(path=str(path),sha256=file_sha256(path),
                                        bytes=path.stat().st_size))
    joins = observed.exporter.manifest()
    save_json("physical_bindings.json", joins)
    result["physical_bindings_verified"] = len(joins["bindings"])
    result["binding_counts"] = joins["counts"]
    result["physical_pair_summary"] = [
        dict(pair_id=b["pair_id"],target_support_count=b["target_support_count"],
             control_support_count=b["control_support_count"],
             physical_support_sha256=b["physical_support_sha256"])
        for b in joins["bindings"]]
    result["gpu_initialized"] = torch.cuda.is_initialized()
    result["physical_items_completed"] = True
    result["native_capture_completed"] = False
    result["model_forward_completed"] = False
    result["scientific_validation_complete"] = False
'''


def remote_code(request):
    code = METADATA_REMOTE.replace(
        'scratch = bundle.parent/(bundle.name+"_metadata_scratch")',
        'scratch = bundle.parent/(bundle.name+"_physical_20260920_0415_retry")')
    if code == METADATA_REMOTE:
        raise ValueError("Metadata scratch anchor changed")
    anchor = "denied = []"
    if code.count(anchor) != 1:
        raise ValueError("Observation anchor changed")
    code = code.replace(anchor, OBSERVE + "\n" + anchor)
    anchor = "except Exception as exc:"
    if code.count(anchor) != 1:
        raise ValueError("Native observation anchor changed")
    code = code.replace(anchor, PHYSICAL + "\n" + anchor)
    return "request = " + repr(request) + "\n" + code


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    manifest = ROOT / (
        "pipeline/diagnostic_bundles/"
        "registry_geometry_20260920_0315_88b51c997a74/manifest.json")
    import hashlib
    request = dict(manifest_sha256=file_sha256(manifest),
                   manifest_lf_sha256=hashlib.sha256(
                       manifest.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                   manifest=json.loads(manifest.read_text(encoding="utf-8")),
                   annotation_and_cache_before=prior["annotation_and_cache_before"])
    completed = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
         "songcl@100.64.3.28",
         "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
        input=remote_code(request), text=True, capture_output=True, timeout=480)
    if completed.returncode:
        report = dict(returncode=completed.returncode, stdout=completed.stdout[-6000:],
                      stderr=completed.stderr[-6000:])
    else:
        report = json.loads(completed.stdout.splitlines()[-1])
        report["stderr"] = completed.stderr[-6000:]
        if "training" in report:
            report["training"]["steps"] = training_steps(
                report["training"].get("tail", ""))
    report["probe_sha256"] = file_sha256(__file__)
    report["metadata_probe_sha256"] = file_sha256(
        ROOT / "scripts/probe_staged_metadata_20260920.py")
    with OUTPUT.open("x", encoding="ascii") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k:v for k,v in report.items()
                      if k not in ("native_metadata_plan","training","items")}))
    if report.get("physical_items_completed") is not True or report.get("error"):
        raise RuntimeError("Physical observation incomplete; inspect saved report")


if __name__ == "__main__":
    main()
