"""Read-only CPU-only installed-library and parameter-enumeration observation."""
import os
import socket

assert socket.gethostname() == "dl04-MS-7E06"
assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import inspect
import json
import subprocess
import sys
import traceback

RUNTIME = Path("/data/songcl/Project/Cluster_project/Cluster_hvd_20261106")
EXPECTED = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
assert subprocess.check_output(
    ["git", "-C", str(RUNTIME), "rev-parse", "HEAD"], text=True,
).strip() == EXPECTED
result = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "hostname": socket.gethostname(), "python_executable": sys.executable,
    "CUDA_VISIBLE_DEVICES": os.environ["CUDA_VISIBLE_DEVICES"],
    "scope": "Read-only CPU source/introspection and a newly constructed small CPU module tree. No dataset, checkpoint, forward, backward, optimizer, GPU/NVML or training.",
    "runtime_root": str(RUNTIME), "runtime_source": EXPECTED,
}
try:
    import torch
    import torch.nn.modules.module as torch_module
    torch.set_num_threads(1)
    result["torch"] = {
        "version": torch.__version__, "file": torch.__file__,
        "module_file": torch_module.__file__,
        "module_file_sha256": hashlib.sha256(Path(torch_module.__file__).read_bytes()).hexdigest(),
    }
    methods = {}
    for name in ("parameters", "named_parameters", "_named_members", "named_modules"):
        function = getattr(torch.nn.Module, name)
        source_lines, first_line = inspect.getsourcelines(function)
        text = "".join(source_lines)
        methods[name] = {
            "signature": str(inspect.signature(function)),
            "module": function.__module__, "qualname": function.__qualname__,
            "source_file": inspect.getsourcefile(function),
            "first_line": first_line,
            "source_sha256": hashlib.sha256(text.encode("utf8")).hexdigest(),
            "source": text[:12000],
            "source_truncated": len(text) > 12000,
        }
    result["installed_methods"] = methods
    sys.path.insert(0, str(RUNTIME))
    from framework.torch.nn.modules.activation import MultiheadAttention
    custom_file = Path(inspect.getsourcefile(MultiheadAttention))
    attention = MultiheadAttention(16, 4, batch_first=True, device="cpu")
    bound = attention.named_modules
    result["custom_attention"] = {
        "class_module": MultiheadAttention.__module__,
        "source_file": str(custom_file),
        "source_sha256": hashlib.sha256(custom_file.read_bytes()).hexdigest(),
        "class_own_methods": [
            name for name, value in MultiheadAttention.__dict__.items()
            if callable(value) and not name.startswith("__")],
        "named_modules_in_class_dict": "named_modules" in MultiheadAttention.__dict__,
        "named_modules_signature": str(inspect.signature(bound)),
        "bound_self_is_instance": bound.__self__ is attention,
        "bound_func_is_installed_Module_named_modules": bound.__func__ is torch.nn.Module.named_modules,
        "parameter_devices": sorted({str(p.device) for p in attention.parameters()}),
    }

    leaf = torch.nn.ModuleList([
        attention,
        MultiheadAttention(16, 4, batch_first=True, device="cpu"),
        torch.nn.Linear(16, 16, device="cpu"),
    ])
    tree = leaf
    for _ in range(6):
        wrapper = torch.nn.Module()
        wrapper.add_module("nested", tree)
        tree = wrapper
    # Include a shared attention reference to exercise duplicate memo handling.
    tree.add_module("shared_attention", attention)
    observed_counts = []
    for _ in range(128):
        parameters = list(tree.parameters())
        named = list(tree.named_modules())
        norm = torch.nn.utils.clip_grad_norm_(tree.parameters(), 0.1)
        observed_counts.append((len(parameters), len(named), float(norm)))
    all_modules = list(tree.named_modules(remove_duplicate=False))
    result["cpu_reproduction"] = {
        "completed": True, "iterations": 128, "nesting_wrappers": 6,
        "counts_unique": sorted({row for row in observed_counts}),
        "all_parameter_devices": sorted({str(p.device) for p in tree.parameters()}),
        "remove_duplicate_false_count": len(all_modules),
        "duplicate_memo_path_exercised": True,
        "clip_norm_no_gradients": True,
        "original_failure_reproduced": False,
        "limitation": "Fresh small CPU tree only. It does not reconstruct the crashed HVD object, its batch, prior forward/backward history or original CUDA runtime state.",
    }
    result["conclusion"] = "Persistent parameter-enumeration failure was not reproduced in this bounded installed-library/custom-attention CPU observation. Original HVD crash root cause remains UNKNOWN."
except Exception as error:
    result["probe_error"] = {
        "type": type(error).__name__, "message": str(error),
        "traceback": traceback.format_exc()[-12000:],
    }
    result["conclusion"] = "CPU observation did not complete; preserve actual error without assigning the original crash root cause."
result["finished_at"] = datetime.now(timezone.utc).isoformat()
print(json.dumps(result, ensure_ascii=False))
