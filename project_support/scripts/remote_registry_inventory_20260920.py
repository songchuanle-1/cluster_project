"""Read-only remote inventory and source-derived metadata plan; no model import."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from native_geometry_runtime_20260919 import MODEL_CLASS
from native_registry_geometry_runner_20260920 import runner_manifest
from referent_registry_binding_20260919 import plan_bindings


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "pipeline/reports/referent_control_pairing_20260918-1812.json"


def training_steps(tail):
    matches = re.findall(
        r"(Train|Val)\[(\d+)/(\d+)\]:[^\r\n]*?\|\s*(\d+)/(\d+)\s*\[", tail)
    return [dict(phase=phase, epoch=int(epoch), epochs=int(epochs),
                 step=int(step), total=int(total))
            for phase, epoch, epochs, step, total in matches]

REMOTE = r'''
import ast, datetime, hashlib, json, os, pathlib, re, subprocess, textwrap
root = pathlib.Path("/data3/songcl/Project/Cluster_project/Cluster")
request = json.loads(REQUEST)
def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()
def inventory(path):
    if not path.is_file():
        return dict(path=str(path), exists=False)
    before = path.stat()
    sha = digest(path)
    after = path.stat()
    return dict(path=str(path), exists=True, sha256=sha, bytes=after.st_size,
                stable=(before.st_size, before.st_mtime_ns) ==
                       (after.st_size, after.st_mtime_ns))
model = request["model"]
dataset = root / "framework/dataset/scannetv2.py"
config = root / "configs/Quard/ctf_hcg_csort" / (model + ".yaml")
package = root / "framework/model/Quard_model" / model
h = hashlib.sha256()
model_files = []
for path in sorted(package.rglob("*.py")):
    name = path.relative_to(package).as_posix().encode("ascii")
    payload = path.read_bytes()
    h.update(len(name).to_bytes(4, "big")); h.update(name)
    h.update(len(payload).to_bytes(8, "big")); h.update(payload)
    model_files.append(inventory(path))
sources = [inventory(root.parent / "scripts" / row["path"])
           for row in request["producer_sources"]]
registry = inventory(root.parent / request["registry"])
tree = ast.parse(dataset.read_text())
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
           and n.name == "ScanNetDataset_sample_graph_edge")
init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
lines = dataset.read_text().splitlines()
metadata_start = next(n.lineno for n in init.body if isinstance(n, ast.Expr)
                      and ast.unparse(n).startswith("self.scanrefer.sort"))
metadata_end = next(n.end_lineno for n in init.body if isinstance(n, ast.Assign)
                    and any(ast.unparse(t) == "self.scene_inputs" for t in n.targets))
block = textwrap.dedent("\n".join(lines[metadata_start - 1:metadata_end]))
annotation = pathlib.Path("/data3/songcl/data/data_cluster/scanrefer/ScanRefer_train_new.json")
annotation_info = inventory(annotation)
# Execute only the observed constructor's metadata grouping, not dataset imports.
class Metadata: pass
obj = Metadata()
obj.scanrefer = json.loads(annotation.read_text())
namespace = dict(self=obj, lang_num_max=request["lang_num_max"])
exec(compile(block, str(dataset) + ":metadata-only", "exec"), namespace)
annotation_info["stable_after_grouping"] = digest(annotation) == annotation_info["sha256"]
checkpoints = []
checkpoint_root = root.parent / "Cluster_checkpoints" / model
if checkpoint_root.is_dir():
    for path in sorted(checkpoint_root.glob("*/best*.pth")):
        checkpoints.append(inventory(path))
result = dict(
    observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    root=str(root), dataset=inventory(dataset), config=inventory(config),
    config_text=config.read_text(), dataset_grouping_source=block,
    model_source_sha256=h.hexdigest() if model_files else None,
    model_files=model_files, producer_sources=sources, registry=registry,
    checkpoint_root=str(checkpoint_root), checkpoints=checkpoints,
    annotation=annotation_info, scene_inputs=obj.scene_inputs,
    grouping_lang_num_max=request["lang_num_max"],
    metadata_method="Executed only AST-located native constructor metadata grouping",
    native_dataset_instantiated=False, gpu_allocated=False,
)
result["gpu"] = subprocess.check_output([
    "nvidia-smi", "-i", "7",
    "--query-gpu=uuid,memory.total,memory.used,memory.free,utilization.gpu",
    "--format=csv,noheader,nounits"], text=True).strip()
result["gpu_processes"] = subprocess.check_output([
    "nvidia-smi", "-i", "7", "--query-compute-apps=gpu_uuid,pid,used_memory",
    "--format=csv,noheader,nounits"], text=True).strip()
pid = 1134192
proc = pathlib.Path("/proc") / str(pid)
if proc.exists():
    command = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode()
    log = os.readlink(proc / "fd/1")
    result["training"] = dict(pid=pid, command=command, log=log)
    expected = model + "_pirs"
    if expected in command and expected in log:
        with open(log, "rb") as stream:
            stream.seek(max(0, os.fstat(stream.fileno()).st_size - 18000))
            tail = stream.read(18000).decode(errors="replace")
        result["training"]["tail"] = tail
        result["training"]["steps"] = re.findall(
            r"(Train|Val)\[(\d+)/(\d+)\]\s*\[(\d+)/(\d+)\]", tail)
print(json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError("Inventory output must be new")
    manifest = runner_manifest()
    request = dict(model=MODEL_CLASS, registry=REGISTRY,
                   producer_sources=manifest["sources"], lang_num_max=4)
    code = REMOTE.replace("REQUEST", repr(json.dumps(request)), 1)
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
               "songcl@100.64.3.28",
               "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"]
    result = subprocess.run(command, input=code, text=True, capture_output=True,
                            timeout=240, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    remote = json.loads(result.stdout)
    if "training" in remote:
        remote["training"]["steps"] = training_steps(remote["training"]["tail"])
    registry = json.loads((ROOT / REGISTRY).read_text(encoding="utf-8"))
    scene_inputs = remote.pop("scene_inputs")
    plan = plan_bindings(registry, file_sha256(ROOT / REGISTRY), scene_inputs)
    local_config = ROOT / "Cluster/configs/Quard/ctf_hcg_csort" / (MODEL_CLASS + ".yaml")
    comparisons = dict(
        dataset_matches=remote["dataset"]["sha256"] ==
        file_sha256(ROOT / "Cluster/framework/dataset/scannetv2.py"),
        model_matches=remote["model_source_sha256"] ==
        model_package_sha256(ROOT / "Cluster", MODEL_CLASS),
        config_bytes_match=remote["config"]["sha256"] == file_sha256(local_config),
        registry_matches=remote["registry"].get("sha256") == file_sha256(ROOT / REGISTRY),
        producer_missing=[row["path"] for row in remote["producer_sources"]
                          if not row["exists"]],
        producer_mismatches=[
            row["path"] for row, expected in zip(remote["producer_sources"], manifest["sources"])
            if row["exists"] and row["sha256"] != expected["sha256"]])
    report = dict(
        contract="read_only_remote_registry_inventory_v1",
        remote=remote, comparisons=comparisons, metadata_plan=plan,
        local_runner_manifest=manifest,
        native_execution_completed=False, physical_bindings_verified=0,
        scientific_validation_complete=False,
        limitations=[
            "Source-derived metadata plan is not instantiated dataset or physical capture.",
            "Exact remote config semantics still require review before binding.",
            "No producer deployment, expected-binding approval or checkpoint loading.",
            "Hard-link capability not tested: remote filesystem was read-only.",
            "Geometry is annotation-assisted nuisance, not independent objectness.",
        ])
    with output.open("x", encoding="ascii") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(comparisons=comparisons, counts=plan["counts"],
                          checkpoints=remote["checkpoints"], gpu=remote["gpu"],
                          processes=remote["gpu_processes"],
                          training_steps=remote.get("training", {}).get("steps", []))))


if __name__ == "__main__":
    main()
