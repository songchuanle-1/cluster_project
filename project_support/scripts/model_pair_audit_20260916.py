"""Bounded source audit for M95/PIRS; never imports a native model."""
import ast
import hashlib
from pathlib import Path


def functions(source):
    tree = ast.parse(source)
    result = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result[node.name + "." + child.name] = ast.dump(
                        child, include_attributes=False)
    return result


def callsites(source):
    tree = ast.parse(source)
    return [
        dict(line=node.lineno, call=ast.unparse(node.func))
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and ast.unparse(node.func) == "FurthestPointSampling.apply"
    ]


def audit(root):
    root = Path(root)
    name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
    base = root / "Cluster/framework/model/Quard_model"
    files = ("__init__.py", "backbone.py", "dec.py", "hier_postprocess.py",
             "loss.py", "network.py", "sample_model.py")
    sources, evidence, equal = {}, [], {}
    for label, package in (("M95", name), ("PIRS", name + "_pirs")):
        sources[label] = {}
        for filename in files:
            path = base / package / filename
            raw = path.read_bytes()
            sources[label][filename] = raw.decode("utf-8-sig")
            evidence.append(dict(path=path.relative_to(root).as_posix(),
                                 sha256=hashlib.sha256(raw).hexdigest()))
    for filename in files:
        equal[filename] = (
            sources["M95"][filename] == sources["PIRS"][filename])
    left, right = (functions(sources[label]["loss.py"]) for label in ("M95", "PIRS"))
    changed = sorted(key for key in left.keys() | right.keys()
                     if left.get(key) != right.get(key))
    sites = {filename: callsites(sources["M95"][filename])
             for filename in ("network.py", "hier_postprocess.py")}
    return dict(
        scope="Local static model/source comparison, not deployed-code verification",
        source_equal=equal, changed_loss_methods=changed,
        matcher_ast_equal=(left.get("Criterion.match_sampled_ins") is not None
                           and left.get("Criterion.match_sampled_ins")
                           == right.get("Criterion.match_sampled_ins")),
        fps_callsites=sites,
        evidence=evidence,
        finding="Entry FPS capture does not record hierarchical FPS outputs.",
        native_execution_completed=False,
        scientific_validation_complete=False,
        next_action="Record hierarchical partition outputs plus entry FPS for both "
                    "bound model classes on frozen inputs; require equality of "
                    "exogenous geometry, not learned query selections.",
        limitations=[
            "Source equality does not imply checkpoint or native-output equality.",
            "External CUDA FPS kernel and runtime nondeterminism are not audited.",
            "Native entry remains M95-only; PIRS class binding remains required.",
            "No expanded semantic sample, efficacy result or admission."])
