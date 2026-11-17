import unittest

from m95_target_seed_scene_control_20260927 import analyze
from test_m95_target_seed_failure_20260927 import capture


class SceneControlTest(unittest.TestCase):
    def setUp(self):
        self.a = capture(1999, .4, 1)
        self.b = capture(2000, .4, 1)

    def test_same_target_control(self):
        result = analyze([self.a, self.b])
        first = result["arms"][0]
        self.assertEqual(first["with_same_scene_success_control"], 1)
        self.assertEqual(first["with_same_physical_target_success_control"], 1)
        self.assertEqual(first["paired_scenes"], 1)

    def test_different_target_is_not_matched(self):
        for row in self.a["rows"][1:4]:
            row["target_instances"] = [2]
            row["selected_seed_instance"] = 2
        self.assertEqual(
            analyze([self.a, self.b])["arms"][0]["with_same_physical_target_success_control"],
            0)

    def test_empty_control_reported(self):
        for row in self.a["rows"][1:4]:
            row["selected_seed_matches_target_instance"] = False
            row["selected_seed_instance"] = 2
        self.assertEqual(analyze([self.a, self.b])["arms"][0]["with_same_scene_success_control"], 0)

    def test_fails_inconsistent_binding(self):
        self.a["rows"][1]["selected_seed_matches_target_instance"] = False
        with self.assertRaises(ValueError):
            analyze([self.a, self.b])


if __name__ == "__main__":
    unittest.main()
