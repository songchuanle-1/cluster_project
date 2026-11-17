import unittest
import closure


class MultiviewClosureTests(unittest.TestCase):
    def test_native_steps(self):
        self.assertEqual(closure.steps(
            "Epoch: [2]  [  0/9166]\nEpoch: [2] [ 10/9166]\n"
            "Test: [2] [20/1188]"), [(2, 0), (2, 10)])

    def test_program_and_guards(self):
        program = closure.multiview_program("/project/code",
            "configs/train/train_mvggt_refer_m89.yaml", 2, "/project/code/logs/x.log")
        compile(program, "<launch>", "exec")
        self.assertIn("train=train_mvggt_refer_m89", program)
        self.assertIn("MVGGT_GPU", program)
        self.assertNotIn("write_text", program)
        for config in ("../x.yaml", "configs/train/x;bad.yaml"):
            with self.assertRaises(ValueError):
                closure.multiview_program("/p", config, 2, "/p/log")

    def test_launch_uses_project_adapter(self):
        server = dict(remote_code_root="/project/code", conda_source="/conda.sh",
                      conda_env="/env", host="host", user="user")
        captured = []
        def ssh(*args):
            captured.append(args)
            return '{"pid":123,"log":"/project/log"}'
        result = closure.launch_multiview(server,
            {"config": "configs/train/train_mvggt_refer_m89.yaml"}, 1,
            "/project/log", ssh)
        self.assertEqual(result["pid"], 123)
        self.assertIn("accelerate.commands.launch", captured[0][2])
