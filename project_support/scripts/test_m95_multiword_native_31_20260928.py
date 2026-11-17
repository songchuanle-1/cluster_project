"""CPU-only contract tests for the frozen 31-expression M95 adapter."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/m95_multiword_native_31_20260928.py"
SPEC = importlib.util.spec_from_file_location("m95_multiword_native_31", SOURCE)
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


class FrozenAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = ADAPTER.frozen_rows(
            ROOT / "pipeline/reports/m95_multiword_capture_manifest_20260928.json")

    def make_dataset(self, target_changed=False, text_changed=False):
        groups = {}
        graphs = {}
        for (scene, aid), record in self.rows.items():
            target = list(record["target_instances"])
            if target_changed and (scene, aid) == next(iter(self.rows)):
                target = [max(target) + 100]
            groups.setdefault(scene, []).append({
                "scene_id": scene, "ann_id": aid, "object_ids": target,
            })
            original = record["text"].removesuffix(" . not mentioned")
            if text_changed and (scene, aid) == next(iter(self.rows)):
                original += " altered"
            graphs.setdefault(scene, {})[str(aid)] = {"utterance": original}

        class Dataset:
            scene_inputs = list(groups.values())
            scene_graphs = graphs

        return Dataset()

    def test_frozen_identity_text_and_target(self):
        dataset = self.make_dataset()
        self.assertEqual(len(ADAPTER.select_native_indices(dataset, self.rows)), 2)

    def test_target_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "text or target differs"):
            ADAPTER.select_native_indices(self.make_dataset(target_changed=True), self.rows)

    def test_text_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "text or target differs"):
            ADAPTER.select_native_indices(self.make_dataset(text_changed=True), self.rows)

    def test_missing_identity_rejected(self):
        dataset = self.make_dataset()
        dataset.scene_inputs[0].pop()
        with self.assertRaisesRegex(ValueError, "lacks"):
            ADAPTER.select_native_indices(dataset, self.rows)

    def test_duplicate_identity_rejected(self):
        dataset = self.make_dataset()
        dataset.scene_inputs[0].append(dict(dataset.scene_inputs[0][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            ADAPTER.select_native_indices(dataset, self.rows)

    def test_unselected_scene_does_not_change_cohort(self):
        dataset = self.make_dataset()
        dataset.scene_inputs.append([{
            "scene_id": "scene_extra", "ann_id": 999, "object_ids": [1],
        }])
        self.assertEqual(ADAPTER.select_native_indices(dataset, self.rows), [0, 1])

    def test_loader_preserves_odd_last_group_and_order(self):
        class Source:
            def __getitem__(self, index):
                return index

            def collate_fn(self, items):
                return items

        def fake_loader(selected, **kwargs):
            self.assertEqual(kwargs["batch_size"], 1)
            self.assertFalse(kwargs["shuffle"])
            self.assertFalse(kwargs["drop_last"])
            self.assertEqual(kwargs["collate_fn"]([3]), [3])
            return [selected.collate_fn([selected[index]])
                    for index in range(len(selected))]

        self.assertEqual(
            ADAPTER.selected_loader(Source(), [3, 1, 4], fake_loader),
            [[3], [1], [4]],
        )

    def test_frozen_rows_span_native_four_expression_groups(self):
        groups = []
        graphs = {}
        expected = []
        for scene, total in (("scene0029_00", 55), ("scene0065_00", 50)):
            for start in range(0, total, 4):
                group = []
                for aid in range(start, min(start + 4, total)):
                    record = self.rows.get((scene, aid))
                    group.append({
                        "scene_id": scene, "ann_id": aid,
                        "object_ids": record["target_instances"] if record else [-1],
                    })
                    if record:
                        graphs.setdefault(scene, {})[str(aid)] = {
                            "utterance": record["text"].removesuffix(" . not mentioned")
                        }
                if any((scene, item["ann_id"]) in self.rows for item in group):
                    expected.append(len(groups))
                groups.append(group)

        class Dataset:
            scene_inputs = groups
            scene_graphs = graphs

        indices = ADAPTER.select_native_indices(Dataset(), self.rows)
        self.assertEqual(indices, expected)
        self.assertEqual(len(indices), 21)
        self.assertEqual(sum(
            (item["scene_id"], item["ann_id"]) in self.rows
            for index in indices for item in groups[index]), 31)


if __name__ == "__main__":
    unittest.main()
