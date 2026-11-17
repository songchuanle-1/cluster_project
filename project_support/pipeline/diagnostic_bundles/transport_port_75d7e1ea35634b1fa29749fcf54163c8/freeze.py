"""Bind the executable port to unchanged science pins and its actual preparation."""

import json
from pathlib import Path
import stage

stage.guard(120)
prepared = stage.tick.load(stage.BUNDLE / "preparation.json")
assert prepared["status"] == "PASS" and prepared["gpu_forwards"] == 0
assert prepared["parameter_gradient_calls"] == 0 and prepared["native_getter_calls"] == 8
assert prepared["gpu_slot"]["status"] == "occupied" and prepared["training_lease"] == "held"
audit = stage.tick.load(stage.BUNDLE / "ast_audit.json")
files = [stage.BUNDLE / name for name in (
    "runtime.py", "native_adapter.py", "cpu_prepare.py", "assets_manifest.json", "ast_audit.json",
    "build.py", "launch_native.py", "preparation.json", "preparation_execution.json",
)]
files += sorted(stage.ASSETS.iterdir())
files += [stage.PROJECT / "pipeline/designs/bps_parameter_transport_prereg_20261014_1434.md"]
rows = [{"path": path.relative_to(stage.PROJECT).as_posix(), "sha256": stage.tick.digest(path)} for path in files]
remote_names = ["runtime.py", "native_adapter.py", "cpu_prepare.py", "assets_manifest.json", "ast_audit.json"]
remote_names += ["assets/" + path.name for path in sorted(stage.ASSETS.iterdir())]
remote_files = [{"name": name, "sha256": stage.tick.digest(stage.BUNDLE / name)} for name in remote_names]
stage.save("frozen_manifest", {
    "files": rows, "remote_files": remote_files, "server": "server-4", "gpu": 0,
    "gpu_uuid": "GPU-7f82edb9-f620-8045-caea-a75232265cd1", "max_tasks": 1,
    "cohort": [0, 60, 101, 124], "checkpoint_epoch": 4,
    "checkpoint_sha256": stage.PINS["checkpoint_snapshot.pth"],
    "seed": 1999, "restored_repeats": 2, "absolute_tolerance": 1e-6,
    "allocator_fraction": .25, "hard_timeout_seconds": 600, "foreground_margin_seconds": 120,
    "optimizer_steps": 0, "native_test_executed": False,
    "future_command": ["python", "-B", str(stage.BUNDLE / "launch_native.py"), "--token", "<current_owned_token>"],
    "scope": "Host/path/exclusive-lock port only; preparation PASS is not original native parameter-gradient PASS, old FD/full-forward repair, novelty or efficacy.",
    "attempted_alternatives": [
        "Fetched eleven original immutable assets, audited AST equality and completed interrupted checkpoint transfer by verified prefix resume.",
        "Imported flattened adapter without main; audited model source/epoch4 strict state plus exactly identical nonpersistent constants on server4 CPU.",
        "Executed eight native CPU getters for four preregistered groups, exact within-group repeats, CUDA uninitialized.",
        "Checked actual GPU slot and native training flock; occupied by registered M201 training, no GPU diagnostic launched.",
    ],
})
print(json.dumps({"manifest": str(stage.BUNDLE / "frozen_manifest.json"), "files": len(rows)}))
