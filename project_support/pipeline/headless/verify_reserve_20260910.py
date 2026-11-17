"""Static isolation and parent-equivalence admission for the three copies."""
import ast
import hashlib
import json
from pathlib import Path
import yaml
from prepare_reserve_20260910 import ROOT, BASE, SUFFIXES


def main():
    code = ROOT / "Cluster"
    results = []
    for suffix in SUFFIXES:
        parent = code / "framework/model/Quard_model" / f"{BASE}_{suffix}"
        child = parent.with_name(parent.name + "_tr")
        files = sorted(child.glob("*.py"))
        assert len(files) == 7
        for file in files:
            tree = ast.parse(file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert "Quard_model.model_" not in node.module, (file, node.module)
            if file.name != "dec.py":
                assert file.read_bytes() == (parent / file.name).read_bytes()
        old = (parent / "dec.py").read_text(encoding="utf-8")
        new = (child / "dec.py").read_text(encoding="utf-8")
        assert new.count("if layer_i == len(self.decoder_layers) - 1 and previous_masks is not None:") == 1
        if suffix != "mqtd":
            assert new == old.replace("if previous_masks is not None:",
                                      "if layer_i == len(self.decoder_layers) - 1 and previous_masks is not None:")
        config = code / "configs/Quard" / f"ctf_hcg_csort_{suffix}_tr" / f"{BASE}_{suffix}_tr.yaml"
        original = code / "configs/Quard" / f"ctf_hcg_csort_{suffix}" / f"{BASE}_{suffix}.yaml"
        assert len(list((code / "configs").rglob(config.name))) == 1
        assert yaml.safe_load(config.read_text()) == yaml.safe_load(original.read_text())
        assert config.read_bytes() == original.read_bytes()
        results.append({"suffix": suffix, "passed": True, "files": len(files),
                        "config": str(config.relative_to(code)).replace("\\", "/"),
                        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest()})
    ast.parse((code / "tools/validate_terminal_reserve.py").read_text())
    (ROOT / "pipeline/reports/reserve_static_20260910.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
