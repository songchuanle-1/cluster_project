"""Provenance check for the 2D (clip_feat) modality alignment.

`scannetv2.py` does `feat_2d = load(clip_feat/<scan>.pth)[unique]`, then the decoder
does `inst_feats = sum_norm(inst_feats + input_proj_2d(feats_2d))`. That is only
well-defined if the clip_feat rows are indexed by superpoint id and the superpoint
ids are the contiguous range 0..N-1. This measures that empirically.
"""
import hashlib
import json
import logging
import os
from pathlib import Path

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")
ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
OUT = ROOT.parent / "pipeline/modality_provenance_20260916"


def main():
    import sys
    import numpy as np
    import torch

    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import gorilla
    from framework.dataset import build_dataset

    cfg = gorilla.Config.fromfile(str(
        ROOT / "configs/Quard/ctf_hcg_csort/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml"))
    cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    ds = build_dataset(cfg.data.train, logging.getLogger("prov"))
    rows = []
    n_scene = len(ds.scene_inputs)
    for idx in range(min(25, n_scene)):
        try:
            scene_input = ds.scene_inputs[idx]
            data = scene_input[0]
            scan_id = data["scene_id"]
            sp_filename = next((fn for fn in ds.sp_filenames if scan_id in fn),
                               None)
            scene = ds.load(sp_filename)
            scene = ds.transform_train(*scene) if ds.training else ds.transform_test(*scene)
            xyz, xyz_middle, rgb, superpoint, sem, inst, unique = scene
            unique = np.asarray(unique)
            sp = np.asarray(superpoint)
            f2d = ds._torch_load_compat(
                os.path.join(cfg.data.train.data_root, "clip_feat", scan_id + ".pth"))
            rows.append(dict(
                index=idx, scene=scan_id,
                points=int(sp.shape[0]),
                distinct_superpoints=int(np.unique(sp).size),
                unique_len=int(unique.size),
                unique_is_contiguous=bool(
                    unique.size and int(unique.min()) == 0 and
                    unique.size == int(unique.max()) + 1 and
                    np.array_equal(unique, np.arange(unique.size))),
                unique_min=int(unique.min()) if unique.size else None,
                unique_max=int(unique.max()) if unique.size else None,
                clip_feat_rows=int(f2d.shape[0]),
                clip_feat_dim=int(f2d.shape[1]) if f2d.dim() > 1 else None,
                rows_match_distinct=bool(int(f2d.shape[0]) == int(np.unique(sp).size)),
                mod_dim=int(xyz.shape[1])))
        except Exception as exc:  # keep going, record the failure
            rows.append(dict(index=idx, error=repr(exc)[:200]))
    ok = [r for r in rows if "error" not in r]
    summary = dict(
        scenes_checked=len(rows), scenes_ok=len(ok),
        errors=[r for r in rows if "error" in r][:5],
        all_unique_contiguous=all(r["unique_is_contiguous"] for r in ok)
        if ok else None,
        all_rows_match_distinct=all(r["rows_match_distinct"] for r in ok)
        if ok else None,
        all_unique_len_equals_rows=all(r["unique_len"] == r["clip_feat_rows"]
                                       for r in ok) if ok else None,
        distinct_examples=[(r["scene"], r["distinct_superpoints"],
                            r["clip_feat_rows"]) for r in ok[:5]])
    report = dict(summary=summary, rows=rows,
                  scope="Loader provenance only: reads the same sp file and "
                        "clip_feat file the training dataset reads, through the "
                        "dataset's own load/transform, and checks the superpoint-id "
                        "range against the clip_feat row count. It does not test "
                        "feature quality or alignment beyond indexing. Diagnosis "
                        "only; no model, novelty or efficacy admission.",
                  sources={str(Path(__file__)): hashlib.sha256(
                      Path(__file__).read_bytes()).hexdigest(),
                      str(ROOT / "framework/dataset/scannetv2.py"): hashlib.sha256(
                      (ROOT / "framework/dataset/scannetv2.py").read_bytes()
                  ).hexdigest()})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
