"""Authorized native CPU verification of the separate exact-batch adapter."""
import hashlib
import json
from pathlib import Path
import subprocess

from frozen_capture_contract_20260916 import file_sha256
from probe_saved_collation_20260920 import OBSERVE, parse_output
from probe_staged_metadata_20260920 import REMOTE


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "pipeline/reports/saved_replay_20260920-0615.json"
VERIFY = r'''
result["capacity"] = observation
if (manifest != request["manifest"]
        or file_sha256(bundle/"manifest.json") != request["manifest_lf_sha256"]):
    raise ValueError("Immutable manifest changed")
if before_data != request["physical"]["annotation_and_cache_before"]:
    raise ValueError("Annotation/cache changed")
for row in request["physical"]["input_files"]:
    if file_sha256(row["path"]) != row["sha256"]:
        raise ValueError("Original scene/CLIP bytes changed")
adapter = request["adapter"]
if hashlib.sha256(adapter.encode("utf-8")).hexdigest() != request["adapter_sha256"]:
    raise ValueError("Replay adapter bytes changed")
adapter_path = scratch/"saved_geometry_replay_20260920.py"
with adapter_path.open("xb") as stream:
    stream.write(adapter.encode("utf-8"))
    stream.flush()
    os.fsync(stream.fileno())
sys.path.insert(0,str(scratch))
'''
REPLAY = r'''
    from saved_geometry_replay_20260920 import prepare_replay
    from referent_registry_binding_20260919 import BindingExporter
    from frozen_capture_contract_20260916 import fingerprint
    source_binding = {k:v for k,v in before.items()
                      if k not in ("dataset_source_sha256","registry_sha256")}
    exporter = BindingExporter(json.loads(registry.read_text()),
        before["registry_sha256"],native.scene_inputs,source_binding,
        before["dataset_source_sha256"])
    prepared, joins = prepare_replay(request, exporter,
        lambda path: torch.load(path,map_location="cpu",weights_only=False))
    result["prepared"] = [dict(dataset_index=saved["dataset_index"],
        saved_payload_sha256=digest,batch_sha256=fingerprint(saved["batch"]),
        axes_sha256=fingerprint(saved["axes"]),expressions=len(saved["axes"]))
        for saved,digest in prepared]
    result.update(saved_replay_verified=True,
        physical_bindings_verified=len(joins["bindings"]),binding_counts=joins["counts"],
        full_binding_sha256=fingerprint(joins),adapter_sha256=file_sha256(adapter_path),
        gpu_initialized=torch.cuda.is_initialized(),model_forward_completed=False,
        new_train_transforms=False,scientific_validation_complete=False)
    if result["gpu_initialized"]:
        raise ValueError("CPU boundary violated")
'''


def remote_code(request):
    code = REMOTE.replace(
        'scratch = bundle.parent/(bundle.name+"_metadata_scratch")',
        'scratch = bundle.parent/(bundle.name+"_saved_replay_20260920_0615")')
    if code == REMOTE:
        raise ValueError("Scratch anchor differs")
    for anchor, insertion in (("denied = []", VERIFY),
                              ("except Exception as exc:", REPLAY)):
        if code.count(anchor) != 1:
            raise ValueError("Probe anchor differs")
        code = code.replace(anchor, insertion + "\n" + anchor)
    code = code.replace('print(json.dumps(result))',
                        'print("RESULT_JSON:"+json.dumps(result),flush=True)')
    return "request = " + repr(request) + "\n" + OBSERVE + "\n" + code


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    read = lambda name: json.loads((ROOT / name).read_text(encoding="utf-8"))
    manifest = ROOT / ("pipeline/diagnostic_bundles/"
        "registry_geometry_20260920_0315_88b51c997a74/manifest.json")
    adapter = ROOT / "scripts/saved_geometry_replay_20260920.py"
    adapter_bytes = adapter.read_bytes()
    physical = read("pipeline/reports/physical_items_20260920-0415-retry.json")
    collated = read("pipeline/reports/saved_collation_20260920-0515.json")
    request = dict(
        physical={k:physical[k] for k in ("scratch","artifacts","observed_binding",
            "annotation_and_cache_before","input_files")},
        collated={k:collated[k] for k in ("scratch","artifacts","items",
            "observed_binding","full_binding_sha256")},
        manifest=json.loads(manifest.read_text(encoding="utf-8")),
        manifest_lf_sha256=hashlib.sha256(
            manifest.read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
        adapter=adapter_bytes.decode("utf-8"),
        adapter_sha256=hashlib.sha256(adapter_bytes).hexdigest())
    try:
        result = subprocess.run(
            ["ssh","-o","BatchMode=yes","-o","ConnectTimeout=15","songcl@100.64.3.28",
             "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
            input=remote_code(request),text=True,capture_output=True,timeout=480)
        report = parse_output(result.stdout,result.stderr,result.returncode)
    except subprocess.TimeoutExpired as exc:
        text = lambda x: x.decode(errors="replace") if isinstance(x,bytes) else x or ""
        report = parse_output(text(exc.stdout),text(exc.stderr),"timeout")
    report.update(probe_sha256=file_sha256(__file__),
                  local_adapter_sha256=file_sha256(adapter))
    if report.get("saved_replay_verified"):
        report.pop("stdout_tail",None)
    with OUTPUT.open("x",encoding="ascii") as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write("\n")
    print(json.dumps({k:v for k,v in report.items()
                      if k not in ("native_metadata_plan","capacity")}))
    capacity = report.get("capacity",{})
    print(json.dumps({k:v for k,v in capacity.items() if k != "training"}))
    steps = capacity.get("training",{}).get("steps",[])
    print(json.dumps(dict(first=steps[0] if steps else None,
                          last=steps[-1] if steps else None)))
    if (report.get("saved_replay_verified") is not True or report.get("error")
            or report["returncode"] != 0):
        raise RuntimeError("Saved replay verification incomplete; evidence retained")


if __name__ == "__main__":
    main()
