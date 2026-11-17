"""Explain caption-only differences using the original parser fallback prefix."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    original = PIPE / "graph_identity_audit_20261012_1908.json"
    source = ROOT / "framework/dataset/scannetv2.py"
    assert sha(original) == "3ab4f8d6816b0495cd931d908b223188a5bcb6045711b5c0583024a8f44291b4"
    assert sha(source) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    fn = next(n for n in ast.parse(source.read_text()).body
              if isinstance(n, ast.FunctionDef) and n.name == "Scene_graph_parse")
    assignment = next(n for n in ast.walk(fn) if isinstance(n, ast.Assign)
                      and isinstance(n.value, ast.BinOp)
                      and isinstance(n.value.left, ast.Constant)
                      and n.value.left.value == "This is an object . ")
    fallback_if = next(n for n in fn.body if isinstance(n, ast.If)
                       and assignment in n.body)
    audit = json.loads(original.read_text())
    explained = [r for r in audit["mismatch_rows"]
                 if r["actual"] == assignment.value.left.value + r["expected"]]
    unexplained = [r for r in audit["mismatch_rows"] if r not in explained]
    # Execute the original fallback branch with a deliberately empty parse.
    calls = []

    class Parser:
        @staticmethod
        def parse(caption):
            calls.append(caption)
            return ([{"node_id": 0, "node_type": "Object"}], [])

    namespace = {"caption": "a test object", "graph_node": [], "graph_edge": [],
                 "sng_parser": Parser}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fallback_if], type_ignores=[])),
                 str(source), "exec"), namespace)
    assert namespace["caption"] == "This is an object . a test object"
    assert calls == [namespace["caption"]]
    result = {
        "tick_token": "5d01839a3f8642658868200f877656f3",
        "observed_at": datetime.now(timezone.utc).isoformat(), "cpu_only": True,
        "raw_mismatches": audit["caption_mismatches"], "fallback_explained": len(explained),
        "unexplained": len(unexplained), "unexplained_rows": unexplained,
        "fallback_prefix": assignment.value.left.value,
        "synthetic_native_branch_control": True,
        "actual_parser_empty_condition_replayed": False,
        "identity_result_sha256": sha(original), "dataset_sha256": sha(source),
        "script_sha256": sha(Path(__file__)),
        "scope": "Stored caption body identity and native branch compatibility, not semantic correctness or a real parser replay.",
    }
    output = PIPE / "graph_fallback_audit_20261012_1908.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"fallback_explained": len(explained), "unexplained": len(unexplained),
                      "output_sha256": sha(output)}), flush=True)


if __name__ == "__main__":
    main()
