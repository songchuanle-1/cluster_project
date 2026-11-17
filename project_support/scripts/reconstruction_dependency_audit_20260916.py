"""Source-level reconstruction shortcut audit; no actual learned leakage claim."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def method(tree, class_name, name):
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)


def calls(function, attribute):
    return [n for n in ast.walk(function) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute) and n.func.attr == attribute]


def has_path(edges, start, end):
    seen, todo = set(), [start]
    while todo:
        node = todo.pop()
        if node == end:
            return True
        if node in seen:
            continue
        seen.add(node)
        todo.extend(b for a, b in edges if a == node)
    return False


def main():
    network = PACKAGE / "network.py"
    decoder = PACKAGE / "dec.py"
    ntree, dtree = [ast.parse(p.read_text(encoding="utf-8")) for p in (network, decoder)]
    # Locate the concrete class owning native loss, without assuming its spelling.
    cls = next(c for c in ntree.body if isinstance(c, ast.ClassDef)
               and any(isinstance(n, ast.FunctionDef) and n.name == "loss" for n in c.body))
    loss = method(ntree, cls.name, "loss")
    text = calls(loss, "text_encoder")
    dec = calls(loss, "dec")
    encoder = method(dtree, "Encoder_layer", "forward")
    ila = calls(encoder, "ila")
    forward = method(dtree, "DEC", "forward_iter_pred")
    assert len(text) == len(dec) == len(ila) == 1
    assert ast.unparse(text[0].args[0]) == "lang_tokenss"
    assert ast.unparse(dec[0].args[3]) == "lang_feats"
    assert [ast.unparse(x) for x in ila[0].args[:2]] == ["lang_feats", "inst_feats"]
    assert text[0].lineno < dec[0].lineno
    assert any(isinstance(n, ast.For) and "self.encoder_layers" in ast.unparse(n.iter)
               for n in ast.walk(forward))
    edges = [
        ("unmasked_tokens", "language_encoder"),
        ("language_encoder", "lang_feats"),
        ("lang_feats", "ila"),
        ("ila", "conditioned_visual"),
        ("conditioned_visual", "hypothetical_reconstruction_head"),
        ("unmasked_tokens", "late_mask"),
        ("late_mask", "hypothetical_reconstruction_head"),
    ]
    assert has_path(edges, "unmasked_tokens", "conditioned_visual")
    without_late = [(a, b) for a, b in edges if a != "late_mask" and b != "late_mask"]
    assert has_path(without_late, "unmasked_tokens", "hypothetical_reconstruction_head")
    # A complete-context countermodel recovers a binary hidden token without vision.
    outcomes = [
        dict(hidden=token, image=0, conditioned_visual=token, prediction=token)
        for token in (0, 1)
    ]
    assert all(row["prediction"] == row["hidden"] for row in outcomes)
    # Masking BEFORE any encoder and using an image-only branch removes that bypass.
    masked_edges = [
        ("masked_context", "language_encoder"),
        ("image", "visual_encoder"),
        ("visual_encoder", "hypothetical_reconstruction_head"),
        ("language_encoder", "hypothetical_reconstruction_head"),
    ]
    assert not has_path(masked_edges, "hidden_token", "hypothetical_reconstruction_head")
    source_files = [
        Path(__file__), network, decoder,
        ROOT / "pipeline/reports/mask_grounding_original_20260916.pdf",
        ROOT / "pipeline/reports/3dwg_original_20260916.pdf",
    ]
    result = dict(
        scope="Static AST/source dependency verification and finite countermodel only.",
        checks_passed=6,
        code_locations=dict(text_encoder=f"{network.relative_to(ROOT).as_posix()}:{text[0].lineno}",
                            decoder=f"{network.relative_to(ROOT).as_posix()}:{dec[0].lineno}",
                            language_to_visual=f"{decoder.relative_to(ROOT).as_posix()}:{ila[0].lineno}"),
        bypass_edges=edges, late_mask_bypass=True,
        countermodel=outcomes, mask_before_encoder_removes_direct_bypass=True,
        limitations=[
            "No reconstruction head currently exists;not a demonstrated bug in native grounding.",
            "Graph reachability allows information transfer;does not prove trained features encode a word.",
            "Removing direct leakage does not remove textual priors or establish visual dependence.",
            "Masked conditional categorical prediction is not invalidated by diverse same-object captions.",
            "Mask Grounding Eq4 already masks before language encoding and uses image-only features.",
            "No novelty,resource,nativebackward,efficacy or admission claim.",
        ],
        evidence=[dict(path=p.relative_to(ROOT).as_posix(),
                       sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in source_files])
    out = ROOT / "pipeline/reports/reconstruction_dependency_20260916.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
