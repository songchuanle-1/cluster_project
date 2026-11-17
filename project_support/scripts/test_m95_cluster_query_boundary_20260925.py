import unittest

from m95_cluster_query_boundary_20260925 import boundary_trace_record


def event(layer):
    return dict(
        layer=layer,
        cluster_input=[[1.0], [2.0]],
        cluster_message=[[0.1], [0.2]],
        readback=[[1.1], [2.2]],
        decoder_points=[[1.1], [2.2]],
        decoder_query_input=[[3.0], [4.0]],
        decoder_query_output=[[3.1], [4.1]],
    )


class BoundaryTraceTest(unittest.TestCase):
    def test_preserves_order_and_values(self):
        row = boundary_trace_record([event(4), event(5)], [4, 5], 2, 2)
        self.assertEqual(row["layers"][0]["readback"][0], [1.1])
        self.assertEqual(row["contract"], "m95_cluster_query_boundary_v1")

    def test_missing_layer_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            boundary_trace_record([event(4)], [4, 5], 2, 2)

    def test_reordered_layer_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "order"):
            boundary_trace_record([event(5), event(4)], [4, 5], 2, 2)

    def test_support_and_query_axes_fail_closed(self):
        wrong = event(4)
        wrong["readback"] = [[1.0]]
        with self.assertRaisesRegex(ValueError, "support"):
            boundary_trace_record([wrong], [4], 2, 2)
        wrong = event(4)
        wrong["decoder_query_output"] = [[3.0]]
        with self.assertRaisesRegex(ValueError, "query axis"):
            boundary_trace_record([wrong], [4], 2, 2)

    def test_feature_width_fails_closed(self):
        wrong = event(4)
        wrong["cluster_message"] = [[1.0, 2.0], [3.0, 4.0]]
        with self.assertRaisesRegex(ValueError, "width"):
            boundary_trace_record([wrong], [4], 2, 2)


if __name__ == "__main__":
    unittest.main()
