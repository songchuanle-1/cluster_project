"""Static audit of cached paired outcomes; no native data or model execution."""
import ast
import hashlib
import json
from pathlib import Path


def audit(root):
    source = root / "pipeline/reports/baseline_matched_20260916.json"
    data = json.loads(source.read_text())["results"]
    packages = root / "Cluster/framework/model/Quard_model"
    paths = [packages / name / "loss.py" for name in (
        "model_base1", "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort")]
    functions = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_iou")
        functions.append(ast.dump(fn, include_attributes=False))
    assert functions[0] == functions[1], "Native metric implementations differ"
    rows = []
    for label, expressions in data.items():
        assert len({(r["scene"], r["ann_id"]) for r in expressions}) == len(expressions)
        for row in expressions:
            final = row["layers"][-1]
            rows.append({
                "model": label, "scene": row["scene"], "ann_id": row["ann_id"],
                "selected": final["selected"], "oracle": final["best"],
                "selected_at_half": final["selected"] == .5,
                "oracle_at_half": final["best"] == .5,
                "selected_within_1e6_of_half": abs(final["selected"] - .5) <= 1e-6,
                "oracle_within_1e6_of_half": abs(final["best"] - .5) <= 1e-6,
            })
    counts = {}
    for label in data:
        subset = [r for r in rows if r["model"] == label]
        counts[label] = {
            "expressions": len(subset),
            "selected_gt_half": sum(r["selected"] > .5 for r in subset),
            "selected_ge_half": sum(r["selected"] >= .5 for r in subset),
            "oracle_gt_half": sum(r["oracle"] > .5 for r in subset),
            "selected_at_half": sum(r["selected_at_half"] for r in subset),
            "oracle_at_half": sum(r["oracle_at_half"] for r in subset),
            "near_half_not_equal": sum(
                (r["selected_within_1e6_of_half"] and not r["selected_at_half"]) or
                (r["oracle_within_1e6_of_half"] and not r["oracle_at_half"])
                for r in subset),
        }
    capture = root / "scripts/coverage_stage_capture_20260916.py"
    return {
        "native_get_iou_ast_identical": True,
        "counts": counts,
        "boundary_rows": [r for r in rows if r["selected_within_1e6_of_half"]
                          or r["oracle_within_1e6_of_half"]],
        "sources": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in [source, capture, *paths]},
        "findings": [
            "Native mask threshold is sigmoid(logit)>=0.5 in both models; zero is included.",
            "Capture uses logit>=0, not the strict positive threshold suspected in memory.",
            "Native denominator is union+1e-6; capture uses union.clamp_min(1).",
            "With identical binary masks and nonempty union, absolute IoU difference is <=1e-6.",
            "Real-arithmetic sigmoid threshold equivalence is not a floating-point proof: "
            "small negative logits may round to sigmoid 0.5. Raw logits are not retained.",
            "Do not relabel stored strict >0.5 success as >=0.5 or point-level validation.",
        ],
        "limitations": "Static cached TRAIN summary only. No raw logits/intersection/union, "
        "so exact native float boundary reconciliation remains unverified. No causal or "
        "novelty claim. Near-half envelope concerns denominator only, not rounded masks.",
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = audit(root)
    destination = root / "pipeline/reports/paired_metric_audit_20260916.json"
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"], indent=2))
