"""Whole frozen VAL export for two existing checkpoints, never training."""
import os
os.environ.update(CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES="0",
                  PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="1")
import copy
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

STAGE = Path(__file__).resolve().parent
manifest = json.loads((STAGE / "paired_manifest_isolated.json").read_text())
parser=argparse.ArgumentParser();parser.add_argument('--lease',required=True);args=parser.parse_args()
lease=json.loads(Path(args.lease).read_text())
assert lease['project']=='cluster_project' and lease['thread_id']=='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
assert lease['token']==manifest['owner_token'] and lease['deadline_at']==manifest['deadline_at']
assert hashlib.sha256((STAGE/'paired_manifest_isolated.json').read_bytes()).hexdigest()==lease['native_manifest_sha256']
deadline = datetime.fromisoformat(manifest["deadline_at"])
remaining=(deadline-datetime.now(timezone.utc)).total_seconds()
assert remaining>600
signal.alarm(min(1200,int(remaining)-150))
assert socket.gethostname() == "dl04-MS-7E06"
ROOT = Path(manifest["root"])
UUID = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def gpu():
    row = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu",
                                   "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    cells = [value.strip() for value in row.split(",")]
    assert cells[:2] == ["0", UUID]
    contexts = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-compute-apps=pid,used_memory",
                                        "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    own = 0
    for line in contexts.splitlines():
        pid, used = [int(value.strip()) for value in line.split(",")]
        assert pid == os.getpid(), "Other GPU context; no overlap/eviction"
        own += used
    assert int(cells[4]) + own >= int(cells[2]) - 1024
    return {"row": row, "contexts": contexts}


def time_guard():
    assert (deadline - datetime.now(timezone.utc)).total_seconds() > 90


