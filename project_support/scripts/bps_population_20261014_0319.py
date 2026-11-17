"""Prediction-blind native SP-majority coverage for all stored TRAIN events."""
import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import time

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
TOKEN = "1d59938f077948578e91e2cf34fc9d53"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    assert args.token == TOKEN and socket.gethostname() == "das"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    import numpy as np
    import torch
    import torch_scatter
    torch.set_num_threads(1)
    source = ROOT / "framework/dataset/scannetv2.py"
    assert sha(source) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    function = next(n for n in ast.walk(ast.parse(source.read_text()))
                    if isinstance(n, ast.FunctionDef) and n.name == "get_sp_label")
    namespace = {"torch": torch, "torch_scatter": torch_scatter}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                 str(source), "exec"), namespace)
    get_sp_label = namespace["get_sp_label"]
    package = PIPE / ("bps_staging_" + TOKEN) / NAME
    manifest = json.loads((package.parent / "source_manifest.json").read_text())
    assert sha(package / "between_support.py") == manifest["package"]["between_support.py"]
    spec = importlib.util.spec_from_file_location("bps_population_operator", package / "between_support.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    catalog_path = PIPE / ("bps_catalog_" + TOKEN + ".json")
    assert sha(catalog_path) == "9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2"
    runtime = module.BetweenSupportCatalog(str(catalog_path))
    grouped = defaultdict(list)
    for key, record in runtime.catalog["records"].items():
        scene, aid = key.split("/")
        grouped[scene].append((int(aid), record))
    output = PIPE / ("bps_population_" + TOKEN + ".json")
    progress = PIPE / ("bps_population_" + TOKEN + ".progress.jsonl")
    counts, unknown_reasons = Counter(), Counter()
    rows = []
    max_field = max_pair_count = 0
    elapsed = 0.
    with progress.open("x") as stream:
        for scene, records in sorted(grouped.items()):
            path = DATA / ("scannetv2/train/" + scene + "_refer.pth")
            assert sha(path) == runtime.catalog["raw_scene_sha256"][scene]
            xyz, _, superpoint, semantic, instance = torch.load(
                path, map_location="cpu", weights_only=False)
            _, sp = np.unique(np.asarray(superpoint), return_inverse=True)
            sp = torch.as_tensor(sp, dtype=torch.long)
            labels, _ = get_sp_label(None, sp, torch.as_tensor(instance).long(),
                                    torch.as_tensor(semantic).long())
            records.sort(key=lambda x: x[0])
            ann_ids = [aid for aid, _ in records]
            objects = [record["target_ids"] for _, record in records]
            coords = torch.as_tensor(np.asarray(xyz), dtype=torch.float32)
            started = time.perf_counter()
            supports = runtime.prepare(ann_ids, [scene], [len(records)], objects,
                                       sp, coords, torch.tensor([0, len(labels)]), [labels])
            seconds = time.perf_counter() - started
            elapsed += seconds
            scene_count = Counter()
            for (aid, record), support, readout in zip(records, supports, runtime.last_readout):
                counts["expressions"] += 1
                counts["events"] += len(record["events"])
                counts["resolved_expressions"] += bool(support["costs"])
                counts["resolved_events"] += len(support["costs"])
                counts["unknown_events"] += len(support["unknowns"])
                scene_count["resolved_expressions"] += bool(support["costs"])
                scene_count["resolved_events"] += len(support["costs"])
                scene_count["unknown_events"] += len(support["unknowns"])
                for unknown in support["unknowns"]:
                    unknown_reasons[unknown["reason"]] += 1
                    unknown_reasons.update(unknown["unavailable"])
                for costs in support["costs"]:
                    assert bool(torch.isfinite(costs).all())
                    counts["valid_pair_fields"] += costs.shape[-1]
                    max_pair_count = max(max_pair_count, costs.shape[-1])
                    max_field = max(max_field, float(costs.max()))
                gt = torch.stack([labels == oid for oid in record["target_ids"]])
                has_gt = bool(gt.any())
                counts["raw_gt_missing_expressions"] += not has_gt
                if support["costs"]:
                    if not has_gt:
                        counts["resolved_but_raw_gt_missing"] += 1
                    else:
                        counts["resolved_with_raw_gt"] += 1
                rows.append({"scene": scene, "ann_id": aid, "target_ids": record["target_ids"],
                             "raw_gt_present": has_gt, **readout})
            scene_row = {"scene": scene, "expressions": len(records),
                         "prepare_seconds": seconds, "counts": dict(scene_count),
                         "raw_sha256": sha(path)}
            stream.write(json.dumps(scene_row) + "\n")
            stream.flush()
            if len(rows) % 100 < len(records):
                print(json.dumps({"scenes_done": len({r["scene"] for r in rows}),
                                  "expressions_done": len(rows),
                                  "resolved_events": counts["resolved_events"]}), flush=True)
            del xyz, superpoint, semantic, instance, supports, coords, labels
            gc.collect()
    assert counts["expressions"] == 1498 and counts["events"] == 1502
    assert counts["resolved_events"] + counts["unknown_events"] == counts["events"]
    result = {"tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "catalog_sha256": sha(catalog_path),
              "source_manifest": manifest, "native_dataset_sha256": sha(source),
              "counts": dict(counts), "unknown_reasons": dict(unknown_reasons),
              "scene_count": len(grouped), "all_train_denominator": 36665,
              "max_candidate_pairs_per_event": max_pair_count, "max_finite_pair_cost": max_field,
              "total_prepare_seconds": elapsed, "rows": rows, "cpu_only": True,
              "optimizer_steps": 0,
              "scope": "All stored TRAIN events on raw unaugmented native SP-majority supports; not augmented population, true witness labels or predicted/trained benefit."}
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "counts": dict(counts), "scenes": len(grouped),
                      "max_pairs": max_pair_count, "max_cost": max_field,
                      "prepare_seconds": elapsed}), flush=True)


if __name__ == "__main__":
    main()
