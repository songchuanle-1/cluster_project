"""Reject unintended parent, numeric, or independence changes before admission."""
import ast
import argparse
import hashlib
import json
from pathlib import Path
import yaml
from prepare_flow_20260910 import BASE, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suffix", choices=("mqhf", "mqhc"), default="mqhf")
    args = parser.parse_args()
    code = ROOT / "Cluster"
    parent = code / "framework/model/Quard_model" / (BASE + "_" + args.suffix)
    child = parent.with_name(parent.name + "_tr")
    files = sorted(child.glob("*.py"))
    assert len(files) == 7
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "Quard_model.model_" not in node.module, node.module
        if path.name != "dec.py":
            assert path.read_bytes() == (parent / path.name).read_bytes()
    old = (parent / "dec.py").read_text(encoding="utf-8")
    new = (child / "dec.py").read_text(encoding="utf-8")
    assert old.count("if previous_masks is not None:") == 1
    assert new == old.replace("if previous_masks is not None:",
                             "if layer_i == len(self.decoder_layers) - 1 and previous_masks is not None:")
    config = code / "configs/Quard" / ("ctf_hcg_csort_" + args.suffix + "_tr") / (child.name + ".yaml")
    original = code / "configs/Quard" / ("ctf_hcg_csort_" + args.suffix) / (parent.name + ".yaml")
    assert config.read_bytes() == original.read_bytes()
    assert len(list((code / "configs").rglob(config.name))) == 1
    cfg = yaml.safe_load(config.read_text())
    assert (cfg["train"]["seed"], cfg["train"]["epochs"], cfg["lr_scheduler"]["max_iters"]) == (1999, 50, 70)
    test = "validate_flow_terminal.py" if args.suffix == "mqhf" else "validate_consensus_terminal.py"
    ast.parse((code / "tools" / test).read_text())
    result = dict(passed=True, files=7, numerical_yaml_byte_identical=True,
                  only_change="remove four recurrent feedback edges", config=str(config),
                  config_sha256=hashlib.sha256(config.read_bytes()).hexdigest())
    label = "flow" if args.suffix == "mqhf" else "consensus"
    (ROOT / f"pipeline/reports/{label}_static_20260910.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
