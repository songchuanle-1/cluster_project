"""Static identifiability audit, not a native training or admission test."""
import hashlib
import json
import math
from pathlib import Path
from target_equivalence_audit_20260916 import audit


def marginal_nll(losses):
    pivot = min(losses)
    terms = [math.exp(pivot - loss) for loss in losses]
    total = sum(terms)
    return pivot - math.log(total / len(losses)), [x / total for x in terms]


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / "pipeline/reports/same_target_native_20260916_metadata_corrected.json"
    original_summary = root / "pipeline/reports/same_target_summary_20260916.json"
    native = json.loads(source.read_text(encoding="utf-8"))
    result = audit(native["rows"])
    original = json.loads(original_summary.read_text(encoding="utf-8"))
    by_identity = {(p["scene"], tuple(p["ann_ids"])): p for p in original["pairs"]}
    for pair in result["pairs"]:
        old = by_identity[(pair["scene"], tuple(pair["ann_ids"]))]
        for key, value in pair.items():
            if key != "utterances":
                assert value == old[key], (key, pair["scene"])
        pair["candidate_covered"] = old["candidate_covered"]
        pair["sampled_target"] = old["sampled_target"]
    result["summary"] = original["summary"]
    result["limitations"] = original["limitations"] + [
        "Texts identity-corrected; all original nontext pair fields checked equal.",
        "Equivalent referent IDs do not establish interchangeable semantic content.",
    ]
    discordant = [p for p in result["pairs"] if p["success_disagreement"]]
    partition = dict(
        total=len(discordant),
        observable_different_winner=sum(p["same_winner"] is False for p in discordant),
        observable_same_winner=sum(p["same_winner"] is True for p in discordant),
        unobservable=sum(p["same_winner"] is None for p in discordant),
    )
    assert sum(partition[k] for k in partition if k != "total") == partition["total"]
    value, grad = marginal_nll([0.0, 10.0])
    eps = 1e-5
    numerical = [
        (marginal_nll([0.0 + (eps if i == 0 else 0), 10.0 + (eps if i == 1 else 0)])[0]
         - marginal_nll([0.0 - (eps if i == 0 else 0), 10.0 - (eps if i == 1 else 0)])[0])
        / (2 * eps) for i in range(2)
    ]
    assert max(abs(a - b) for a, b in zip(grad, numerical)) < 1e-8
    assert grad[1] < 0.00005 and value < math.log(2)
    singleton = marginal_nll([3.0])
    assert singleton == (3.0, [1.0])
    evidence = [
        dict(path=p.relative_to(root).as_posix(),
             sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in (source, original_summary, Path(__file__))
    ]
    result["evidence"] = evidence
    corrected = root / "pipeline/reports/same_target_summary_20260916_metadata_corrected.json"
    corrected.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report = dict(
        kind="static_formula_and_existing_evidence_audit",
        partition=partition,
        counterexample=dict(losses=[0, 10], marginal_loss=value,
                            gradient_wrt_losses=grad, finite_difference=numerical),
        singleton_identity=True,
        disposition="Reject marginal-likelihood aggregation as a remedy for hard-description failures: "
                    "its loss gradient favors the already-easy expression. This does not reject all "
                    "multi-description training or require pretrained hard-IoU gains.",
        limitations="Independent loss variables; no model-gradient or efficacy claim. "
                    "Conditional Bernoulli target probability is illustrative, not the native composite loss.",
        evidence=evidence,
    )
    out = root / "pipeline/reports/description_group_objective_20260916.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
