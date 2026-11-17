"""Static bounds for the native saved-input continuation wrapper."""
import ast
import unittest

from probe_next_saved_replay_20260920 import remote_code


class NextSavedReplayTest(unittest.TestCase):
    def test_exact_groups_required(self):
        for indices in ([], [2690], [3011,2690], [2690,2690], [2690,3011,3040]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                remote_code(dict(items=[dict(dataset_index=i) for i in indices]))

    def test_native_cpu_program(self):
        code = remote_code(dict(items=[dict(dataset_index=i) for i in (2690,3011)]))
        tree = ast.parse(code)
        compile(tree,"<probe>","exec")
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertEqual(calls.count("subprocess.check_output"),2)
        self.assertIn("prepare_replay",calls)
        self.assertNotIn("replay_forward",calls)
        self.assertNotIn("capture_forward",calls)
        self.assertNotIn("model_factory",calls)
        self.assertIn('CUDA_VISIBLE_DEVICES=""',code)
        self.assertIn('sys.path.insert(1,str(scratch))',code)
        self.assertIn('sys.addaudithook(audit)',code)
        self.assertIn('scratch.mkdir(exist_ok=False)',code)
        self.assertIn('new_train_transforms=False',code)
        self.assertIn('driver_model_path_executed=False',code)
        self.assertIn('if joins != reconstructed:',code)


if __name__ == "__main__":
    unittest.main()
