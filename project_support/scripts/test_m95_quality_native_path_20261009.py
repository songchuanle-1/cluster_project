"""Execute fixed controls against unmodified champion loss on server-6 CPU."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path


NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
LOSS_SHA = "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"
NETWORK_SHA = "5a77eb852b3c6e5de2804d80a2c7a16504f1fd8a57aa94dc6045d9f35587625d"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def method(tree, name, class_name=None):
    if class_name is not None:
        tree = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.ClassDef) and n.name == class_name)
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


def calls(node, name):
    return sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == name for n in ast.walk(node))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if str(args.root.resolve()) != "/data3/songcl/Project/Cluster_project/Cluster":
        raise ValueError("Native checks must run on authorized server-6")
    package = args.root / "framework/model/Quard_model" / NAME
    loss_path, network_path = package / "loss.py", package / "network.py"
    if sha(loss_path) != LOSS_SHA or sha(network_path) != NETWORK_SHA:
        raise ValueError("Frozen source changed")
    import torch
    torch.set_num_threads(1)
    spec = importlib.util.spec_from_file_location("frozen_champion_loss", loss_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    criterion = module.Criterion()
    mask = torch.tensor([[2., -2., -2., -2.], [2., 2., 2., -2.]],
                        requires_grad=True)
    score = torch.tensor([[.5], [.5]], requires_grad=True)
    target = torch.ones(1, 4)
    matched = [(torch.tensor([0, 1]), torch.tensor([0, 0]))]
    bce, dice, quality_loss = criterion.loss_masks(
        [mask], [score], [{"masks": target}], matched, torch.tensor([2.]))
    mask_gradient = torch.autograd.grad(bce + dice, mask, retain_graph=True)[0]
    score_gradient = torch.autograd.grad(quality_loss, score)[0]
    iou = module.get_iou(mask, target.expand_as(mask)).detach().tolist()
    loss_tree = ast.parse(loss_path.read_text())
    network_tree = ast.parse(network_path.read_text())
    predict = method(network_tree, "predict_by_feat")
    score_reads = [n for n in ast.walk(predict) if isinstance(n, ast.Subscript)
                   and isinstance(n.slice, ast.Constant) and n.slice.value == "scores"]
    checks = {
        "native_iou_matches_fixed_control": abs(iou[0] - .25) < 1e-6
            and abs(iou[1] - .75) < 1e-6,
        "censored_low_iou_score_gradient_zero": float(score_gradient[0]) == 0,
        "high_iou_score_gradient_nonzero": float(score_gradient[1]) != 0,
        "both_matched_mask_gradients_finite_nonzero":
            bool(torch.isfinite(mask_gradient).all())
            and all(float(row.norm()) > 0 for row in mask_gradient),
        "deployment_does_not_read_quality_scores": not score_reads,
        "auxiliary_loss_does_not_rematch":
            calls(method(loss_tree, "get_layer_loss", "Criterion"), "match_sampled_ins") == 0,
        "target_geometry_matching_occurs_in_forward":
            calls(method(loss_tree, "forward", "Criterion"), "match_sampled_ins") == 2,
        "cpu_only_no_cuda_initialized": not torch.cuda.is_initialized(),
    }
    result = {
        "contract": "m95_quality_native_path_control_v1",
        "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL",
        "iou": iou, "mask_gradient_norms": [float(row.norm()) for row in mask_gradient],
        "score_gradients": score_gradient.flatten().tolist(),
        "source_hashes": {"loss": LOSS_SHA, "network": NETWORK_SHA},
        "script_sha256": sha(Path(__file__)), "device": "cpu",
        "admission": False, "training_started": False,
        "limitations": "Fixed native-loss control and source audit, not native full-model backward or trained efficacy.",
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
