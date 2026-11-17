"""Recompute grouped banks on CPU and summarize measured protocol drift."""
import argparse
import ast
import json
import os
from pathlib import Path
from typing import Union

os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
from d1_candidate_bank_20260911 import bank_metrics, key, sha


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--code-root", required=True)
    args = p.parse_args()
    root = Path(args.root)
    torch.set_num_threads(1)
    source = Path(args.code_root) / "framework/model/Quard_model/model_base1/loss.py"
    fn = next(n for n in ast.parse(source.read_text()).body
              if isinstance(n, ast.FunctionDef) and n.name == "get_iou")
    ns = dict(torch=torch, Union=Union)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), ns)
    output = dict(status="passed", models={}, banks_verified=0)
    reference = {}
    groups_reference = None
    for name in ("baseline", "m95"):
        s = json.loads((root / name / "summary.json").read_text())
        assert s["status"] == "complete" and len(s["rows"]) == 8
        if groups_reference is None:
            groups_reference = s["groups"]
        else:
            assert s["groups"] == groups_reference
        for row in s["rows"]:
            path = root / name / row["artifact"]
            assert sha(path) == row["artifact_sha256"]
            bank = torch.load(path, map_location="cpu", weights_only=False)
            assert list(key(bank["identity"])) == row["identity"]
            metrics = bank_metrics(bank["mask_logits"], bank["score_logits"],
                                   bank["superpoints"], bank["gt_pmask"], ns["get_iou"])
            for k in ("selected_index", "oracle_index"):
                assert metrics[k] == row["grouped_metrics"][k]
            assert torch.allclose(torch.tensor(metrics["candidate_ious"]),
                                  torch.tensor(row["grouped_metrics"]["candidate_ious"]),
                                  atol=1e-7, rtol=0)
            identity = tuple(row["identity"])
            if name == "baseline":
                reference[identity] = {k: bank[k] for k in ("superpoints", "gt_pmask", "gt_spmask")}
            else:
                assert all(torch.equal(v, bank[k]) for k, v in reference[identity].items())
            output["banks_verified"] += 1
        modes = {}
        for mode in ("repeat", "padding", "batch_effect", "total_group_effect", "versus_prior_pilot"):
            rows = [r[mode] for r in s["rows"]]
            modes[mode] = dict(
                n=len(rows), mask_logits_max_abs=max(r["mask_logits_max_abs"] for r in rows),
                score_logits_max_abs=max(r["score_logits_max_abs"] for r in rows),
                selected_probabilities_max_abs=max(r["selected_probabilities_max_abs"] for r in rows),
                bank_bit_changes=sum(r["bank_bit_changes"] for r in rows),
                selected_point_bit_changes=sum(r["selected_point_bit_changes"] for r in rows),
                index_changes=sum(not r["selected_index_equal"] for r in rows),
                max_abs_selected_iou_delta=max(abs(r["selected_iou_delta"]) for r in rows),
                max_abs_oracle_iou_delta=max(abs(r["oracle_iou_delta"]) for r in rows),
                all_seed_sample_mapping_gt_equal=all(
                    r[k + "_equal"] for r in rows for k in
                    ("seed_indices", "sample_indices", "superpoints", "gt_pmask")))
        output["models"][name] = dict(modes=modes, groups=len(s["groups"]),
            group_sizes=[len(g["members"]) for g in s["groups"]],
            unique_context_descriptions=len({tuple(v) for g in s["groups"] for v in g["members"]}),
            peak_allocated_mib=s["peak_allocated_mib"], elapsed_seconds=s["elapsed_seconds"],
            summary_sha256=sha(root / name / "summary.json"))
    output["cuda_initialized"] = torch.cuda.is_initialized()
    assert not output["cuda_initialized"]
    (root / "verification.json").write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
