"""CPU readback of all pilot banks, original IoU and matched input identity."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Union

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"
import torch
from d1_candidate_bank_20260911 import bank_metrics, key, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--code-root", required=True)
    args = parser.parse_args()
    root = Path(args.root)
    torch.set_num_threads(1)
    loss = Path(args.code_root) / "framework/model/Quard_model/model_base1/loss.py"
    tree = ast.parse(loss.read_text(encoding="utf-8"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_iou")
    scope = {"torch": torch, "Union": Union}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(loss), "exec"), scope)
    summaries = {}
    baseline = {}
    for name in ("baseline", "m95"):
        summary = json.loads((root / name / "summary.json").read_text())
        assert summary["descriptions"] == 8
        assert summary["selected_scenes"] == ["scene0030_00", "scene0046_00"]
        scene_rows = {}
        identities = []
        for row in summary["rows"]:
            path = root / name / row["artifact"]
            assert sha(path) == row["artifact_sha256"]
            payload = torch.load(path, map_location="cpu", weights_only=False)
            assert key(payload["identity"]) == key(row)
            metrics = bank_metrics(payload["mask_logits"], payload["score_logits"],
                                   payload["superpoints"], payload["gt_pmask"], scope["get_iou"])
            assert metrics["selected_index"] == row["selected_index"]
            assert metrics["oracle_index"] == row["oracle_index"]
            for metric in ("selected_iou", "oracle_iou", "bank_limitation", "selection_gap"):
                assert abs(metrics[metric] - row[metric]) < 1e-7
            assert torch.allclose(torch.tensor(metrics["candidate_ious"]),
                                  torch.tensor(row["candidate_ious"]), atol=1e-7, rtol=0)
            probabilities = payload["mask_logits"][metrics["selected_index"]][payload["superpoints"]].sigmoid()
            assert torch.allclose(probabilities, payload["selected_probabilities"], atol=1e-7, rtol=1e-6)
            assert torch.equal(probabilities >= .5, payload["selected_probabilities"] >= .5)
            identity = key(row)
            identities.append(identity)
            if name == "baseline":
                baseline[identity] = {k: payload[k] for k in ("superpoints", "gt_pmask", "gt_spmask")}
            else:
                for k in baseline[identity]:
                    assert torch.equal(baseline[identity][k], payload[k])
            scene_rows.setdefault(row["scene_id"], []).append(row)
        assert len(set(identities)) == 8
        aggregates = {}
        for scene, rows in {"pilot": summary["rows"], **scene_rows}.items():
            aggregates[scene] = dict(
                n=len(rows),
                **{metric: sum(r[metric] for r in rows) / len(rows) for metric in
                   ("selected_iou", "oracle_iou", "bank_limitation", "selection_gap")},
                selected_acc50=sum(r["selected_iou"] > .5 for r in rows) / len(rows),
                selected_fail_oracle_pass50=sum(r["selected_iou"] <= .5 < r["oracle_iou"] for r in rows))
        summaries[name] = dict(summary_sha256=sha(root / name / "summary.json"),
                               aggregates=aggregates, input_hashes=summary["input_hashes"],
                               scene_graph_sha256=summary["scene_graph_sha256"],
                               worker_sha256=summary["worker_sha256"])
    assert summaries["baseline"]["input_hashes"] == summaries["m95"]["input_hashes"]
    assert summaries["baseline"]["scene_graph_sha256"] == summaries["m95"]["scene_graph_sha256"]
    assert summaries["baseline"]["worker_sha256"] == summaries["m95"]["worker_sha256"]
    verification = dict(status="passed", banks_verified=16,
                        cpu_recomputed=True, cuda_initialized=torch.cuda.is_initialized(),
                        matched_gt_and_superpoints=True, fixed_diagnostic_remaining=276,
                        remaining_physical_scenes=69, summaries=summaries,
                        limitation="Two-scene correctness pilot only; no prevalence or causal/mechanism conclusion, no historical full-validation replay.")
    assert not verification["cuda_initialized"]
    (root / "readback_verification.json").write_text(json.dumps(verification, indent=2))
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
