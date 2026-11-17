import unittest
from pathlib import Path

from model_pair_audit_20260916 import audit, callsites, functions


class ModelAuditTests(unittest.TestCase):
    def test_method_body_change(self):
        a = functions("class C:\n def f(self): return 1\n")
        b = functions("class C:\n def f(self): return 2\n")
        self.assertNotEqual(a["C.f"], b["C.f"])

    def test_comments_do_not_change_ast(self):
        self.assertEqual(functions("class C:\n def f(self): return 1\n"),
                         functions("class C:\n # comment\n def f(self): return 1\n"))

    def test_fps_site_is_call_not_comment(self):
        source = "# FurthestPointSampling.apply(x)\ny=FurthestPointSampling.apply(x, 4)"
        self.assertEqual(callsites(source),
                         [dict(line=2, call="FurthestPointSampling.apply")])

    def test_actual_model_boundary(self):
        result = audit(Path(__file__).resolve().parents[1])
        self.assertTrue(result["matcher_ast_equal"])
        self.assertEqual(sum(result["source_equal"].values()), 6)
        self.assertIn("Criterion.loss_indi", result["changed_loss_methods"])
        self.assertEqual(len(result["fps_callsites"]["network.py"]), 2)
        self.assertEqual(len(result["fps_callsites"]["hier_postprocess.py"]), 1)


if __name__ == "__main__":
    unittest.main()
