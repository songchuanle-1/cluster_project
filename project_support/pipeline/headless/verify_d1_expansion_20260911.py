"""CPU bank readback and paired physical-scene diagnostic summaries."""
import argparse
import ast
from collections import defaultdict
import json
import os
from pathlib import Path
from typing import Union

os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy as np
import torch
from d1_candidate_bank_20260911 import MANIFEST_SHA, bank_metrics, key, sha


def scene_summary(rows):
    scenes = defaultdict(list)
    for row in rows:
        scenes[row["scene_id"].split("_")[0]].append(row)
    fields = ("selected_iou", "oracle_iou", "bank_limitation", "selection_gap",
              "acc50", "recoverable_failure50", "bank_failure50")
    complete = {k: v for k, v in scenes.items() if len(v) == 4}
    means = {scene: {f: float(np.mean([r[f] for r in members])) for f in fields}
             for scene, members in sorted(complete.items())}
    result = dict(descriptions=len(rows), physical_scenes=len(scenes),
                  complete_scenes=len(complete), incomplete_scenes=sorted(set(scenes) - set(complete)),
                  description_mean={f: float(np.mean([r[f] for r in rows])) for f in fields},
                  complete_scene_means=means)
    if len(means) >= 2:
        values = np.array([[v[f] for f in fields] for v in means.values()])
        rng = np.random.default_rng(1999)
        indices = rng.integers(len(values), size=(10000, len(values)))
        replicates = values[indices].mean(axis=1)
        result["complete_scene_bootstrap95"] = {
            f: dict(mean=float(values[:, i].mean()),
                    low=float(np.quantile(replicates[:, i], .025)),
                    high=float(np.quantile(replicates[:, i], .975)))
            for i, f in enumerate(fields)}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--code-root", required=True)
    args = parser.parse_args()
    root = Path(args.root)
    torch.set_num_threads(1)
    source = Path(args.code_root) / "framework/model/Quard_model/model_base1/loss.py"
    fn = next(n for n in ast.parse(source.read_text()).body
              if isinstance(n, ast.FunctionDef) and n.name == "get_iou")
    ns = dict(torch=torch, Union=Union)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), ns)
    output = dict(status="passed", models={}, banks_verified=0, paired_mapping_gt_equal=True)
    summaries, by_model = {}, {}
    for name in ("baseline", "m95"):
        s = json.loads((root / name / "summary.json").read_text())
        assert s["status"] in ("complete", "partial") and s["manifest_sha256"] == MANIFEST_SHA
        expected = {tuple(k) for k in s["expected_ids"]}
        rows = s["rows"]
        observed = {key(r) for r in rows}
        assert len(expected) == 284 and len(observed) == len(rows)
        assert observed.isdisjoint(map(tuple, s["missing_ids"]))
        assert observed | set(map(tuple, s["missing_ids"])) == expected
        by_model[name] = {}
        for row in rows:
            path = root / name / row["artifact"]
            assert sha(path) == row["artifact_sha256"]
            bank = torch.load(path, map_location="cpu", weights_only=False)
            assert key(bank["identity"]) == key(row)
            metrics = bank_metrics(bank["mask_logits"], bank["score_logits"],
                                   bank["superpoints"], bank["gt_pmask"], ns["get_iou"])
            for k in ("selected_index", "oracle_index"):
                assert metrics[k] == row[k]
            assert torch.allclose(torch.tensor(metrics["candidate_ious"]),
                                  torch.tensor(row["candidate_ious"]), atol=1e-7, rtol=0)
            probabilities = bank["mask_logits"][metrics["selected_index"]][bank["superpoints"]].sigmoid()
            # Match the existing pilot's CPU/GPU sigmoid tolerance; bits stay exact.
            assert torch.allclose(probabilities, bank["selected_probabilities"], atol=1e-7, rtol=1e-6)
            assert torch.equal(probabilities >= .5, bank["selected_probabilities"] >= .5)
            row = dict(row, acc50=float(row["selected_iou"] > .5),
                       recoverable_failure50=float(row["selected_iou"] <= .5 < row["oracle_iou"]),
                       bank_failure50=float(row["oracle_iou"] <= .5))
            by_model[name][key(row)] = row
            output["banks_verified"] += 1
        summaries[name] = s
        output["models"][name] = dict(
            **scene_summary(list(by_model[name].values())),
            summary_sha256=sha(root / name / "summary.json"), missing_ids=s["missing_ids"],
            skipped_groups=[g for g in s["groups"] if g["status"] != "complete"],
            groups=len(s["groups"]), peak_allocated_mib=s["peak_allocated_mib"],
            elapsed_seconds=s["elapsed_seconds"],
            unique_context_descriptions=len({tuple(k) for g in s["groups"] for k in g["members"]}))
    assert summaries["baseline"]["input_hashes"] == summaries["m95"]["input_hashes"]
    assert summaries["baseline"]["scene_graph_sha256"] == summaries["m95"]["scene_graph_sha256"]
    assert [g["members"] for g in summaries["baseline"]["groups"]] == [
        g["members"] for g in summaries["m95"]["groups"]]
    matched = sorted(set(by_model["baseline"]) & set(by_model["m95"]))
    deltas = []
    for identity in matched:
        banks = [torch.load(root / name / by_model[name][identity]["artifact"],
                            map_location="cpu", weights_only=False) for name in ("baseline", "m95")]
        assert all(torch.equal(banks[0][k], banks[1][k])
                   for k in ("superpoints", "gt_pmask", "gt_spmask"))
        a, b = [by_model[name][identity] for name in ("baseline", "m95")]
        deltas.append(dict(scene_id=a["scene_id"],
                           **{k: b[k] - a[k] for k in (
                               "selected_iou", "oracle_iou", "bank_limitation", "selection_gap",
                               "acc50", "recoverable_failure50", "bank_failure50")}))
    output["paired_m95_minus_baseline"] = scene_summary(deltas)
    output["ci_protocol"] = "10000 paired physical-scene bootstrap replicates, seed1999, percentile95; complete scenes only. Conditional exploratory uncertainty, not untouched-test significance."
    output["verifier_sha256"] = sha(__file__)
    output["probability_tolerance"] = dict(atol=1e-7, rtol=1e-6, binary_masks="exact")
    output["cuda_initialized"] = torch.cuda.is_initialized()
    assert not output["cuda_initialized"]
    (root / "verification.json").write_text(json.dumps(output, indent=2))
    print("CPU_VERIFIED", output["banks_verified"], "banks; matched", len(matched), flush=True)


if __name__ == "__main__":
    main()
