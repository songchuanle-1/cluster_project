import unittest

from m95_contact_language_screen_20260926 import analyze, contact_phrases


class ContactScreenTests(unittest.TestCase):
    def test_word_boundaries_and_bare_on(self):
        self.assertEqual(contact_phrases("the box is on the table near another"), [])
        self.assertEqual(contact_phrases("A lamp is STANDING ON a table"), ["standing on"])
        self.assertEqual(contact_phrases("underneathish and below"), ["below"])

    def test_same_scene_discordance(self):
        rows = [
            dict(scene="a", stratum="ambiguous", failed=True,
                 contact_phrases=["below"], direction_words=[]),
            dict(scene="a", stratum="ambiguous", failed=False,
                 contact_phrases=[], direction_words=["left"]),
        ]
        summary = analyze(rows)
        self.assertEqual(summary["same_scene_discordant_pairs"], 1)
        self.assertEqual(summary["same_scene_contact_failures"], 1)


if __name__ == "__main__":
    unittest.main()
