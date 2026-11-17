"""Collate two existing physical groups and verify exact replay on native CPU."""
import hashlib
import json
from pathlib import Path
import subprocess

from frozen_capture_contract_20260916 import file_sha256
from probe_saved_collation_20260920 import COLLATE, OBSERVE, parse_output
from probe_staged_metadata_20260920 import REMOTE

ROOT = Path(__file__).resolve().parents[1]
TAG = "20260920_0815"
OUTPUT = ROOT / "pipeline/reports/next_saved_replay_20260920-0815.json"
PHYSICAL = ROOT / "pipeline/reports/next_physical_20260920-0715.json"

VERIFY = r'''
result["capacity"] = observation
if (manifest != request["manifest"]
        or file_sha256(bundle/"manifest.json") != request["manifest_lf_sha256"]
        or before_data != request["annotation_and_cache_before"]):
    raise ValueError("Immutable producer or data differs")
saved = pathlib.Path(request["physical"]["scratch"])
if saved != bundle.parent/(bundle.name+"_physical_20260920_0715"):
    raise ValueError("Unexpected saved physical source")
for row in request["artifacts"]:
    path = pathlib.Path(row["path"])
    if (path.parent != saved or path.is_symlink()
            or path.stat().st_size != row["bytes"]
            or file_sha256(path) != row["sha256"]):
        raise ValueError("Saved artifact differs")
for row in request["input_files"]:
    if file_sha256(row["path"]) != row["sha256"]:
        raise ValueError("Scene/CLIP input differs")
for row in request["separate_sources"]:
    content = row["content"].encode("utf-8")
    if (pathlib.Path(row["name"]).name != row["name"]
            or hashlib.sha256(content).hexdigest() != row["sha256"]):
        raise ValueError("Separate source name/hash differs")
    with (scratch/row["name"]).open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
# Immutable producer resolves first; only the two separate modules live here.
sys.path.insert(1,str(scratch))
result["saved_artifacts_verified"] = True
'''

REPLAY = r'''
    import contextlib
    from saved_geometry_replay_20260920 import prepare_replay, verify_artifacts
    import native_saved_geometry_driver_20260920 as driver
    replay_request = dict(
        physical=request["physical"],
        collated={k:result[k] for k in (
            "scratch","artifacts","items","observed_binding","full_binding_sha256")},
        manifest=manifest,
        adapter_sha256=request["separate_sources"][0]["sha256"],
        driver_sha256=request["separate_sources"][1]["sha256"])
    fresh_exporter = BindingExporter(json.loads(registry.read_text()),
        before["registry_sha256"],native.scene_inputs,source_binding,
        before["dataset_source_sha256"])
    prepared, joins = prepare_replay(replay_request,fresh_exporter,
        lambda path:torch.load(path,map_location="cpu",weights_only=False))
    if joins != reconstructed:
        raise ValueError("Replay joins differ from saved collation")
    result["prepared"] = [dict(dataset_index=value["dataset_index"],
        saved_payload_sha256=digest,batch_sha256=fingerprint(value["batch"]),
        axes_sha256=fingerprint(value["axes"]),expressions=len(value["axes"]))
        for value,digest in prepared]
    for module in tuple(sys.modules.values()):
        path = getattr(module,"__file__",None)
        if path is None:
            continue
        path = pathlib.Path(path).resolve()
        for row in manifest["files"]:
            if path.suffix == ".py" and path.name == pathlib.Path(row["path"]).name:
                if path != (bundle/row["path"]).resolve():
                    raise ValueError("Producer imported outside immutable bundle")
    for row in request["separate_sources"]:
        if file_sha256(scratch/row["name"]) != row["sha256"]:
            raise ValueError("Staged source differs")
    help_text = io.StringIO()
    try:
        with contextlib.redirect_stdout(help_text):
            driver.main(["--help"])
    except SystemExit as exc:
        if exc.code != 0:
            raise
    else:
        raise ValueError("Driver help did not exit")
    if "--coordinated-slot" not in help_text.getvalue():
        raise ValueError("Driver CLI parser differs")
    try:
        driver.main(["--request",str(scratch/"request.json"),
                     "--output",str(scratch/"unallocated_capture")])
    except ValueError as exc:
        if str(exc) != "External GPU7 slot coordination required":
            raise
    else:
        raise ValueError("Uncoordinated driver did not fail closed")
    request_path = scratch/"request.json"
    with request_path.open("x",encoding="ascii") as stream:
        json.dump(replay_request,stream,indent=2,allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    for key in ("physical","collated"):
        verify_artifacts(replay_request[key]["artifacts"],replay_request[key]["scratch"])
    if any(file_sha256(row["path"]) != row["sha256"] for row in request["input_files"]):
        raise ValueError("Scene/CLIP changed during replay")
    result.update(saved_replay_verified=True,driver_import_verified=True,
        immutable_import_precedence_verified=True,driver_help_verified=True,
        driver_uncoordinated_rejected=True,driver_model_path_executed=False,
        driver_cli_help=help_text.getvalue(),replay_request=dict(
            path=str(request_path),sha256=file_sha256(request_path)),
        separate_sources=[dict(path=str(scratch/row["name"]),sha256=row["sha256"])
                          for row in request["separate_sources"]],
        gpu_initialized=torch.cuda.is_initialized(),model_forward_completed=False,
        new_train_transforms=False,scientific_validation_complete=False)
    if result["gpu_initialized"]:
        raise ValueError("CPU boundary violated")
'''


