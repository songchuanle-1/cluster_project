"""Bind actual BEI diagnostics and paired resources to the tested Git commit."""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "Cluster"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bei"
CONFIG = "configs/Quard/bei/" + NAME + ".yaml"
OUTPUT = "pipeline/reports/bei_admission_audit_20261009-1042.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def git(*args):
    return subprocess.check_output(["git", "-C", str(CODE), *args])


def main():
    resources = {name: load("pipeline/reports/bei_resource_" + name +
                           "_20261009-1030.json")
                 for name in ("baseline", "champion", "candidate")}
    protocols = [row["protocol"] for row in resources.values()]
    paired = all(row == protocols[0] for row in protocols)
    paired = paired and all(row["status"] == "ok" for row in resources.values())
    paired = paired and protocols[0]["forward_mode"] == "predict"
    paired = paired and protocols[0]["batch_size"] == 1
    paired = paired and protocols[0]["warmup"] == 20 and protocols[0]["repeat"] == 100
    fields = ("params", "trainable_params", "flops_g", "latency_ms_median",
              "latency_ms_p90", "peak_allocated_mib", "peak_reserved_mib")
    measured = {name: {key: row["resources"][key] for key in fields}
                for name, row in resources.items()}
    candidate = measured["candidate"]
    delta = {name: {
        "params": candidate["params"] - ref["params"],
        "flops_g": candidate["flops_g"] - ref["flops_g"],
        "median_ms": candidate["latency_ms_median"] - ref["latency_ms_median"],
        "p90_ms": candidate["latency_ms_p90"] - ref["latency_ms_p90"],
        "memory_percent": 100 * (candidate["peak_allocated_mib"] /
                                 ref["peak_allocated_mib"] - 1)}
        for name, ref in measured.items() if name != "candidate"}
    package = CODE / "framework/model/Quard_model" / NAME
    package_hash = hashlib.sha256()
    files = []
    for path in sorted(package.glob("*.py")):
        assert not path.is_symlink()
        relative = path.relative_to(package).as_posix().encode("ascii")
        committed = git("show", "HEAD:" + path.relative_to(CODE).as_posix())
        assert path.read_bytes().replace(b"\r\n", b"\n") == committed, path
        for node in ast.walk(ast.parse(committed)):
            imports = ([node.module or ""] if isinstance(node, ast.ImportFrom)
                       else [item.name for item in node.names]
                       if isinstance(node, ast.Import) else [])
            assert not any("framework.model.Quard_model." in item for item in imports)
        package_hash.update(len(relative).to_bytes(4, "big"))
        package_hash.update(relative)
        package_hash.update(len(committed).to_bytes(8, "big"))
        package_hash.update(committed)
        files.append({"path": path.relative_to(ROOT).as_posix(),
                      "sha256": hashlib.sha256(committed).hexdigest()})
    assert len(files) == 8
    assert git("show", "HEAD:" + CONFIG) == (CODE / CONFIG).read_bytes().replace(b"\r\n", b"\n")
    parent = "configs/Quard/ctf_hcg_csort/" + NAME.removesuffix("_bei") + ".yaml"
    same_config = yaml.safe_load((CODE / CONFIG).read_text()) == yaml.safe_load(
        (CODE / parent).read_text())
    assert len(list(CODE.glob("configs/**/" + NAME + ".yaml"))) == 1
    bound = resources["candidate"]["bound_identity"]
    identity = package_hash.hexdigest() == bound["model_source_sha256"]
    identity = identity and digest(CODE / CONFIG) == bound["config_sha256"]
    identity = identity and bound["seed"] == 1999
    diagnosis = load("pipeline/reports/m95_boundary_incidence_20261009-1014.json")["summary"]
    native = load("pipeline/reports/bei_sorted_native_20261009-1030.json")
    batch2 = load("pipeline/reports/bei_sorted_batch2_20261009-1030.json")
    operator = load("pipeline/reports/bei_contracts_20261009-1029.json")
    goal = load("pipeline/goal.json")
    gates = {
        "diagnosis": diagnosis["scenes"] == 32 and diagnosis["expressions"] == 128
        and diagnosis["expressions_with_crossing_edges"] == 123
        and diagnosis["crossing_edges"] == 789 and diagnosis["repeat_exact"],
        "controls": operator["passed"] and all(row["matched_control_pass"] and
                    row["strict_repeat_pass"] for row in (native, batch2)),
        "native_backward": all(row["native_backward_pass"] for row in (native, batch2))
        and batch2["physical_group_batch_size"] == 2,
        "resources": paired and candidate["flops_g"] <= 10 and
        candidate["params"] == measured["champion"]["params"],
        "independence": identity and same_config}
    evidence_paths = [
        "pipeline/reports/bei_contracts_20261009-1029.json",
        "pipeline/reports/bei_native_20261009-1029.json",
        "pipeline/reports/bei_sorted_native_20261009-1030.json",
        "pipeline/reports/bei_sorted_batch2_20261009-1030.json",
        "pipeline/reports/m95_boundary_incidence_20261009-1014.json",
        *("pipeline/reports/bei_resource_" + name + "_20261009-1030.json"
          for name in resources)]
    result = {
        "contract": "bei_visible_admission_audit_v1",
        "timestamp": datetime.now().astimezone().isoformat(),
        "code_commit": git("rev-parse", "HEAD").decode().strip(),
        "goal_sha256": digest(ROOT / "pipeline/goal.json"),
        "config": CONFIG, "model_source_sha256": package_hash.hexdigest(),
        "physical_sources": files, "same_numeric_config_as_champion": same_config,
        "resources": measured, "candidate_minus": delta, "paired_predict_protocol": paired,
        "gates": gates, "constraint_count": len(goal["constraints"]),
        "banned_count": len(goal["banned"]),
        "requires_posttraining_gain_for_memory_retention":
        any(row["memory_percent"] > 15 for row in delta.values()),
        "limitations": [
            "Latency is measured on a shared training GPU; not an isolated speed claim.",
            "fvcore unsupported operations retain the historical paired protocol.",
            "No trained efficacy or exhaustive novelty is established.",
            "Separate substantive constraints review is required."],
        "evidence": [{"path": path, "sha256": digest(ROOT / path)}
                     for path in evidence_paths],
        "admission": False, "queue_mutated": False}
    with (ROOT / OUTPUT).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"output": OUTPUT, "gates": gates, "candidate_minus": delta,
                      "sha256": digest(ROOT / OUTPUT)}))


if __name__ == "__main__":
    main()
