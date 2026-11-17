"""Static source fixtures only; no native package or data imports."""
from pathlib import Path
import unittest
from unittest.mock import patch

from model_execution_inventory_20260921 import (
    import_execution_audit, import_phase_events, checked_bytes, PACKAGE,
)


class ImportPhaseTests(unittest.TestCase):
    def events(self, source):
        return import_phase_events(source, "fixture.py")

    def calls(self, source, phase):
        return [r["expression"] for r in self.events(source)
                if r["kind"] == "call" and r["phase"] == phase]

    def test_imports_remain_in_source_order(self):
        rows = self.events("import pointgroup_ops\nimport torch\n")
        self.assertEqual([r["expression"] for r in rows],
                         ["import pointgroup_ops", "import torch"])
        self.assertTrue(all(r["phase"] == "import_time_possible" for r in rows))

    def test_function_body_is_deferred_but_default_is_eager(self):
        source = "def forward(x=allocate()):\n    x.cuda()\n"
        self.assertEqual(self.calls(source, "import_time_possible"), ["allocate"])
        self.assertEqual(self.calls(source, "deferred_body"), ["x.cuda"])

    def test_class_body_and_bases_eager_methods_deferred(self):
        source = "class Model(make_base()):\n    x = register()\n    def forward(self):\n        run()\n"
        self.assertEqual(self.calls(source, "import_time_possible"),
                         ["make_base", "register"])
        self.assertEqual(self.calls(source, "deferred_body"), ["run"])

    def test_bare_decorator_application_is_recorded(self):
        rows = self.events("@compile_kernel\ndef kernel():\n    allocate()\n")
        applications = [r for r in rows if r["kind"] == "decorator_application"]
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0]["expression"], "compile_kernel")
        self.assertEqual(applications[0]["phase"], "import_time_possible")

    def test_nested_definition_defaults_stay_deferred(self):
        source = "def outer():\n    @decorate()\n    def inner(x=allocate()):\n        execute()\n"
        self.assertEqual(self.calls(source, "import_time_possible"), [])
        self.assertEqual(self.calls(source, "deferred_body"),
                         ["decorate", "allocate", "execute"])

    def test_lambda_default_and_body(self):
        source = "f = lambda x=default(): body()\n"
        self.assertEqual(self.calls(source, "import_time_possible"), ["default"])
        self.assertEqual(self.calls(source, "deferred_body"), ["body"])

    def test_generator_outer_iterable_only_is_eager(self):
        source = "g = (transform(x) for x in source() if predicate(x))\n"
        self.assertEqual(self.calls(source, "import_time_possible"), ["source"])
        self.assertEqual(self.calls(source, "deferred_body"), ["transform", "predicate"])

    def test_conditional_calls_are_not_claimed_unreachable(self):
        source = "if __name__ == '__main__':\n    torch.cuda.init()\n"
        self.assertEqual(self.calls(source, "import_time_possible"), ["torch.cuda.init"])

    def test_annotations_conservatively_eager(self):
        source = "def f(x: annotation()) -> result():\n    return x\n"
        self.assertEqual(self.calls(source, "import_time_possible"), ["annotation", "result"])

    def test_async_function_body_deferred(self):
        source = "async def f(x=default()):\n    await run()\n"
        self.assertEqual(self.calls(source, "import_time_possible"), ["default"])
        self.assertEqual(self.calls(source, "deferred_body"), ["run"])

    def test_malformed_source_fails(self):
        with self.assertRaises(SyntaxError):
            self.events("def missing")

    def test_existing_bounded_sources_preserve_unverified_gates(self):
        root = Path(__file__).resolve().parents[1] / "Cluster"
        audit = import_execution_audit(root)
        self.assertEqual(len(audit["sources"]), 31)
        for key in ("execution_order_verified", "transitive_closure_complete",
                    "native_environment_verified", "native_execution_completed",
                    "production_dependency_loader_implemented", "admission"):
            self.assertIs(audit[key], False)
        loss = next(s for s in audit["sources"] if s["path"] == PACKAGE + "/loss.py")
        self.assertTrue(any(e["expression"] == "torch.jit.script"
                            and e["kind"] == "decorator_application"
                            and e["phase"] == "import_time_possible"
                            for e in loss["events"]))

    def test_source_drift_after_manifests_rejected(self):
        root = Path(__file__).resolve().parents[1] / "Cluster"
        counts = {}

        def changed(path):
            key = str(path)
            counts[key] = counts.get(key, 0) + 1
            raw = checked_bytes(path)
            # Model manifest reads each source twice, then the phase audit reads it.
            return raw + b"\n# drift\n" if counts[key] == 3 else raw

        with patch("model_execution_inventory_20260921.checked_bytes", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "changed before audit"):
                import_execution_audit(root)


if __name__ == "__main__":
    unittest.main()
