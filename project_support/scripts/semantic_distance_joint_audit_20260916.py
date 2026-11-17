"""Native TRAIN joint semantic-distance diagnostic; no model or reranking."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

ROOT = Path("/data3/songcl/Project/Cluster_project/pipeline")
DATA = Path("/data3/songcl/data/data_cluster")
SOURCE = ROOT / "anchor_identity_20260916/instance_names.json"


def joint_signature(features, positions, center):
    """Cov(feature, distance), invariant to translation/orthogonal transforms."""
    distance = torch.linalg.vector_norm(positions - center, dim=-1)
    centered = features - features.mean(0)
    return ((distance - distance.mean())[:, None] * centered).mean(0)


def synthetic_controls():
    positions = torch.tensor([[0., 0, 0], [1., 0, 0], [2., 0, 0],
                              [3., 0, 0]], dtype=torch.float64)
    features = torch.tensor([[1., 0], [1., 0], [0., 1], [0., 1]],
                            dtype=torch.float64, requires_grad=True)
    center = positions[0]
    original = joint_signature(features, positions, center)
    broken = joint_signature(features.flip(0), positions, center)
    rotation = torch.tensor([[0., -1, 0], [1., 0, 0], [0., 0, -1]],
                            dtype=torch.float64)
    moved = joint_signature(features, positions @ rotation + 9,
                            center @ rotation + 9)
    assert torch.allclose(original, moved)
    assert torch.allclose(original, -broken)
    assert not torch.allclose(original, broken)
    assert torch.equal(features.mean(0), features.flip(0).mean(0))
    assert torch.allclose(joint_signature(torch.ones_like(features), positions, center),
                          torch.zeros_like(original))
    original.square().sum().backward()
    assert torch.isfinite(features.grad).all() and features.grad.abs().sum() > 0
    return dict(equal_semantic_marginals=True, joint_changes=True,
                orthogonal_translation_invariant=True, constant_feature_zero=True,
                nonzero_finite_gradient=True)


def main():
    torch.set_num_threads(1)
    controls = synthetic_controls()
    rows = json.loads(SOURCE.read_text())["rows"]
    output, sources = [], {}
    for scene in sorted({r["scene"] for r in rows}):
        raw = DATA / "scannetv2/train" / (scene + "_refer.pth")
        cached = DATA / "clip_feat" / (scene + ".pth")
        xyz, _, sp, _, instances = torch.load(raw, weights_only=False, map_location="cpu")
        xyz, sp, instances = map(np.asarray, (xyz, sp, instances))
        feature = torch.load(cached, weights_only=False, map_location="cpu").double()
        positions = torch.as_tensor(np.stack([xyz[sp == s].mean(0)
                                              for s in range(len(feature))])).double()
        if not torch.isfinite(positions).all():
            raise ValueError("Missing superpoint coordinates")
        for row in [r for r in rows if r["scene"] == scene]:
            target = row["target_ids"]
            if len(target) != 1:
                raise ValueError("Expected fixed single-target manifest")
            t, w = target[0], row["winner_id"]
            tc = torch.as_tensor(xyz[instances == t].mean(0)).double()
            wc = torch.as_tensor(xyz[instances == w].mean(0)).double()
            a = joint_signature(feature, positions, tc)
            b = joint_signature(feature, positions, wc)
            distance = float(torch.linalg.vector_norm(a-b))
            # Destroy the feature-coordinate association while preserving both marginals.
            null_a = joint_signature(feature.roll(1, 0), positions, tc)
            null_b = joint_signature(feature.roll(1, 0), positions, wc)
            output.append(dict(scene=scene, ann_id=row["ann_id"],
                target=int(t), winner=int(w), before=row["before"],
                wrong=row["before"] <= .5 and row["winner_overlap"] > .5 and t != w,
                joint_distance=distance,
                shifted_distance=float(torch.linalg.vector_norm(null_a-null_b)),
                centroid_distance=float(torch.linalg.vector_norm(tc-wc)),
                same_identity_exact_zero=(distance == 0) if t == w else None))
        sources[scene] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (raw, cached)}
        print(json.dumps(dict(scene=scene, completed=len(output))), flush=True)
    wrong = [r for r in output if r["wrong"]]
    report = dict(rows=output, controls=controls, sources=sources,
        manifest_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        summary=dict(expressions=len(output), wrong=len(wrong),
                     wrong_nonzero=sum(r["joint_distance"] > 0 for r in wrong)),
        limitations="GT instance centroids diagnostic only, not deployable query centers. "
        "Raw cached features, no model intervention. Nonzero signatures and shifted "
        "controls establish distinguishability only, NOT correct language association, "
        "causal relevance, prediction gain, novelty or admission.")
    destination = ROOT / "semantic_distance_joint_20260916"
    destination.mkdir(exist_ok=True)
    (destination / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["summary"]), flush=True)


if __name__ == "__main__":
    main()
