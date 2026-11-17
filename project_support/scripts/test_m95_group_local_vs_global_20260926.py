import unittest

from m95_group_local_vs_global_20260926 import compare


class LocalGlobalTests(unittest.TestCase):
    def test_all_peer_cue_is_stricter(self):
        self.assertTrue(compare(0, [1], True))
        self.assertFalse(compare(0, [-1, 1], True))
        self.assertTrue(compare(2, [0, 1], False))
        self.assertFalse(compare(0, [-1, 1], False))
        with self.assertRaisesRegex(ValueError, "peer"):
            compare(0, [], True)


if __name__ == "__main__":
    unittest.main()
