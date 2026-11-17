"""Bounded AST/support-plan checks; never import Torch or execute a model."""
from datetime import datetime, timezone
from pathlib import Path
import ast
import hashlib
import json
import math
import os
import subprocess
import sys
import traceback

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
PARENT = "f6257de79148581334ee495e6e2d60ccb525457c"
OLD = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd"
NEW = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde"
PACKAGE = "framework/model/Quard_model/" + NEW
CHECKS = []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(name, condition, observation=None):
    CHECKS.append({"name": name, "passed": bool(condition), "observation": observation})
    if not condition:
        raise AssertionError(name)


def ast_form(node):
    return ast.dump(node, include_attributes=False)


def named(tree, kind, name):
    return next(node for node in tree.body if isinstance(node, kind) and node.name == name)


def run():
    check("bytecode_disabled", sys.dont_write_bytecode)
    check("torch_not_imported_before_checks", "torch" not in sys.modules)
    version = json.loads((HERE / "source_version.json").read_bytes())
    check("exact_parent_and_candidate_identity",
          version["source_parent_commit"] == PARENT
          and version["candidate_id"] == "hierarchy-native-distribution-embedding-composition"
          and version["experiment_id"] == "M233-NDE")
    actual = sorted(p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob("*") if p.is_file())
    check("exactly_nine_source_files", len(actual) == 9 and actual == sorted(
        entry["path"] for entry in version["files"]))
    check("all_nine_hashes_match_manifest", all(
        digest((SOURCE / entry["path"]).read_bytes()) == entry["sha256"]
        for entry in version["files"]))
    git = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks",
           "-c", "core.fsmonitor=false", "-C", str(ROOT / "Cluster")]
    head = subprocess.check_output(git + ["rev-parse", "HEAD"], timeout=15).decode().strip()
    index = Path(subprocess.check_output(
        git + ["rev-parse", "--git-path", "index"], timeout=15).decode().strip())
    if not index.is_absolute():
        index = ROOT / "Cluster" / index
    index_before = digest(index.read_bytes())
    check("main_still_exact_parent", head == PARENT)
    unchanged = [entry for entry in version["files"] if entry.get("byte_exact_parent")]
    check("six_model_files_and_native_YAML_byte_exact_parent",
          len(unchanged) == 7 and all(
              (SOURCE / entry["path"]).read_bytes() == subprocess.check_output(
                  git + ["show", PARENT + ":" + entry["parent_path"]], timeout=15)
              for entry in unchanged))
    trees = {}
    for relative in actual:
        if relative.endswith(".py"):
            tree = ast.parse((SOURCE / relative).read_text(encoding="utf8"), filename=relative)
            compile(tree, relative, "exec")
            trees[relative] = tree
    check("all_eight_python_sources_parse_and_compile_without_execution", len(trees) == 8)
    parent_hier = ast.parse(subprocess.check_output(
        git + ["show", PARENT + ":framework/model/Quard_model/" + OLD + "/hier_postprocess.py"],
        timeout=15).decode())
    hier = trees[PACKAGE + "/hier_postprocess.py"]
    for name in ("PointCloudPartitioner", "SharedClusterBank",
                 "C2F_ClusterAttn_CTF_HCG", "C2F_ClusterAttn_CTF_HCG_CSORT"):
        check("unchanged_original_" + name,
              ast_form(named(hier, ast.ClassDef, name)) ==
              ast_form(named(parent_hier, ast.ClassDef, name)))
    core = trees[PACKAGE + "/distribution_embedding.py"]
    support = named(core, ast.FunctionDef, "build_support_plan")
    context = {}
    exec(compile(ast.Module(body=[support], type_ignores=[]),
                 "<NDE-support-plan-only>", "exec"), context)
    plan = context["build_support_plan"]
    ids0 = [7, 2, 7, 5]
    ids1 = [0, 0, 4, 0, 0, 1, 0, 4, 0, 0]
    ids2 = [0, 3, 0, 0, 2, 0]
    expected = {"nodes": [[2, 5, 7], [1, 4], [2, 3]],
                "point_to_fine": [2, 0, 2, 1],
                "fine_to_middle": [1, 0, 1], "middle_to_coarse": [1, 0]}
    check("true_ancestry_sparse_gaps_and_multiple_roots",
          plan(ids0, ids1, ids2, 4, [10, 6, 4]) == expected)
    permutation = [2, 0, 3, 1]
    permuted = plan([ids0[i] for i in permutation], ids1, ids2, 4, [10, 6, 4])
    check("row_permutation_preserves_physical_support",
          permuted["nodes"] == expected["nodes"]
          and permuted["fine_to_middle"] == expected["fine_to_middle"]
          and permuted["middle_to_coarse"] == expected["middle_to_coarse"]
          and permuted["point_to_fine"] == [expected["point_to_fine"][i] for i in permutation])
    check("empty_support_has_no_private_bias_nodes",
          plan([], [], [], 0, [1, 1, 1]) ==
          {"nodes": [[], [], []], "point_to_fine": [],
           "fine_to_middle": [], "middle_to_coarse": []})
    singleton = plan([0], [0], [0], 1, [1, 1, 1])
    check("single_supported_path", singleton == {
        "nodes": [[0], [0], [0]], "point_to_fine": [0],
        "fine_to_middle": [0], "middle_to_coarse": [0]})
    for label, args in (
        ("boolean_fine_id", ([True], [0], [0], 1, [1, 1, 1])),
        ("negative_fine_id", ([-1], [0], [0], 1, [1, 1, 1])),
        ("missing_parent", ([2], [0], [0], 1, [3, 1, 1])),
        ("invalid_true_parent", ([0], [2], [0], 1, [1, 2, 1])),
    ):
        refused = False
        try:
            plan(*args)
        except ValueError:
            refused = True
        check("support_refuses_" + label, refused)
    cls = named(core, ast.ClassDef, "HierarchicalDistributionEmbedding")
    forward = named(cls, ast.FunctionDef, "forward")
    assignments = {node.targets[0].id: node.value for node in ast.walk(forward)
                   if isinstance(node, ast.Assign) and len(node.targets) == 1
                   and isinstance(node.targets[0], ast.Name)}
    fine = assignments["fine_state"]
    check("first_native_mean_receives_transformed_point_values",
          isinstance(fine, ast.Call) and isinstance(fine.func, ast.Name)
          and fine.func.id == "_group_mean"
          and isinstance(fine.args[0], ast.Call)
          and ast_form(fine.args[0].func) == ast_form(ast.parse("self.analysis", mode="eval").body)
          and "Name(id='valid'" in ast_form(fine.args[0]))
    check("three_analysis_and_three_synthesis_calls",
          sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "analysis" for node in ast.walk(forward)) == 3
          and sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "synthesis" for node in ast.walk(forward)) == 3)
    check("both_cores_use_original_GELU_two_linear_structure",
          sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "Linear" for node in ast.walk(cls)) == 4
          and sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "GELU" for node in ast.walk(cls)) == 2)
    check("no_private_attention_scalar_weights_precision_or_custom_init",
          not any(isinstance(node, ast.Attribute) and node.attr in
                  {"softmax", "scatter_softmax", "float", "double", "half", "bfloat16",
                   "uniform_", "normal_", "constant_", "fill_"}
                  for node in ast.walk(core)))
    core_text = (SOURCE / PACKAGE / "distribution_embedding.py").read_text(encoding="utf8")
    check("raw_parent_bank_and_parent_synthesis_are_both_inputs",
          "selected[0].index_select(0, p0)" in core_text
          and "selected[1].index_select(0, p1)" in core_text
          and "selected[2].index_select(0, p2)" in core_text
          and "middle_delta.index_select(0, p1)" in core_text
          and "coarse_delta.index_select(0, p2)" in core_text)
    check("padding_excluded_before_embedding_and_only_supported_nodes_written",
          "valid = points[batch][~point_mask[batch]]" in core_text
          and "empty.index_copy(0, ids[level], delta)" in core_text)
    hier_text = (SOURCE / PACKAGE / "hier_postprocess.py").read_text(encoding="utf8")
    check("NDE_integration_preserves_raw_skip_HCG_and_single_call",
          "changes = self.distribution_embedding(" in hier_text
          and hier_text.count("changes = self.distribution_embedding(") == 1
          and "refined_cluster_feats = [raw + delta" in hier_text
          and "self.spatial_dirichlet" not in hier_text
          and "self.distribution_embedding = HierarchicalDistributionEmbedding(d_model)" in hier_text)
    config = version["config"]
    check("unique_native_config_basename_absent_from_current_main",
          Path(config).stem == NEW
          and not list((ROOT / "Cluster/configs").rglob(NEW + ".yaml")))
    original_text = (SOURCE / config).read_text(encoding="utf8")
    check("frozen_training_protocol_not_changed",
          all(fragment in original_text for fragment in
              ("seed: 1999", "epochs: 50", "max_iters: 70",
               "loss_weight: [1.0, 1.0, 0.5, 5.0, 0.1, 0.1, 0.1, 1.0]",
               "cluster_layer_nums: [256, 64, 8]")))
    # A constructed representational example only: no model/Torch/native task run.
    values = [1.0, -2.0, 1.0, 0.0]
    opposite = [-value for value in values]
    def descriptors(xs):
        return [sum(xs) / 4, sum(x * x for x in xs) / 4,
                sum(i * x for i, x in enumerate(xs)) / 4,
                sum((x - y) ** 2 for x, y in zip(xs, xs[1:])) / 3]
    def gelu(x):
        return 0.5 * x * (1 + math.erf(x / math.sqrt(2)))
    embedding = [sum(gelu(x + 1) for x in xs) / 4 for xs in (values, opposite)]
    check("constructed_mean_variance_scatter_chain_energy_equal",
          descriptors(values) == descriptors(opposite), descriptors(values))
    check("constructed_nonlinear_value_embedding_separates_distribution",
          embedding[0] != embedding[1],
          {"values": embedding,
           "scope": "Constructed function expressivity only; not default weights, native deficit or gain."})
    check("user_main_index_unchanged_by_checks",
          subprocess.check_output(git + ["rev-parse", "HEAD"], timeout=15).decode().strip() == head
          and digest(index.read_bytes()) == index_before)
    check("torch_not_imported_after_checks", "torch" not in sys.modules)


def main():
    error = None
    try:
        run()
    except Exception:
        error = traceback.format_exc()
    value = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "hierarchy-native-distribution-embedding-composition",
        "experiment_id": "M233-NDE",
        "source_parent_commit": PARENT,
        "command": [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve())],
        "checker_sha256": digest(Path(__file__).read_bytes()),
        "passed": error is None,
        "check_count": len(CHECKS),
        "checks": CHECKS,
        "error": error,
        "scope": "AST compilation, extracted pure support-plan and constructed math only.",
        "Torch_imported": "torch" in sys.modules,
        "model_forward": "NOT_RUN",
        "Torch_autograd": "NOT_RUN",
        "native": "NOT_RUN",
        "resources": "NOT_RUN",
        "efficacy": "UNKNOWN",
        "novelty": "UNKNOWN",
    }
    target = HERE / "static_validation.json"
    with target.open("x", encoding="utf8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": value["passed"], "checks": len(CHECKS),
                      "path": str(target), "error": error}))
    if error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
