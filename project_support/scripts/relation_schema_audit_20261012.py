"""Bounded remote CPU schema audit of frozen native TRAIN inputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = {
        "manifest": PIPE / "point_detail_population_20261009/result.manifest.json",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "loss": ROOT / f"framework/model/Quard_model/{NAME}/loss.py",
    }
    expected = {
        "manifest": "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
    }
    hashes = {k: sha(p) for k, p in paths.items()}
    assert all(hashes[k] == v for k, v in expected.items())
    manifest = json.loads(paths["manifest"].read_text())
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    samples = []
    for row in manifest[:2]:
        for a in row["annotations"][:2]:
            source = next(v for v in annotations if v["scene_id"] == row["scene"]
                          and int(v["ann_id"]) == int(a["ann_id"]))
            graph = graphs[row["scene"]][str(a["ann_id"])]
            samples.append({"frozen": a, "scene": row["scene"],
                            "annotation": source, "graph": graph})
    result = {
        "contract": "relation_schema_audit_v1",
        "frozen_scene_count": len(manifest),
        "frozen_expression_count": sum(len(r["annotations"]) for r in manifest),
        "annotation_count": len(annotations),
        "input_hashes": hashes, "samples": samples,
        "script_sha256": sha(Path(__file__)),
        "cpu_only": True, "admission": False,
    }
    output = PIPE / "relation_schema_audit_20261012.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
