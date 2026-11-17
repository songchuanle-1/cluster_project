"""Read-only frozen-bank common-seed paired-switching applicability."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import torch


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    torch.set_num_threads(1)
    root = Path("/tmp/cluster_semantic_projection_20260912/full")
    manifest = json.loads((root / "summary.json").read_text())
    output = Path("/tmp/cps_applicability_20260914.json")
    assert not output.exists()
    assert len(manifest["rows"]) == 284
    results, inputs = [], {}
    for scene in sorted({r["scene_id"] for r in manifest["rows"]}):
        raw = Path("/home/songcl/data/data/scannetv2/val") / (scene + "_refer.pth")
        _, _, sp, sem, ins = torch.load(raw, map_location="cpu", weights_only=False)
        _, mapping = np.unique(sp, return_inverse=True)
        sem, ins = np.asarray(sem), np.asarray(ins)
        counts = np.bincount(mapping)
        labels = np.full(len(counts), 199)
        for obj in np.unique(ins):
            votes = np.bincount(mapping[ins == obj], minlength=len(counts))
            labels[2 * votes > counts] = obj
        inputs[str(raw)] = sha(raw)
        banks = []
        for row in (r for r in manifest["rows"] if r["scene_id"] == scene):
            path = root / row["artifact"]
            assert sha(path) == row["artifact_sha256"]
            b = torch.load(path, map_location="cpu", weights_only=False)
            t = b["tensors"]
            assert np.array_equal(mapping, t["superpoints"].numpy().ravel())
            target = int(b["identity"]["object_id"])
            assert np.array_equal(t["gt_spmask"].numpy().ravel() > .5, labels == target)
            seeds = t["seed_indices"].numpy().ravel()[t["sample_indices"].numpy().ravel()].astype(int)
            assert len(np.unique(seeds)) == len(seeds)
            d = np.diff(t["indis_logits"].double().numpy(), axis=1).ravel()
            hard = t["mask_logits"].numpy() >= 0
            gt = t["gt_spmask"].numpy().ravel() > .5
            iou = (hard & gt).sum(1) / (hard | gt).sum(1)
            categories, freq = np.unique(sem[ins == target], return_counts=True)
            cat = int(categories[freq.argmax()]) if len(categories) else None
            banks.append(dict(identity=b["identity"], target=target, seeds=seeds, d=d,
                              category=cat, selected_iou=float(iou[d.argmax()])))
        assert len(banks) == 4
        for a, b in itertools.combinations(banks, 2):
            r = dict(scene_id=scene, a=a["identity"], b=b["identity"],
                     same_category=a["category"] == b["category"] if a["category"] is not None and b["category"] is not None else None,
                     selected_iou_a=a["selected_iou"], selected_iou_b=b["selected_iou"])
            if a["target"] == b["target"]:
                results.append(dict(**r, status="same_target_excluded"))
                continue
            common, ia, ib = np.intersect1d(a["seeds"], b["seeds"], return_indices=True)
            ma, mb = labels[common] == a["target"], labels[common] == b["target"]
            r.update(common_seeds=len(common), target_a_seeds=int(ma.sum()), target_b_seeds=int(mb.sum()))
            if not ma.any() or not mb.any():
                results.append(dict(**r, status="missing_shared_target"))
                continue
            z = np.array([[a["d"][ia][ma].mean(), a["d"][ia][mb].mean()],
                          [b["d"][ib][ma].mean(), b["d"][ib][mb].mean()]])
            delta = z[0, 0] + z[1, 1] - z[0, 1] - z[1, 0]
            results.append(dict(**r, status="eligible", cells=z.tolist(), delta=float(delta),
                                row_a_margin=float(z[0, 0]-z[0, 1]),
                                row_b_margin=float(z[1, 1]-z[1, 0])))
    assert len(results) == 426
    eligible = [r for r in results if r["status"] == "eligible"]
    summary = dict(pairs=len(results), banks=284, scenes=71,
                   status_counts={k: sum(r["status"] == k for r in results)
                                  for k in ("same_target_excluded", "missing_shared_target", "eligible")},
                   eligible_scenes=len({r["scene_id"] for r in eligible}))
    for name, subset in (("all", eligible), ("same_category", [r for r in eligible if r["same_category"]])):
        summary[name] = dict(pairs=len(subset), scenes=len({r["scene_id"] for r in subset}),
                             nonpositive_delta=sum(r["delta"] <= 0 for r in subset),
                             not_both_row_correct=sum(r["row_a_margin"] <= 0 or r["row_b_margin"] <= 0 for r in subset),
                             at_least_one_hard_failure=sum(r["selected_iou_a"] <= .5 or r["selected_iou_b"] <= .5 for r in subset))
    payload = dict(summary=summary, rows=results, raw_hashes=inputs,
                   capture_sha256=sha(root / "summary.json"), worker_sha256=sha(__file__))
    output.write_text(json.dumps(payload, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
