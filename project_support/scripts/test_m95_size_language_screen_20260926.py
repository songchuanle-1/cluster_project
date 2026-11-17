import unittest

from m95_size_language_screen_20260926 import size_direction, analyze


class SizeScreenTests(unittest.TestCase):
    def test_direction_and_token_boundary(self):
        self.assertEqual(size_direction("LARGER chair"), "larger")
        self.assertEqual(size_direction("largest and smaller"), "both")
        self.assertIsNone(size_direction("big or biggers"))

    def test_same_scene_control(self):
        rows = [dict(scene="s", stratum="ambiguous", failed=True,
                     size_direction="smaller"),
                dict(scene="s", stratum="ambiguous", failed=False,
                     size_direction=None)]
        result = analyze(rows)
        self.assertEqual(result["same_scene_discordant_pairs"], 1)
        self.assertEqual(result["same_scene_size_failures"], 1)


if __name__ == "__main__":
    unittest.main()
