"""Full original TRAIN secondary/OTHER incidence; native mapper on remote CPU."""
import argparse
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    options = parser.parse_args()
    assert socket.gethostname() == "das" and os.environ["CUDA_VISIBLE_DEVICES"] == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    old_path = PIPE / "role_weight_audit_20261013_0908.json"
    assert sha(old_path) == "48d7a2243257a0287f4669a98dbd80ca4fbb982faa1da79143d6e143d796b5df"
    original = json.loads(old_path.read_text())
    paths = {
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "config": PIPE / "majority_erasure_original_config_20261012_0910.yaml",
    }
    for key, path in paths.items():
        assert sha(path) == original["source_and_data_sha256"][key]
    cfg = gorilla.Config.fromfile(str(paths["config"]))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("secondary-other-population"))
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    assert len(annotations) == 36665
    trials, examples = [], []
    for trial in (0, 1):
        gorilla.set_random_seed(1999)
        counts = Counter()
        scenes = {name: set() for name in ("modifier", "pronoun", "relation", "union")}
        digest = hashlib.sha256()
        current_examples = []
        for number, ann in enumerate(annotations, 1):
            scene, aid = ann["scene_id"], str(ann["ann_id"])
            values = dataset._get_token_positive_map_by_parse(graphs[scene][aid], None)
            other = values[4][0] > 0
            roles = {}
            for name, index in (("modifier", 2), ("pronoun", 3), ("relation", 6)):
                data = np.ascontiguousarray(values[index][:1])
                digest.update(data.tobytes())
                overlap = (data[0] > 0) & other
                tokens = np.flatnonzero(overlap).tolist()
                roles[name] = tokens
                counts[name + "_tokens"] += len(tokens)
                if tokens:
                    counts[name + "_expressions"] += 1
                    scenes[name].add(scene)
            digest.update(np.ascontiguousarray(values[4][:1]).tobytes())
            union = sorted(set(token for tokens in roles.values() for token in tokens))
            counts["union_tokens"] += len(union)
            if union:
                counts["union_expressions"] += 1
                scenes["union"].add(scene)
                current_examples.append({"scene": scene, "ann_id": int(aid),
                                         "roles": roles, "union_tokens": union})
            if number % 5000 == 0:
                print(json.dumps({"trial": trial, "processed": number,
                                  "union_expressions": counts["union_expressions"]}), flush=True)
        summary = {"counts": dict(counts), "scenes": {key: len(value) for key, value in scenes.items()},
                   "maps_sha256": digest.hexdigest(), "processed": len(annotations)}
        trials.append(summary)
        if trial == 0:
            examples = current_examples
        else:
            assert current_examples == examples
    assert trials[0] == trials[1]
    assert trials[0]["counts"]["relation_expressions"] == 220
    output = PIPE / ("native_secondary_population_" + options.token + ".json")
    result = {"tick_token": options.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "cpu_only": True, "seed": 1999,
              "input_shas": {key: sha(path) for key, path in paths.items()},
              "trials": trials, "repeat_exact": True, "examples": examples,
              "scope": "Original fullTRAIN native mapper incidence, not gradient signs, wrong labels, localization harm or admission."}
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "counts": trials[0]["counts"], "scenes": trials[0]["scenes"]}), flush=True)


if __name__ == "__main__":
    main()
