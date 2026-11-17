"""Prediction-blind native CPU label diagnosis and boundary-event contracts."""
import argparse
import ast
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time

NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
DATASET_SHA = "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def edges_from_centroids(xyz):
    import numpy as np
    from scipy.spatial import cKDTree
    if len(xyz) < 2:
        return np.empty((0, 2), dtype=np.int64)
    _, nearest = cKDTree(xyz).query(xyz, k=2, workers=1)
    other = [next(int(j) for j in row if int(j) != i)
             for i, row in enumerate(nearest)]
    return np.unique(np.sort(np.column_stack((np.arange(len(xyz)), other)), axis=1),
                     axis=0)


def boundary_loss(logits, labels, edges):
    import torch
    import torch.nn.functional as F
    if not len(edges):
        return logits.sum() * 0
    u, v = edges.T
    a, b = logits[..., u], logits[..., v]
    log_same = torch.logaddexp(F.logsigmoid(a) + F.logsigmoid(b),
                              F.logsigmoid(-a) + F.logsigmoid(-b))
    log_diff = torch.logaddexp(F.logsigmoid(a) + F.logsigmoid(-b),
                              F.logsigmoid(-a) + F.logsigmoid(b))
    different = (labels[..., u] != labels[..., v])
    return -torch.where(different, log_diff, log_same).mean()


def contracts():
    import torch
    import torch.nn.functional as F
    torch.manual_seed(1999)
    e = torch.tensor([[0, 1], [1, 2], [2, 3]], dtype=torch.long)
    y = torch.tensor([0, 0, 1, 1], dtype=torch.bool)
    z = torch.tensor([-1.5, -.7, .9, 1.8], dtype=torch.double, requires_grad=True)
    loss = boundary_loss(z, y, e)
    g = torch.autograd.grad(loss, z)[0]
    complement = float((loss - boundary_loss(-z, ~y, e)).abs())
    stationary = torch.zeros(4, dtype=torch.double, requires_grad=True)
    stationary_g = torch.autograd.grad(boundary_loss(stationary, y, e), stationary)[0]
    wrong = -z.detach().requires_grad_(True)
    wrong_g = torch.autograd.grad(boundary_loss(wrong, y, e), wrong)[0]
    bce = F.binary_cross_entropy_with_logits(wrong, y.double())
    bce_g = torch.autograd.grad(bce, wrong)[0]
    return {
        "gradcheck": bool(torch.autograd.gradcheck(lambda x: boundary_loss(x, y, e), (z,))),
        "complement_symmetry_error": complement,
        "correct_logits_gradient": g.tolist(),
        "complemented_wrong_logits_gradient": wrong_g.tolist(),
        "pointwise_bce_wrong_logits_gradient": bce_g.tolist(),
        "all_half_probability_gradient": stationary_g.tolist(),
        "stationary_at_all_half": bool(stationary_g.abs().sum() == 0),
        "event_target_complement_invariance": bool(torch.equal(y[e[:, 0]] != y[e[:, 1]],
                                                             (~y)[e[:, 0]] != (~y)[e[:, 1]])),
        "synthetic_only": True,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    root = args.root.resolve()
    if (os.name != "posix" or os.environ.get("CUDA_VISIBLE_DEVICES") != ""
            or args.output.exists()
            or not args.output.resolve().is_relative_to(root.parent / "pipeline")):
        raise ValueError("Remote CPU-only diagnosis and fresh project output required")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    dataset_path = root / "framework/dataset/scannetv2.py"
    if sha(dataset_path) != DATASET_SHA:
        raise ValueError("Frozen dataset source differs")
    population_path = root.parent / "pipeline/point_detail_population_20261009/result.manifest.json"
    population = json.loads(population_path.read_text())
    if len(population) != 32:
        raise ValueError("Frozen 32-scene population differs")
    criterion_path = root / "framework/model/Quard_model" / NAME / "loss.py"
    tree = ast.parse(criterion_path.read_text())
    calls = sorted({ast.unparse(node.func) for node in ast.walk(tree)
                    if isinstance(node, ast.Call)})
    cfg = gorilla.Config.fromfile(str(root / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")))
    cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("boundary-incidence"))
    records = []
    started = time.time()
    for repeat in range(2):
        gorilla.set_random_seed(1999)
        for frozen in population:
            index = frozen["native_group"]
            group = source.scene_inputs[index]
            if group[0]["scene_id"] != frozen["scene"]:
                raise ValueError("Native scene index differs")
            item = source[index]
            ann_ids, scene, _, xyz, _, sp, targets = item[:7]
            native_labels = item[11]
            xyz = xyz.numpy().astype(np.float64)
            sp = sp.numpy().astype(np.int64)
            n = int(sp.max()) + 1
            centers = np.column_stack([np.bincount(sp, weights=xyz[:, d], minlength=n)
                                       for d in range(3)])
            count = np.bincount(sp, minlength=n)
            if (count == 0).any():
                raise ValueError("Native superpoint indexing has empty support")
            centers /= count[:, None]
            edges = edges_from_centroids(centers)
            edge_hash = hashlib.sha256(edges.tobytes()).hexdigest()
            for aid, target in zip(ann_ids, targets):
                label = np.isin(native_labels.numpy(), target)
                cross = label[edges[:, 0]] != label[edges[:, 1]]
                records.append(dict(repeat=repeat, scene=scene, ann_id=int(aid),
                                    target_ids=list(map(int, target)), superpoints=n,
                                    edges=len(edges), crossing_edges=int(cross.sum()),
                                    target_sp=int(label.sum()), edge_sha256=edge_hash,
                                    target_sha256=hashlib.sha256(label.tobytes()).hexdigest()))
            print(json.dumps({"repeat": repeat, "scene": scene, "edges": len(edges)}), flush=True)
    a = [r for r in records if r["repeat"] == 0]
    b = [{k: v for k, v in r.items() if k != "repeat"} for r in records if r["repeat"] == 1]
    agreement = [{k: v for k, v in r.items() if k != "repeat"} for r in a] == b
    result = dict(
        contract="m95_native_boundary_incidence_v1", admission=False,
        optimizer_created=False, training_started=False, cuda_initialized=torch.cuda.is_initialized(),
        script_sha256=sha(__file__), population_sha256=sha(population_path),
        dataset_sha256=sha(dataset_path), criterion_sha256=sha(criterion_path),
        criterion_calls=calls, records=records, operator=contracts(),
        summary=dict(scenes=len({r["scene"] for r in a}), expressions=len(a),
                     expressions_with_crossing_edges=sum(r["crossing_edges"] > 0 for r in a),
                     crossing_edges=sum(r["crossing_edges"] for r in a),
                     edges=sum(r["edges"] for r in a), repeat_exact=agreement),
        elapsed_seconds=time.time() - started)
    if result["cuda_initialized"]:
        raise ValueError("CPU diagnosis initialized CUDA")
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"summary": result["summary"], "operator": result["operator"],
                      "sha256": sha(args.output)}), flush=True)


if __name__ == "__main__":
    main()
