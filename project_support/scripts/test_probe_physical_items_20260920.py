"""Static boundary tests; these do not substitute for native execution."""
import ast
import hashlib
import json
import unittest

from probe_physical_items_20260920 import remote_code


class PhysicalProbeTest(unittest.TestCase):
    def test_remote_program_compiles(self):
        compile(remote_code({}), "<physical-probe>", "exec")

    def test_retry_has_no_gpu_query_or_model_execution(self):
        tree = ast.parse(remote_code({}))
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertNotIn("subprocess.check_output", calls)
        self.assertNotIn("capture_forward", calls)
        self.assertNotIn("capture_planned", calls)
        self.assertNotIn("torch.load", calls)
        self.assertIn("torch.cuda.is_initialized", calls)
        self.assertIn("observed", {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)})

    def test_scratch_and_writes_remain_bounded(self):
        code = remote_code({})
        self.assertIn('"_physical_20260920_0415_retry"', code)
        self.assertIn('scratch.mkdir(exist_ok=False)', code)
        self.assertIn('sys.addaudithook(audit)', code)
        self.assertIn('path.open("xb")', code)
        self.assertIn('observed.indices[:2]', code)
        self.assertIn('native_capture_completed"] = False', code)

    def test_manifest_only_accepts_exact_lf_representation(self):
        value = {"files": [{"path": "a.py", "sha256": "1" * 64}]}
        windows = json.dumps(value, indent=2).replace("\n", "\r\n").encode()
        linux = json.dumps(value, indent=2).encode()
        normalize = lambda x: hashlib.sha256(x.replace(b"\r\n", b"\n")).hexdigest()
        self.assertEqual(normalize(windows), normalize(linux))
        self.assertEqual(json.loads(windows), json.loads(linux))
        changed = linux.replace(b"a.py", b"b.py")
        self.assertNotEqual(normalize(windows), normalize(changed))
        self.assertNotEqual(json.loads(windows), json.loads(changed))
        self.assertNotEqual(normalize(windows), normalize(linux + b"\n"))


if __name__ == "__main__":
    unittest.main()
