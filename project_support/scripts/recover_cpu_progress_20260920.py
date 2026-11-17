"""Recover interrupted replay evidence and continue two original CPU groups."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from frozen_capture_contract_20260916 import file_sha256
from probe_next_physical_20260920 import remote_code as physical_code, select_indices
from probe_saved_collation_20260920 import parse_output

ROOT = Path(__file__).resolve().parents[1]
REPLAY = "pipeline/reports/next_saved_replay_20260920-0815.json"
PHYSICAL = "pipeline/reports/next_physical_20260920-0715.json"
OUTPUT = "pipeline/reports/recovery_physical_20260920-0915.json"


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write_new(name, value):
    with (ROOT / name).open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def validate_recovery(replay, physical):
    for key in ("saved_collation_completed", "saved_replay_verified",
                "driver_import_verified", "driver_help_verified",
                "driver_uncoordinated_rejected", "immutable_import_precedence_verified",
                "full_binding_equal", "sources_stable", "annotation_and_cache_stable"):
        if replay.get(key) is not True:
            raise ValueError("Recovered replay gate failed: " + key)
    if (replay.get("error") or replay["returncode"] != 0
            or replay["gpu_initialized"] or replay["model_forward_completed"]
            or replay["driver_model_path_executed"]
            or replay["observed_binding"] != physical["observed_binding"]
            or replay["binding_counts"] != {"bound": 2, "missing_capture": 29}
            or [row["dataset_index"] for row in replay["prepared"]] != [2690, 3011]):
        raise ValueError("Recovered execution identity/boundary differs")
    if (replay["physical_sha256"] != file_sha256(ROOT / PHYSICAL)
            or replay["probe_sha256"] != file_sha256(
                ROOT / "scripts/probe_next_saved_replay_20260920.py")):
        raise ValueError("Recovered local source/evidence hash differs")
    for row in replay["separate_sources"]:
        if file_sha256(ROOT / "scripts" / Path(row["path"]).name) != row["sha256"]:
            raise ValueError("Separate driver/adapter changed")


RECHECK = r'''
recovery_rows = []
for saved_group in request["recovery_groups"]:
    parent = pathlib.Path(saved_group["scratch"])
    if parent.parent != bundle.parent or not parent.name.startswith(bundle.name+"_"):
        raise ValueError("Recovery source outside diagnostic siblings")
    for row in saved_group["artifacts"]:
        path = pathlib.Path(row["path"])
        if (path.parent != parent or path.is_symlink()
                or ("bytes" in row and path.stat().st_size != row["bytes"])
                or file_sha256(path) != row["sha256"]):
            raise ValueError("Recovered artifact changed")
        recovery_rows.append(row)
result["recovered_artifacts_verified"] = True
'''


def remote_code(request):
    if (request["selected_indices"] != [3040, 3893]
            or request["consumed_indices"] != [1097, 1524, 2690, 3011]):
        raise ValueError("Recovery requires next two unobserved groups")
    code = physical_code(request)
    anchor = 'bundle.name+"_physical_20260920_0715"'
    if code.count(anchor) != 1 or code.count("denied = []") != 1:
        raise ValueError("Existing physical exporter anchors differ")
    code = code.replace(anchor, 'bundle.name+"_physical_20260920_0915"')
    code = code.replace("denied = []", RECHECK + "\ndenied = []")
    anchor = 'result["training_launch"] = False'
    if code.count(anchor) != 1:
        raise ValueError("Postcheck anchor differs")
    code = code.replace(anchor, '''
result["recovered_artifacts_stable"] = all(
    file_sha256(row["path"]) == row["sha256"] for row in recovery_rows)
if not result["recovered_artifacts_stable"]:
    result["error"] = dict(type="ValueError",message="Recovery artifacts mutated")
''' + anchor)
    compile(code, "<recovery-physical>", "exec")
    return code


def probe():
    if (ROOT / OUTPUT).exists():
        raise FileExistsError(OUTPUT)
    physical, replay = read(PHYSICAL), read(REPLAY)
    validate_recovery(replay, physical)
    original = read("pipeline/reports/physical_items_20260920-0415-retry.json")
    manifest = ROOT / ("pipeline/diagnostic_bundles/"
        "registry_geometry_20260920_0315_88b51c997a74/manifest.json")
    consumed = [1097, 1524, 2690, 3011]
    request = dict(
        selected_indices=select_indices(replay["native_metadata_plan"], consumed),
        consumed_indices=consumed, native_metadata_plan=replay["native_metadata_plan"],
        previous_artifacts=physical["artifacts"], previous_scratch=physical["scratch"],
        annotation_and_cache_before=physical["annotation_and_cache_before"],
        manifest=json.loads(manifest.read_text(encoding="utf-8")),
        manifest_lf_sha256=hashlib.sha256(
            manifest.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        recovery_groups=[
            dict(scratch=original["scratch"], artifacts=original["artifacts"]),
            dict(scratch=replay["scratch"], artifacts=replay["artifacts"]
                 + replay["separate_sources"] + [replay["replay_request"]])])
    code = remote_code(request)
    try:
        completed = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
             "songcl@100.64.3.28",
             "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
            input=code, text=True, capture_output=True, timeout=480)
        report = parse_output(completed.stdout, completed.stderr, completed.returncode)
    except subprocess.TimeoutExpired as exc:
        text = lambda x: x.decode(errors="replace") if isinstance(x, bytes) else x or ""
        report = parse_output(text(exc.stdout), text(exc.stderr), "timeout")
    report.update(
        selected_indices=request["selected_indices"], consumed_indices=consumed,
        recovered_replay_sha256=file_sha256(ROOT / REPLAY),
        remote_program_sha256=hashlib.sha256(code.encode()).hexdigest(),
        recovered_artifact_count=sum(len(g["artifacts"]) for g in request["recovery_groups"]))
    if report.get("physical_items_completed"):
        report.pop("stdout_tail", None)
    write_new(OUTPUT, report)
    print(json.dumps({k: report.get(k) for k in (
        "selected_indices", "binding_counts", "physical_pair_summary",
        "sources_stable", "recovered_artifacts_stable", "error", "returncode")}))
    capacity = report.get("capacity", {})
    steps = capacity.get("training", {}).get("steps", [])
    print(json.dumps(dict(
        capacity={k: v for k, v in capacity.items() if k != "training"},
        first=steps[0] if steps else None, last=steps[-1] if steps else None)))
    if (report.get("physical_items_completed") is not True or report.get("error")
            or report["returncode"] != 0):
        raise RuntimeError("CPU continuation incomplete; retain raw evidence")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    probe()
