"""Default NOP. Actual r0/r1 constructor statements, CPU only."""
import argparse
import ast
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import pickle
import random
import socket
import subprocess
import sys
import traceback
from types import SimpleNamespace


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def constructor(tree):
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)
               and node.name == "C2F_ClusterAttn_RVEC_CSORT"]
    assert len(classes) == 1
    methods = [node for node in classes[0].body if isinstance(node, ast.FunctionDef)
               and node.name == "__init__"]
    assert len(methods) == 1
    return methods[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_OR_EXTERNAL_ACTION"}))
        return
    assert sys.dont_write_bytecode and not sys.flags.isolated
    assert socket.gethostname() == "dl04-MS-7E06" and os.getuid() == os.geteuid() == 1001
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    payload = globals()["BOUND_PAYLOAD"]
    request = payload["request"]
    binding_raw = base64.b64decode(payload["binding"], validate=True)
    binding = json.loads(binding_raw)
    assert digest(binding_raw) == request["source_binding_sha256"]
    assert request["owner"] == binding["owner"] and request["execution_authorized"] is True
    assert datetime.now(timezone.utc) < datetime.fromisoformat(binding["owner"]["deadline_at"])
    assert request["producer_sha256"] == globals()["ACTUAL_PRODUCER_SHA256"]
    assert request["GPU_use_authorized"] is False and request["training_launch_authorized"] is False
    assert binding["source_parent_commit"] == "0f8cc0f978b38c24e159d3a2d37344f59cc9a0be"
    assert binding["runtime_original_parent_commit"] == "0747f6acec1c61018ec99acf2efa5329c9b3523c"
    assert binding["source_version_proof"]["source_commit"] == binding["source_commit"]
    assert binding["source_version_proof"]["owner"] == binding["owner"]
    source = {name: base64.b64decode(raw, validate=True)
              for name, raw in payload["sources"].items()}
    assert set(source) == {"r0_hierarchy", "r1_hierarchy", "operator"}
    assert all(digest(source[name]) == binding["probe_source_hashes"][name] for name in source)
    head = subprocess.check_output(
        ["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C",
         "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107", "rev-parse", "HEAD"],
        text=True, timeout=15).strip()
    assert head == binding["runtime_original_parent_commit"]
    r0, r1 = (ast.parse(source[name].decode("utf-8")) for name in ("r0_hierarchy", "r1_hierarchy"))
    raw_init, guarded_init = constructor(r0), constructor(r1)
    assert len(raw_init.body) == len(guarded_init.body) == 5
    raw_statement, guarded_statement = raw_init.body[2], guarded_init.body[2]
    assert isinstance(raw_statement, ast.Assign) and isinstance(guarded_statement, ast.With)
    expected = ast.parse("with torch.random.fork_rng(devices=[]):\n    pass\n").body[0]
    assert len(guarded_statement.items) == len(guarded_statement.body) == 1
    assert ast.dump(guarded_statement.items[0]) == ast.dump(expected.items[0])
    assert ast.dump(guarded_statement.body[0]) == ast.dump(raw_statement)
    unwrapped = copy.deepcopy(r1)
    constructor(unwrapped).body[2:3] = copy.deepcopy(guarded_statement.body)
    assert ast.dump(unwrapped) == ast.dump(r0), "Full hierarchy AST must equal r0 after only unwrapping"
    operator_tree = ast.parse(source["operator"].decode("utf-8"))
    classes = [node for node in operator_tree.body if isinstance(node, ast.ClassDef)
               and node.name == "FineLeafReceiverVectorExchange"]
    assert len(classes) == 1
    result = {
        "owner": binding["owner"], "candidate_id": binding["candidate_id"],
        "experiment_id": "M234-RVE", "implementation_revision": 1,
        "producer_sha256": request["producer_sha256"],
        "request_sha256": globals()["ACTUAL_REQUEST_SHA256"],
        "source_binding_sha256": digest(binding_raw),
        "source_commit": binding["source_commit"],
        "source_parent_commit": binding["source_parent_commit"],
        "runtime_HEAD": head, "probe_source_hashes": binding["probe_source_hashes"],
        "full_hierarchy_AST_exact_after_only_unwrapping": True,
        "actual_constructor_statements_executed": True,
        "operator_class_extracted_from_hash_bound_full_source": True,
        "GPU_use": False, "native_model_imported": False, "data_or_checkpoint_loaded": False,
        "forward_backward_optimizer": "NOT_RUN", "CPU8": "NOT_REPEATED",
        "efficacy": "UNKNOWN", "novelty": "UNKNOWN", "scientific_admission": False,
    }
    python_state = random.getstate()
    torch = None
    torch_state = None
    numpy_rng = None
    numpy_state = None
    failure = None
    try:
        import torch
        import numpy as np
        result["cuda_initialized_before"] = torch.cuda.is_initialized()
        assert result["cuda_initialized_before"] is False
        torch_state = torch.get_rng_state().clone()
        numpy_rng = np.random
        numpy_state = pickle.dumps(numpy_rng.get_state())
        scope = {"torch": torch, "nn": torch.nn, "math": math}
        operator_module = ast.Module(body=[copy.deepcopy(classes[0])], type_ignores=[])
        exec(compile(ast.fix_missing_locations(operator_module), "<actual-operator-class>", "exec"), scope)
        entry = torch.get_rng_state().clone()
        raw_self = SimpleNamespace(d_model=256, per_layer_topk_list=[32, 16, 8], nhead=8)
        raw_module = ast.Module(body=[copy.deepcopy(raw_statement)], type_ignores=[])
        exec(compile(ast.fix_missing_locations(raw_module), "<actual-r0-constructor-statement>", "exec"),
             scope, {"self": raw_self})
        raw_after = torch.get_rng_state().clone()
        raw_parameters = {name: value.detach().clone()
                          for name, value in raw_self.fine_exchange.named_parameters()}
        torch.set_rng_state(entry)
        guarded_self = SimpleNamespace(d_model=256, per_layer_topk_list=[32, 16, 8], nhead=8)
        guarded_module = ast.Module(body=[copy.deepcopy(guarded_statement)], type_ignores=[])
        exec(compile(ast.fix_missing_locations(guarded_module), "<actual-r1-constructor-statement>", "exec"),
             scope, {"self": guarded_self})
        guarded_after = torch.get_rng_state().clone()
        guarded_parameters = dict(guarded_self.fine_exchange.named_parameters())
        assert set(raw_parameters) == set(guarded_parameters) == {"wr", "wd", "w2", "b1", "b2"}
        result["parameters"] = []
        for name in ("wr", "wd", "w2", "b1", "b2"):
            raw, guarded = raw_parameters[name], guarded_parameters[name].detach()
            expected_shape = (8, 32) if name.startswith("b") else (8, 32, 32)
            assert tuple(raw.shape) == tuple(guarded.shape) == expected_shape
            assert raw.dtype == guarded.dtype == torch.float32
            assert raw.device.type == guarded.device.type == "cpu"
            raw_hash = digest(raw.contiguous().numpy().tobytes())
            guarded_hash = digest(guarded.contiguous().numpy().tobytes())
            equal = torch.equal(raw, guarded) and raw_hash == guarded_hash
            assert equal, name
            result["parameters"].append({
                "name": name, "shape": list(raw.shape), "dtype": str(raw.dtype),
                "r0_sha256": raw_hash, "r1_sha256": guarded_hash, "equal": equal})
        result["all_five_parameters_identical"] = True
        result["parameter_count"] = sum(value.numel() for value in raw_parameters.values())
        assert result["parameter_count"] == 25088
        result["raw_caller_rng_advanced"] = not torch.equal(entry, raw_after)
        result["guarded_caller_rng_preserved_exact"] = torch.equal(entry, guarded_after)
        result["CPU_rng_hashes"] = {name: digest(state.numpy().tobytes()) for name, state in (
            ("entry", entry), ("r0_after", raw_after), ("r1_after", guarded_after))}
        assert result["raw_caller_rng_advanced"] is True
        assert result["guarded_caller_rng_preserved_exact"] is True
        result["all_fixed_tests_passed"] = True
        result["libraries"] = {"torch": torch.__version__, "torch_file": torch.__file__,
                               "numpy": np.__version__, "python": sys.executable}
    except Exception as error:
        failure = error
        result["all_fixed_tests_passed"] = False
        result["error"] = {"type": type(error).__name__, "message": str(error),
                           "traceback": traceback.format_exc()}
    finally:
        random.setstate(python_state)
        result["python_rng_restored_exact"] = random.getstate() == python_state
        if torch_state is not None:
            torch.set_rng_state(torch_state)
            result["torch_CPU_rng_restored_exact"] = torch.equal(torch.get_rng_state(), torch_state)
        if numpy_state is not None:
            numpy_rng.set_state(pickle.loads(numpy_state))
            result["numpy_rng_restored_exact"] = pickle.dumps(numpy_rng.get_state()) == numpy_state
        if torch is not None:
            result["cuda_initialized_after"] = torch.cuda.is_initialized()
    result["recorded_at"] = datetime.now(timezone.utc).isoformat()
    result["status"] = "CONSTRUCTOR_CPU_DISCRIMINATING_PROBE_PASS" if failure is None else "CONSTRUCTOR_CPU_PROBE_FAIL"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    assert failure is None, "Preserve actual failure; no replay"
    assert all(result[name] is True for name in (
        "python_rng_restored_exact", "torch_CPU_rng_restored_exact", "numpy_rng_restored_exact"))
    assert result["cuda_initialized_before"] is False and result["cuda_initialized_after"] is False


if __name__ == "__main__":
    main()
