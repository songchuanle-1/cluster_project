"""Exact binary-support IoU ceiling on unchanged native TRAIN partitions."""
from datetime import datetime, timezone
from fractions import Fraction
from functools import cmp_to_key
import hashlib
import itertools
import json
import logging
import os
from pathlib import Path
import random
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
CONFIG = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
TOKEN = "612469e22d634f7a971797ff5bd0342e"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_oracle(a, b):
    total = sum(a)
    assert total > 0

    def compare(i, j):
        cross = a[i] * b[j] - a[j] * b[i]
        return -1 if cross > 0 else (1 if cross < 0 else i - j)

    order = sorted((j for j in range(len(a)) if a[j] > 0),
                   key=cmp_to_key(compare))
    tp, fp, best, best_size = 0, 0, Fraction(0), 0
    # At optimal ratio r, every included support has a_j - r*b_j >= 0.
    for size, j in enumerate(order, 1):
        tp += a[j]
        fp += b[j]
        value = Fraction(tp, total + fp)
        if value > best:
            best, best_size = value, size
    selected = order[:best_size]
    return best, selected


def main():
    assert socket.gethostname() == "das"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    manifest_path = PIPE / "point_detail_population_20261009/result.manifest.json"
    source_path = ROOT / "framework/dataset/scannetv2.py"
    assert sha(manifest_path) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    assert sha(source_path) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    assert sha(CONFIG) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    manifest = json.loads(manifest_path.read_text())
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("support-oracle"))
    controls = {}
    for name, a, b, expected in (
        ("impure_merged", [1], [3], Fraction(1, 4)),
        ("perfect_partition", [4, 0], [0, 5], Fraction(1)),
        ("majority_suboptimal", [4, 4], [0, 5], Fraction(8, 13)),
    ):
        value, ids = exact_oracle(a, b)
        assert value == expected
        controls[name] = {"oracle": float(value), "selected": ids}
    rng = random.Random(1999)
    for _ in range(256):
        a = [rng.randrange(0, 8) for _ in range(7)]
        b = [rng.randrange(0, 8) for _ in range(7)]
        if not sum(a):
            a[0] = 1
        exhaustive = max(
            Fraction(sum(x * y for x, y in zip(a, bits)),
                     sum(a) + sum(x * y for x, y in zip(b, bits)))
            for bits in itertools.product((0, 1), repeat=len(a)))
        assert exact_oracle(a, b)[0] == exhaustive
    controls["brute_force"] = {"cases": 256, "exact_equal": True}

    trials = []
    for trial in range(2):
        gorilla.set_random_seed(1999)
        rows = []
        for scene in manifest:
            sample = dataset[int(scene["native_group"])]
            assert sample[1] == scene["scene"]
            sp = sample[5].numpy().astype(np.int64)
            counts = np.bincount(sp)
            expected = {int(x["ann_id"]): list(map(int, x["object_ids"]))
                        for x in scene["annotations"]}
            assert set(map(int, sample[0])) == set(expected)
            for aid, ids, p, s in zip(sample[0], sample[6], sample[7], sample[8]):
                aid = int(aid)
                assert list(map(int, ids)) == expected[aid]
                mask = p.numpy().astype(np.int64)
                a = np.bincount(sp, weights=mask, minlength=len(counts)).astype(np.int64)
                b = counts - a
                aa, bb = list(map(int, a)), list(map(int, b))
                oracle, chosen = exact_oracle(aa, bb)
                native = s.numpy().astype(bool)
                assert np.array_equal(native, a > b)
                majority = Fraction(int(a[native].sum()),
                                    int(mask.sum() + b[native].sum()))
                assert oracle >= majority
                digest = hashlib.sha256(
                    np.stack((a, b), axis=1).tobytes()).hexdigest()
                rows.append({
                    "scene": sample[1], "ann_id": aid, "object_ids": expected[aid],
                    "native_group": int(scene["native_group"]),
                    "target_points": int(mask.sum()), "superpoints": len(counts),
                    "mixed_supports": int(((a > 0) & (b > 0)).sum()),
                    "oracle_iou": float(oracle), "majority_iou": float(majority),
                    "oracle_gap": float(oracle - majority),
                    "below_half": oracle < Fraction(1, 2),
                    "selected_supports": chosen, "partition_sha256": digest,
                })
            print(json.dumps({"trial": trial, "groups_done": len(rows) // 4}),
                  flush=True)
        assert len(rows) == 128
        trials.append(rows)
    assert trials[0] == trials[1]
    rows = trials[0]
    result = {
        "contract": "exact_native_superpoint_union_ceiling_v1", "tick_token": TOKEN,
        "observed_at": datetime.now(timezone.utc).isoformat(), "hostname": socket.gethostname(),
        "cpu_only": True, "seed": 1999, "native_groups": len(manifest),
        "expressions": len(rows), "optimizer_steps": 0, "native_repeat_exact": True,
        "below_half_count": sum(r["below_half"] for r in rows),
        "below_half_scenes": len({r["scene"] for r in rows if r["below_half"]}),
        "min_oracle_iou": min(r["oracle_iou"] for r in rows),
        "mean_oracle_iou": sum(r["oracle_iou"] for r in rows) / len(rows),
        "positive_gap_count": sum(r["oracle_gap"] > 0 for r in rows),
        "max_gap": max(r["oracle_gap"] for r in rows),
        "controls": controls, "rows": rows, "script_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(manifest_path), "dataset_sha256": sha(source_path),
        "config_sha256": sha(CONFIG),
        "prediction_source_sha256": sha(ROOT / "framework/model/Quard_model/"
            "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/network.py"),
        "scope": "TRAIN oracle ceiling, not predicted masks, efficacy, novelty or full-model backward.",
    }
    output = PIPE / "superpoint_oracle_audit_20261012_1611.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "expressions", "below_half_count", "min_oracle_iou",
        "mean_oracle_iou", "positive_gap_count", "max_gap", "native_repeat_exact")}),
        flush=True)
    print(json.dumps({"output_sha256": sha(output)}), flush=True)


if __name__ == "__main__":
    main()
