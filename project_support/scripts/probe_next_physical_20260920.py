"""Continue original-index physical exports; never initialize CUDA or a model."""
import hashlib
import json
from pathlib import Path
import subprocess

from frozen_capture_contract_20260916 import file_sha256
from probe_physical_items_20260920 import PHYSICAL
from probe_saved_collation_20260920 import OBSERVE, parse_output
from probe_staged_metadata_20260920 import REMOTE

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "pipeline/reports/next_physical_20260920-0715.json"


def select_indices(plan, consumed):
    if plan["counts"] != {"planned": 31}:
        raise ValueError("Require complete 31-pair metadata plan")
    indices = sorted({row["dataset_index"] for row in plan["rows"]
                      if row["status"] == "planned"})
    if any(type(i) is not int for i in indices + list(consumed)):
        raise ValueError("Integer original indices required")
    if not set(consumed).issubset(indices):
        raise ValueError("Unknown consumed index")
    selected = [i for i in indices if i not in consumed][:2]
    if not selected:
        raise ValueError("No remaining physical groups")
    return selected


VERIFY = r'''
result["capacity"] = observation
if (manifest != request["manifest"]
        or file_sha256(bundle/"manifest.json") != request["manifest_lf_sha256"]
        or before_data != request["annotation_and_cache_before"]):
    raise ValueError("Immutable producer or data changed")
for row in request["previous_artifacts"]:
    path = pathlib.Path(row["path"])
    if (path.parent != pathlib.Path(request["previous_scratch"]) or path.is_symlink()
            or path.stat().st_size != row["bytes"] or file_sha256(path) != row["sha256"]):
        raise ValueError("Previously saved physical artifact changed")
'''


def remote_code(request):
    indices = request["selected_indices"]
    if (not 1 <= len(indices) <= 2 or len(set(indices)) != len(indices)
            or any(type(i) is not int for i in indices)
            or set(indices) & set(request["consumed_indices"])):
        raise ValueError("Require bounded unobserved original indices")
    code = REMOTE.replace('bundle.name+"_metadata_scratch"',
                          'bundle.name+"_physical_20260920_0715"')
    physical = PHYSICAL.replace("observed.indices[:2]", 'request["selected_indices"]')
    anchor = '    result["requested_item_indices"]'
    physical = physical.replace(anchor, '''
    if (plan != request["native_metadata_plan"]
            or not set(request["selected_indices"]).issubset(observed.indices)):
        raise ValueError("Original metadata plan changed")
''' + anchor)
    physical += '''
    result["previous_artifacts_stable"] = all(
        file_sha256(row["path"]) == row["sha256"]
        for row in request["previous_artifacts"])
    if not result["previous_artifacts_stable"]:
        raise ValueError("Previously saved inputs changed during export")
    if any(file_sha256(row["path"]) != row["sha256"] for row in result["input_files"]):
        raise ValueError("Scene/CLIP changed after export")
'''
    for anchor, insertion in (("denied = []", VERIFY),
                              ("except Exception as exc:", physical)):
        if code.count(anchor) != 1:
            raise ValueError("Native probe anchor differs")
        code = code.replace(anchor, insertion + "\n" + anchor)
    code = code.replace('print(json.dumps(result))',
                        'print("RESULT_JSON:"+json.dumps(result),flush=True)')
    return "request = " + repr(request) + "\n" + OBSERVE + "\n" + code


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    read = lambda name: json.loads((ROOT / name).read_text(encoding="utf-8"))
    prior = read("pipeline/reports/physical_items_20260920-0415-retry.json")
    replay = read("pipeline/reports/saved_replay_20260920-0615.json")
    plan = replay["native_metadata_plan"]
    consumed = [row["dataset_index"] for row in replay["prepared"]]
    manifest = ROOT / ("pipeline/diagnostic_bundles/"
                      "registry_geometry_20260920_0315_88b51c997a74/manifest.json")
    request = dict(native_metadata_plan=plan, consumed_indices=consumed,
        selected_indices=select_indices(plan, consumed),
        previous_artifacts=prior["artifacts"], previous_scratch=prior["scratch"],
        annotation_and_cache_before=prior["annotation_and_cache_before"],
        manifest=json.loads(manifest.read_text(encoding="utf-8")),
        manifest_lf_sha256=hashlib.sha256(
            manifest.read_bytes().replace(b"\r\n", b"\n")).hexdigest())
    try:
        completed = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
             "songcl@100.64.3.28",
             "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
            input=remote_code(request), text=True, capture_output=True, timeout=480)
        report = parse_output(completed.stdout, completed.stderr, completed.returncode)
    except subprocess.TimeoutExpired as exc:
        text = lambda x: x.decode(errors="replace") if isinstance(x, bytes) else x or ""
        report = parse_output(text(exc.stdout), text(exc.stderr), "timeout")
    report.update(probe_sha256=file_sha256(__file__),
                  selected_indices=request["selected_indices"],
                  consumed_indices=consumed)
    if report.get("physical_items_completed"):
        report.pop("stdout_tail", None)
    with OUTPUT.open("x", encoding="ascii") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: report.get(k) for k in (
        "selected_indices", "binding_counts", "physical_pair_summary",
        "sources_stable", "previous_artifacts_stable", "error", "returncode")}))
    capacity = report.get("capacity", {})
    print(json.dumps({k: v for k, v in capacity.items() if k != "training"}))
    steps = capacity.get("training", {}).get("steps", [])
    print(json.dumps(dict(first=steps[0] if steps else None,
                         last=steps[-1] if steps else None)))
    if (report.get("physical_items_completed") is not True or report.get("error")
            or report["returncode"] != 0):
        raise RuntimeError("Physical continuation incomplete; raw evidence retained")


if __name__ == "__main__":
    main()
