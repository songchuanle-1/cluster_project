import unittest

from m95_physical_semantic_contract_20260926 import audit, native_mapping


class PhysicalSemanticContractTest(unittest.TestCase):
    def test_mapping_and_unresolved_alias(self):
        source = "self.type2class = {'chair': 2, 'others': 17}\nself.sem2nyu = [5]\nself.nyu40ids = np.array([5])\n"
        tsv = "header\n" + "\t".join(["x"] * 4 + ["5"] + ["x"] * 2 + ["chair"])
        self.assertEqual(native_mapping(source, tsv), (
            {"chair": 2, "others": 17}, {0: 2}))

    def test_fails_closed_on_duplicate_mapping(self):
        source = "self.type2class = {'others': 17}\nself.sem2nyu = [5]\nself.sem2nyu = [6]\nself.nyu40ids = [5]\n"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            native_mapping(source, "header\n")

    def test_exact_physical_mismatch_and_controls(self):
        capture = {"producer_sha256": "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a",
                   "capture_mode": "full_train_scan", "native_capture_completed": True,
                   "rows": []}
        annotations = []
        for index in range(256):
            capture["rows"].append({
                "manifest_index": index, "scene": "scene%03d" % index,
                "ann_id": index, "target_object_id": 1, "target_instances": [1],
                "physical_instance_labels": [1, 2],
                "semantic_labels": [1 if index == 1 else 0, 0],
                "stratum": "ambiguous" if index < 128 else "class_unique",
                "selected_query": 0, "ious": [0.1 if index == 1 else 0.9],
            })
            annotations.append({"scene_id": "scene%03d" % index,
                                "ann_id": index, "object_id": 1,
                                "object_name": "chair" if index != 2 else "arm_chair"})
        result = audit(capture, annotations, {"chair": 2, "others": 17},
                       {0: 2, 1: 3})
        self.assertEqual(result["summary"]["all"]["eligible"], 255)
        self.assertEqual(result["summary"]["all"]["exposed"], 1)
        self.assertEqual(result["summary"]["all"]["exposed_failures"], 1)
        self.assertTrue(result["rows"][2]["unresolved"])


if __name__ == "__main__":
    unittest.main()
