"""Original native coordinate transport and protection-primitive audit, CPU only."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import socket
import sys
import types
from unittest.mock import patch

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
CONFIG = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
PRIMARY = PIPE / "butd_joint_dataset_source_20261012_1319.py"
RELS = ("front", "behind", "back", "left", "right", "facing",
        "leftmost", "rightmost", "looking", "across")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proposed_permit(text):
    return not any(" " + rel + " " in text + " " for rel in RELS)


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
    paths = {
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "manifest": PIPE / "point_detail_population_20261009/result.manifest.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "config": CONFIG, "primary_source": PRIMARY,
    }
    expected = {
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "manifest": "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a",
        "primary_source": "6bf22712dc98ee2635ad36c552efeA34fb885cdf3d3570a4a2fe1b851db8a0a9".lower(),
    }
    hashes = {key: sha(path) for key, path in paths.items()}
    assert hashes == expected
    primary_tree = ast.parse(PRIMARY.read_text())
    primary_method = next(node for node in ast.walk(primary_tree)
                          if isinstance(node, ast.FunctionDef) and node.name == "_augment_nr3d")
    primary_method.decorator_list = []
    ns = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[primary_method], type_ignores=[])),
                 str(PRIMARY), "exec"), ns)
    official_permit = ns["_augment_nr3d"]
    graph = json.loads(paths["graphs"].read_text())
    annotations = json.loads(paths["annotations"].read_text())
    manifest = json.loads(paths["manifest"].read_text())
    counts, examples = Counter(), []
    for ann in annotations:
        text = graph[ann["scene_id"]][str(ann["ann_id"])]["utterance"]
        official, proposed = official_permit(text), proposed_permit(text)
        counts["annotations"] += 1
        counts["protected_by_original_predicate"] += int(not official)
        counts["predicate_mismatch"] += int(official != proposed)
        if not official and len(examples) < 8:
            examples.append({"scene": ann["scene_id"], "ann_id": ann["ann_id"],
                             "utterance": text})
    controls = {}
    for text in ("the chair on the left of the table", "the chair beside the table"):
        controls[text] = {"official_permit": official_permit(text),
                          "proposed_permit": proposed_permit(text)}
    assert not controls["the chair on the left of the table"]["official_permit"]
    assert controls["the chair beside the table"]["official_permit"]
    assert counts["predicate_mismatch"] == 0
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.aug and cfg.data.train.with_elastic
    dataset = build_dataset(cfg.data.train, logging.getLogger("directional-audit"))
    original_aug = dataset.data_aug
    basis = np.eye(3)
    controls["native_identity"] = original_aug(basis, False, False, False).tolist()
    with patch("numpy.random.randint", return_value=0):
        controls["native_x_reflection"] = original_aug(basis, False, True, False).tolist()
    assert np.array_equal(np.array(controls["native_identity"]), basis)
    assert np.array_equal(np.array(controls["native_x_reflection"]), np.diag([-1., 1., 1.]))
    traces, rows, inputs = [], [], []

    def traced(self, xyz, jitter=False, flip=False, rot=False):
        out = original_aug(xyz, jitter, flip, rot)
        idx = np.arange(min(len(xyz), 2048))
        matrix = np.linalg.lstsq(xyz[idx].astype(np.float64), out[idx], rcond=None)[0]
        residual = float(np.abs(xyz[idx] @ matrix - out[idx]).max())
        traces.append({"jitter": jitter, "flip": flip, "rot": rot,
                       "matrix": matrix.tolist(), "det": float(np.linalg.det(matrix)),
                       "fit_residual": residual})
        assert residual < 1e-8
        return out

    dataset.data_aug = types.MethodType(traced, dataset)
    gorilla.set_random_seed(1999)
    for scene in manifest:
        before = len(traces)
        sample = dataset[int(scene["native_group"])]
        assert sample[1] == scene["scene"] and len(traces) == before + 1
        expected_ids = {int(a["ann_id"]) for a in scene["annotations"]}
        assert set(map(int, sample[0])) == expected_ids
        trace = traces[-1]
        path = DATA / f"scannetv2/train/{scene['scene']}_refer.pth"
        inputs.append({"scene": scene["scene"], "path": str(path), "sha256": sha(path)})
        for aid, text, view_dep in zip(sample[0], sample[10], sample[14]):
            original_text = graph[scene["scene"]][str(aid)]["utterance"]
            assert text == " ".join(original_text.replace(",", " ,").split()) + " . not mentioned"
            rows.append({"scene": scene["scene"], "ann_id": int(aid),
                         "protected_by_original_predicate": not official_permit(original_text),
                         "view_dependent": view_dep,
                         "native_jitter": trace["jitter"], "native_flip": trace["flip"],
                         "native_rot": trace["rot"], "native_det": trace["det"]})
    assert len(rows) == 128 and len(traces) == 32
    summary = {
        "native_groups": len(traces), "native_expressions": len(rows),
        "directional_expressions": sum(r["protected_by_original_predicate"] for r in rows),
        "directional_reflected": sum(r["protected_by_original_predicate"] and r["native_det"] < 0
                                      for r in rows),
        "all_groups_augmented": all(t["jitter"] and t["flip"] and t["rot"] for t in traces),
        "all_view_flags_none": all(r["view_dependent"] is None for r in rows),
    }
    result = {
        "contract": "native_directional_augmentation_v1",
        "tick_token": "8e65b0e186784f1ca037a3d81231f738",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "counts": dict(counts), "summary": summary, "controls": controls,
        "examples": examples, "rows": rows, "transforms": traces, "native_inputs": inputs,
        "input_hashes": hashes, "script_sha256": sha(Path(__file__)),
        "primary_url": "https://raw.githubusercontent.com/nickgkan/butd_detr/main/src/joint_det_dataset.py",
        "scope": "Transport and lexical incidence; coordinates/camera semantics and actual task harm are not certified. Predicate equality and prior protection primitive, not whole-model equivalence or efficacy.",
    }
    output = PIPE / "directional_augmentation_audit_20261012_1319.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": dict(counts), "summary": summary,
                      "controls": controls, "examples": examples[:2],
                      "output_sha256": sha(output)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
