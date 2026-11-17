"""Read-only audit of retained SCM evidence; not training admission."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "Cluster"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
PARENT = CODE / "framework/model/Quard_model" / NAME
CANDIDATE = PARENT.with_name(NAME + "_scm")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    unchanged = {}
    for path in PARENT.glob("*.py"):
        other = CANDIDATE / path.name
        ast.parse(other.read_text(encoding="utf-8-sig"))
        unchanged[path.name] = digest(path) == digest(other)
    assert all(value for name, value in unchanged.items() if name != "loss.py")
    assert not unchanged["loss.py"]
    ast.parse((CANDIDATE / "spatial_transport.py").read_text(encoding="utf-8-sig"))
    cross_imports = []
    for path in CANDIDATE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            cross_imports.extend(
                [path.name, name] for name in names
                if "Quard_model.model_" in name and NAME + "_scm" not in name
            )
    assert not cross_imports, cross_imports
    configs = list((CODE / "configs").rglob(NAME + "_scm.yaml"))
    assert len(configs) == 1
    parent_configs = list((CODE / "configs").rglob(NAME + ".yaml"))
    assert len(parent_configs) == 1
    assert digest(configs[0]) == digest(parent_configs[0])
    reports = ROOT / "pipeline/reports"
    candidate = json.loads((reports / "scm_full_results_20260914.json").read_text())
    parent = json.loads((reports / "scm_parent_full_results_20260914.json").read_text())
    assert candidate["timing_input"] == parent["timing_input"]
    assert candidate["torch"] == parent["torch"] and candidate["gpu"] == parent["gpu"]
    assert candidate["flops"] == parent["flops"]
    result = {
        "unchanged_parent_files": unchanged,
        "cross_variant_imports": cross_imports,
        "config_unique_and_parent_bytes_equal": True,
        "syntax_pass": True,
        "paired_input": candidate["timing_input"],
        "counted_torch_delta_g": candidate["flops"]["counted_g"] - parent["flops"]["counted_g"],
        "inference_allocated_delta_mib": candidate["timing"]["peak_allocated_mib"] - parent["timing"]["peak_allocated_mib"],
        "training_peak_delta_mib": candidate["real_batch"]["peak_mib"] - parent["real_batch"]["peak_mib"],
        "median_delta_ms": candidate["timing"]["median_ms"] - parent["timing"]["median_ms"],
        "p90_delta_ms": candidate["timing"]["p90_ms"] - parent["timing"]["p90_ms"],
        "admitted": False,
        "limits": "Static audit only; novelty and matched historical VAL resource protocol pending. No runtime resolver test.",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
