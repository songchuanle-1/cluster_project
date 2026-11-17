"""Static source-contract and synthetic index checks; no native model execution."""
import ast
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT/"Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
paths = [ROOT/"Cluster/framework/dataset/scannetv2.py", MODEL/"network.py", MODEL/"dec.py"]
trees = [ast.parse(p.read_text(encoding="utf-8")) for p in paths]


def method(tree, name):
    found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(found) == 1, (name, len(found))
    return ast.unparse(found[0])


checks = {}
for name in ("transform_train", "transform_test"):
    text = method(trees[0], name)
    checks[name] = all(x in text for x in (
        "np.unique(superpoint[valid_idxs], return_inverse=True)",
        "xyz_middle = xyz_middle[valid_idxs]",
        "instance_label = instance_label[valid_idxs]"))
getitem = method(trees[0], "__getitem__")
checks["cache_uses_original_ids"] = (
    "feat_2d = self._torch_load_compat(feat_pth)[torch.tensor(unique).long()]" in getitem)
expand = method(trees[1], "expand_and_fps")
checks["same_expansion_order"] = all(
    f"{name}[s:e].repeat(scenes_len[i], 1)" in expand
    for name in ("sp_feats", "sp_coords_float", "feats_2d"))
pad = method(trees[2], "get_batches")
checks["padding_preserves_order"] = "new_feats[i, :cur] = x[s:e]" in pad
checks["lia_source_is_sp"] = any(
    isinstance(n, ast.Call) and ast.unparse(n.func) == "self.lia"
    and [ast.unparse(a) for a in n.args[:2]] == ["inst_feats", "lang_feats"]
    for n in ast.walk(trees[2]))
assert all(checks.values()), checks

cases = 0
negative_controls = 0
original_ids = [9, 2, 9, 5]
cache = {2: "feature2", 5: "feature5", 9: "feature9"}
# All point selections, including repeated points and dropped superpoints.
for count in range(1, 5):
    for selection in itertools.product(range(len(original_ids)), repeat=count):
        selected = [original_ids[i] for i in selection]
        unique = sorted(set(selected))
        inverse = [unique.index(i) for i in selected]
        cached_rows = [cache[i] for i in unique]
        assert [cached_rows[i] for i in inverse] == [cache[i] for i in selected]
        for repeats in (1, 2, 4):
            geometry_ids = unique * repeats
            expanded_cache = cached_rows * repeats
            assert expanded_cache == [cache[i] for i in geometry_ids]
        if len(unique) > 1:
            wrong_rows = cached_rows[1:] + cached_rows[:1]
            assert [wrong_rows[i] for i in inverse] != [cache[i] for i in selected]
            negative_controls += 1
        cases += 1

report = dict(
    source_checks=checks, synthetic_cases=cases,
    deliberately_misaligned_controls_detected=negative_controls,
    shared_index="(batch, scene occurrence, expanded expression offset, local superpoint index)",
    conclusion="Consumer code preserves SP-row correspondence; no index-misalignment evidence.",
    limitations=[
        "Static source contract plus synthetic indexing, not native cache provenance verification.",
        "clip_feat cache producer and source per-view/visibility metadata remain unverified.",
        "Independent captures do not persist vectors/support IDs; matching expression IDs alone "
        "cannot establish tensor alignment across runs.",
        "Aligned rows do not guarantee semantic alignment or justify fusion novelty.",
        "Point subsampling changes 3D aggregation; cached2D comes from precomputed SPs. "
        "This distinction is not evidence of harmful mismatch.",
    ],
    sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in [*paths, Path(__file__)]},
)
out = ROOT/"pipeline/reports/modality_index_contract_20260916.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
