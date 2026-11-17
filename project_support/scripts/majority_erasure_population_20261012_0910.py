"""Full unchanged TRAIN physical-target census with the native mask method."""
from collections import Counter, defaultdict
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


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    annotations_path = DATA / "scanrefer/ScanRefer_train_new.json"
    source_path = ROOT / "framework/dataset/scannetv2.py"
    assert sha(annotations_path) == "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
    assert sha(source_path) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    assert sha(CONFIG) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    annotations = json.loads(annotations_path.read_text())
    scenes = defaultdict(lambda: defaultdict(list))
    for ann in annotations:
        ids = ann["object_ids"] if "object_ids" in ann else [ann["object_id"]]
        ids = tuple(map(int, ids))
        assert len(ids) == 1
        scenes[ann["scene_id"]][ids].append(int(ann["ann_id"]))
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.data.train.data_root = str(DATA) + "/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("majority-population"))
    groups = {(row["scene_id"], int(row["ann_id"])): index
              for index, group in enumerate(dataset.scene_inputs) for row in group}
    physical_counts, annotation_counts = Counter(), Counter()
    inputs, missing, rows, incidents = [], [], [], []
    for number, scene in enumerate(sorted(scenes), 1):
        path = DATA / f"scannetv2/train/{scene}_refer.pth"
        if not path.is_file():
            missing.append({"scene": scene, "path": str(path)})
            for ids, aids in scenes[scene].items():
                physical_counts["missing_geometry"] += 1
                annotation_counts["missing_geometry"] += len(aids)
            continue
        _, _, sp, _, ins = torch.load(path, map_location="cpu", weights_only=False)
        _, sp = np.unique(sp, return_inverse=True)
        ins, sp = torch.as_tensor(ins).long(), torch.as_tensor(sp).long()
        inputs.append({"scene": scene, "path": str(path), "sha256": sha(path)})
        for ids, aids in sorted(scenes[scene].items()):
            point_mask, sp_mask = dataset.get_ref_mask(None, ins, sp, list(ids))
            positive_points, positive_sp = int(point_mask.sum()), int(sp_mask.sum())
            status = ("point_target_absent" if not positive_points else
                      ("majority_erased" if not positive_sp else "represented"))
            row = {"scene": scene, "object_ids": ids, "ann_ids": aids,
                   "positive_points": positive_points, "positive_superpoints": positive_sp,
                   "status": status}
            rows.append(row)
            physical_counts[status] += 1
            annotation_counts[status] += len(aids)
            if status != "represented":
                incidents.append(row)
        if number % 50 == 0:
            print(json.dumps({"scenes_done": number, "physical_counts": dict(physical_counts),
                              "annotation_counts": dict(annotation_counts)}), flush=True)
    native_incidents = []
    for incident in incidents:
        if incident["status"] != "majority_erased":
            continue
        aid = incident["ann_ids"][0]
        group = groups[incident["scene"], aid]
        gorilla.set_random_seed(1999)
        sample = dataset[group]
        index = list(map(int, sample[0])).index(aid)
        p, s = sample[7][index], sample[8][index]
        native_incidents.append({**incident, "native_group": group,
                                 "native_ann_id": aid, "native_positive_points": int(p.sum()),
                                 "native_positive_superpoints": int(s.sum())})
    result = {
        "contract": "native_majority_erasure_population_v1",
        "tick_token": "544cb1c4187542cd9ebe69d68351bd98",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "scenes": len(scenes), "annotation_total": len(annotations),
        "physical_counts": dict(physical_counts), "annotation_counts": dict(annotation_counts),
        "missing_geometry": missing, "incidents": incidents, "native_incidents": native_incidents,
        "physical_rows": rows, "input_geometry": inputs, "cpu_only": True,
        "annotations_sha256": sha(annotations_path), "dataset_sha256": sha(source_path),
        "config_sha256": sha(CONFIG), "script_sha256": sha(Path(__file__)),
        "scope": "Full original TRAIN raw target masks plus actual augmented erasure incidents; no model/optimizer/effectiveness claim.",
    }
    output = PIPE / "majority_erasure_population_20261012_0910.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"scenes": len(scenes), "physical_counts": dict(physical_counts),
                      "annotation_counts": dict(annotation_counts), "incidents": incidents[:8],
                      "native_incidents": native_incidents[:8], "output_sha256": sha(output)}),
          flush=True)


if __name__ == "__main__":
    main()
