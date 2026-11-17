"""Read-only independent-package and inference-source audit."""
import ast
import hashlib
import json
from pathlib import Path
import yaml

root = Path("D:/project/cluster_project/Cluster")
base = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
parent = root / "framework/model/Quard_model" / base
child = parent.with_name(base + "_cps")
changed = []
for source in parent.glob("*.py"):
    target = child / source.name
    assert target.is_file() and not target.is_symlink()
    if source.read_bytes() != target.read_bytes():
        changed.append(source.name)
assert sorted(changed) == ["loss.py", "network.py"]
for source in child.glob("*.py"):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert "Quard_model." not in (node.module or "")
pt = ast.parse((parent / "network.py").read_text(encoding="utf-8"))
ct = ast.parse((child / "network.py").read_text(encoding="utf-8"))
methods = lambda tree: {n.name: ast.dump(n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
p, c = methods(pt), methods(ct)
assert {k for k in p if p[k] != c[k]} == {"loss"}
configs = list((root / "configs").rglob(base + "_cps.yaml"))
assert len(configs) == 1
pc = next((root / "configs").rglob(base + ".yaml"))
assert yaml.safe_load(pc.read_text()) == yaml.safe_load(configs[0].read_text())
print(json.dumps(dict(status="PASS", changed_parent_files=changed,
                     inference_ast_unchanged=True, independent=True,
                     exact_parent_config=True, unique_basename=True,
                     files={str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest()
                            for f in [*child.glob("*.py"), configs[0]]}), indent=2))
