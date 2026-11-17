"""Independent generic-NLL comparison on saved native tensors; remote CPU."""
import hashlib
import json
import os
from pathlib import Path

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    import torch
    torch.set_num_threads(1)
    rows = []
    for trial in (0, 1):
        cp = PIPE / f"caption_equivalence_capture_20261012_trial{trial}.pt"
        capture = torch.load(cp, map_location="cpu", weights_only=False)
        allowed = torch.cat(capture["positive_ids"]).unique()
        for b in range(2):
            z = capture["logits"][b].double().clone().requires_grad_(True)
            s = z[:, 1] - z[:, 0]
            proposed = s.logsumexp(0) - s[allowed].logsumexp(0)
            gp = torch.autograd.grad(proposed, z, retain_graph=True)[0]
            probability = s.softmax(0)
            y = torch.zeros_like(probability)
            y[allowed] = 1
            generic = -(probability * y).sum().log()
            gg = torch.autograd.grad(generic, z, retain_graph=True)[0]
            gs = probability - probability * y / (probability * y).sum()
            analytic = torch.stack((-gs, gs), -1)
            repeated = s.logsumexp(0) - s[allowed].logsumexp(0)
            gr = torch.autograd.grad(repeated, z, retain_graph=True)[0]
            perm = torch.arange(len(s) - 1, -1, -1)
            yp = y[perm]
            sp = s[perm]
            reversed_loss = sp.logsumexp(0) - sp[yp.bool()].logsumexp(0)
            placebo = s.logsumexp(0) - s[(allowed + len(s)//2) % len(s)].logsumexp(0)
            gplacebo = torch.autograd.grad(placebo, z)[0]
            rows.append({
                "trial": trial, "expression": b, "capture_sha256": sha(cp),
                "query_count": len(s), "allowed_query_count": len(allowed),
                "proposal_loss": float(proposed.detach()),
                "generic_partial_label_nll": float(generic.detach()),
                "loss_delta": float((proposed - generic).abs().detach()),
                "gradient_max_delta": float((gp - gg).abs().max()),
                "analytic_gradient_max_delta": float((gp - analytic.detach()).abs().max()),
                "same_target_control_gradient_max_delta": float((gp - gr).abs().max()),
                "query_permutation_loss_delta": float((proposed - reversed_loss).abs().detach()),
                "rotated_set_placebo_gradient_max_delta": float((gp - gplacebo).abs().max()),
                "finite_nonzero_gradient": bool(torch.isfinite(gp).all()) and float(gp.abs().sum()) > 0,
            })
    result = {
        "contract": "caption_allowed_set_generic_nll_equivalence_v1",
        "cpu_only": True, "admission": False, "operator_dtype": "float64",
        "rows": rows, "script_sha256": sha(Path(__file__)),
        "equivalence_pass": all(max(r["loss_delta"], r["gradient_max_delta"],
                                   r["analytic_gradient_max_delta"]) <= 1e-6 for r in rows),
        "limits": "Detached native logits; not full native model backward/resources/efficacy. Original native forward repeat FAIL is retained, not repaired by this operator-level PASS.",
    }
    out = PIPE / "caption_equivalence_operator_20261012.json"
    assert not out.exists()
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
