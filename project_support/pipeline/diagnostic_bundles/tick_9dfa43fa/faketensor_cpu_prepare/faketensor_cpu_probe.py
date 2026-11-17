"""Default NOP. One fixed CPU FakeTensor/type-check/_apply observation only."""
import argparse
import base64
import builtins
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import pickle
import random
import socket
import subprocess
import sys
import traceback

EXPECTED_OWNER = {'token': '9dfa43fa89ad4dc4832126a940ed821e', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-08T19:05:14.568365+00:00', 'deadline_at': '2026-11-08T20:05:14.568365+00:00', 'context_sha256': '12e82b3f247ce035e8d9d8c8a16ad534b0ef96de3948a3d3c2d07c4abd3177c5', 'pending_sha256': 'a50fe33d3236d8b847c8c284b2fe917ac60aae7caf766e0969b25b33ee0a10d5'}
SOURCE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
GPU_UUID_PROVENANCE_ONLY = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
RECEIPT_SHA = "52bf897dc89729063ffb429035b1cd07f14d3ea8d3e690812a4e3adfb48ed266"
REVISION_SHA = "3edbff4aa35f05a36da799b23cb54e154e6387faa30b1953a659b47267ccf9e2"
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def callable_identity(obj):
    result = {"process_local_id": id(obj), "object_type_module": type(obj).__module__,
              "object_type_qualname": type(obj).__qualname__, "repr": repr(obj)[:1000],
              "module": getattr(obj, "__module__", None), "qualname": getattr(obj, "__qualname__", None),
              "is_class": inspect.isclass(obj), "is_builtin": inspect.isbuiltin(obj), "callable": callable(obj)}
    for name, operation in (("signature", lambda: str(inspect.signature(obj))),
                            ("source_file", lambda: inspect.getsourcefile(obj))):
        try:
            result[name] = operation()
        except (TypeError, ValueError, OSError) as error:
            result[name + "_unavailable"] = type(error).__name__ + ": " + str(error)
    code = getattr(obj, "__code__", None)
    if code is not None:
        result["code_filename"] = code.co_filename
        result["code_first_line"] = code.co_firstlineno
        result["bytecode_sha256"] = sha(code.co_code)
    path = result.get("source_file")
    if path and Path(path).is_file():
        result["source_file_sha256"] = sha(Path(path).read_bytes())
    return result


def case(name, operation):
    try:
        return {"name": name, "returned": True, "observation": operation()}
    except Exception as error:
        return {"name": name, "returned": False, "exception_type": type(error).__name__,
                "exception_message": str(error), "traceback": traceback.format_exc()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_IMPORT_OR_EXTERNAL_ACTION"}))
        return
    assert sys.flags.isolated and sys.dont_write_bytecode
    assert socket.gethostname() == "dl04-MS-7E06" and os.getuid() == os.geteuid() == 1001
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "" and os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert Path.cwd() == Path("/") and str(Path(sys.executable)) == PYTHON
    request = globals()["BOUND_REQUEST"]
    assert request["owner"] == EXPECTED_OWNER and request["execution_authorized"] is True
    assert request["producer_sha256"] == globals()["ACTUAL_PRODUCER_SHA256"]
    assert request["source_commit"] == SOURCE and request["runtime_root"] == RUNTIME
    assert request["gpu_uuid_provenance_only"] == GPU_UUID_PROVENANCE_ONLY
    assert request["GPU_use_authorized"] is False and request["training_launch_authorized"] is False
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED_OWNER["deadline_at"])
    receipt_bytes = base64.b64decode(request["admission_receipt"]["bytes_base64"], validate=True)
    assert sha(receipt_bytes) == request["admission_receipt"]["sha256"] == RECEIPT_SHA
    receipt = json.loads(receipt_bytes)
    assert receipt["id"] == "M233-NDE" and receipt["code_commit"] == SOURCE
    assert receipt["implementation_revision_sha256"] == request["implementation_revision_sha256"] == REVISION_SHA
    assert receipt["canonical_receipt"] is True and receipt["draft"] is False
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(PATH="/usr/bin:/bin", GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_SYSTEM="/dev/null", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_COUNT="0")
    head = subprocess.check_output(["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", RUNTIME,
                                    "rev-parse", "--verify", "HEAD"], env=env, text=True, timeout=15).strip()
    assert head == SOURCE
    result = {"recorded_at": datetime.now(timezone.utc).isoformat(), "owner": EXPECTED_OWNER,
              "producer_sha256": globals()["ACTUAL_PRODUCER_SHA256"], "request_sha256": globals()["ACTUAL_REQUEST_SHA256"],
              "source_commit": SOURCE, "runtime_root": RUNTIME, "runtime_HEAD": head,
              "gpu_uuid_provenance_only": GPU_UUID_PROVENANCE_ONLY, "python": sys.executable,
              "scope": "One fresh CPU process; fixed type-check, identity _apply, float64 CPU _apply, and separate constructor text control.",
              "model_data_checkpoint_or_native_train_imported": False, "GPU_use": False,
              "reconstructed_failed_training_process": False, "root_cause": "UNKNOWN", "cases": []}
    python_state = random.getstate()
    torch = None
    torch_state = None
    numpy_rng = None
    numpy_state = None
    failure = None
    try:
        import torch
        import torch.nn.modules.module as module_library
        import torch._subclasses.fake_tensor as fake_library
        from torch._subclasses.fake_tensor import FakeTensor
        result["cuda_initialized_before"] = torch.cuda.is_initialized()
        assert result["cuda_initialized_before"] is False
        torch_state = torch.get_rng_state().clone()
        numpy = sys.modules.get("numpy")
        if numpy is not None:
            numpy_rng = numpy.random
            numpy_state = pickle.dumps(numpy_rng.get_state())
        result["torch"] = {"version": torch.__version__, "file": torch.__file__,
                           "module_file": module_library.__file__, "module_file_sha256": sha(Path(module_library.__file__).read_bytes()),
                           "fake_tensor_file": fake_library.__file__, "fake_tensor_file_sha256": sha(Path(fake_library.__file__).read_bytes())}
        result["bindings"] = {"FakeTensor": callable_identity(FakeTensor), "FakeTensor_metaclass": callable_identity(type(FakeTensor)),
                              "metaclass_instancecheck": callable_identity(type(FakeTensor).__instancecheck__),
                              "FakeTensor_new": callable_identity(FakeTensor.__new__),
                              "builtins_isinstance": callable_identity(builtins.isinstance),
                              "Module_apply": callable_identity(torch.nn.Module._apply)}
        result["binding_identity_checks"] = {"imported_FakeTensor_is_module_attribute": FakeTensor is fake_library.FakeTensor,
                                              "nn_Module_is_installed_module_Module": torch.nn.Module is module_library.Module,
                                              "isinstance_global_shadow_present": "isinstance" in globals()}
        source_lines, first_line = inspect.getsourcelines(torch.nn.Module._apply)
        hits = [i for i, line in enumerate(source_lines) if "FakeTensor" in line or "isinstance(param" in line]
        context = sorted({j for i in hits for j in range(max(0, i - 2), min(len(source_lines), i + 3))})
        result["apply_FakeTensor_source_context"] = [{"line": first_line + j, "text": source_lines[j].rstrip()} for j in context]
        result["apply_source_sha256"] = sha("".join(source_lines).encode("utf8"))

        def tensor_snapshot(value):
            return {"type": type(value).__module__ + "." + type(value).__qualname__, "shape": list(value.shape),
                    "dtype": str(value.dtype), "device": str(value.device), "values": value.detach().tolist()}

        parameter = torch.nn.Parameter(torch.arange(6, device="cpu", dtype=torch.float32).reshape(2, 3))
        def parameter_type_check():
            value = builtins.isinstance(parameter, FakeTensor)
            return {"parameter": tensor_snapshot(parameter), "isinstance_FakeTensor": value, "expected_false": value is False}
        result["cases"].append(case("fresh_cpu_parameter_isinstance_FakeTensor", parameter_type_check))

        class Tiny(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.weight = torch.nn.Parameter(torch.arange(6, device="cpu", dtype=torch.float32).reshape(2, 3))
                self.register_buffer("fixed_buffer", torch.tensor([1.0, 2.0, 3.0], device="cpu", dtype=torch.float32))

        def apply_case(convert):
            tiny = Tiny()
            before = {"weight": tensor_snapshot(tiny.weight), "buffer": tensor_snapshot(tiny.fixed_buffer)}
            bound = tiny._apply
            bound_identity = {"self_is_tiny": bound.__self__ is tiny, "func_is_installed_Module_apply": bound.__func__ is torch.nn.Module._apply,
                              "callable": callable_identity(bound)}
            result.setdefault("apply_before_bindings", {})["float64_CPU" if convert else "identity"] = {"bound_identity": bound_identity, "tensor_state": before}
            original_parameter = tiny.weight
            returned = tiny._apply((lambda value: value.to(device="cpu", dtype=torch.float64)) if convert else (lambda value: value))
            expected_dtype = torch.float64 if convert else torch.float32
            assert tiny.weight.device.type == tiny.fixed_buffer.device.type == "cpu"
            assert tiny.weight.dtype == tiny.fixed_buffer.dtype == expected_dtype
            assert tuple(tiny.weight.shape) == (2, 3) and tuple(tiny.fixed_buffer.shape) == (3,)
            return {"bound_identity": bound_identity, "returned_same_module": returned is tiny,
                    "parameter_object_preserved": tiny.weight is original_parameter, "before": before,
                    "after": {"weight": tensor_snapshot(tiny.weight), "buffer": tensor_snapshot(tiny.fixed_buffer)}}
        result["cases"].append(case("fresh_tiny_Module_apply_identity_once", lambda: apply_case(False)))
        result["cases"].append(case("fresh_tiny_Module_apply_float64_CPU_once", lambda: apply_case(True)))
        def invalid_constructor_text_control():
            value = FakeTensor()
            return {"unexpected_return_type": type(value).__module__ + "." + type(value).__qualname__, "repr": repr(value)[:1000]}
        text_control = case("zero_argument_FakeTensor_constructor_TEXT_CONTROL_ONLY", invalid_constructor_text_control)
        text_control["expected_TypeError"] = text_control.get("exception_type") == "TypeError"
        text_control["same_training_path_or_root_cause_claimed"] = False
        text_control["interpretation"] = "Explicit invalid constructor invocation; matching error text alone is NOT a reconstruction of isinstance/_apply or the failed training history."
        result["constructor_text_control"] = text_control
    except Exception as error:
        failure = error
        result["probe_error"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
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
    result["status"] = "CPU_DIAGNOSTIC_OBSERVATION_COMPLETE" if failure is None else "CPU_DIAGNOSTIC_INFRASTRUCTURE_ERROR"
    result["interpretation_limit"] = "Fresh installed-library CPU evidence only; no failed live object/state survives, CUDA history is not reconstructed, no repair/efficacy or restart authorization."
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    assert result["python_rng_restored_exact"] is True
    if torch is not None:
        assert result["cuda_initialized_before"] is False and result["cuda_initialized_after"] is False
    if torch_state is not None:
        assert result["torch_CPU_rng_restored_exact"] is True
    if numpy_state is not None:
        assert result["numpy_rng_restored_exact"] is True
    assert failure is None, "CPU observation infrastructure failed; preserve the recorded evidence"


if __name__ == "__main__":
    main()
