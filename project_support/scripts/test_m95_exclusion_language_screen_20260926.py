import unittest

from m95_exclusion_language_screen_20260926 import analyze, features


class ExclusionScreenTests(unittest.TestCase):
    def test_phrase_boundaries(self):
        self.assertEqual(features("Not the chair, but not a table")[0],
                         ["but not", "not a", "not the"])
        self.assertEqual(features("notable")[0], [])

    def test_same_scene_pair(self):
        rows = [dict(scene="s", stratum="ambiguous", failed=True,
                     exclusion_phrases=["without"], contrast_words=[]),
                dict(scene="s", stratum="ambiguous", failed=False,
                     exclusion_phrases=[], contrast_words=[])]
        self.assertEqual(analyze(rows)["same_scene_discordant_pairs"], 1)


if __name__ == "__main__":
    unittest.main()
