"""Local stdlib checks only; no Torch import, model run, backward or GPU."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
import ast
import hashlib
import json
import math
import random
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/project/cluster_project")
SOURCE = HERE / "source"
preparation = json.loads((HERE / "source_preparation.json").read_text(encoding="utf8"))
prefix = preparation["model_folder"] + "/"
core = SOURCE / (prefix + "spatial_dirichlet.py")
tree = ast.parse(core.read_text(encoding="utf8"))
results = []


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    results.append({"check": label, "passed": True})


def rejects(label, callback):
    try:
        callback()
    except (ValueError, IndexError):
        check(label, True)
    else:
        raise AssertionError(label)


class Index:
    def __init__(self, values):
        self.values = list(values)

    def tolist(self):
        return list(self.values)

    def __iter__(self):
        return iter(self.values)


class ExactArray:
    """Small rational array adapter, explicitly not Torch or autograd."""
    def __init__(self, rows):
        self.rows = [[F(value) for value in row] for row in rows]
        self.shape = (len(rows), len(rows[0]) if rows else 0)
        self.device = "stdlib-rational-adapter"

    def new_zeros(self, shape):
        result = ExactArray([[0] * shape[1] for _ in range(shape[0])])
        result.shape = tuple(shape)
        return result

    def new_ones(self, shape):
        return ExactArray([[1] * shape[1] for _ in range(shape[0])])

    def index_add(self, dim, labels, values):
        assert dim == 0
        out = self.new_zeros(self.shape)
        out.rows = [row[:] for row in self.rows]
        for label, row in zip(labels, values.rows):
            out.rows[label] = [a + b for a, b in zip(out.rows[label], row)]
        return out

    def index_select(self, dim, labels):
        assert dim == 0
        return ExactArray([self.rows[i] for i in labels])

    def clamp_min(self, minimum):
        return ExactArray([[max(F(minimum), x) for x in row] for row in self.rows])

    def __truediv__(self, other):
        return ExactArray([
            [x / (denom[0] if len(denom) == 1 else denom[j]) for j, x in enumerate(row)]
            for row, denom in zip(self.rows, other.rows)])

    def __sub__(self, other):
        return ExactArray([[a - b for a, b in zip(x, y)]
                           for x, y in zip(self.rows, other.rows)])

    def square(self):
        return ExactArray([[x * x for x in row] for row in self.rows])

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return [row[:] for row in self.rows]


names = {"build_support_plan", "build_chain_plan", "_group_mean", "chain_energy"}
definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
check("actual four source functions extracted", len(definitions) == 4)
scope = {
    "math": math,
    "torch": SimpleNamespace(tensor=lambda x, **kwargs: Index(x), long="integer-index"),
}
exec(compile(ast.Module(body=definitions, type_ignores=[]), str(core), "exec"), scope)
support = scope["build_support_plan"]
plan = scope["build_chain_plan"]
energy = scope["chain_energy"]

case = support([0, 2, 2, 4], [3, -1, 1, -1, 3], [-1, 2, -1, 0], 4, [5, 4, 3])
check("compress actual supported IDs", case["nodes"] == [[0, 2, 4], [1, 3], [0, 2]])
check("true original fine parents", case["fine_to_middle"] == [1, 0, 1])
check("true original middle parents", case["middle_to_coarse"] == [1, 0])
check("original input memberships unchanged", case["point_to_fine"] == [0, 1, 1, 2])
check("empty supported forest accepted", support([], [], [], 0, [0, 0, 0])["nodes"] == [[], [], []])
rejects("reject missing point ID", lambda: support([0], [0], [0], 2, [1, 1, 1]))
rejects("reject bool point ID", lambda: support([True], [0], [0], 1, [2, 1, 1]))
rejects("reject unsupported parent", lambda: support([0], [-1], [0], 1, [1, 1, 1]))
rejects("reject invalid coarse ID", lambda: support([0], [0], [9], 1, [1, 1, 1]))

xyz = [[-7, 0, 0], [-5, 0, 0], [-3, 0, 0], [-1, 0, 0],
       [1, 0, 0], [3, 0, 0], [5, 0, 0], [7, 0, 0]]
labels = [0] * 8
feature_a = [1, 1, -1, -1, -1, -1, 1, 1]
feature_b = [1, -1, 1, -1, -1, 1, -1, 1]


def direct_energy(features, positions=xyz, parents=labels, count=1):
    return energy(ExactArray([[x] for x in features]), ExactArray(positions), Index(parents), count).rows


ea = direct_energy(feature_a)
eb = direct_energy(feature_b)
check("counterexample equal native mean", sum(feature_a) == sum(feature_b) == 0)
check("counterexample equal feature second moment", sum(x*x for x in feature_a) == sum(x*x for x in feature_b) == 8)
check("counterexample equal signed position-feature scatter",
      sum(p[0]*f for p, f in zip(xyz, feature_a)) == sum(p[0]*f for p, f in zip(xyz, feature_b)) == 0)
check("actual chain-energy source distinguishes equal HVD/PSC inputs",
      ea == [[F(8, 7)]] and eb == [[F(24, 7)]])
check("uniform feature has zero pair contrast", direct_energy([4] * 8) == [[0]])
check("feature constant shift leaves pair contrast unchanged",
      direct_energy([x + 100 for x in feature_a]) == ea)
check("feature sign reversal leaves pair contrast unchanged",
      direct_energy([-x for x in feature_b]) == eb)
check("coordinate translation leaves edges unchanged",
      direct_energy(feature_b, [[x+19, y-6, z+2] for x, y, z in xyz]) == eb)
check("coordinate reflection reverses chain but preserves energy",
      direct_energy(feature_b, [[-x, y, z] for x, y, z in xyz]) == eb)
order = [7, 0, 5, 2, 3, 6, 1, 4]
check("point row permutation preserves physical chain energy",
      direct_energy([feature_a[i] for i in order], [xyz[i] for i in order]) == ea)
check("singleton geometry has zero energy", direct_energy([5], [[2, 1, -1]], [0]) == [[0]])
check("coincident coordinates merge without row tie break",
      direct_energy([1, 3, 7], [[0, 0, 0], [0, 0, 0], [1, 0, 0]], [0, 0, 0]) == [[25]])
check("coincident feature row permutation invariant",
      direct_energy([3, 1, 7], [[0, 0, 0], [0, 0, 0], [1, 0, 0]], [0, 0, 0]) == [[25]])
separate = direct_energy([1, 2, 10, 13], [[0, 0, 0], [1, 0, 0], [0, 0, 0], [1, 0, 0]], [0, 0, 1, 1], 2)
check("private edges never cross original parent", separate == [[1], [9]])
check("chain edge count is occupied vertices minus nonempty parents",
      len(plan(xyz, labels, 1)["left"]) == 7)
rejects("reject chain invalid label", lambda: plan(xyz, [2]*8, 1))
rejects("reject chain NaN coordinates", lambda: plan([[float("nan"), 0, 0]], [0], 1))
rejects("reject chain missing coordinate rows", lambda: plan([], [0], 1))

python_files = list(SOURCE.rglob("*.py"))
check("exactly eight model Python files", len(python_files) == 8)
for path in python_files:
    compile(path.read_bytes(), str(path), "exec")
check("all isolated source syntax compiles without imports", True)
actual_hashes = {p.relative_to(SOURCE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in SOURCE.rglob("*") if p.is_file()}
check("exact nine source/config hashes", actual_hashes == preparation["source_files_exact9"])
config = SOURCE / preparation["config"]
check("original YAML bytes unchanged", hashlib.sha256(config.read_bytes()).hexdigest()
      == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a")
hierarchy = (SOURCE / (prefix+"hier_postprocess.py")).read_text(encoding="utf8")
decoder = (SOURCE / (prefix+"dec.py")).read_text(encoding="utf8")
check("original padded coordinates reach core", "point_positions=sp_pos" in decoder)
check("only NSD core replaces FFN fork", "self.spatial_dirichlet = HierarchicalSpatialDirichlet(d_model)" in hierarchy
      and "with torch.random.fork_rng(devices=[]):" in hierarchy)
check("unchanged original HCG and original single return", "point_feats, refined_cluster_feats, cluster_ids_list, point_mask" in hierarchy)
classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
forward = next(node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == "forward")
calls = [node for node in ast.walk(forward) if isinstance(node, ast.Call)]
check("actual graph has three bottom-up analysis calls",
      sum(isinstance(c.func, ast.Attribute) and c.func.attr == "analysis" for c in calls) == 3)
check("actual graph has three top-down synthesis calls",
      sum(isinstance(c.func, ast.Attribute) and c.func.attr == "synthesis" for c in calls) == 3)
check("actual graph has native/fine/middle chain operators",
      sum(isinstance(c.func, ast.Name) and c.func.id == "chain_energy" for c in calls) == 3)
check("core graph has no attention or feature-dependent edge choices",
      not any(isinstance(c.func, ast.Attribute) and c.func.attr in ("softmax", "topk", "cdist", "sort", "argsort") for c in ast.walk(tree) if isinstance(c, ast.Call)))
check("only geometric plan reads detached original coordinates", "coordinates.detach().cpu().tolist()" in core.read_text(encoding="utf8"))
check("new path neither changes native loss nor supervision",
      actual_hashes[prefix+"loss.py"] == "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5")

record = {
    "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True,
    "scope": "Actual AST/pure-support/pure-chain source and rational-adapter arithmetic software checks only. No Torch, autograd, full-model forward, native data, GPU or resource measurement.",
    "candidate_id": preparation["candidate_id"], "checks": results,
    "checks_passed": len(results), "source_hashes": actual_hashes,
    "counterexample": {
        "positions": xyz, "feature_A": feature_a, "feature_B": feature_b,
        "same_native_mean": 0, "same_feature_variance": 1,
        "same_signed_position_feature_scatter": 0,
        "actual_source_energy_A": str(ea[0][0]), "actual_source_energy_B": str(eb[0][0]),
        "meaning": "Algebraic information distinction only; not an observed native population deficit or efficacy evidence.",
    },
    "native": "NOT_RUN", "Torch_autograd": "NOT_RUN", "resources": "NOT_RUN",
    "known_limitations": [
        "Coordinate lexicographic chains are not generally rotation invariant; augmentation/sensitivity and task usefulness are unmeasured.",
        "Coordinate-coincident vertices are averaged before graph edges; within-coincident variation is not represented by edge energy.",
        "Native original-precision finite backward, full core updates, paired common initialization, complete resource comparison and independent actual review remain mandatory.",
    ],
}
path = HERE / "static_validation.json"
with path.open("x", encoding="utf8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"passed": True, "checks": len(results), "scope": record["scope"],
                  "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}))
