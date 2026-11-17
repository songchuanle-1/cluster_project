"""Synthetic adapter checks; native CPU verification is recorded separately."""
import ast
import copy
import json
from pathlib import Path
import pickle
import tempfile
import unittest
from unittest.mock import Mock

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from probe_saved_replay_20260920 import remote_code
from referent_registry_binding_20260919 import BindingExporter
from saved_geometry_replay_20260920 import (
    prepare_replay, replay_forward, verify_artifacts, verify_payload,
)
from test_native_registry_geometry_runner_20260920 import setup


class ReplayTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.physical, self.collated = root/"physical", root/"collated"
        self.physical.mkdir()
        self.collated.mkdir()
        native, wrapped, self.model, registry, digest, self.binding = setup()
        item, axes = wrapped[1]
        batch, axes = wrapped.collate_fn([(item,axes)])
        self.exporter = BindingExporter(registry,digest,native.scene_inputs,
                                       self.binding,"e"*64)
        self.payload = dict(item=item,axes=axes,dataset_index=1,
                            source_binding=self.binding)
        self.item_path = self.physical/"item_1.pth"
        self.item_path.write_bytes(pickle.dumps(self.payload))
        self.saved = dict(batch=batch,axes=axes,dataset_index=1,
            source_binding=self.binding,saved_item_sha256=file_sha256(self.item_path),
            item_fingerprint=fingerprint(item),axes_fingerprint=fingerprint(axes))
        self.batch_path = self.collated/"batch_1.pth"
        self.batch_path.write_bytes(pickle.dumps(self.saved))
        joins = wrapped.exporter.manifest()
        self.joins_path = self.physical/"physical_bindings.json"
        self.joins_path.write_text(json.dumps(joins),encoding="ascii")
        self.expected = dict(dataset_index=1,payload_sha256=fingerprint(self.payload),
            native_input_sha256=fingerprint(item),axes_sha256=fingerprint(axes),
            batch_sha256=fingerprint(batch),expressions=len(axes),
            fields={k:dict(sha256=fingerprint(v)) for k,v in batch.items()})
        artifact = lambda p: dict(path=str(p),sha256=file_sha256(p),
                                  bytes=p.stat().st_size)
        observed = dict(self.binding,dataset_source_sha256="e"*64,
                        registry_sha256=digest)
        self.request = dict(
            physical=dict(scratch=str(self.physical),
                artifacts=[artifact(self.item_path),artifact(self.joins_path)],
                observed_binding=observed),
            collated=dict(scratch=str(self.collated),artifacts=[artifact(self.batch_path)],
                observed_binding=observed,items=[self.expected],
                full_binding_sha256=fingerprint(joins)))
        self.load = lambda p: pickle.loads(p.read_bytes())

    def test_verified_exact_inputs_reach_existing_capture_and_cleanup_hooks(self):
        prepared, joins = prepare_replay(self.request,self.exporter,self.load)
        before = fingerprint(prepared)
        seen = []
        records = replay_forward(self.model,prepared,self.binding,
                                 lambda *args:seen.append(args[:2]))
        self.assertEqual(fingerprint(prepared),before)
        self.assertEqual(seen,[(0,1)])
        self.assertEqual(records[0]["criterion_calls"],1)
        self.assertEqual(records[0]["loss"],1.25)
        self.assertEqual(joins["requested"],2)
        self.assertEqual(joins["counts"],{"bound":1,"missing_metadata":1})
        self.assertEqual(len(self.model.criterion.hooks),1)
        self.assertEqual(records[0]["geometry"]["rows"][0]["identity"]["capture_id"],
                         self.saved["axes"][0]["capture_id"])

    def test_tamper_rejected_before_any_deserialization(self):
        self.batch_path.write_bytes(b"changed")
        load = Mock()
        with self.assertRaisesRegex(ValueError,"bytes"):
            prepare_replay(self.request,self.exporter,load)
        load.assert_not_called()

    def test_wrong_path_duplicate_and_missing_inventory_rejected(self):
        for behavior in ("outside","duplicate","missing"):
            request = copy.deepcopy(self.request)
            rows = request["collated"]["artifacts"]
            if behavior == "outside":
                rows[0]["path"] = str(self.item_path)
            elif behavior == "duplicate":
                rows.append(rows[0])
            else:
                rows.clear()
            with self.subTest(behavior=behavior), self.assertRaises(ValueError):
                prepare_replay(request,self.exporter,self.load)

    def test_every_saved_identity_boundary_rejected(self):
        changes = {
            "dataset_index":True,"source_binding":{},"saved_item_sha256":"f"*64,
            "item_fingerprint":"f"*64,"axes_fingerprint":"f"*64,
            "batch":{},"axes":[],
        }
        for key,value in changes.items():
            saved = dict(self.saved,**{key:value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_payload(self.payload,saved,self.expected,
                               file_sha256(self.item_path),self.binding)

    def test_expected_field_hash_and_inventory_are_checked(self):
        for fields in ({},dict(self.expected["fields"],ann_ids={"sha256":"f"*64})):
            with self.assertRaisesRegex(ValueError,"field"):
                verify_payload(self.payload,self.saved,dict(self.expected,fields=fields),
                               file_sha256(self.item_path),self.binding)

    def test_changed_full_bindings_and_current_data_source_rejected(self):
        for which in ("full_binding_sha256","observed_binding"):
            request = copy.deepcopy(self.request)
            request["collated"][which] = "f"*64 if which.endswith("sha256") else {}
            with self.subTest(which=which), self.assertRaises(ValueError):
                prepare_replay(request,self.exporter,self.load)

    def test_reconstruction_must_match_every_binding_field(self):
        joins = json.loads(self.joins_path.read_text())
        joins["bindings"][0]["target_support_count"] = 99
        self.joins_path.write_text(json.dumps(joins),encoding="ascii")
        row = self.request["physical"]["artifacts"][1]
        row.update(sha256=file_sha256(self.joins_path),bytes=self.joins_path.stat().st_size)
        self.request["collated"]["full_binding_sha256"] = fingerprint(joins)
        with self.assertRaisesRegex(ValueError,"Reconstructed"):
            prepare_replay(self.request,self.exporter,self.load)

    def test_prepared_mutation_and_duplicate_fail_before_forward(self):
        prepared,_ = prepare_replay(self.request,self.exporter,self.load)
        model = Mock()
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            replay_forward(model,prepared+prepared,self.binding)
        prepared[0][0]["axes"][0]["capture_id"] = "substituted"
        with self.assertRaisesRegex(ValueError,"mutated"):
            replay_forward(model,prepared,self.binding)
        model.assert_not_called()

    def test_failed_native_forward_preserves_existing_hook(self):
        prepared,_ = prepare_replay(self.request,self.exporter,self.load)
        self.model.behavior = "raise"
        with self.assertRaises(RuntimeError):
            replay_forward(self.model,prepared,self.binding)
        self.assertEqual(len(self.model.criterion.hooks),1)

    def test_load_time_artifact_change_detected(self):
        def load(path):
            value = self.load(path)
            if path == self.batch_path:
                path.write_bytes(path.read_bytes()+b"concurrent")
            return value
        with self.assertRaisesRegex(ValueError,"bytes"):
            prepare_replay(self.request,self.exporter,load)

    def test_group_limits_and_duplicate_indices(self):
        for items in ([],[self.expected]*2,[self.expected]*3):
            request = copy.deepcopy(self.request)
            request["collated"]["items"] = items
            with self.assertRaises(ValueError):
                prepare_replay(request,self.exporter,self.load)

    def test_remote_probe_is_cpu_only_and_compiles(self):
        code = remote_code({})
        tree = ast.parse(code)
        compile(tree,"<saved-replay>","exec")
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertIn("prepare_replay",calls)
        for name in ("capture_forward","replay_forward","native.__getitem__",
                     "collator.collate_fn","torch.cuda.set_device"):
            self.assertNotIn(name,calls)
        self.assertEqual(calls.count("subprocess.check_output"),2)
        self.assertIn('CUDA_VISIBLE_DEVICES=""',code)
        self.assertIn('sys.addaudithook(audit)',code)
        self.assertIn('scratch.mkdir(exist_ok=False)',code)


if __name__ == "__main__":
    unittest.main()
