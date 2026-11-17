"""Tests use mocked SSH only; never contact any server or other project."""

import json
import sys
import unittest
from unittest.mock import patch
from io import StringIO

sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import pipeline_monitor as monitor

SERVER = {"host": "pinned-host", "user": "songcl", "remote_code_root": "/project/Cluster",
          "registered_pid_probe": True}
CONFIG = "configs/Quard/bps/model_bps.yaml"
TASK = {"id": "test", "pid": 123, "config": CONFIG, "gpu": "0", "status": "running"}


class RegisteredProbeTests(unittest.TestCase):
    def test_config_loader_retains_opt_in(self):
        text = (
            "servers:\n  server-4:\n    role: gpu_server\n"
            "    host: pinned-host\n    user: songcl\n"
            "    registered_pid_probe: true\n"
            "  server-other:\n    role: gpu_server\n    host: mock\n    user: mock\n"
        )
        with patch("builtins.open", return_value=StringIO(text)):
            servers = monitor.load_servers("mock_project")
        self.assertIs(servers["server-4"]["registered_pid_probe"], True)
        self.assertIs(servers["server-other"]["registered_pid_probe"], False)

    def probe(self, payload):
        with patch.object(monitor, "ssh", return_value=payload) as ssh:
            value = monitor.find_registered_processes("host", "user", "/project/Cluster", [TASK])
            self.assertNotIn("ps -e", ssh.call_args.args[2])
            self.assertIn("/proc", ssh.call_args.args[2])
            return value

    def test_exact_identity(self):
        record = ["123", CONFIG, "0", "/checkpoint.pth", "python tools/train.py"]
        self.assertEqual(self.probe(json.dumps({"complete": True, "records": [record]})),
                         {CONFIG: tuple(record)})

    def test_absent_observation(self):
        self.assertEqual(self.probe(json.dumps({"complete": True, "records": []})), {})

    def test_unknown_is_not_absent(self):
        for value in ("", "not-json", "[]", '{"complete":false}', '{"complete":true}',
                      '{"complete":true,"records":[["999","x","0",null,"wrong"]]}'):
            with self.subTest(value=value):
                self.assertIsNone(self.probe(value))

    def test_no_registered_pid(self):
        with patch.object(monitor, "ssh") as ssh:
            self.assertEqual(monitor.find_registered_processes("h", "u", "/p", []), {})
            ssh.assert_not_called()

    def test_scoped_opt_in(self):
        queue = {"gpu_queues": {"server-4": [TASK]}}
        with patch.object(monitor, "find_registered_processes", return_value={"exact": 1}) as exact:
            with patch.object(monitor, "find_running_processes", return_value={"legacy": 1}) as legacy:
                self.assertEqual(monitor.find_project_processes("cluster_project", "server-4", SERVER, queue), {"exact": 1})
                exact.assert_called_once()
                legacy.assert_not_called()
                exact.reset_mock()
                cases = [
                    ("unrelated_mock_project", "server-4", SERVER),
                    ("cluster_project", "server-other", SERVER),
                    ("cluster_project", "server-4", {**SERVER, "registered_pid_probe": False}),
                ]
                for name, server, config in cases:
                    self.assertEqual(monitor.find_project_processes(name, server, config, queue), {"legacy": 1})
                exact.assert_not_called()
                self.assertEqual(legacy.call_count, 3)


if __name__ == "__main__":
    unittest.main()
