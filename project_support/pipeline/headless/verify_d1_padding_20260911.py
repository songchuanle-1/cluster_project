"""Local scalar readback, stratified descriptive summaries and explicit limits."""
from datetime import datetime
import json
from pathlib import Path
import numpy as np
from d1_candidate_bank_20260911 import sha, key

P = Path("D:/project/cluster_project/pipeline")
OUT = P / "reports/d1_padding_20260911-1310"


def stats(values):
    if not values:
        return dict(n=0)
    return dict(n=len(values), mean=float(np.mean(values)), median=float(np.median(values)),
                minimum=float(min(values)), maximum=float(max(values)))


def main():
    data = json.loads((OUT / "padding.json").read_text())
    protocol = json.loads((OUT / "protocol.json").read_text())
    assert data["status"] == "complete" and len(data["rows"]) == 42
    assert data["protocol_sha256"] == sha(OUT / "protocol.json")
    assert data["worker_sha256"] == sha(P / "headless/d1_padding_audit_20260911.py")
    assert not data["cuda_initialized"]
    result = dict(status="passed", created=datetime.now().isoformat(),
                  padding_sha256=sha(OUT / "padding.json"), verified_records=42, models={})
    metrics = ("padding_mass_mean", "weighted_padding_mass", "loss_delta",
               "query_gradient_change_ratio", "padded_token_gradient_ratio")
    for name in ("baseline", "m95"):
        rr = [r for r in data["rows"] if r["model"] == name]
        assert len(rr) == 21 and {key(r) for r in rr} == {tuple(k) for k in protocol["ids"]}
        assert sum(r["role"] == "error" for r in rr) == 12
        summary = json.loads((OUT / name / "summary.json").read_text())
        assert summary["status"] == "complete" and not summary["missing_ids"]
        for r in summary["rows"]:
            assert sha(OUT / name / r["artifact"]) == r["artifact_sha256"]
        for r in rr:
            assert not any(r["annotation_padding_support"].values())
            for n, d, ratio in (
                ("padding_mass_sum", "query_count", "padding_mass_mean"),
                ("weighted_mass_numerator", "weighted_mass_denominator", "weighted_padding_mass"),
                ("query_gradient_change_norm", "full_query_gradient_norm", "query_gradient_change_ratio"),
                ("padded_token_gradient_norm", "full_token_gradient_norm", "padded_token_gradient_ratio")):
                assert abs(r[n] / r[d] - r[ratio]) < 1e-12
            assert abs(r["full_loss"] - r["valid_prefix_loss"] - r["loss_delta"]) < 1e-12
            assert abs(r["loss_delta"] - r["analytic_loss_delta"]) < 1e-7
            assert r["padding_logit_gradient_max_error"] < 1e-8
            assert r["chain_gradient_max_error"] < 1e-8
        result["models"][name] = dict(
            scenes=len({r["scene_id"] for r in rr}),
            padded_cases=sum(r["padding_count"] > 0 for r in rr),
            prior_bank_linked_accepted=sum(r["prior_bank_linked_claims_accepted"] for r in rr),
            prior_binary_equal=sum(r["prior_binary_equal"] for r in rr),
            prior_selected_index_equal=sum(r["prior_selected_index_equal"] for r in rr),
            prior_selected_iou_equal=sum(r["prior_selected_iou_equal"] for r in rr),
            max_mask_logit_drift=max(r["bank_max_abs_drift"]["mask_logits"] for r in rr),
            max_score_logit_drift=max(r["bank_max_abs_drift"]["score_logits"] for r in rr),
            strata={role: {f: stats([r[f] for r in rr if role == "all" or r["role"] == role])
                           for f in metrics} for role in ("all", "error", "control")},
            capture_seconds=summary["elapsed_seconds"],
            peak_allocated_mib=summary["peak_allocated_mib"])
    (OUT / "verification.json").write_text(json.dumps(result, indent=2))
    lines = [
        "# D1 Real-Projection Padding Audit",
        "",
        "## Scope",
        "Frozen 21 IDs/11 scenes per checkpoint, 12 outcome-selected M95 errors and",
        "9 controls; 3 missing controls retained. Both captures complete in 14",
        "original language groups. Context descriptions are not scored samples.",
        "These strata are not causal matches or population prevalence estimates.",
        "Historical baseline identity remains unverified. No reserved-scene inference.",
        "",
        "## Source And Derivation",
        "Current source loss_sem_align retains all five maps, fractional annotation",
        "weights, modifier/pronoun/relation terms and ordered token-weight overwrites.",
        "Saved temperature/eos used. Source matching replay on captured FPS/sample",
        "indices equals earlier assignment for all42; per-description normalizer M.",
        "S=V T^T/tau; O indicates other entities; b_q is main-map activity;",
        "w_q is source match weight. All annotation padding support is zero.",
        "A_q=LSE_all((1+O)S); C_q=LSE_valid((1+O)S).",
        "Unchanged positive terms and token-to-query terms cancel, hence",
        "DeltaL=sum_q w_q*b_q*(A_q-C_q)/(2M).",
        "For padding j, dL/dS_qj=w_q*b_q*softmax((1+O)S)_qj/(2M).",
        "The full source AST supplies all other gradients; the separate logit-input",
        "AST gives gV=gS*T/tau and gT=gS^T*V/tau. Autograd/identity checks pass.",
        "These are gradients of detached normalized projection tensors, not the",
        "normalization Jacobian, shared network parameters or training trajectory.",
        "Stored projections originate in float32; source criterion is audited with",
        "float64 projected tensors and source-created map/weight dtypes unchanged.",
        "This validates algebra at the captured values, not bitwise production",
        "float32 loss/gradient execution. All42 cases contain padding; no natural",
        "unpadded control was observed. Earlier synthetic controls cover that case.",
        "",
        "## Results",
        "|Model|N|Padded|Mean padding mass|Mean weighted mass|Mean loss delta|Mean query-gradient change/full|Mean padded/full token-gradient norm|",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, r in result["models"].items():
        a = r["strata"]["all"]
        lines.append(f"|{name}|21|{r['padded_cases']}|" +
                     "|".join(f"{a[f]['mean']:.9g}" for f in metrics) + "|")
    lines += [
        "",
        "verification.json includes all/error/control count, mean, median, min/max;",
        "padding.json includes per-ID numerators and denominators. No confidence",
        "interval or statistical error-vs-control conclusion for this selected set.",
        "",
        "## Recapture Discrepancy",
        "Original audit halted at mask-logit drift 7.2479248e-5. Reporting-only",
        "repair1 retained atol=rtol=1e-5, recorded every comparison, and rejected",
        "linked claims where any comparison failed. No threshold relaxation.",
    ]
    for name, r in result["models"].items():
        lines.append(f"- {name}: prior-bank linked claims accepted {r['prior_bank_linked_accepted']}/21; "
                     f"binary/index/IoU identical {r['prior_binary_equal']}/"
                     f"{r['prior_selected_index_equal']}/{r['prior_selected_iou_equal']} of21; "
                     f"max mask/score logit drift {r['max_mask_logit_drift']:.9g}/{r['max_score_logit_drift']:.9g}.")
    lines += [
        "Current-capture internal criterion evidence is separate from prior-bank",
        "equivalence. Exact indices/GT mapping pass; drift cause remains unknown.",
        "",
        "## Decision And Limits",
        "Measured projected-gradient changes are small in this selected evaluation",
        "sample. Do not prioritize padding correction as the main research mechanism",
        "on this evidence; do not claim zero exposure, training harmlessness or harm.",
        "No model correction, training enqueue, causal efficacy or novelty claim.",
        "Ordinary mask correctness is not an independent core contribution.",
        "Evaluation dropout/augmentation/batch normalizers differ from training.",
        "Both original GPU captures exited0; CPU reporting repair1 exited0.",
        "Runtime/memory reflect shared load and are not the required efficiency benchmark.",
        "",
        "## Next Evidence",
        "Return to the concrete candidate-scoring problem: most recoverable errors",
        "retain usable supervised positives. Next quantify discriminator margins",
        "and gradient directions for selected false candidates versus usable positives",
        "on existing banks, with all successes as controls and scene-level uncertainty.",
        "No automatic new auxiliary loss, selector or pooling descendant. A proposed",
        "mechanism still needs a falsifiable objective/derivation, primary-literature",
        "comparison, matched intervention and resource admission before training.",
    ]
    (OUT / "diagnostic_report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps({n: {k:v for k,v in r.items() if k != "strata"} for n,r in result["models"].items()}, indent=2))


if __name__ == "__main__":
    main()