def remote_code(request):
    if [row["dataset_index"] for row in request["items"]] != [2690, 3011]:
        raise ValueError("Require the exact next two saved groups")
    code = REMOTE.replace('bundle.name+"_metadata_scratch"',
                          'bundle.name+"_saved_replay_' + TAG + '"')
    if code == REMOTE:
        raise ValueError("Scratch anchor differs")
    for anchor, insertion in (("denied = []", VERIFY),
                              ("except Exception as exc:", COLLATE + REPLAY)):
        if code.count(anchor) != 1:
            raise ValueError("Native probe anchor differs")
        code = code.replace(anchor, insertion + "\n" + anchor)
    code = code.replace('print(json.dumps(result))',
                        'print("RESULT_JSON:"+json.dumps(result),flush=True)')
    return "request = " + repr(request) + "\n" + OBSERVE + "\n" + code


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    physical = json.loads(PHYSICAL.read_text(encoding="utf-8"))
    if (physical.get("physical_items_completed") is not True
            or physical["binding_counts"] != {"bound": 2, "missing_capture": 29}
            or physical.get("error")):
        raise ValueError("Saved physical preparation incomplete")
    manifest = ROOT / ("pipeline/diagnostic_bundles/"
        "registry_geometry_20260920_0315_88b51c997a74/manifest.json")
    request = {k: physical[k] for k in (
        "annotation_and_cache_before", "artifacts", "items", "input_files")}
    request.update(
        physical={k: physical[k] for k in (
            "scratch","artifacts","observed_binding","annotation_and_cache_before","input_files")},
        manifest=json.loads(manifest.read_text(encoding="utf-8")),
        manifest_lf_sha256=hashlib.sha256(
            manifest.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        separate_sources=[])
    for name in ("saved_geometry_replay_20260920.py",
                 "native_saved_geometry_driver_20260920.py"):
        data = (ROOT / "scripts" / name).read_bytes()
        request["separate_sources"].append(dict(
            name=name, content=data.decode("utf-8"), sha256=hashlib.sha256(data).hexdigest()))
    code = remote_code(request)
    compile(code, "<next-saved-replay>", "exec")
    try:
        completed = subprocess.run(
            ["ssh","-o","BatchMode=yes","-o","ConnectTimeout=15","songcl@100.64.3.28",
             "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
            input=code,text=True,capture_output=True,timeout=480)
        report = parse_output(completed.stdout,completed.stderr,completed.returncode)
    except subprocess.TimeoutExpired as exc:
        text = lambda x: x.decode(errors="replace") if isinstance(x,bytes) else x or ""
        report = parse_output(text(exc.stdout),text(exc.stderr),"timeout")
    report.update(probe_sha256=file_sha256(__file__),physical_sha256=file_sha256(PHYSICAL),
                  remote_program_sha256=hashlib.sha256(code.encode()).hexdigest())
    if report.get("saved_replay_verified"):
        report.pop("stdout_tail",None)
    with OUTPUT.open("x",encoding="ascii") as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write("\n")
    keys = ("saved_collation_completed","saved_replay_verified","binding_counts",
            "driver_import_verified","driver_help_verified","driver_uncoordinated_rejected",
            "sources_stable","annotation_and_cache_stable","prepared","error","returncode")
    print(json.dumps({k:report.get(k) for k in keys}))
    capacity = report.get("capacity",{})
    print(json.dumps({k:v for k,v in capacity.items() if k != "training"}))
    steps = capacity.get("training",{}).get("steps",[])
    print(json.dumps(dict(first=steps[0] if steps else None,last=steps[-1] if steps else None)))
    if (report.get("saved_replay_verified") is not True or report.get("error")
            or report["returncode"] != 0):
        raise RuntimeError("CPU replay incomplete; evidence retained")


if __name__ == "__main__":
    main()
