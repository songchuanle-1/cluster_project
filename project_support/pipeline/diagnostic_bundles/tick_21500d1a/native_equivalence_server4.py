"""Fixed-TRAIN exporter equivalence; never training or paired model efficacy."""
import os
os.environ.update(CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES="0",
                  HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="1",
                  PYTHONDONTWRITEBYTECODE="1")
import argparse
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
import logging
from pathlib import Path
import signal
import socket
import subprocess
import sys

signal.alarm(300)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--deadline", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text())
    assert socket.gethostname() == manifest["hostname"] == "dl04-MS-7E06"
    assert manifest["physical_gpu"] == 0
    root, checkpoint = Path(manifest["root"]), Path(manifest["checkpoint"])
    stage = root.parent / "pipeline/evidence_producer_21500d1a"
    output = Path(args.output).resolve()
    output.relative_to(stage.resolve())
    assert not output.exists()
    deadline = datetime.fromisoformat(args.deadline)
    assert (deadline - datetime.now(timezone.utc)).total_seconds() > 360

    def time_guard():
        assert (deadline - datetime.now(timezone.utc)).total_seconds() > 90

    def resources():
        row = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu",
                                       "--format=csv,noheader,nounits"], universal_newlines=True, timeout=10).strip()
        cells = [value.strip() for value in row.split(",")]
        assert cells[:2] == ["0", manifest["gpu_uuid"]]
        contexts = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-compute-apps=pid,used_memory",
                                             "--format=csv,noheader,nounits"], universal_newlines=True, timeout=10).strip()
        own = 0
        for line in contexts.splitlines():
            pid, used = [int(value.strip()) for value in line.split(",")]
            assert pid == os.getpid(), "Other GPU context; never evict or overlap"
            own += used
        assert int(cells[5]) < 10 or own > 0
        assert int(cells[4]) + own >= int(cells[2]) - 1024
        return {"gpu": row, "contexts": contexts}

    time_guard()
    initial = resources()
    assert not initial["contexts"]
    locks = []
    try:
        for path in manifest["lifetime_locks"]:
            handle = open(path, "a+b")
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locks.append(handle)
        resources()
        for relative, expected in manifest["source_hashes"].items():
            assert digest(root / relative) == expected, relative
        assert digest(checkpoint) == manifest["checkpoint_sha256"]
        for name, expected in manifest["producer_hashes"].items():
            assert digest(Path(__file__).parent / name) == expected, name
        sys.path[:0] = [str(root), str(root / "framework/lib")]
        from tools import train as native_train
        import torch
        import gorilla
        from framework.dataset import build_dataset
        from torch.utils.data import DataLoader, Subset
        from aligned_evidence import align_pairs, export_prediction, native_mean
        torch.set_num_threads(1)
        cfg = gorilla.Config.fromfile(str(root / manifest["config"]))
        assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
        assert cfg.dataloader.train.batch_size == 2 and cfg.dataloader.train.num_workers == 4
        assert cfg.model.task_type == "res" and cfg.data.train.dataset == "scanrefer"
        cfg.model.data_root = cfg.data.train.data_root = "/home/songcl/data/data/"
        gorilla.set_random_seed(1999)
        model = importlib.import_module("framework.model.Quard_model." + manifest["model"]).Network(**cfg.model)
        state = torch.load(checkpoint, map_location="cpu")["model"]
        extra = set(state) - set(model.state_dict())
        assert extra <= {"text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"}
        buffers = dict(model.named_buffers())
        assert all(name in buffers and torch.equal(state[name], buffers[name]) for name in extra)
        model.load_state_dict({name: value for name, value in state.items() if name not in extra}, strict=True)
        del state
        dataset = build_dataset(cfg.data.train, logging.getLogger("native-evidence-equivalence"))
        loader = DataLoader(Subset(dataset, manifest["train_groups"]), batch_size=1, shuffle=False,
                            num_workers=0, collate_fn=dataset.collate_fn)
        torch.cuda.set_per_process_memory_fraction(.25, 0)
        model.cuda().eval()

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
                elif isinstance(obj, (tuple, list)):
                    h.update(str(len(obj)).encode())
                    for item in obj: feed(item)
                else:
                    h.update(repr(obj).encode())
            feed(value)
            return h.hexdigest()

        records, pious, batches = [], [], []
        torch.cuda.reset_peak_memory_stats()
        with torch.no_grad():
            for group, batch in zip(manifest["train_groups"], loader):
                time_guard(); resources()
                prediction = model(copy.deepcopy(batch), mode="predict")
                assert not prediction["nt_label"], "Not the frozen ScanRefer/res branch"
                assert all(value.dtype == torch.float32 for value in prediction["piou"])
                before = fingerprint(prediction)
                exported, aggregate = export_prediction(prediction, batch, "train")
                assert fingerprint(prediction) == before
                reference = float(torch.stack(prediction["piou"]).cpu().numpy().mean())
                assert aggregate == reference
                records.extend(exported); pious.extend(prediction["piou"])
                batches.append({"group": group, "expressions": len(exported),
                                "native_mean": reference, "exported_mean": aggregate,
                                "payload_sha256_before_after": before})
        assert len(batches) == len(manifest["train_groups"]) == 4
        native = float(torch.stack(pious).cpu().numpy().mean())
        restored = json.loads(json.dumps(records, allow_nan=False))
        assert native == native_mean([record["piou"] for record in restored])
        assert len(align_pairs(records, list(reversed(restored)))) == len(records)
        assert digest(checkpoint) == manifest["checkpoint_sha256"]
        result = {"passed": True, "observed_at": datetime.now(timezone.utc).isoformat(),
                  "native_forwards": len(batches), "optimizer_steps": 0,
                  "checkpoint_sha256": manifest["checkpoint_sha256"], "batches": batches,
                  "records": records, "native_mean": native, "exported_mean": native,
                  "unique_scenes": len({record["scene_id"] for record in records}),
                  "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                  "initial_resource_observation": initial, "last_resource_observation": resources(),
                  "scope": "Unchanged M95 software-equivalence TRAIN diagnostic, not HDS efficacy or whole-run memory"}
        output.write_text(json.dumps(result, indent=2, allow_nan=False))
        print("NATIVE_EVIDENCE_RESULT=" + json.dumps({key: value for key, value in result.items() if key not in ("records", "batches")}))
    finally:
        for handle in reversed(locks):
            handle.close()


if __name__ == "__main__":
    main()
