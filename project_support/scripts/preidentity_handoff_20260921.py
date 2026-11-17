"""Pinned fresh-child handoff, not a native dispatcher or execution permit."""
import copy
import json
from pathlib import Path
import sys

from pinned_diagnostic_imports_20260920 import (
    PreIdentityTorchImports, checked_digest, digest, regular_bytes,
)
from saved_physical_location_20260920 import collect_logical_gpu_identity


CONTRACT = "preidentity-handoff-v1"


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate handoff key")
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError("Nonfinite handoff value: " + value)


def _bootstrap_modules():
    return {
        name: module for name, module in sys.modules.items()
        if name.split(".")[0] not in sys.stdlib_module_names
        and name not in sys.builtin_module_names
    }


class PreIdentityHandoff:
    """Accept independent manifest bytes before loading Torch in a fresh child.

    Bootstrap rows enumerate every already-loaded non-stdlib module. Matching
    files does not attest the bytes that were executed earlier: the parent must
    launch an independently pinned bootstrap/interpreter. Stdlib, callbacks and
    extension shared libraries remain trusted. Discard the child on any failure.
    """

    def __init__(self, path, sha256):
        self.path = Path(path).absolute()
        self.sha256 = checked_digest(sha256)
        self.raw = regular_bytes(self.path)
        if len(self.raw) > 4 * 1024 * 1024 or digest(self.raw) != self.sha256:
            raise ValueError("Handoff size/hash differs")
        payload = json.loads(self.raw, object_pairs_hook=_unique,
                             parse_constant=_nonfinite)
        if (not isinstance(payload, dict)
                or set(payload) != {"contract", "dependencies", "bootstrap"}
                or payload["contract"] != CONTRACT
                or not isinstance(payload["dependencies"], list)
                or not isinstance(payload["bootstrap"], list)):
            raise ValueError("Invalid handoff schema")
        self.bootstrap = {}
        self.initial = _bootstrap_modules()
        for row in payload["bootstrap"]:
            if (not isinstance(row, dict) or set(row) != {"name", "path", "sha256"}
                    or not isinstance(row["name"], str)
                    or row["name"] in self.bootstrap):
                raise ValueError("Invalid or duplicate bootstrap row")
            source = row["path"]
            if (not isinstance(source, str) or not Path(source).is_absolute()
                    or str(Path(source)) != source):
                raise ValueError("Canonical bootstrap path required")
            self.bootstrap[row["name"]] = (
                Path(source), checked_digest(row["sha256"]))
        if set(self.bootstrap) != set(self.initial):
            missing = sorted(set(self.initial) - set(self.bootstrap))
            extra = sorted(set(self.bootstrap) - set(self.initial))
            raise ValueError(
                "Exact non-stdlib bootstrap inventory required; missing=%r extra=%r"
                % (missing, extra))
        self.loader = PreIdentityTorchImports(payload["dependencies"])
        self.used = False
        self.verify()

    def verify(self):
        if regular_bytes(self.path) != self.raw:
            raise ValueError("Immutable handoff changed")
        for name, (path, expected) in self.bootstrap.items():
            module = sys.modules.get(name)
            if (module is None or module is not self.initial[name]
                    or getattr(module, "__file__", None) != str(path)
                    or digest(regular_bytes(path)) != expected):
                raise ValueError("Bootstrap origin/identity/hash differs: " + name)
        extra = set(_bootstrap_modules()) - set(self.initial)
        if extra - set(self.loader.loaded):
            raise ValueError("Untracked bootstrap module")
        self.loader.verify()

    def collect(self, expected_executable, *, gpu, capacity, required_memory_mib,
                slot_check, execution_check):
        """Caller retains its real slot through subsequent model teardown.

        Both checks must freshly return True; they are caller-owned trusted
        verifiers, not booleans manufactured here. No model, launch, receipt or
        admission is produced. Whole-child time/output limits are external.
        """
        if self.used:
            raise ValueError("Handoff is single-use; discard child")
        self.used = True
        if type(gpu) is not int or gpu not in (0, 1):
            raise ValueError("Only server-4 GPU0/1")
        capacity = copy.deepcopy(capacity)

        def check():
            if (not callable(slot_check) or not callable(execution_check)
                    or slot_check("server-4", gpu) is not True
                    or execution_check("server-4", gpu) is not True):
                raise ValueError("Held slot and execution verification required")
            self.verify()

        check()
        with self.loader:
            def load():
                check()
                torch = self.loader.load_torch()
                check()
                return torch

            result = collect_logical_gpu_identity(
                expected_executable, gpu=gpu, capacity=capacity,
                required_memory_mib=required_memory_mib, coordinated_slot=True,
                dependency_loader=load)
            check()
        self.verify()
        return dict(
            contract=CONTRACT, handoff_sha256=self.sha256,
            bootstrap_modules=sorted(self.bootstrap),
            dependency_modules=sorted(self.loader.loaded),
            identity=result, native_execution_authorized=False,
            scientific_validation_complete=False, admission=False,
            training_launch=False)
