import base64
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from stage_registry_diagnostic_20260920 import REGISTRY, publish, unpack


class DiagnosticBundleTest(unittest.TestCase):
    def request(self):
        def row(path, payload):
            return dict(path=path, sha256=hashlib.sha256(payload).hexdigest(),
                        base64=base64.b64encode(payload).decode("ascii"))
        rows = [row("scripts/example.py", b"pass\n"), row(REGISTRY, b"{}\n")]
        return dict(producer=dict(sources=[dict(path="example.py", sha256=rows[0]["sha256"])]),
                    expected=dict(registry_sha256=rows[1]["sha256"]), files=rows)

    def test_round_trip_and_no_overwrite(self):
        request = self.request()
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "bundle"
            manifest = publish(root, request)
            self.assertEqual((root / "scripts/example.py").read_bytes(), b"pass\n")
            self.assertNotIn("base64", manifest["files"][0])
            with self.assertRaises(FileExistsError):
                publish(root, request)
            # Windows read-only files need writable attributes for test cleanup.
            for path in root.rglob("*"):
                if path.is_file():
                    path.chmod(0o666)

    def test_corrupt_payload(self):
        request = self.request()
        request["files"][0]["base64"] = base64.b64encode(b"changed").decode()
        with self.assertRaises(ValueError):
            unpack(request)

    def test_missing_extra_duplicate_and_traversal(self):
        base = self.request()
        for change in ("missing", "extra", "duplicate", "traversal"):
            request = copy.deepcopy(base)
            if change == "missing":
                request["files"].pop()
            elif change == "extra":
                request["files"].append(dict(path="unexpected"))
            elif change == "duplicate":
                request["files"][1] = request["files"][0]
            else:
                request["files"][0]["path"] = "scripts/../escape.py"
                request["producer"]["sources"][0]["path"] = "../escape.py"
            with self.subTest(change=change), self.assertRaises(ValueError):
                unpack(request)

    def test_producer_hash_mismatch(self):
        request = self.request()
        request["producer"]["sources"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            unpack(request)

    def test_registry_hash_mismatch(self):
        request = self.request()
        request["expected"]["registry_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            unpack(request)

    def test_failed_validation_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "bundle"
            request = self.request()
            request["files"][0]["base64"] = "!"
            with self.assertRaises(ValueError):
                publish(root, request)
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
