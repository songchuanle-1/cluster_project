"""Static information dependencies, not native behavior or candidate admission."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "66fa1e81aec94d5eb10265ea533669ac"
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
source = ROOT / "Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py"
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"
function = next(n for n in ast.walk(ast.parse(source.read_text(encoding="utf-8")))
                if isinstance(n, ast.FunctionDef) and n.name == "loss_sem_align")
fields = sorted({n.slice.value for n in ast.walk(function) if isinstance(n, ast.Subscript)
                 and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)})
assert fields == sorted(["positive_map", "modify_positive_map", "pron_positive_map",
                         "other_entity_map", "rel_positive_map"])
assert "masks" not in fields
arguments = [n.arg for n in function.args.args]
assert arguments == ["self", "proj_tokens", "proj_queries", "lang_masks", "targets",
                     "indices", "num_boxes"]
adapter = ROOT / "scripts/native_role_direction_v2_20261014_0010.py"
assert hashlib.sha256(adapter.read_bytes()).hexdigest() == (
    "c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749")
tree = ast.parse(adapter.read_text())
edits = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name == "logit_functions")
strings = [n.value for n in ast.walk(edits) if isinstance(n, ast.Constant)
           and isinstance(n.value, str)]
assert any("nb_pos_obj = positive_map.sum(1)" in value for value in strings)
assert any("tmask[(positive_map &" in value for value in strings)
assert not any("masks" == value or "coords" == value for value in strings)
result = {
    "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
    "source_sha256": digest, "adapter_sha256": hashlib.sha256(adapter.read_bytes()).hexdigest(),
    "native_semantic_arguments": arguments, "read_target_fields": fields,
    "native_semantic_reads_physical_gt_masks": False,
    "native_semantic_reads_reference_instance_identity": False,
    "existing_precedence_mass_edits": "same projected Q/T logits and same role maps; tmask assignment / nb_pos_obj only",
    "limits": "Static dependency check only. The whole model already has geometry; this does not prove geometry absent globally, supervision wrong, new core novel, native backward or any gate PASS.",
    "next_information_path": "A candidate using distinct physical reference roles and support geometry must be distinguished from these scalar role edits, unary sign and generic mask-aware matching."}
path = ROOT / "pipeline/reports/role_information_contract_20261014_0209.json"
with path.open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
