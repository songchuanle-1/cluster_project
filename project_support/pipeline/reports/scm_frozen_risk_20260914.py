"""CPU-only, frozen M95 SCM risk evaluation; no model load or training."""
import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
import torch
from scm_math_check_20260914 import objective


def sha(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(f.read()).hexdigest()


def costs(logits, xyz, target):
    lm = -np.logaddexp(0, -logits)
    b = np.exp(lm - np.logaddexp.reduce(lm, axis=1)[:, None])
    t = target / target.sum()
    result = np.zeros(len(logits))
    diameter = np.linalg.norm(np.ptp(xyz, axis=0))
    for axis in range(3):
        order = np.argsort(xyz[:, axis], kind="stable")
        gaps = np.diff(xyz[order, axis]) / diameter
        result += np.abs(np.cumsum(b[:, order] - t[order], axis=1)[:, :-1]) @ gaps / 3
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--capture", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    root = Path(args.capture)
    manifest = json.loads((root / "summary.json").read_text())
    assert len(manifest["rows"]) == 284
    output = Path(args.output)
    assert not output.exists(), "Refuse to overwrite existing evidence"
    rows, raw_hashes, seen = [], {}, set()
    fd_max = 0.
    for scene in sorted({r["scene_id"] for r in manifest["rows"]}):
        raw = Path(args.data) / "scannetv2/val" / f"{scene}_refer.pth"
        raw_hashes[scene] = sha(raw)
        xyz, _, sp, _, _ = torch.load(raw, map_location="cpu", weights_only=False)
        _, mapping = np.unique(sp, return_inverse=True)
        xyz = np.asarray(xyz, dtype=np.float64)
        count = np.bincount(mapping)
        centers = np.stack([np.bincount(mapping, weights=xyz[:, a]) / count for a in range(3)], axis=1)
        for item in (r for r in manifest["rows"] if r["scene_id"] == scene):
            path = root / item["artifact"]
            digest = sha(path)
            assert digest == item["artifact_sha256"]
            bank = torch.load(path, map_location="cpu", weights_only=False)
            ident = bank["identity"]
            key = tuple(str(ident[k]) for k in ("scene_id", "object_id", "ann_id"))
            assert key == tuple(str(item[k]) for k in ("scene_id", "object_id", "ann_id"))
            assert key not in seen
            seen.add(key)
            t = bank["tensors"]
            assert np.array_equal(t["superpoints"].numpy().ravel(), mapping)
            assert not t["batch_mask"].any()
            masks = t["mask_logits"].double().numpy()
            indis = t["indis_logits"].double().numpy()
            gt = t["gt_spmask"].numpy().ravel() > .5
            assert masks.shape[1] == len(centers) == len(gt)
            assert np.isfinite(masks).all() and np.isfinite(indis).all()
            assert gt.any() and np.linalg.norm(np.ptp(centers, axis=0)) > 0
            d = indis[:, 1] - indis[:, 0]
            hard = masks >= 0
            iou = (hard & gt).sum(1) / (hard | gt).sum(1)
            s, o = int(d.argmax()), int(iou.argmax())
            value, _, gradient = objective(masks, d, centers, gt)
            swapped = objective(masks[::-1], d[::-1], centers, gt)
            assert np.isclose(value, swapped[0], atol=1e-12)
            assert np.allclose(gradient, swapped[2][::-1], atol=1e-12)
            for q in {s, o}:
                e = np.zeros_like(d)
                e[q] = 1e-5
                finite = (objective(masks, d + e, centers, gt)[0] - objective(masks, d - e, centers, gt)[0]) / 2e-5
                error = abs(finite - gradient[q])
                fd_max = max(fd_max, error)
                assert error < 1e-7, (key, error)
            c = costs(masks, centers, gt)
            loga = -np.logaddexp(0, -d)
            alpha = np.exp(loga - np.logaddexp.reduce(loga))
            expected = alpha @ iou
            expected_grad = alpha * (iou - expected) * (1 - np.exp(loga))
            velocity = float(-gradient[s] + gradient[o])
            rows.append(dict(
                **ident, artifact_sha256=digest, selected=s, oracle=o,
                selected_iou=float(iou[s]), oracle_iou=float(iou[o]),
                selected_argmax_ties=int((d == d.max()).sum()),
                oracle_argmax_ties=int((iou == iou.max()).sum()),
                stratum="success" if iou[s] > .5 else "recoverable" if iou[o] > .5 else "limited",
                scm=float(value), selected_cost=float(c[s]), oracle_cost=float(c[o]),
                selected_minus_oracle_velocity=velocity,
                pair_direction="same_query" if s == o else "adverse" if velocity > 1e-12 else "correcting" if velocity < -1e-12 else "zero",
                expected_iou=float(expected),
                expected_iou_velocity=float(-expected_grad @ gradient),
            ))
    assert len(rows) == len(seen) == 284 and len(raw_hashes) == 71
    summary = {}
    rng = np.random.default_rng(1999)
    for group in ("recoverable", "success", "limited"):
        subset = [r for r in rows if r["stratum"] == group]
        scenes = sorted({r["scene_id"] for r in subset})
        counts = np.array([sum(r["scene_id"] == s for r in subset) for s in scenes])
        entry = dict(banks=len(subset), scenes=len(scenes),
                     directions={v: sum(r["pair_direction"] == v for r in subset) for v in ("same_query", "adverse", "correcting", "zero")})
        for name, predicate in (
            ("adverse_pair_fraction", lambda r: r["pair_direction"] == "adverse"),
            ("expected_iou_decreasing_fraction", lambda r: r["expected_iou_velocity"] < -1e-12),
            ("selected_cost_below_oracle_fraction", lambda r: r["selected_cost"] < r["oracle_cost"] - 1e-12),
        ):
            successes = np.array([sum(predicate(r) for r in subset if r["scene_id"] == s) for s in scenes])
            indices = rng.integers(0, len(scenes), size=(10000, len(scenes)))
            boot = successes[indices].sum(1) / counts[indices].sum(1)
            entry[name] = dict(count=int(successes.sum()), denominator=len(subset),
                               fraction=float(successes.sum() / len(subset)),
                               scene_bootstrap_95=np.quantile(boot, [.025, .975]).tolist())
        summary[group] = entry
    payload = dict(status="complete", scope="Frozen M95 Sep12 SCM-only logit-space; NOT M194/full-loss/Adam",
                   capture_summary_sha256=sha(root / "summary.json"),
                   checkpoint_sha256=manifest["checkpoint_sha256"],
                   worker_sha256=sha(__file__), reference_sha256=sha(Path(__file__).with_name("scm_math_check_20260914.py")),
                   raw_scene_sha256=raw_hashes, banks=len(rows), scenes=len(raw_hashes),
                   missing=0, finite_difference_max_error=fd_max, summary=summary, rows=rows)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k not in ("rows", "raw_scene_sha256")}, indent=2))


if __name__ == "__main__":
    main()
