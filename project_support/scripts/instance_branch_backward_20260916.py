"""Native component backward for independent seed-owner masks; not a model admission."""
import copy
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
ns = {"__file__": str(base)}
exec(compile(base.read_text().split(
    "model.criterion.register_forward_pre_hook(capture)")[0], str(base), "exec"), ns)
torch, model = ns["torch"], ns["model"]
F = torch.nn.functional
d = model.dec.d_model
torch.manual_seed(1999)
branch = torch.nn.Sequential(torch.nn.Linear(d, d), torch.nn.ReLU(),
                             torch.nn.Linear(d, d)).cuda()
state, rows = {}, []


def capture_features(module, args):
    state["features"] = args[2]


def capture_labels(module, args):
    state.update(labels=args[4], fps=args[7].long(), pred=args[0])


model.dec.encoder_layers[0].register_forward_pre_hook(capture_features)
model.criterion.register_forward_pre_hook(capture_labels)
model.train()
for step, batch in enumerate(ns["batches"][:2]):
    model.zero_grad(set_to_none=True)
    branch.zero_grad(set_to_none=True)
    ns["gorilla"].set_random_seed(1999)
    native, _ = model(copy.deepcopy(batch), mode="loss")
    features = state["features"]
    terms, valid_count, owners_count = [], 0, 0
    for b, labels in enumerate(state["labels"]):
        features_b = features[b, :len(labels)]
        seeds = state["fps"][b]
        owners = labels[seeds]
        valid = (owners >= 0) & (owners != 199)
        point_valid = (labels >= 0) & (labels != 199)
        if not valid.any() or not point_valid.any():
            continue
        logits = branch(features_b[seeds[valid]]) @ features_b[point_valid].T
        truth = (owners[valid, None] == labels[None, point_valid]).float()
        bce = F.binary_cross_entropy_with_logits(logits, truth)
        p = logits.sigmoid()
        dice = (1-(2*(p*truth).sum(-1)+1)/(p.sum(-1)+truth.sum(-1)+1)).mean()
        terms.append(bce+dice)
        valid_count += int(valid.sum())
        owners_count += int(owners[valid].unique().numel())
    assert terms
    auxiliary = torch.stack(terms).mean()
    # The auxiliary branch must not impose labels on native referent-mask outputs.
    direct = torch.autograd.grad(auxiliary, state["pred"]["masks"],
                                 allow_unused=True, retain_graph=True)[0]
    assert direct is None
    shared_grad = torch.autograd.grad(auxiliary, features, retain_graph=True)[0]
    native_grad = torch.autograd.grad(native, features, retain_graph=True)[0]
    assert torch.isfinite(shared_grad).all() and shared_grad.abs().sum() > 0
    assert torch.isfinite(native_grad).all()
    gradients = []
    for b, labels in enumerate(state["labels"]):
        g = shared_grad[b, :len(labels)].flatten()
        h = native_grad[b, :len(labels)].flatten()
        gradients.append(dict(expression=b, dot=float((g*h).sum()),
            cosine=float(F.cosine_similarity(g, h, dim=0)),
            auxiliary_norm=float(g.norm()), native_norm=float(h.norm())))
    total = native + auxiliary
    assert torch.isfinite(total).all()
    total.backward()
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in branch.parameters())
    rows.append(dict(batch=step, native_loss=float(native.detach()),
        auxiliary_loss=float(auxiliary.detach()), valid_seeds=valid_count,
        owner_expression_pairs=owners_count,
        native_mask_direct_aux_gradient_absent=True,
        per_expression_shared_gradients=gradients,
        prelanguage_feature_aux_gradient_l1=float(shared_grad.abs().sum()),
        branch_gradient_l1=float(sum(p.grad.abs().sum() for p in branch.parameters())),
        full_parameter_gradients_finite=True,
        peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20))
    print(json.dumps(rows[-1]), flush=True)
    del native, auxiliary, total, features, shared_grad, native_grad, terms, p, logits, truth
    state.clear()
result = dict(records=rows, branch_parameters=sum(p.numel() for p in branch.parameters()),
    scope="Two fixed native TRAIN batches,train-mode full backward,existing FPS "
          "and labels. Independent output masks only;shared backbone gradients interact. "
          "BCE+Dice unweighted component test is not a production loss choice. "
          "No optimizer step,novelty,efficacy,matched resources or model admission.",
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), base, ns["config"], ns["checkpoint"])})
out = ns["ROOT"].parent / "pipeline/instance_branch_backward_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(result, indent=2))
