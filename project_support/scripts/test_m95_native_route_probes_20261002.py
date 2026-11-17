"""Run with server-6 project_cluster torch on CPU, not the local machine."""
import unittest

import torch

from m95_distinct_referent_ownership_20261002 import pair_probe
from m95_native_task_jacobian_20261002 import flat_parameter_grad, similarity


class NativeProbeContracts(unittest.TestCase):
    def setUp(self):
        self.z = torch.tensor([[1.0, -1.0, 0.0, 0.3],
                               [-1.0, 1.0, 0.0, -0.3]], dtype=torch.float64)
        self.target = torch.tensor([[True, False, False, False],
                                    [False, True, False, False]])

    def test_joint_and_independent_corrective(self):
        result = pair_probe(torch, self.z, self.target)
        for arm in ("joint", "independent"):
            self.assertTrue(all(x > 0 for x in result[arm]["margin_velocity"]))

    def test_overlap_rejected(self):
        target = self.target.clone()
        target[1, 0] = True
        with self.assertRaises(ValueError):
            pair_probe(torch, self.z, target)

    def test_empty_target_rejected(self):
        target = self.target.clone()
        target[1] = False
        with self.assertRaises(ValueError):
            pair_probe(torch, self.z, target)

    def test_unbound_shape_rejected(self):
        with self.assertRaises(ValueError):
            pair_probe(torch, self.z[:, :3], self.target)

    def test_nonfinite_rejected(self):
        z = self.z.clone()
        z[0, 0] = float("nan")
        with self.assertRaises(ValueError):
            pair_probe(torch, z, self.target)

    def test_component_grad_sum(self):
        p = torch.tensor([1.0, 2.0], requires_grad=True)
        a, b = p.square().sum(), (p * 3).sum()
        ga, _ = flat_parameter_grad(torch, a, [p])
        gb, _ = flat_parameter_grad(torch, b, [p])
        total, checks = flat_parameter_grad(torch, a + b, [p])
        self.assertTrue(torch.equal(ga + gb, total))
        self.assertEqual(checks["connected_tensors"], 1)

    def test_zero_component_reported_disconnected(self):
        p = torch.tensor([1.0, 2.0], requires_grad=True)
        grad, checks = flat_parameter_grad(torch, torch.tensor(0.0), [p])
        self.assertEqual(int(grad.count_nonzero()), 0)
        self.assertEqual(checks["connected_tensors"], 0)
        self.assertEqual(checks["nonzero_tensors"], 0)

    def test_undefined_cosine_not_zero(self):
        self.assertIsNone(similarity(torch, torch.zeros(3), torch.ones(3))["cosine"])


if __name__ == "__main__":
    unittest.main()
