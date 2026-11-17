import unittest
import numpy as np
from m95_geometry_screen_20260926 import graph_features, scene_graph, matched_pairs


class GeometryScreenTest(unittest.TestCase):
    def test_graph_components_and_boundary(self):
        edges = np.array([[0, 1], [1, 2], [2, 3]])
        a = graph_features([1, 0, 1, 0], edges)
        self.assertEqual(a["components"], 2)
        self.assertEqual(a["boundary_fraction"], 1.0)

    def test_centroid_graph(self):
        xyz = np.array([[0., 0., 0.], [0., 0., 0.1],
                        [3., 0., 0.], [6., 0., 0.]])
        edges = scene_graph(xyz, np.array([0, 0, 1, 2]), 3)
        self.assertEqual(len(edges), 3)

    def test_pair_prefers_same_scene(self):
        rows = [
            dict(manifest_index=0, scene="a", selected_iou=0.,
                 size_fraction=0.1, boundary_fraction=0.5,
                 shuffled_boundary_fraction=0.5),
            dict(manifest_index=1, scene="a", selected_iou=1.,
                 size_fraction=0.8, boundary_fraction=0.2,
                 shuffled_boundary_fraction=0.2),
            dict(manifest_index=2, scene="b", selected_iou=1.,
                 size_fraction=0.1, boundary_fraction=0.1,
                 shuffled_boundary_fraction=0.1),
        ]
        self.assertEqual(matched_pairs(rows)[0]["success_index"], 1)


if __name__ == "__main__":
    unittest.main()
