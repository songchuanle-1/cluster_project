"""Source-bound synthetic check of sampled-superpoint CLIP indexing."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source(dataset, network, decoder):
    tree = ast.parse(dataset.read_text(encoding="utf-8"))
    methods = {
        node.name: ast.get_source_segment(dataset.read_text(encoding="utf-8"), node)
        for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)
        for node in cls.body if isinstance(node, ast.FunctionDef)
    }
    expected = {
        "transform_train": "np.unique(superpoint[valid_idxs], return_inverse=True)",
        "transform_test": "np.unique(superpoint[valid_idxs], return_inverse=True)",
        "__getitem__": "[torch.tensor(unique).long()]",
    }
    for method, fragment in expected.items():
        if fragment not in methods.get(method, ""):
            raise ValueError(f"Dataset contract absent: {method}: {fragment}")
    net = network.read_text(encoding="utf-8")
    dec = decoder.read_text(encoding="utf-8")
    for fragment in (
        "feats_2d[s:e].repeat(scenes_len[i],1)",
        "feats_2d_expand = torch.cat",
        "self.dec(sp_feats, fps_seed_sp, batch_offsets, lang_feats, lang_masks, sp_coords_float, feats_2d)",
    ):
        if fragment not in net:
            raise ValueError(f"Network contract absent: {fragment}")
    for fragment in ("self.input_proj_2d(feats_2d)", "inst_feats + inst_feats_2d"):
        if fragment not in dec:
            raise ValueError(f"Decoder contract absent: {fragment}")


def main():
    parser = argparse.ArgumentParser()
    for key in ("dataset", "network", "decoder", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    verify_source(args.dataset, args.network, args.decoder)
    original = np.array([9, 41, 9, 6, 41, 20, 6, 9])
    clip = np.arange(50) * 17 + 3
    cases = {
        "all": np.arange(len(original)),
        "permuted": np.array([7, 4, 0, 5, 3]),
        "duplicate": np.array([0, 0, 2, 7, 4]),
        "singleton": np.array([5]),
    }
    results = {}
    for name, selected in cases.items():
        unique, inverse = np.unique(original[selected], return_inverse=True)
        indexed = clip[unique]
        restored = indexed[inverse]
        expected = clip[original[selected]]
        if not np.array_equal(restored, expected):
            raise AssertionError(name)
        results[name] = {
            "selected_points": int(len(selected)),
            "unique_superpoints": int(len(unique)),
            "correspondence_exact": True,
        }
    output = {
        "contract": "m95_clip_index_contract_v1",
        "admission": False,
        "sources": {str(p): sha(p) for p in (args.dataset, args.network, args.decoder)},
        "cases": results,
        "finding": "The native source indexing is order-preserving for these synthetic cases.",
        "limits": "Synthetic source contract only; does not prove native CLIP feature physical provenance or efficacy.",
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(results, sort_keys=True))


if __name__ == "__main__":
    main()
