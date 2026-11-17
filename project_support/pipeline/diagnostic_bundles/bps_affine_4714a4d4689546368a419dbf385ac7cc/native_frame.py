"""Capture actual native dataset frames, without changing returned inputs."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
import torch

torch.set_num_threads(2)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tensor_hash(tensor):
    return hashlib.sha256(tensor.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    root = Path(args.code_root)
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    from framework.dataset import build_dataset

    source = root / "framework/dataset/scannetv2.py"
    assert digest(source) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    cfg = gorilla.Config.fromfile(str(root / args.config))
    logger = logging.getLogger("bps_native_frame")
    logger.addHandler(logging.NullHandler())
    dataset = build_dataset(cfg.data.train, logger)
    selected = json.loads(Path(args.selection).read_text())["cases"]
    desired = {}
    for case in selected:
        desired.setdefault(case["scene"], set()).add(case["ann_id"])
    indices = {}
    for i, group in enumerate(dataset.scene_inputs):
        scene = group[0]["scene_id"]
        if scene in desired and {int(r["ann_id"]) for r in group} == desired[scene]:
            assert scene not in indices
            indices[scene] = i
    assert set(indices) == set(desired), "Frozen native group unavailable"
    package = root / "framework/model/Quard_model" / (
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps/between_support.py")
    assert digest(package) == "18e2a35e3df74c2823b2af36457dbbb7944c3b3697616f480b234d172797ce74"
    spec = importlib.util.spec_from_file_location("native_frame_bps", package)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    catalog = module.BetweenSupportCatalog(cfg.model.between_catalog,
                                           cfg.model.between_catalog_sha256)
    original = dataset.data_aug
    frames = []

    def capture(xyz, jitter=False, flip=False, rot=False):
        before = np.random.get_state()
        output = original(xyz, jitter, flip, rot)
        after = np.random.get_state()
        np.random.set_state(before)
        matrix = original(np.eye(3), jitter, flip, rot)
        np.random.set_state(after)
        assert np.array_equal(output, xyz @ matrix)
        frames.append(dict(raw=np.asarray(xyz).copy(), matrix=matrix.copy()))
        return output

    dataset.data_aug = capture
    gorilla.set_random_seed(1999)
    rows = []
    for scene in sorted(indices):
        before = len(frames)
        item = dataset[indices[scene]]
        assert len(frames) == before + 1
        frame = frames[-1]
        ann_ids, scan, coord, coord_float, feat, sp, objects, gt_points, gt_supports = item[:9]
        labels = item[11]
        assert scan == scene and set(map(int, ann_ids)) == desired[scene]
        aligned = len(coord_float) == len(frame["raw"])
        transported = torch.as_tensor(frame["raw"] @ frame["matrix"]).float()
        exact = torch.equal(coord_float, transported) if aligned else None
        if aligned:
            assert exact
        offsets = torch.tensor([0, len(labels)])
        support = catalog.prepare(ann_ids, [scene], [len(ann_ids)], objects, sp,
                                  coord_float, offsets, [labels])
        rows.append(dict(scene=scene, native_group_index=indices[scene],
                         ann_ids=list(map(int, ann_ids)), matrix=frame["matrix"].tolist(),
                         singular_values=np.linalg.svd(frame["matrix"])[1].tolist(),
                         points=len(coord_float), raw_points=len(frame["raw"]),
                         supports=len(labels), point_alignment_available=aligned,
                         original_aug_return_exact=True, coords_float_transport_exact=exact,
                         coords_sha256=tensor_hash(coord_float),
                         instance_support_sha256=tensor_hash(labels),
                         gt_support_sha256=[tensor_hash(gt) for gt in gt_supports],
                         gt_positive_support_counts=[int(gt.sum()) for gt in gt_supports],
                         available_events=[len(s["costs"]) for s in support],
                         readout=catalog.last_readout))
        print("completed " + scene, flush=True)
    result = dict(token=args.token, remote_observed_at=datetime.datetime.now(
                  datetime.timezone.utc).isoformat(), script_sha256=digest(__file__),
                  source_sha256=digest(source), selection_sha256=digest(args.selection),
                  rows=rows, cuda_visible_devices=os.environ["CUDA_VISIBLE_DEVICES"],
                  cpu_threads=torch.get_num_threads(),
                  scope="Native __getitem__ frame/instance/GT transport only; no collation, "
                        "model output, gradient, optimizer, trained task harm or novelty.")
    destination = Path(args.output)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(destination)
    print(json.dumps(dict(groups=len(rows), expressions=sum(len(r["ann_ids"]) for r in rows),
                          output=str(destination), sha256=digest(destination))), flush=True)


if __name__ == "__main__":
    main()
