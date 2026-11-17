import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("aggregate_registry_geometry_diagnostic_20260921.py")
SPEC = importlib.util.spec_from_file_location("aggregate_geometry", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AggregateTest(unittest.TestCase):
    def test_rejects_duplicate_indices(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = {"pairs": []}
            binding = {"producer_sha256": "a" * 64}

            for name in ("one", "two"):
                bundle = root / name
                bundle.mkdir()
                (bundle / "capture.json").write_text(
                    json.dumps({
                        "native_capture_completed": True,
                        "binding": binding,
                        "original_dataset_indices": [1],
                        "artifacts": [],
                    }),
                    encoding="ascii",
                )
                (bundle / "bindings.json").write_text(
                    json.dumps({
                        "registry_sha256": "b" * 64,
                        "source_binding": binding,
                        "bindings": [],
                    }),
                    encoding="ascii",
                )

            with self.assertRaises(ValueError):
                MODULE.aggregate_bundles(root, registry, "b" * 64)


if __name__ == "__main__":
    unittest.main()
