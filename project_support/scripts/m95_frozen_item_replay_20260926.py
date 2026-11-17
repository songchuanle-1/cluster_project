"""Replay only the frozen M95 TRAIN loader to bind historical native items."""
import argparse
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

from frozen_capture_contract_20260916 import fingerprint, model_package_sha256
from native_manifest_capture_20260922 import load_manifest


MANIFEST_SHA256 = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
CONFIG_SHA256 = "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
CHECKPOINT_SHA256 = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
MODEL_SHA256 = "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0"
EXPECTED = {
    134: (9, 4332, "46643118212fbbabf71cfc396dddd1413178f84e03a072cced1ae813c9565dc0"),
    83: (3137, 3799, "a39cfebecda7333f23c3abcf9bdd0029bee13be070305a604d195397fdbc068c"),
    174: (2751, 8848, "a7bbf63a74172c28bfc0cb1076377cd66d0df9380516a2ebb4d1bbc4cc5449b7"),
}


class HashedDataset:
    def __init__(self, dataset, target_indices):
        self.dataset = dataset
        self.pending = []
        self.target_indices = target_indices

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        item = self.dataset[index]
        self.pending.append((
            index, fingerprint(item) if index in self.target_indices else None
        ))
        return item

    def collate_fn(self, items):
        return self.dataset.collate_fn(items)


def record_progress(path, payload):
    with path.open("a", encoding="ascii") as handle:
        handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "manifest", "checkpoint", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--progress", required=True)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--batch-dir")
    parser.add_argument("--save-batches", action="store_true")
    args = parser.parse_args()
    if args.save_batches and not args.batch_dir:
        raise ValueError("Batch directory is required when saving target batches")
    output = Path(args.output)
    progress = Path(args.progress)
    if output.exists() or progress.exists() or output == progress:
        raise ValueError("Output or progress already exists")
    if args.progress_every < 1:
        raise ValueError("Progress interval must be positive")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Authorized physical GPU7 required")
    root = Path(args.root).resolve()
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    import gorilla
    import torch
    from framework.dataset import build_dataset, build_dataloader

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    config = root / "configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml"
    if (sha256(config) != CONFIG_SHA256
            or sha256(args.checkpoint) != CHECKPOINT_SHA256
            or model_package_sha256(root, "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort") != MODEL_SHA256):
        raise ValueError("Frozen model identity differs")
    manifest = load_manifest(args.manifest, MANIFEST_SHA256)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    dataset = build_dataset(cfg.data.train, logging.getLogger("item_replay"))
    subset = HashedDataset(dataset, {row[1] for row in EXPECTED.values()})
    loader = build_dataloader(subset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    model = importlib.import_module(
        "framework.model.Quard_model."
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
    ).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()
    found = {}
    max_step = max(row[0] for row in EXPECTED.values())
    target_steps = {row[0]: key for key, row in EXPECTED.items()}
    if args.save_batches:
        batch_dir = Path(args.batch_dir)
        batch_dir.mkdir(parents=True, exist_ok=False)
    record_progress(progress, {
        "event": "started", "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_size": len(dataset), "checkpoint_sha256": CHECKPOINT_SHA256,
    })
    for step, batch in enumerate(loader):
        if step > max_step:
            break
        if len(subset.pending) != 2:
            raise ValueError("Expected exactly two transformed items per batch")
        if step in target_steps:
            key = target_steps[step]
            expected_step, dataset_index, frozen_sha = EXPECTED[key]
            index, digest = next(
                ((index, digest) for index, digest in subset.pending
                 if index == dataset_index), (None, None)
            )
            found[str(key)] = {
                "step": step,
                "dataset_index": index,
                "native_item_sha256": digest,
                "frozen_native_input_sha256": frozen_sha,
                "matches": digest == frozen_sha,
                "scan_ids": [str(value) for value in batch["scan_ids"]],
            }
            record_progress(progress, {
                "event": "target", "step": step, "manifest_index": key,
                "observed": found[str(key)],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            if args.save_batches:
                batch_path = batch_dir / ("step_%d_row_%d.pt" % (step, key))
                torch.save({
                    "contract": "m95_frozen_target_batch_v1",
                    "step": step,
                    "manifest_index": key,
                    "dataset_index": dataset_index,
                    "native_item_sha256": found[str(key)]["native_item_sha256"],
                    "frozen_native_input_sha256": found[str(key)][
                        "frozen_native_input_sha256"
                    ],
                    "scan_ids": found[str(key)]["scan_ids"],
                    "ann_ids": [int(value) for value in batch["ann_ids"]],
                    "batch": batch,
                }, batch_path)
                record_progress(progress, {
                    "event": "batch_saved", "step": step, "manifest_index": key,
                    "path": str(batch_path), "bytes": batch_path.stat().st_size,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            if key == 134 and not found[str(key)]["matches"]:
                raise ValueError("Early frozen item control differs; stop before full scan")
        elif step % args.progress_every == 0:
            record_progress(progress, {
                "event": "progress", "step": step,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        subset.pending.clear()
        gorilla.set_random_seed(1999)
    result = {
        "contract": "m95_frozen_loader_order_probe_v1",
        "manifest_sha256": MANIFEST_SHA256,
        "config_sha256": CONFIG_SHA256,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "model_source_sha256": MODEL_SHA256,
        "target_steps": {str(k): v[0] for k, v in EXPECTED.items()},
        "observed": found,
        "last_step": step,
        "native_item_binding": (
            "pass" if len(found) == len(EXPECTED)
            and all(row["matches"] for row in found.values()) else "fail"
        ),
        "admission": False,
    }
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                      encoding="ascii")
    record_progress(progress, {
        "event": "complete", "step": step, "binding": result["native_item_binding"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


if __name__ == "__main__":
    main()
