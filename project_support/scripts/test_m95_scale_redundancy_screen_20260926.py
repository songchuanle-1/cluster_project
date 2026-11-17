import unittest

from m95_scale_redundancy_screen_20260926 import screen


class ScreenTest(unittest.TestCase):
    def test_real_frozen_contract(self):
        import json
        from pathlib import Path

        source = json.loads(Path(
            "pipeline/reports/cluster_scale_necessity_20260916.json"
        ).read_text())
        result = screen(source)
        self.assertEqual(result["summary"]["expressions"], 123)
        self.assertEqual(result["summary"]["scenes"], 32)

    def test_duplicate_fails_closed(self):
        import json
        from pathlib import Path

        source = json.loads(Path(
            "pipeline/reports/cluster_scale_necessity_20260916.json"
        ).read_text())
        source["duplication"].append(source["duplication"][0])
        with self.assertRaises(ValueError):
            screen(source)


if __name__ == "__main__":
    unittest.main()
