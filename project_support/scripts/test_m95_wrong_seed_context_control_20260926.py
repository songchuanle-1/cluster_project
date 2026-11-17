import unittest

from m95_wrong_seed_context_control_20260926 import analyze


class EndpointControlTest(unittest.TestCase):
    def test_join_and_missing_id(self):
        rows = [{"manifest_index": i, "scene": "scene%03d" % i,
                 "stratum": "ambiguous" if i < 128 else "class_unique",
                 "failed": i < 49, "selected_exposed": i == 0,
                 "selected_unresolved": False} for i in range(256)]
        partition_rows = [{"manifest_index": i, "scene_id": "scene%03d" % i,
                           "category": "wrong_instance"} for i in range(49)]
        screen = {"contract": "m95_wrong_seed_context_v1", "rows": rows}
        partition = {"contract": "m95_negative_intrusion_partition_v1",
                     "summary": {"mismatch_rows": partition_rows}}
        result = analyze(screen, partition)
        self.assertEqual(result["summary"]["all_native_negative"]["rows"], 49)
        self.assertEqual(result["summary"]["wrong_instance"]["exposed"], 1)
        partition_rows[0]["scene_id"] = "wrong"
        with self.assertRaisesRegex(ValueError, "identity"):
            analyze(screen, partition)


if __name__ == "__main__":
    unittest.main()
