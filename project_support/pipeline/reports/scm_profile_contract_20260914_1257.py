"""Audit profiler source only; does not execute training or validate resources."""
import ast
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    source = root / "Cluster/tools/train.py"
    raw = source.read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig"))
    profile = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "model_profile"
    )
    assignments = {
        ast.unparse(target): ast.unparse(node.value)
        for node in ast.walk(profile)
        if isinstance(node, ast.Assign)
        for target in node.targets
    }
    expected = {
        "profile_data_cfg": "copy.deepcopy(cfg.data.val)",
        "profile_data_cfg['lang_num_max']": "1",
        "profile_dl_cfg": "copy.deepcopy(cfg.dataloader.val)",
        "profile_dl_cfg['batch_size']": "1",
        "sample_batch": "next(iter(profile_dataloader))",
        "flops_analysis": "FlopCountAnalysis(model, (sample_batch, 'predict'))",
        "n_warmup": "3",
        "n_iter": "10",
    }
    for key, value in expected.items():
        assert assignments.get(key) == value, (key, assignments.get(key), value)
    calls = {
        ast.unparse(node)
        for node in ast.walk(profile)
        if isinstance(node, ast.Call)
    }
    assert "model.eval()" in calls
    assert "torch.cuda.synchronize(device)" in calls
    assert "torch.no_grad()" in [ast.unparse(d) for d in profile.decorator_list]
    result = {
        "status": "PASS_SOURCE_CONTRACT_ONLY",
        "source": str(source.relative_to(root)),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "historical_profile": expected,
        "goal_timing": {"batch_size": 1, "warmup": 20, "repeat": 100,
                        "statistics": ["median", "P90", "peak_memory"]},
        "historical_timing_satisfies_goal": False,
        "runtime_executed": False,
        "resources_measured": False,
        "training_admitted": False,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
