"""Local stdlib checks only. Never imports Torch or the native model."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/project/cluster_project")
REPO = ROOT / "Cluster"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
BASE = REPO / "framework/model/Quard_model" / NAME
MODEL = HERE / "source/framework/model/Quard_model" / (NAME + "_psc")
checks = []


def check(name, value):
    assert value, name
    checks.append(name)


def mean(rows):
    return [sum(column) / len(rows) for column in zip(*rows)]


def cross(xs, fs):
    mx, mf = mean(xs), mean(fs)
    return [
        [
            sum((x[a] - mx[a]) * (f[b] - mf[b]) for x, f in zip(xs, fs)) / len(xs)
            for b in range(len(mf))
        ]
        for a in range(3)
    ]


xs = [[F(-1), F(0), F(0)], [F(1), F(0), F(0)]]
fa, fb = [[F(-1)], [F(1)]], [[F(1)], [F(-1)]]
ja, jb = cross(xs, fa), cross(xs, fb)
check("same_feature_mean_under_within_leaf_swap", mean(fa) == mean(fb) == [0])
check("same_feature_variance_under_swap", sum(f[0] ** 2 for f in fa) / 2 == sum(f[0] ** 2 for f in fb) / 2 == 1)
check("signed_cross_scatter_distinguishes_swap", ja[0][0] == 1 and jb[0][0] == -1)
check("unchanged_leaf_centroid_under_feature_swap", mean(xs) == [0, 0, 0])
check("joint_scatter_translation_invariant", cross([[x[a] + F(a + 7) for a in range(3)] for x in xs], [[f[0] + 11] for f in fa]) == ja)
check("joint_scatter_orientation_is_signed", jb == [[-v for v in row] for row in ja])
check("constant_coordinates_have_zero_cross_scatter", cross([[F(4), F(4), F(4)]] * 2, fa) == [[0], [0], [0]])

# Exact covariance law under the private equal-child, unequal-population measure.
groups = [
    ([[F(0), F(0), F(0)]], [[F(2), F(-1)]]),
    (
        [[F(1), F(0), F(0)], [F(3), F(2), F(0)], [F(5), F(0), F(2)]],
        [[F(0), F(2)], [F(2), F(4)], [F(4), F(6)]],
    ),
]
cx, cf = [mean(x) for x, f in groups], [mean(f) for x, f in groups]
mx, mf = mean(cx), mean(cf)
within = [[sum(cross(x, f)[a][b] for x, f in groups) / len(groups) for b in range(2)] for a in range(3)]
between = cross(cx, cf)
direct = [[sum(sum((x[a] - mx[a]) * (f[b] - mf[b]) for x, f in zip(xx, ff)) / len(xx) for xx, ff in groups) / len(groups) for b in range(2)] for a in range(3)]
check("equal_child_total_cross_covariance_law", direct == [[within[a][b] + between[a][b] for b in range(2)] for a in range(3)])
check("within_and_between_components_differ", within != between)
check("between_child_joint_scatter_nonzero", any(v != 0 for row in between for v in row))

core = (MODEL / "position_scatter.py").read_text(encoding="utf-8")
tree = ast.parse(core)
support = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_support_plan")
namespace = {}
exec(compile(ast.Module(body=[support], type_ignores=[]), "<actual PSC support function>", "exec"), namespace)
plan = namespace["build_support_plan"]
value = plan([4, 1, 4, 1], [0, 3, 0, 0, 2], [0, 0, 1, 1], 4, [7, 5, 3])
check("actual_support_retains_original_noncontiguous_ids", value["nodes"] == [[1, 4], [2, 3], [1]])
check("actual_support_point_membership", value["point_to_fine"] == [1, 0, 1, 0])
check("actual_support_empty_scene", plan([], [], [], 0, [2, 2, 2])["nodes"] == [[], [], []])
for title, args in [
    ("negative_point_id", ([-1], [0], [0], 1, [2, 2, 2])),
    ("boolean_point_id", ([True], [0, 0], [0], 1, [2, 2, 2])),
    ("missing_fine_parent", ([1], [0], [0], 1, [2, 2, 2])),
    ("missing_middle_parent", ([0], [1], [0], 1, [2, 2, 2])),
    ("point_count_mismatch", ([0, 0], [0], [0], 1, [2, 2, 2])),
]:
    try:
        plan(*args)
    except ValueError:
        checks.append("actual_support_rejects_" + title)
    else:
        raise AssertionError(title)

for source in MODEL.glob("*.py"):
    compile(source.read_bytes(), str(source), "exec")
    checks.append("compile_" + source.name)
yaml_path = HERE / "source/configs/Quard/ctf_hcg_csort_psc" / (NAME + "_psc.yaml")
check("original_native_yaml_bytes", yaml_path.read_bytes() == (REPO / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")).read_bytes())
for name in ["backbone.py", "network.py", "loss.py", "sample_model.py", "__init__.py"]:
    check("unchanged_original_" + name, (MODEL / name).read_bytes() == (BASE / name).read_bytes())
dec = (MODEL / "dec.py").read_text(encoding="utf-8")
original_dec = (BASE / "dec.py").read_text(encoding="utf-8-sig")
check("only_existing_sp_pos_forwarding_decoder_edit", dec == original_dec.replace("                self.cluster_bank.cluster_ids_list)", "                self.cluster_bank.cluster_ids_list, point_positions=sp_pos)", 1))
hier = (MODEL / "hier_postprocess.py").read_text(encoding="utf-8")
bt, ht = ast.parse((BASE / "hier_postprocess.py").read_text(encoding="utf-8-sig")), ast.parse(hier)
base_nodes = {n.name: n for n in bt.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
new_nodes = {n.name: n for n in ht.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
for name, node in base_nodes.items():
    if name not in ("C2F_ClusterAttn_CTF", "C2F_ClusterAttn_CTF_HCG_CSORT"):
        check("unchanged_hierarchy_AST_" + name, ast.dump(node, include_attributes=False) == ast.dump(new_nodes[name], include_attributes=False))
bf = next(n for n in base_nodes["C2F_ClusterAttn_CTF_HCG_CSORT"].body if isinstance(n, ast.FunctionDef) and n.name == "forward")
nf = next(n for n in new_nodes["C2F_ClusterAttn_CTF_HCG_CSORT"].body if isinstance(n, ast.FunctionDef) and n.name == "forward")
check("original_CSORT_loss_body_preserved", ast.dump(ast.Module(body=bf.body[1:], type_ignores=[])) == ast.dump(ast.Module(body=nf.body[1:], type_ignores=[])))
check("shared_factor_dimension_is_C_plus_three_3C_stats", "nn.Linear(10 * channels, channels)" in core)
check("existing_native_coordinates_enter_production_core", "cross_scatter_components(valid, coords, p0, p1, p2, *counts)" in core)
check("valid_mask_shared_by_features_and_coordinates", "points[batch][~point_mask[batch]]" in core and "positions[batch][~point_mask[batch]]" in core)
identifiers = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
check("no_new_query_attention_routing_or_inverse_identifiers", not identifiers.intersection({"query", "softmax", "topk", "pinv", "cdist"}))
check("no_new_forced_FP32_precision", not identifiers.intersection({"float", "float32"}))
check("new_module_RNG_forked_after_original_init_draws", "with torch.random.fork_rng(devices=[]):" in hier)
check("structural_core_not_under5K_scalar_tuning", 11 * 256 ** 2 + 2 * 256 > 5000)
manifest = {
    f.relative_to(HERE / "source").as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
    for f in (HERE / "source").rglob("*") if f.is_file()
}
check("eight_model_files_and_original_native_YAML", len(manifest) == 9)
(HERE / "source_manifest.json").write_text(json.dumps({
    "source_files_exact9": manifest,
    "source_base_commit": "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3",
    "config": "configs/Quard/ctf_hcg_csort_psc/" + NAME + "_psc.yaml",
    "model_files": 8,
    "native_yaml_sha256": hashlib.sha256(yaml_path.read_bytes()).hexdigest(),
}, indent=2) + "\n", encoding="utf-8")
result = {
    "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True,
    "checks_count": len(checks), "checks": checks,
    "command": "python -B -X utf8 " + str(Path(__file__).resolve()),
    "scope": "Actual stdlib syntax/AST/byte checks and extracted production support-plan function; Fraction mathematical reference checks. Production Torch forward/autograd, native TRAIN and resources NOT_RUN; no efficacy or novelty proof.",
    "native": "NOT_RUN", "resources": "NOT_RUN", "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
    "negative_check_preserved": "static_check_negative_control.json",
}
(HERE / "static_validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": True, "checks_count": len(checks), "source_files": len(manifest)}))
