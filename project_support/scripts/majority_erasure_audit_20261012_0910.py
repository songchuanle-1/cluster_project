"""Original native target-mask quantization, remote CPU, no model or optimizer."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
CONFIG = PIPE / "majority_erasure_original_config_20261012_0910.yaml"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mask_hash(mask):
    return hashlib.sha256(mask.contiguous().numpy().tobytes()).hexdigest()


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
    assert cfg.data.train.aug and cfg.data.train.with_elastic
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("majority-erasure"))

    def summarize(p, s):
        points, supports = int(p.sum()), int(s.sum())
        return {"positive_points": points, "positive_superpoints": supports,
                "status": "point_target_absent" if not points else
                ("majority_erased" if not supports else "represented"),
                "point_mask_sha256": mask_hash(p), "superpoint_mask_sha256": mask_hash(s)}

    def evaluate(ins, sp, ids):
        p, s = dataset.get_ref_mask(None, ins.long(), sp.long(), ids)
        return summarize(p, s)

    controls = {}
    for name, ins, ids, expected in (
        ("singleton_identity", [17, 17, 17], [17], (3, 1)),
        ("absent_identity", [17, 17, 17], [23], (0, 0)),
        ("tie_erased", [17, 23], [17], (1, 0)),
        ("majority_retained", [17, 17, 23], [17], (2, 1)),
    ):
        result = evaluate(torch.tensor(ins), torch.zeros(len(ins)), ids)
        assert (result["positive_points"], result["positive_superpoints"]) == expected
        controls[name] = result
    raw, inputs = [], []
    for scene in manifest:
        path = DATA / f"scannetv2/train/{scene['scene']}_refer.pth"
        _, _, sp, _, ins = torch.load(path, map_location="cpu", weights_only=False)
        _, sp = np.unique(sp, return_inverse=True)
        ins, sp = torch.as_tensor(ins), torch.as_tensor(sp)
        inputs.append({"scene": scene["scene"], "sha256": sha(path), "path": str(path)})
        for ann in scene["annotations"]:
            raw.append({"scene": scene["scene"], "ann_id": int(ann["ann_id"]),
                        "object_ids": list(map(int, ann["object_ids"])),
                        **evaluate(ins, sp, list(map(int, ann["object_ids"])))})
    trials = []
    for trial in (0, 1):
        gorilla.set_random_seed(1999)
        rows = []
        for scene in manifest:
            group = int(scene["native_group"])
            sample = dataset[group]
            assert sample[1] == scene["scene"]
            expected = {int(a["ann_id"]): list(map(int, a["object_ids"]))
                        for a in scene["annotations"]}
            assert set(map(int, sample[0])) == set(expected)
            for aid, ids, p, s in zip(sample[0], sample[6], sample[7], sample[8]):
                aid, ids = int(aid), list(map(int, ids))
                assert ids == expected[aid]
                result = summarize(p, s)
                rows.append({"scene": sample[1], "ann_id": aid, "native_group": group,
                             "object_ids": ids, **result})
            print(json.dumps({"trial": trial, "groups_done": len(rows) // 4,
                              "expressions": len(rows)}), flush=True)
        assert len(rows) == 128
        trials.append(rows)
    assert trials[0] == trials[1]
    result = {
        "contract": "native_majority_erasure_v1", "tick_token": "544cb1c4187542cd9ebe69d68351bd98",
        "observed_at": datetime.now(timezone.utc).isoformat(), "hostname": socket.gethostname(),
        "cpu_only": True, "seed": 1999, "optimizer_steps": 0,
        "raw_counts": dict(Counter(row["status"] for row in raw)),
        "native_counts": dict(Counter(row["status"] for row in trials[0])),
        "native_repeat_exact": True, "native_groups": len(manifest),
        "expressions": len(trials[0]), "controls": controls,
        "raw_rows": raw, "native_rows": trials[0], "native_inputs": inputs,
        "manifest_sha256": sha(manifest_path), "dataset_sha256": sha(source_path),
        "config_sha256": sha(CONFIG), "script_sha256": sha(Path(__file__)),
        "scope": "Complete erasure incidence on frozen TRAIN cohort; not full-population prevalence, backward certification, resources or efficacy.",
    }
    output = PIPE / "majority_erasure_audit_20261012_0910.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"raw_counts": result["raw_counts"], "native_counts": result["native_counts"],
                      "repeat_exact": True, "output_sha256": sha(output)}), flush=True)


if __name__ == "__main__":
    main()
