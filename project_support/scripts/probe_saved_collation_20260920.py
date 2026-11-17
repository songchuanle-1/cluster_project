"""Verify exact saved TRAIN inputs on server-6 CPU without new transforms."""
import hashlib
import json
from pathlib import Path
import subprocess

from frozen_capture_contract_20260916 import file_sha256
from probe_staged_metadata_20260920 import REMOTE as METADATA_REMOTE
from remote_registry_inventory_20260920 import training_steps


ROOT = Path(__file__).resolve().parents[1]
TAG = "20260920-0515"
OUTPUT = ROOT / ("pipeline/reports/saved_collation_" + TAG + ".json")
PRIOR = ROOT / "pipeline/reports/physical_items_20260920-0415-retry.json"

OBSERVE = r'''
import datetime, json, os, pathlib, subprocess, traceback
observation = dict(observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   gpu=7, gpu_execution_authorized=False, training_launch=False)
try:
    observation["gpu_raw"] = subprocess.check_output(["nvidia-smi", "-i", "7",
        "--query-gpu=uuid,memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits"], text=True, timeout=30).strip()
    observation["processes_raw"] = subprocess.check_output(["nvidia-smi", "-i", "7",
        "--query-compute-apps=gpu_uuid,pid,used_memory",
        "--format=csv,noheader,nounits"], text=True, timeout=30).strip()
    uuid, total, used, free, utilization = [
        x.strip() for x in observation["gpu_raw"].split(",")]
    processes = []
    for row in observation["processes_raw"].splitlines():
        row_uuid, pid, memory = [x.strip() for x in row.split(",")]
        if row_uuid != uuid:
            continue
        proc = pathlib.Path("/proc")/pid
        command = ((proc/"cmdline").read_bytes().replace(b"\0",b" ").decode()
                   if proc.exists() else "exited")
        processes.append(dict(pid=int(pid), memory_mib=int(memory), command=command))
    observation.update(total_mib=int(total), used_mib=int(used), free_mib=int(free),
        utilization=int(utilization), processes=processes,
        process_cap_reached=len(processes)>=2,
        measured_memory_sufficient=int(free)>=.15*int(total))
    proc = pathlib.Path("/proc/1134192")
    training = dict(pid=1134192, exists=proc.exists())
    if proc.exists():
        command = (proc/"cmdline").read_bytes().replace(b"\0",b" ").decode()
        log = os.readlink(proc/"fd/1")
        training.update(command=command,log=log)
        expected = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs"
        if expected not in command or expected not in log:
            raise ValueError("M197 PID/config/log identity differs")
        with open(log,"rb") as stream:
            stream.seek(max(0,os.fstat(stream.fileno()).st_size-18000))
            training["tail"] = stream.read(18000).decode(errors="replace")
    observation["training"] = training
except Exception as exc:
    observation["error"] = dict(type=type(exc).__name__,message=str(exc))
# Emit independently: later native errors cannot discard the capacity observation.
print("CAPACITY_JSON:"+json.dumps(observation),flush=True)
'''

VERIFY = r'''
result["capacity"] = observation
manifest_bytes = (bundle/"manifest.json").read_bytes()
if (manifest != request["manifest"]
        or hashlib.sha256(manifest_bytes).hexdigest() != request["manifest_lf_sha256"]):
    raise ValueError("Immutable manifest changed")
if before_data != request["annotation_and_cache_before"]:
    raise ValueError("Annotation/cache changed")
saved = bundle.parent/(bundle.name+"_physical_20260920_0415_retry")
for artifact in request["artifacts"]:
    path = pathlib.Path(artifact["path"])
    if path.parent != saved or path.is_symlink():
        raise ValueError("Untrusted saved artifact path")
    if path.stat().st_size != artifact["bytes"] or file_sha256(path) != artifact["sha256"]:
        raise ValueError("Saved artifact hash changed")
for row in request["input_files"]:
    if file_sha256(row["path"]) != row["sha256"]:
        raise ValueError("Original scene/CLIP bytes changed")
result["saved_artifacts_verified"] = True
'''

