import unittest

from m95_entry_fps_input_capture_20260925 import TARGET_ROWS, bind_fps_calls


class EntryFpsBindingTests(unittest.TestCase):
    def test_exact_step_and_indices(self):
        rows = [
            {"manifest_index": index, "step": index, "fps_superpoints": [index]}
            for index in TARGET_ROWS
        ]
        calls = [
            {"step": index, "indices": [index], "coordinates": None}
            for index in TARGET_ROWS
        ]
        self.assertEqual(set(bind_fps_calls(rows, calls)), TARGET_ROWS)

    def test_ambiguous_binding_fails(self):
        rows = [
            {"manifest_index": index, "step": index, "fps_superpoints": [index]}
            for index in TARGET_ROWS
        ]
        calls = [{"step": r["step"], "indices": r["fps_superpoints"]} for r in rows]
        calls.append(dict(calls[0]))
        with self.assertRaisesRegex(ValueError, "matching calls"):
            bind_fps_calls(rows, calls)

    def test_missing_target_fails(self):
        rows = [
            {"manifest_index": index, "step": index, "fps_superpoints": [index]}
            for index in TARGET_ROWS if index != 193
        ]
        calls = [{"step": r["step"], "indices": r["fps_superpoints"]} for r in rows]
        with self.assertRaisesRegex(ValueError, "coverage differs"):
            bind_fps_calls(rows, calls)


if __name__ == "__main__":
    unittest.main()
