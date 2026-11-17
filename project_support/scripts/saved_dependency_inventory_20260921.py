"""Bounded static requirements for saved collation, not runtime attestation."""
import ast
import hashlib
from pathlib import Path
import sys

from relocated_native_factory_20260920 import REQUIRED_ASSETS


SOURCES = (
    "framework/__init__.py",
    "framework/dataset/__init__.py",
    "framework/dataset/scannetv2.py",
    "framework/lib/pointgroup_ops/__init__.py",
    "framework/lib/pointgroup_ops/pointgroup_ops.py",
)
DIRECT_PACKAGES = {
    "dgl", "gorilla", "numpy", "scipy", "sng_parser", "torch",
    "torch_scatter", "tqdm", "transformers",
}


def source_requirements(raw, filename):
    """Parse checked bytes only; include function-local/conditional imports."""
    tree = ast.parse(raw, filename=filename)
    imports, dynamic = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(dict(module=a.name, level=0, names=[],
                                line=node.lineno) for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(dict(module=node.module or "", level=node.level,
                                names=[a.name for a in node.names], line=node.lineno))
        elif isinstance(node, ast.Call):
            function = node.func
            name = (function.id if isinstance(function, ast.Name) else
                    function.attr if isinstance(function, ast.Attribute) else "")
            if name in {"import_module", "__import__"}:
                value = node.args[0] if node.args else None
                dynamic.append(dict(
                    line=node.lineno, call=ast.unparse(function),
                    literal=value.value if isinstance(value, ast.Constant)
                    and isinstance(value.value, str) else None,
                    resolved=False))
    return dict(imports=sorted(imports, key=lambda row: (row["line"], row["module"])),
                dynamic_imports=sorted(dynamic, key=lambda row: row["line"]))


def inventory(code_root):
    """Inspect five explicit sources, without package imports or directory scans.

    This is a deployment checklist for the existing saved-only operation. Native
    package files, transitive dependencies and constructor bytes must be measured
    independently on the authorized host before executing the handoff.
    """
    root = Path(code_root).absolute()
    records, packages = [], set()
    for name in SOURCES:
        path = root / name
        if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
                or not path.is_file()):
            raise ValueError("Missing or redirected inventory source: " + name)
        raw = path.read_bytes()
        parsed = source_requirements(raw, name)
        for row in parsed["imports"]:
            if row["level"]:
                continue
            top = row["module"].split(".")[0]
            if top not in sys.stdlib_module_names | {"framework", "pointgroup_ops"}:
                packages.add(top)
        records.append(dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), **parsed))
    if packages != DIRECT_PACKAGES:
        raise ValueError("Direct package inventory drift: missing=%s added=%s" % (
            sorted(DIRECT_PACKAGES - packages), sorted(packages - DIRECT_PACKAGES)))
    # Recheck all inputs after parsing to catch ordinary source edits during audit.
    for row in records:
        path = root / row["path"]
        if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
                or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]):
            raise ValueError("Inventory source changed during audit")
    return dict(
        contract="saved-collation-static-requirements-v1",
        sources=records, direct_packages=sorted(packages),
        local_package="pointgroup_ops",
        native_extension="pointgroup_ops.pointgroup_ops_ext",
        native_extension_requirements=[
            "Resolve actual loaded extension path and hash on server-4.",
            "Match project_cluster Python ABI, Torch ABI and shared-library dependencies.",
            "Verify CPU voxelize_idx behavior inside the enforced scratch boundary.",
            "Do not select an archived binary by filename alone or build while CUDA is hidden."],
        constructor_requirements=dict(
            required_assets=sorted(REQUIRED_ASSETS),
            tokenizer_inventory="Every existing file under roberta-base, including optional files.",
            scene_file_listing=dict(
                pattern="scannetv2/train/*_refer.pth", minimum_entries=1,
                contents_loaded_by_constructor=False,
                reason="get_sp_filenames runs before TRAIN metadata and asserts nonempty."),
            scene_graph_cache="Must already exist; absent-cache path parses and writes.",
            data_source_policy="Verify saved migration bytes before loading; never resample saved groups."),
        scope="Direct static imports and manually audited constructor requirements only.",
        native_environment_verified=False, external_dependency_attestation=False,
        native_execution_completed=False, scientific_validation_complete=False,
        admission=False,
        limitations=[
            "Import names do not establish installed distribution names, versions or file hashes.",
            "Transitive package imports, shared libraries and dynamic imports remain unresolved.",
            "AST parsing includes nonexecuted branches and does not establish runtime reachability.",
            "Stdlib classification uses the local interpreter, not the target Python runtime.",
            "Constructor requirements are source-audited expectations, not destination observations.",
            "A readable host root is not an exhaustive dependency boundary.",
            "The original physical producer hash and saved registry are unchanged."])