COLLATE = r'''
    import io
    from frozen_capture_contract_20260916 import fingerprint
    from native_frozen_capture_20260916 import FrozenDataset
    from referent_registry_binding_20260919 import BindingExporter
    source_binding = {k:v for k,v in before.items()
                      if k not in ("dataset_source_sha256","registry_sha256")}
    exporter = BindingExporter(json.loads(registry.read_text()),
        before["registry_sha256"],native.scene_inputs,source_binding,
        before["dataset_source_sha256"])
    collator = FrozenDataset(native,scratch.name,before["producer_sha256"])
    saved_joins = json.loads((saved/"physical_bindings.json").read_text())
    result["items"] = []
    result["artifacts"] = []
    def layout(value):
        if torch.is_tensor(value):
            if value.device.type != "cpu":
                raise ValueError("Non-CPU tensor in saved replay")
            return dict(type="tensor",dtype=str(value.dtype),shape=list(value.shape),
                        device=str(value.device),contiguous=value.is_contiguous())
        if isinstance(value,dict):
            return {k:layout(v) for k,v in value.items()}
        if isinstance(value,(tuple,list)):
            return dict(type=type(value).__name__,length=len(value),
                        children=[layout(x) for x in value])
        return dict(type=type(value).__name__)
    for expected_item in request["items"]:
        index = expected_item["dataset_index"]
        path = saved/("item_%d.pth"%index)
        # File hash is verified before loading our own trusted tensor bundles.
        payload = torch.load(path,map_location="cpu",weights_only=False)
        if payload["dataset_index"] != index or payload["source_binding"] != source_binding:
            raise ValueError("Saved payload source/index differs")
        item, axes = payload["item"],payload["axes"]
        initial = fingerprint(payload)
        if fingerprint(item) != expected_item["native_input_sha256"]:
            raise ValueError("Saved native item fingerprint differs")
        axis_hash = fingerprint(axes)
        exporter.export_item(index,item,axes)
        buffer = io.BytesIO()
        torch.save(payload,buffer)
        buffer.seek(0)
        roundtrip = torch.load(buffer,map_location="cpu",weights_only=False)
        if fingerprint(roundtrip) != initial or fingerprint(payload) != initial:
            raise ValueError("Serialization round-trip differs")
        batch,batch_axes = collator.collate_fn([(item,axes)])
        if fingerprint(payload) != initial or fingerprint(batch_axes) != axis_hash:
            raise ValueError("Native collation mutated item or axes")
        if (batch["batch_offsets"].tolist() != [0,len(item[11])]
                or batch["scenes_len"].tolist() != [len(axes)]
                or batch["scan_ids"] != [item[1]]
                or batch["ann_ids"] != item[0]):
            raise ValueError("Collated native index/count identity differs")
        for field, expected_value in (
                ("coords_float",item[3]),("superpoints",item[5]),
                ("feats_2d",item[15]),("gt_pmasks",item[7]),
                ("gt_spmasks",item[8]),("sp_ref_masks",item[9]),
                ("sp_ins_labels",[item[11]]),("object_idss",item[6])):
            if fingerprint(batch[field]) != fingerprint(expected_value):
                raise ValueError("Collated field differs: "+field)
        expected_feats = (torch.cat((item[4],item[3]),dim=1)
                          if native.use_xyz else item[4])
        if not torch.equal(batch["feats"],expected_feats):
            raise ValueError("Native feature concatenation differs")
        first_digest = fingerprint(batch)
        again,again_axes = collator.collate_fn([(item,axes)])
        if (fingerprint(again) != first_digest
                or fingerprint(again_axes) != axis_hash
                or fingerprint(payload) != initial):
            raise ValueError("Repeated CPU collation not deterministic or mutates input")
        frozen_batch = dict(batch=batch,axes=batch_axes,dataset_index=index,
            source_binding=source_binding,saved_item_sha256=file_sha256(path),
            item_fingerprint=fingerprint(item),axes_fingerprint=axis_hash)
        out = scratch/("batch_%d.pth"%index)
        with out.open("xb") as stream:
            torch.save(frozen_batch,stream)
            stream.flush()
            os.fsync(stream.fileno())
        loaded_batch = torch.load(out,map_location="cpu",weights_only=False)
        if fingerprint(loaded_batch) != fingerprint(frozen_batch):
            raise ValueError("Collated artifact round-trip differs")
        result["artifacts"].append(dict(path=str(out),sha256=file_sha256(out),
                                       bytes=out.stat().st_size))
        result["items"].append(dict(dataset_index=index,scene=item[1],
            native_input_sha256=fingerprint(item),axes_sha256=axis_hash,
            payload_sha256=initial,batch_sha256=first_digest,
            expressions=len(axes),roundtrip_verified=True,
            repeated_collation_identical=True,inputs_unchanged=True,
            fields={k:dict(sha256=fingerprint(v),layout=layout(v))
                    for k,v in batch.items()}))
        if torch.cuda.is_initialized():
            raise ValueError("CPU boundary violated")
    reconstructed = exporter.manifest()
    if reconstructed != saved_joins:
        raise ValueError("Reconstructed full physical binding differs")
    result.update(physical_bindings_verified=len(reconstructed["bindings"]),
        binding_counts=reconstructed["counts"],full_binding_equal=True,
        full_binding_sha256=fingerprint(reconstructed),
        saved_collation_completed=True,gpu_initialized=torch.cuda.is_initialized(),
        native_capture_completed=False,model_forward_completed=False,
        new_train_transforms=False,scientific_validation_complete=False)
'''


