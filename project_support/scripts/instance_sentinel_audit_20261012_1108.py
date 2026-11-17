"""Native target-ID/sentinel contract, remote CPU only, no model mutation."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    from framework.dataset.scannetv2 import ScanNetDataset_sample_graph_edge
    torch.set_num_threads(1)
    paths = {
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "manifest": PIPE / "point_detail_population_20261009/result.manifest.json",
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "criterion": ROOT / f"framework/model/Quard_model/{NAME}/loss.py",
    }
    expected = {
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "manifest": "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "criterion": "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5",
    }
    hashes = {key: sha(path) for key, path in paths.items()}
    assert hashes == expected
    annotations = json.loads(paths["annotations"].read_text())
    manifest = json.loads(paths["manifest"].read_text())
    target_ids = []
    collisions = []
    for row in annotations:
        ids = row["object_ids"] if "object_ids" in row else [row["object_id"]]
        ids = list(map(int, ids))
        target_ids.extend(ids)
        if 199 in ids:
            collisions.append({"scene": row["scene_id"], "ann_id": int(row["ann_id"]),
                               "object_ids": ids})
    frozen = [int(oid) for row in manifest for ann in row["annotations"]
              for oid in ann["object_ids"]]
    dataset = ScanNetDataset_sample_graph_edge.__new__(ScanNetDataset_sample_graph_edge)
    synthetic_ins = torch.tensor([17, 23, 17, 17], dtype=torch.long)
    synthetic_sp = torch.tensor([0, 0, 1, 1], dtype=torch.long)
    native_labels, _ = dataset.get_sp_label(
        synthetic_sp, synthetic_ins, torch.full_like(synthetic_ins, -1))
    assert native_labels.tolist() == [199.0, 17.0]
    tree = ast.parse(paths["criterion"].read_text())
    expressions = [node.value for node in ast.walk(tree)
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "masks"
                           for target in node.targets)
                   and isinstance(node.value, ast.Call)
                   and ast.unparse(node.value) == "torch.stack([sp_ins_labels[b] == obj_id for obj_id in obj_ids])"]
    assert len(expressions) == 1
    code = compile(ast.Expression(body=expressions[0]), str(paths["criterion"]), "eval")

    def criterion_masks(labels, ids):
        return eval(code, {"torch": torch, "sp_ins_labels": [labels],
                           "b": 0, "obj_ids": ids})

    controls = {
        "native_unassigned_labels": native_labels.tolist(),
        "counterfactual_target199": criterion_masks(native_labels, [199]).tolist(),
        "present_target17": criterion_masks(native_labels, [17]).tolist(),
        "absent_target23": criterion_masks(native_labels, [23]).tolist(),
        "shifted_sentinel_control": criterion_masks(
            torch.where(native_labels == 199, 198, native_labels), [199]).tolist(),
    }
    assert controls["counterfactual_target199"] == [[True, False]]
    assert controls["present_target17"] == [[False, True]]
    assert controls["absent_target23"] == [[False, False]]
    assert controls["shifted_sentinel_control"] == [[False, False]]
    actual_scene_controls = []
    for scene in sorted({row["scene"] for row in collisions}):
        path = DATA / f"scannetv2/train/{scene}_refer.pth"
        _, _, sp, sem, ins = torch.load(path, map_location="cpu", weights_only=False)
        _, sp = np.unique(sp, return_inverse=True)
        sp, sem, ins = map(torch.as_tensor, (sp, sem, ins))
        labels, _ = dataset.get_sp_label(sp.long(), ins.long(), sem.long())
        point_mask, target_mask = dataset.get_ref_mask(None, ins.long(), sp.long(), [199])
        native_mask = criterion_masks(labels, [199])[0]
        actual_scene_controls.append({
            "scene": scene, "geometry_sha256": sha(path),
            "target_points": int(point_mask.sum()), "positive_target_supports": int(target_mask.sum()),
            "criterion_supports": int(native_mask.sum()),
            "false_positive_supports": int((native_mask & ~target_mask.bool()).sum()),
        })
    result = {
        "contract": "native_instance_sentinel_collision_v1",
        "tick_token": "63db8202cf55406f8f29e19f14229f70",
        "observed_at": datetime.now(timezone.utc).isoformat(), "cpu_only": True,
        "annotations": len(annotations), "target_id_count": len(target_ids),
        "target_id_min": min(target_ids), "target_id_max": max(target_ids),
        "distinct_target_ids": len(set(target_ids)),
        "target199_annotations": len(collisions),
        "frozen_target_ids": len(frozen), "frozen_target199": frozen.count(199),
        "native_sentinel": 199, "controls": controls,
        "actual_collision_annotations": collisions, "actual_scene_controls": actual_scene_controls,
        "input_hashes": hashes, "script_sha256": sha(Path(__file__)),
        "scope": "Actual target collision prerequisite and native code sensitivity; no full model/backward/resource/efficacy claim.",
    }
    output = PIPE / "instance_sentinel_audit_20261012_1108.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("input_hashes", "actual_collision_annotations")},
                     indent=2), flush=True)
    print(json.dumps({"output_sha256": sha(output)}), flush=True)


if __name__ == "__main__":
    main()
