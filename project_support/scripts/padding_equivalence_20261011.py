"""CPU operator-contract comparison; not a repeated native cohort capture."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import types


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--old-probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import torch
    torch.set_num_threads(1)
    path = args.root / ("framework/model/Quard_model/"
                       "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py")
    tree = ast.parse(path.read_text())
    criterion = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Criterion")
    sem = next(n for n in criterion.body if isinstance(n, ast.FunctionDef) and n.name == "loss_sem_align")
    idx = next(n for n in criterion.body if isinstance(n, ast.FunctionDef)
               and n.name == "_get_src_permutation_idx")
    old_tree = ast.parse(args.old_probe.read_text())
    old_expression = next(n for n in ast.walk(old_tree)
                          if isinstance(n, ast.JoinedStr)
                          and "masked_fill(~lang_masks.bool()" in ast.unparse(n))
    old_text = ast.unparse(old_expression)
    assert "logsumexp(2)" in old_text and "float('-inf')" in old_text
    native_scope = {"torch": torch}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[idx, sem], type_ignores=[])),
                 "<current-sem>", "exec"), native_scope)
    patched = ast.parse(ast.unparse(sem))
    replaced = 0
    for n in ast.walk(patched):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "neg_term"
                                            for t in n.targets) and isinstance(n.value, ast.Call):
            if n.value.func.attr == "logsumexp" and n.value.args[0].value == 2:
                expression = ast.unparse(n.value.func.value)
                n.value = ast.parse(
                    f"({expression}).masked_fill(~lang_masks.bool()[:, None, :], "
                    "float('-inf')).logsumexp(2)", mode="eval").body
                replaced += 1
    assert replaced == 1
    patch_scope = {"torch": torch}
    exec(compile(ast.fix_missing_locations(patched), "<same-old-patch>", "exec"), patch_scope)
    obj = types.SimpleNamespace(temperature=0.07, eos_coef=0.1)
    obj._get_src_permutation_idx = types.MethodType(native_scope["_get_src_permutation_idx"], obj)
    native = types.MethodType(native_scope["loss_sem_align"], obj)
    fixed = types.MethodType(patch_scope["loss_sem_align"], obj)
    torch.manual_seed(1999)
    q = (torch.randn(1, 3, 4) * 0.02).requires_grad_(True)
    t = (torch.randn(1, 7, 4) * 0.02).requires_grad_(True)
    valid = torch.tensor([[1, 1, 1, 1, 1, 0, 0]])
    target = {key: torch.zeros(1, 7) for key in (
        "positive_map", "modify_positive_map", "pron_positive_map", "other_entity_map", "rel_positive_map")}
    target["positive_map"][0, 1] = 1
    indices = [(torch.tensor([0]), torch.tensor([0]))]
    loss = native(t, q, valid, [target], indices, 1)
    g = torch.autograd.grad(loss, t)[0]
    fl = fixed(t, q, valid, [target], indices, 1)
    fg = torch.autograd.grad(fl, t)[0]
    pad = ~valid.bool()
    assert g[pad].abs().sum() > 0 and fg[pad].abs().sum() == 0
    t2 = t.detach().clone()
    t2[pad] *= 11
    changed = native(t2, q, valid, [target], indices, 1)
    unchanged = fixed(t2, q, valid, [target], indices, 1)
    torch.testing.assert_close(fl, unchanged, atol=0, rtol=0)
    assert changed != loss
    result = {"contract": "padding_operator_equivalence_v1", "seed": 1999,
              "native_source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "old_probe_sha256": hashlib.sha256(args.old_probe.read_bytes()).hexdigest(),
              "one_identical_support_mask_rewrite": replaced == 1,
              "native_padding_gradient_l1": float(g[pad].abs().sum()),
              "masked_padding_gradient_l1": float(fg[pad].abs().sum()),
              "native_invalid_only_loss_delta": float(changed.detach() - loss.detach()),
              "masked_invalid_only_loss_delta": float(unchanged.detach() - fl.detach()),
              "disposition": "Current repair repeats the 20260916 support-mask operator; not an independent Phase1 mechanism.",
              "limits": "CPU synthetic operator contract only; existing native cohort evidence cited separately; no efficacy claim."}
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