def remote_code(request):
    code = METADATA_REMOTE.replace(
        'scratch = bundle.parent/(bundle.name+"_metadata_scratch")',
        'scratch = bundle.parent/(bundle.name+"_saved_collation_20260920_0515")')
    if code == METADATA_REMOTE:
        raise ValueError("Scratch anchor changed")
    for anchor, insertion in (("denied = []", VERIFY),
                              ("except Exception as exc:", COLLATE)):
        if code.count(anchor) != 1:
            raise ValueError("Native probe anchor changed")
        code = code.replace(anchor, insertion + "\n" + anchor)
    code = code.replace('print(json.dumps(result))',
                        'print("RESULT_JSON:"+json.dumps(result),flush=True)')
    return "request = " + repr(request) + "\n" + OBSERVE + "\n" + code


def parse_output(stdout, stderr, returncode):
    frames = {}
    for line in stdout.splitlines():
        for prefix, key in (("CAPACITY_JSON:", "capacity"), ("RESULT_JSON:", "result")):
            if line.startswith(prefix):
                frames[key] = json.loads(line[len(prefix):])
    report = frames.get("result", {})
    if "capacity" in frames:
        report["capacity"] = frames["capacity"]
        training = report["capacity"].get("training", {})
        training["steps"] = training_steps(training.get("tail", ""))
    report.update(returncode=returncode, stderr=stderr[-6000:])
    if not report.get("saved_collation_completed"):
        report["stdout_tail"] = stdout[-6000:]
    return report


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    manifest_path = ROOT / (
        "pipeline/diagnostic_bundles/"
        "registry_geometry_20260920_0315_88b51c997a74/manifest.json")
    request = {key:prior[key] for key in (
        "annotation_and_cache_before","artifacts","items","input_files")}
    request.update(manifest=json.loads(manifest_path.read_text(encoding="utf-8")),
        manifest_lf_sha256=hashlib.sha256(
            manifest_path.read_bytes().replace(b"\r\n",b"\n")).hexdigest())
    try:
        completed = subprocess.run(
            ["ssh","-o","BatchMode=yes","-o","ConnectTimeout=15","songcl@100.64.3.28",
             "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
            input=remote_code(request),text=True,capture_output=True,timeout=480)
        report = parse_output(completed.stdout,completed.stderr,completed.returncode)
    except subprocess.TimeoutExpired as exc:
        text = lambda x: x.decode(errors="replace") if isinstance(x,bytes) else x or ""
        report = parse_output(text(exc.stdout),text(exc.stderr),"timeout")
    report["probe_sha256"] = file_sha256(__file__)
    report["prior_sha256"] = file_sha256(PRIOR)
    with OUTPUT.open("x",encoding="ascii") as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write("\n")
    print(json.dumps({k:v for k,v in report.items()
                      if k not in ("items","native_metadata_plan","capacity")}))
    capacity = report.get("capacity", {})
    print(json.dumps({k:v for k,v in capacity.items() if k != "training"}))
    steps = capacity.get("training",{}).get("steps",[])
    print(json.dumps(dict(first_step=steps[0] if steps else None,
                          last_step=steps[-1] if steps else None)))
    if (report.get("saved_collation_completed") is not True
            or report.get("error") or report["returncode"] != 0):
        raise RuntimeError("Saved collation incomplete; inspect retained report")


if __name__ == "__main__":
    main()
