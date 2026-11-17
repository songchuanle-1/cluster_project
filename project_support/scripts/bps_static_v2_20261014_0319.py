"""Candidate-local static provenance/config check, guarded by current lease."""
import ast
import hashlib
import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "1d59938f077948578e91e2cf34fc9d53"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    package = ROOT / "Cluster/framework/model/Quard_model" / NAME
    config = ROOT / "Cluster/configs/Quard/bps" / (NAME + ".yaml")
    parent = ROOT / "Cluster/configs/Quard/ctf_hcg_csort" / (NAME[:-4] + ".yaml")
    candidate = yaml.safe_load(config.read_text())
    original = yaml.safe_load(parent.read_text())
    catalog_path = candidate["model"].pop("between_catalog")
    catalog_sha256 = candidate["model"].pop("between_catalog_sha256")
    assert candidate == original
    assert candidate["train"]["seed"] == 1999
    assert candidate["train"]["epochs"] == 50 and candidate["lr_scheduler"]["max_iters"] == 70
    findings = []
    for path in package.glob("*.py"):
        module = ast.parse(path.read_text(encoding="utf-8"))
        compile(module, str(path), "exec")
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                if "Quard_model.model_" in node.module:
                    findings.append({"file": path.name, "cross_variant": node.module})
            if isinstance(node, ast.Name) and node.id in ("TargetMentionRoles", "PointDetailField"):
                findings.append({"file": path.name, "forbidden_field": node.id})
    assert not findings
    network = ast.parse((package / "network.py").read_text())
    predict = next(n for n in ast.walk(network) if isinstance(n, ast.FunctionDef) and n.name == "predict")
    assert "between_support" not in ast.unparse(predict)
    result = {"tick_token": TOKEN, "package": {p.name: sha(p) for p in sorted(package.glob("*.py"))},
              "config_sha256": sha(config), "parent_config_sha256": sha(parent),
              "config_delta_only": "nonlearned TRAIN catalog path and frozen content hash",
              "catalog_sha256": catalog_sha256,
              "catalog_path": catalog_path, "no_cross_variant_imports": True,
              "no_tmr_or_pdc_field": True, "prediction_ast_catalog_free": True,
              "compiled_files": len(list(package.glob("*.py"))),
              "scope": "Static independence/config evidence, not native backward/resources/admission."}
    output = ROOT / "pipeline/reports" / ("bps_source_manifest_v2_" + TOKEN + ".json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"manifest": str(output), "sha256": sha(output), "files": result["compiled_files"]}))


if __name__ == "__main__":
    main()
