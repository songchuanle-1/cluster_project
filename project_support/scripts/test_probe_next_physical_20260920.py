"""Bounded continuation selection and CPU execution boundary tests."""
import ast
import unittest

from probe_next_physical_20260920 import remote_code, select_indices


class NextPhysicalTest(unittest.TestCase):
    def test_select_next_unique_indices(self):
        plan = dict(counts={"planned": 31}, rows=[
            dict(status="planned", dataset_index=i) for i in [3011, 1097, 2690, 1524, 2690]])
        self.assertEqual(select_indices(plan, [1097, 1524]), [2690, 3011])
        with self.assertRaises(ValueError):
            select_indices(plan, [999])
        with self.assertRaises(ValueError):
            select_indices(plan, [1097, 1524, 2690, 3011])

    def test_reject_repeated_invalid_or_consumed_indices(self):
        for indices in ([], [1, 1], [1, 2, 3], [True], [1097]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                remote_code(dict(selected_indices=indices, consumed_indices=[1097]))

    def test_cpu_program_preserves_producer_and_old_artifacts(self):
        code = remote_code(dict(selected_indices=[2690, 3011],
                                consumed_indices=[1097, 1524]))
        tree = ast.parse(code)
        compile(tree, "<next-physical>", "exec")
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertEqual(calls.count("subprocess.check_output"), 2)
        for name in ("torch.load", "capture_forward", "replay_forward"):
            self.assertNotIn(name, calls)
        self.assertIn('CUDA_VISIBLE_DEVICES=""', code)
        self.assertIn('scratch.mkdir(exist_ok=False)', code)
        self.assertIn('sys.addaudithook(audit)', code)
        self.assertIn('plan != request["native_metadata_plan"]', code)
        self.assertNotIn("observed.indices[:2]", code)
        self.assertIn('previous_artifacts_stable', code)


if __name__ == "__main__":
    unittest.main()
