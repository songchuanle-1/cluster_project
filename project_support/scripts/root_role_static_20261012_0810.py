"""Local static-only independent package/config verification."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr"
BASE = NAME.removesuffix("_tmr")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
    assert owner["token"] == args.token and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    import yaml
    cfg_path = ROOT / f"Cluster/configs/Quard/ctf_hcg_csort_tmr/{NAME}.yaml"
    base_cfg = ROOT / f"Cluster/configs/Quard/ctf_hcg_csort/{BASE}.yaml"
    assert yaml.safe_load(cfg_path.read_text()) == yaml.safe_load(base_cfg.read_text())
    assert len(list((ROOT / "Cluster/configs").rglob(NAME + ".yaml"))) == 1
    package = ROOT / f"Cluster/framework/model/Quard_model/{NAME}"
    base_package = package.with_name(BASE)
    files, differences = [], []
    for file in sorted(package.glob("*.py")):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        imports = [node.module for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom) and node.module]
        assert not any(BASE in module for module in imports)
        assert not any("Quard_model.model_" in module for module in imports)
        files.append({"filename": file.name, "sha256": sha(file)})
        original = base_package / file.name
        if not original.exists() or sha(original) != sha(file):
            differences.append(file.name)
    assert differences == ["mention_roles.py", "network.py"]
    result = {
        "contract": "target_mention_independent_static_v1", "name": NAME,
        "files": files, "differences_from_champion": differences,
        "config_sha256": sha(cfg_path), "config_values_unchanged": True,
        "basename_unique": True, "cross_variant_imports": False,
        "local_static_only": True, "admission": False,
    }
    output = ROOT / "pipeline/reports/root_role_static_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
