"""Read-only native TRAIN support census; never initializes CUDA."""
import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import sys
from datetime import datetime, timezone

os.environ.update(PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1",
                  HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
ROOT = Path("/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b")
DATA = Path("/home/songcl/data/data")
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
EXPECTED = {
    "hierarchy": "7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f",
    "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
    "annotation": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
    "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a",
}


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    assert socket.gethostname() == "dl04-MS-7E06"
    lease = json.loads(Path(sys.argv[1]).read_text())
    assert lease["project"] == "cluster_project"
    assert lease["thread_id"] == "01a04987-fdbe-7301-b2f0-f9b6ab60f74c"
    remaining = (datetime.fromisoformat(lease["deadline_at"])
                 - datetime.now(timezone.utc)).total_seconds()
    assert remaining > 300
    signal.alarm(min(1200, int(remaining) - 180))
    protocol_path = Path(__file__).with_name("resolution_protocol.json")
    assert sha(protocol_path) == lease["protocol_sha256"]
    protocol = json.loads(protocol_path.read_text())
    assert protocol["runner"]["sha256"] == sha(__file__)
    paths = {
        "hierarchy": ROOT / "framework/model/Quard_model" / NAME / "hier_postprocess.py",
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "annotation": DATA / "scanrefer/ScanRefer_train_new.json",
        "config": ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml"),
    }
    before = {key: sha(path) for key, path in paths.items()}
    assert before == EXPECTED, before
    import torch
    import numpy as np
    import yaml
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized()
    config = yaml.safe_load(paths["config"].read_text())
    sizes = config["model"]["dec"]["cluster_layer_nums"]
    maximum = config["data"]["train"]["voxel_cfg"]["max_npoint"]
    assert sizes == [256, 64, 8] and maximum == 2500000
    tree = ast.parse(paths["hierarchy"].read_text())
    partitioner = next(node for node in tree.body
                       if isinstance(node, ast.ClassDef)
                       and node.name == "PointCloudPartitioner")
    forward = next(node for node in partitioner.body
                   if isinstance(node, ast.FunctionDef) and node.name == "forward")
    clamp = next(node for node in forward.body
                 if isinstance(node, ast.Assign)
                 and any(ast.unparse(target) == "layer_nums[0]" for target in node.targets))
    code = compile(ast.Expression(body=clamp.value), str(paths["hierarchy"]), "eval")

    def resolution(lengths):
        return eval(code, {"__builtins__": {"min": min}},
                    {"layer_nums": list(sizes), "lens": list(lengths)})

    controls = {
        "large_peer": resolution([300, 500]),
        "small_peer": resolution([300, 100]),
        "row_order": resolution([500, 300]),
        "same_valid_support_extra_padding": resolution([300, 500]),
    }
    assert controls == {"large_peer": 256, "small_peer": 100,
                        "row_order": 256, "same_valid_support_extra_padding": 256}
    annotations = json.loads(paths["annotation"].read_text())
    scenes = sorted({row["scene_id"] for row in annotations})
    records = []
    failures = []
    for scene in scenes:
        path = DATA / "scannetv2/train" / (scene + "_refer.pth")
        try:
            stamp = path.stat()
            payload = torch.load(path, map_location="cpu", weights_only=False)
            assert isinstance(payload, (tuple, list)) and len(payload) == 5
            xyz, _, superpoints, _, _ = payload
            superpoints = np.asarray(superpoints)
            points = len(xyz)
            assert len(superpoints) == points and points > 0
            count = int(np.unique(superpoints).size)
            end = path.stat()
            assert (stamp.st_size, stamp.st_mtime_ns) == (end.st_size, end.st_mtime_ns)
            records.append({
                "scene_id": scene, "points": points,
                "raw_superpoints": count,
                "native_train_all_points_retained": points <= maximum,
                "exact_train_support_count": count if points <= maximum else None,
                "raw_file_bytes": stamp.st_size, "raw_file_mtime_ns": stamp.st_mtime_ns,
                "scene_content_sha256": sha(path),
            })
            del payload, xyz, superpoints
        except Exception as error:
            failures.append({"scene_id": scene, "error_type": type(error).__name__,
                             "error": str(error)})
    after = {key: sha(path) for key, path in paths.items()}
    assert before == after
    exact = [row for row in records if row["exact_train_support_count"] is not None]
    small = [row for row in exact if row["exact_train_support_count"] < sizes[0]]
    unknown = [row["scene_id"] for row in records
               if row["exact_train_support_count"] is None]
    result = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "execution_completed": True, "project": lease["project"],
        "token": lease["token"], "protocol_sha256": lease["protocol_sha256"],
        "hostname": socket.gethostname(), "asset_hashes": before,
        "clamp_source": ast.unparse(clamp), "source_controls": controls,
        "train_annotation_rows": len(annotations), "expected_train_scenes": len(scenes),
        "loaded_train_scenes": len(records), "exact_support_scenes": len(exact),
        "minimum_exact_support": min((row["exact_train_support_count"] for row in exact),
                                     default=None),
        "maximum_points": max((row["points"] for row in records), default=None),
        "small_scene_count": len(small), "small_scene_ids": [row["scene_id"] for row in small],
        "sampling_unknown_scenes": unknown, "failures": failures, "records": records,
        "cuda_initialized": torch.cuda.is_initialized(), "new_training": 0,
        "scientific_admission": False,
        "scope": "Native TRAIN support-incidence only; not trained efficacy, geometry robustness, or attention novelty.",
    }
    assert not result["cuda_initialized"]
    output = Path(__file__).with_name("native_resolution_result.json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({key: value for key, value in result.items() if key != "records"}))


if __name__ == "__main__":
    main()
