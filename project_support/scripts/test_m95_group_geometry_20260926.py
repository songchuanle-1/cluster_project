import unittest

from m95_group_geometry_20260926 import vertical_control


class VerticalControlTest(unittest.TestCase):
    def test_lower_and_reverse(self):
        c = {1: [0, 0, 0], 2: [0, 0, 1], 3: [0, 0, 2]}
        self.assertTrue(vertical_control("bottom of stack", c, 1, [2, 3])["target_wins"])
        self.assertTrue(vertical_control("lower towel", c, 3, [1, 2])["reverse_wins"])

    def test_middle_requires_bracketing(self):
        c = {1: [0, 0, 1], 2: [0, 0, 0], 3: [0, 0, 2]}
        self.assertTrue(vertical_control("middle column", c, 1, [2, 3])["target_wins"])
        self.assertFalse(vertical_control("middle column", c, 2, [1, 3])["target_wins"])

    def test_unresolved_control(self):
        self.assertIsNone(vertical_control("row of sinks", {1: [0, 0, 0]}, 1, [])["target_wins"])
        c = {1: [0, 0, 0], 2: [0, 0, 1]}
        self.assertEqual(vertical_control("under mirrors", c, 1, [2])["relation"],
                         "under_reference")
        self.assertEqual(vertical_control("middle column under box", c, 1, [2])["relation"],
                         "mixed_reference")


if __name__ == "__main__":
    unittest.main()
