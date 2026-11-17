"""Guarded source/config provenance for the exact computation optimization."""
import ast
import hashlib
import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "c9de23ffb1804f1eaa81cf54b94b9d6a"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text(encoding="utf-8"))
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    package = ROOT / "Cluster/framework/model/Quard_model" / NAME
    archive = ROOT / "pipeline/reports" / ("bps_package_v2_" + TOKEN)
    config = ROOT / "Cluster/configs/Quard/bps" / (NAME + ".yaml")
    parent = ROOT / "Cluster/configs/Quard/ctf_hcg_csort" / (NAME[:-4] + ".yaml")
    candidate, original = yaml.safe_load(config.read_text(encoding="utf-8")), yaml.safe_load(parent.read_text(encoding="utf-8"))
    candidate["model"].pop("between_catalog")
    candidate["model"].pop("between_catalog_sha256")
    assert candidate == original
    changed = []
    for path in package.glob("*.py"):
        module = ast.parse(path.read_text(encoding="utf-8"))
        compile(module, str(path), "exec")
        if sha(path) != sha(archive / path.name):
            changed.append(path.name)
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom) and not node.level:
                assert "Quard_model.model_" not in (node.module or "")
    assert changed == ["between_support.py"]
    def operator(path):
        return ast.dump(next(n for n in ast.parse(path.read_text(encoding="utf-8")).body
                             if isinstance(n, ast.FunctionDef) and n.name == "support_excess"))
    assert operator(package / "between_support.py") == operator(archive / "between_support.py")
    manifest = {"tick_token": TOKEN, "package": {p.name: sha(p) for p in sorted(package.glob("*.py"))},
                "config_sha256": sha(config), "changed_files": changed,
                "loss_operator_ast_unchanged": True, "numerical_config_unchanged": True,
                "no_cross_variant_imports": True, "version": "exact-prepare-v3",
                "scope": "Static provenance only, not native equivalence or admission."}
    output = ROOT / "pipeline/reports" / ("bps_source_manifest_" + TOKEN + ".json")
    with output.open("x") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"manifest": str(output), "sha256": sha(output)}))


if __name__ == "__main__":
    main()
