"""Recovery cannot overwrite saved geometry or allocate CUDA."""
import ast
import unittest
from unittest.mock import patch

from recover_cpu_progress_20260920 import remote_code, validate_recovery


class RecoveryTest(unittest.TestCase):
    def test_two_unobserved_groups(self):
        for indices in ([], [3040], [3893, 3040], [3040, 3040], [2690, 3011]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                remote_code(dict(selected_indices=indices,
                                 consumed_indices=[1097, 1524, 2690, 3011]))

    def test_bound_cpu_program(self):
        code = remote_code(dict(selected_indices=[3040, 3893],
                                consumed_indices=[1097, 1524, 2690, 3011]))
        tree = ast.parse(code)
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertEqual(calls.count("subprocess.check_output"), 2)
        for name in ("capture_forward", "replay_forward", "torch.load", "model_factory"):
            self.assertNotIn(name, calls)
        self.assertIn('bundle.name+"_physical_20260920_0915"', code)
        self.assertIn('recovered_artifacts_stable', code)
        self.assertIn('CUDA_VISIBLE_DEVICES=""', code)
        self.assertIn('scratch.mkdir(exist_ok=False)', code)
        self.assertIn('sys.addaudithook(audit)', code)

    def fixture(self):
        replay = {k: True for k in (
            "saved_collation_completed", "saved_replay_verified", "driver_import_verified",
            "driver_help_verified", "driver_uncoordinated_rejected",
            "immutable_import_precedence_verified", "full_binding_equal",
            "sources_stable", "annotation_and_cache_stable")}
        replay.update(returncode=0, gpu_initialized=False, model_forward_completed=False,
            driver_model_path_executed=False, observed_binding={"source": "same"},
            binding_counts={"bound": 2, "missing_capture": 29},
            prepared=[dict(dataset_index=i) for i in [2690, 3011]],
            physical_sha256="hash", probe_sha256="hash", separate_sources=[])
        return replay, dict(observed_binding={"source": "same"})

    def test_recovered_gates(self):
        replay, physical = self.fixture()
        with patch("recover_cpu_progress_20260920.file_sha256", return_value="hash"):
            validate_recovery(replay, physical)
            for key, value in (("gpu_initialized", True), ("returncode", 1),
                               ("saved_replay_verified", False), ("probe_sha256", "drift"),
                               ("binding_counts", {"bound": 31})):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    validate_recovery(dict(replay, **{key: value}), physical)


if __name__ == "__main__":
    unittest.main()
