"""Static orchestration checks, not native behavioral evidence."""
import ast
import json
import unittest

from probe_saved_collation_20260920 import parse_output, remote_code


class SavedCollationProbeTest(unittest.TestCase):
    def test_program_compiles(self):
        compile(remote_code({}),"<saved-collation>","exec")

    def test_no_new_transforms_or_model_execution(self):
        tree = ast.parse(remote_code({}))
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        for name in ("capture_forward","capture_planned","torch.cuda.set_device",
                     "native.__getitem__","native.transform_train"):
            self.assertNotIn(name,calls)
        self.assertIn("collator.collate_fn",calls)
        self.assertIn("exporter.export_item",calls)
        self.assertEqual(calls.count("subprocess.check_output"),2)

    def test_saved_hashes_checked_before_load(self):
        code = remote_code({})
        self.assertLess(code.index('Saved artifact hash changed'),
                        code.index('payload = torch.load'))
        self.assertIn('scratch.mkdir(exist_ok=False)',code)
        self.assertIn('sys.addaudithook(audit)',code)
        self.assertIn('out.open("xb")',code)
        self.assertIn('if reconstructed != saved_joins:',code)
        self.assertIn('map_location="cpu",weights_only=False',code)

    def test_capacity_survives_later_failure(self):
        frame = dict(gpu=7,free_mib=123,training={"tail":""})
        result = parse_output("CAPACITY_JSON:"+json.dumps(frame)+"\n",
                              "native import failed",1)
        self.assertEqual(result["capacity"]["free_mib"],123)
        self.assertEqual(result["returncode"],1)
        self.assertNotIn("saved_collation_completed",result)

    def test_final_frame_and_training_progress(self):
        cap = {"training":{"tail":
            "Train[26/50]: | 10/100 [abc]\rTrain[26/50]: | 12/100 [abc]"}}
        text = ("CAPACITY_JSON:"+json.dumps(cap)+"\nRESULT_JSON:"+
                json.dumps({"saved_collation_completed":True})+"\n")
        result = parse_output(text,"",0)
        self.assertTrue(result["saved_collation_completed"])
        self.assertEqual(result["capacity"]["training"]["steps"][-1]["step"],12)

    def test_cpu_and_mutation_checks_present(self):
        code = remote_code({})
        self.assertIn('CUDA_VISIBLE_DEVICES=""',code)
        self.assertIn('fingerprint(payload) != initial',code)
        self.assertIn('fingerprint(again) != first_digest',code)
        self.assertIn('fingerprint(loaded_batch) != fingerprint(frozen_batch)',code)
        self.assertIn('new_train_transforms=False',code)


if __name__ == "__main__":
    unittest.main()
