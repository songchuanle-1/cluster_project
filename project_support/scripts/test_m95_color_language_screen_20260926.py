import unittest

from m95_color_language_screen_20260926 import COLOR, analyze, words


class ColorScreenTests(unittest.TestCase):
    def test_standalone_case_insensitive_words(self):
        self.assertEqual(words("A Blueish RED chair") & COLOR, {"red"})

    def test_matched_scene_count(self):
        rows = [
            dict(scene="s", stratum="ambiguous", failed=True,
                 color_words=["red"], spatial_words=[]),
            dict(scene="s", stratum="ambiguous", failed=False,
                 color_words=[], spatial_words=["left"]),
            dict(scene="t", stratum="unique", failed=False,
                 color_words=[], spatial_words=[]),
        ]
        summary = analyze(rows)
        self.assertEqual(summary["same_scene_discordant_pairs"], 1)
        self.assertEqual(summary["same_scene_color_failures"], 1)
        self.assertEqual(summary["by_stratum"]["ambiguous"]["color_words"]["exposed"], 1)


if __name__ == "__main__":
    unittest.main()