initial = gpu()
assert not initial["contexts"] and int(initial["row"].split(",")[3]) < 1024
locks = []
try:
    for kind in ("training", "diagnostic", "exclusive"):
        handle = open("/tmp/cluster_project_gpu0_" + kind + ".lock", "a+b")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(handle)
    gpu()
    for relative, expected in manifest["source_hashes"].items():
        assert digest(ROOT / relative) == expected, relative
    for name, expected in manifest["producer_hashes"].items():
        assert digest(STAGE / name) == expected, name
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    from tools import train as native_train
    import torch
    import gorilla
    import logging
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader
    from aligned_evidence import align_pairs, export_prediction, native_mean
    import numpy as np
    assert digest(STAGE/'reference_m95_epoch16.json')==manifest['reference_export_sha256']
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.25, 0)

    def fingerprint(value):
        h = hashlib.sha256()
        def feed(obj):
            if torch.is_tensor(obj):
                arr = obj.detach().cpu().contiguous().numpy()
                h.update(str((arr.dtype.str, arr.shape)).encode())
                h.update(arr.tobytes())
            elif isinstance(obj, dict):
                for name in sorted(obj):
                    h.update(name.encode()); feed(obj[name])
            elif isinstance(obj, (list, tuple)):
                h.update(str(len(obj)).encode())
                for item in obj: feed(item)
            else:
                h.update(repr(obj).encode())
        feed(value)
        return h.hexdigest()

    results = {}
    val_config = copy.deepcopy(gorilla.Config.fromfile(str(ROOT / manifest["conditions"]["reference_m95_epoch16"]["config"])).data.val)
    val_config.data_root = "/home/songcl/data/data/"
    for condition in ("candidate_fle_epoch13",):
        time_guard(); gpu()
        spec = manifest["conditions"][condition]
        assert digest(spec["checkpoint"]) == spec["checkpoint_sha256"]
        cfg = gorilla.Config.fromfile(str(ROOT / spec["config"]))
        assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
        assert cfg.dataloader.train.batch_size == 2 and cfg.dataloader.train.num_workers == 4
        assert cfg.model.task_type == "res" and cfg.data.val.prefix == "val"
        assert cfg.data.val.dataset == "scanrefer" and not cfg.data.val.training and not cfg.data.val.aug
        cfg.model.data_root = cfg.data.val.data_root = "/home/songcl/data/data/"
        if val_config is None:
            val_config = copy.deepcopy(cfg.data.val)
        else:
            assert cfg.data.val == val_config, "Unmatched native VAL configurations"
        gorilla.set_random_seed(1999)
        model = importlib.import_module("framework.model.Quard_model." + spec["model"]).Network(**cfg.model)
        state = torch.load(spec["checkpoint"], map_location="cpu")["model"]
        extra = set(state) - set(model.state_dict())
        assert extra <= {"text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"}
        buffers = dict(model.named_buffers())
        assert all(name in buffers and torch.equal(state[name], buffers[name]) for name in extra)
        model.load_state_dict({name: value for name, value in state.items() if name not in extra}, strict=True)
        del state
        dataset = build_dataset(copy.deepcopy(cfg.data.val), logging.getLogger(condition))
        loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)
        model.cuda().eval()
        fine_partitions=[]
        def capture_fine(module,arguments,keywords,value):
            fine_partitions.append([ids.detach().cpu().clone() for ids in arguments[5][0]])
        observation=model.dec.cluster_att.register_forward_hook(capture_fine,with_kwargs=True)
        gorilla.set_random_seed(1999)
        records, pious, batches = [], [], []
        torch.cuda.reset_peak_memory_stats()
        start = time.monotonic()
        print("PAIRED_NATIVE_PROGRESS=" + json.dumps({"condition": condition, "batches_total": len(loader), "batches_done": 0}), flush=True)
        with torch.no_grad():
            for index, batch in enumerate(loader, 1):
                time_guard()
                fine_partitions.clear()
                prediction = model(batch, mode="predict")
                assert not prediction["nt_label"] and all(value.dtype == torch.float32 for value in prediction["piou"])
                before = fingerprint(prediction)
                exported, aggregate = export_prediction(prediction, batch, "val")
                assert before == fingerprint(prediction)
                assert aggregate == float(torch.stack(prediction["piou"]).cpu().numpy().mean())
                memberships=fine_partitions[-1] if fine_partitions else []
                masks=batch.get('gt_spmasks',[])
                for expression,record in enumerate(exported):
                    record['mixed_fine_leaf']=None
                    if expression>=len(masks) or not memberships:continue
                    ids=memberships[0 if len(memberships)==1 else expression].numpy().reshape(-1)
                    target=masks[expression].detach().cpu().numpy().reshape(-1)
                    if ids.shape!=target.shape or (ids<0).any() or not np.isin(target,[0,1]).all():continue
                    count=np.bincount(ids);positive=np.bincount(ids,weights=target,minlength=len(count))
                    record['mixed_fine_leaf']=bool(np.any((positive>0)&(positive<count)))
                    record['fine_partition_sha256']=hashlib.sha256(ids.tobytes()).hexdigest()
                records.extend(exported); pious.extend(prediction["piou"])
                batches.append({"index": index, "expressions": len(exported), "payload_sha256_before_after": before})
                if index % 50 == 0 or index == len(loader):
                    gpu()
                    print("PAIRED_NATIVE_PROGRESS=" + json.dumps({"condition": condition, "batches_done": index,
                          "batches_total": len(loader), "expressions": len(records), "elapsed_seconds": time.monotonic()-start}), flush=True)
        aggregate = float(torch.stack(pious).cpu().numpy().mean())
        assert aggregate == native_mean([record["piou"] for record in records])
        assert len(align_pairs(records, records)) == len(records) == manifest["expected_expressions"] == 9508
        assert digest(spec["checkpoint"]) == spec["checkpoint_sha256"]
        result = {"condition": condition, "observed_at": datetime.now(timezone.utc).isoformat(),
                  "checkpoint_sha256": spec["checkpoint_sha256"], "checkpoint_epoch": spec["epoch"],
                  "records": records, "batches": batches, "native_float32_miou": aggregate,
                  "unique_scenes": len({record["scene_id"] for record in records}),
                  "peak_inference_allocated_bytes": torch.cuda.max_memory_allocated(),
                  "native_forwards": len(batches), "optimizer_steps": 0, "elapsed_seconds": time.monotonic()-start,
                  "optional_subgroup_metadata": "predeclared mixed native fine leaf;GT read only after prediction;missing is null",
                  "scope": "Original full VAL fixed-checkpoint inference, not training RNG replay or whole-run training peak"}
        output = STAGE / (condition + ".json")
        assert not output.exists()
        output.write_text(json.dumps(result, indent=2, allow_nan=False))
        results[condition] = {"path": str(output), "sha256": digest(output),
                              "native_float32_miou": aggregate, "unique_scenes": result["unique_scenes"],
                              "expressions": len(records), "native_forwards": len(batches),
                              "elapsed_seconds": result["elapsed_seconds"]}
        print("PAIRED_NATIVE_CONDITION=" + json.dumps(results[condition]), flush=True)
        observation.remove()
        del model, prediction, batch, dataset, loader, records, pious, batches, exported
        torch.cuda.empty_cache()
    for relative, expected in manifest["source_hashes"].items():
        assert digest(ROOT / relative) == expected, relative
    index = {"passed": True, "observed_at": datetime.now(timezone.utc).isoformat(), "conditions": results,
             "initial_resources": initial, "last_resources": gpu(), "optimizer_steps": 0,
             "torch": torch.__version__, "scope": manifest["scope"]}
    (STAGE / "paired_candidate_capture_index.json").write_text(json.dumps(index, indent=2, allow_nan=False))
    print("PAIRED_NATIVE_RESULT=" + json.dumps(index), flush=True)
finally:
    for handle in reversed(locks):
        handle.close()
