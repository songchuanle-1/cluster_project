"""Audit measured PDC gates without performing an admission or queue mutation."""
import argparse
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "Cluster"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pdc"
CONFIG = "configs/Quard/pdc/" + NAME + ".yaml"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def git(*args):
    return subprocess.check_output(["git", "-C", str(CODE), *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource-prefix", required=True)
    parser.add_argument("--native", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    if output.exists() or not output.resolve().is_relative_to(ROOT / "pipeline/reports"):
        raise ValueError("Fresh local report output required")
    resources = {
        name: load(args.resource_prefix + "_" + name + "_20261009.json")
        for name in ("baseline", "champion", "candidate")}
    protocols = [value["protocol"] for value in resources.values()]
    paired = all(value == protocols[0] for value in protocols)
    paired = paired and protocols[0].get("forward_mode") == "predict"
    paired = paired and protocols[0]["warmup"] == 20 and protocols[0]["repeat"] == 100
    measured = {name: value["resources"] for name, value in resources.items()}
    candidate = measured["candidate"]
    delta = {
        name: {
            "params": candidate["params"] - ref["params"],
            "flops_g": candidate["flops_g"] - ref["flops_g"],
            "median_ms": candidate["latency_ms_median"] - ref["latency_ms_median"],
            "p90_ms": candidate["latency_ms_p90"] - ref["latency_ms_p90"],
            "memory_mib": candidate["peak_allocated_mib"] - ref["peak_allocated_mib"],
            "memory_percent": 100 * (candidate["peak_allocated_mib"] /
                                    ref["peak_allocated_mib"] - 1),
        }
        for name, ref in measured.items() if name != "candidate"}
    package = CODE / "framework/model/Quard_model" / NAME
    files, package_digest = [], hashlib.sha256()
    for path in sorted(package.glob("*.py")):
        if path.is_symlink():
            raise ValueError("Physical independent files required")
        relative = path.relative_to(package).as_posix().encode("ascii")
        committed = git("show", "HEAD:" + path.relative_to(CODE).as_posix())
        payload = path.read_bytes().replace(b"\r\n", b"\n")
        if payload != committed:
            raise ValueError("Uncommitted candidate model file: " + str(path))
        tree = ast.parse(payload, filename=str(path))
        for node in ast.walk(tree):
            imports = []
            if isinstance(node, ast.ImportFrom):
                imports = [node.module or ""]
            elif isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            if any("framework.model.Quard_model." in value for value in imports):
                raise ValueError("Cross-variant import in independent model")
        package_digest.update(len(relative).to_bytes(4, "big"))
        package_digest.update(relative)
        package_digest.update(len(committed).to_bytes(8, "big"))
        package_digest.update(committed)
        files.append({"path": path.relative_to(ROOT).as_posix(),
                      "git_blob_sha256": hashlib.sha256(committed).hexdigest()})
    config = yaml.safe_load((CODE / CONFIG).read_text())
    parent = yaml.safe_load((CODE / (
        "configs/Quard/ctf_hcg_csort/" + NAME.removesuffix("_pdc") + ".yaml")).read_text())
    unchanged_numeric_config = config == parent
    bound = resources["candidate"]["bound_identity"]
    identity = (package_digest.hexdigest() == bound["model_source_sha256"]
                and digest(CODE / CONFIG) == bound["config_sha256"])
    native = load(args.native)
    backward = native["native_backward_pass"] is True
    controls = native["matched_control_pass"] is True and native["strict_repeat_pass"] is True
    diagnosis = load("pipeline/reports/m95_point_detail_population_20261009.json")
    rows = [row for row in diagnosis["records"] if row["repeat"] == 0]
    mixed = [row for row in rows if row["mixed_superpoints"] > 0]
    information = len(rows) == 128 and len(mixed) == 19 and all(
        row["normalized_mixed_detail_energy"] > 0 for row in mixed)
    goal = load("pipeline/goal.json")
    resource_pass = (paired and candidate["flops_g"] <= 10
                     and candidate["params"] - measured["champion"]["params"] == 9280)
    result = {
        "contract": "pdc_visible_admission_audit_v1",
        "timestamp": datetime.now().astimezone().isoformat(),
        "code_commit": git("rev-parse", "HEAD").decode().strip(),
        "goal_sha256": digest(ROOT / "pipeline/goal.json"),
        "config": CONFIG, "model_source_sha256": package_digest.hexdigest(),
        "physical_sources": files, "same_numeric_config_as_champion": unchanged_numeric_config,
        "resources": measured, "candidate_minus": delta, "paired_predict_protocol": paired,
        "requires_posttraining_gain_for_memory_retention": any(
            value["memory_percent"] > 15 for value in delta.values()),
        "retention_gain_if_required": 0.003,
        "gates": {"diagnosis": information, "controls": controls,
                  "native_backward": backward, "resources": resource_pass,
                  "independence": identity and unchanged_numeric_config},
        "constraint_count": len(goal["constraints"]), "banned_count": len(goal["banned"]),
        "constraints_review": "Separate visible substantive review required; no automatic PASS.",
        "novelty_exhaustively_verified": False, "trained_efficacy_known": False,
        "admission": False, "queue_mutated": False,
        "evidence": [{"path": path, "sha256": digest(ROOT / path)}
                     for path in [args.native,
                                  "pipeline/reports/m95_point_detail_population_20261009.json",
                                  *(args.resource_prefix + "_" + name + "_20261009.json"
                                    for name in ("baseline", "champion", "candidate"))]],
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"output": args.output, "gates": result["gates"],
                      "candidate_minus": delta, "sha256": digest(output)}))


if __name__ == "__main__":
    main()
