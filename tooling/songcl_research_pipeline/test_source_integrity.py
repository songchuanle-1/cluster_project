"""Execute remote verifier programs locally against disposable Git fixtures."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import closure
import source_integrity as integrity


class SourceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        (self.root / 'configs').mkdir()
        (self.root / 'model.py').write_text('weight = 1\n', encoding='utf-8')
        (self.root / 'README.md').write_text('notes\n', encoding='utf-8')
        (self.root / 'configs/test.yaml').write_text('root: /local/data\nwidth: 4\n', encoding='utf-8')
        self.commit = self.commit_all()
        self.server = dict(host='unused', user='unused', remote_code_root=str(self.root))
        self.legacy_path_api = False

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root),
            '-c', 'core.autocrlf=false', '-c', 'user.name=Pipeline Test',
            '-c', 'user.email=pipeline-test@example.invalid', *args],
            stderr=subprocess.DEVNULL).decode().strip()

    def commit_all(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'isolated fixture')
        return self.git('rev-parse', 'HEAD')

    def remote(self, _host, _user, command):
        program = shlex.split(command)[-1]
        if self.legacy_path_api:
            program = ("import pathlib\n"
                       "def unavailable_api(*args, **kwargs):\n"
                       "    raise AttributeError('Path API unavailable on Python3.8')\n"
                       "pathlib.Path.is_relative_to = unavailable_api\n"
                       "pathlib.PurePath.is_relative_to = unavailable_api\n" + program)
        result = subprocess.run([sys.executable, '-B', '-c', program],
                                capture_output=True, text=True, timeout=15)
        return result.stdout

    def verify(self, mappings=()):
        integrity.verify_git(self.server, self.commit, list(mappings), self.remote)

    def test_clean_tracked_source_passes(self):
        self.verify()

    def test_same_head_with_modified_model_fails(self):
        (self.root / 'model.py').write_text('weight = 2\n')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            self.verify()

    def test_staged_modified_source_also_fails(self):
        (self.root / 'model.py').write_text('weight = 2\n')
        self.git('add', 'model.py')
        with self.assertRaises(ValueError):
            self.verify()

    def test_deleted_source_fails(self):
        (self.root / 'model.py').unlink()
        with self.assertRaises(ValueError):
            self.verify()

    def test_untracked_source_fails_but_notes_do_not(self):
        (self.root / 'notes.txt').write_text('local notes')
        (self.root / 'README.md').write_text('changed notes')
        self.verify()
        (self.root / 'unadmitted.py').write_text('weight = 2')
        with self.assertRaises(ValueError):
            self.verify()

    def test_only_deterministic_config_mapping_is_allowed(self):
        path = self.root / 'configs/test.yaml'
        path.write_text('root: /remote/data\nwidth: 4\n')
        self.verify([('/local/data', '/remote/data')])
        path.write_text('root: /remote/data\nwidth: 5\n')
        with self.assertRaises(ValueError):
            self.verify([('/local/data', '/remote/data')])

    def test_config_changes_without_mapping_fail(self):
        (self.root / 'configs/test.yaml').write_text('root: /remote/data\nwidth: 4\n')
        with self.assertRaises(ValueError):
            self.verify()

    def test_ssh_failure_cannot_look_like_clean_source(self):
        for output in ('', '{}', '{"ok":false}', 'warning\n{"ok":true}'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                integrity.verify_git(self.server, self.commit, [], Mock(return_value=output))

    def test_changed_head_fails_expected_commit_check(self):
        (self.root / 'model.py').write_text('weight = 3\n')
        self.commit_all()
        with self.assertRaises(ValueError):
            self.verify()

    def test_safe_sync_cannot_bypass_content_check_when_heads_match(self):
        (self.root / 'model.py').write_text('weight = 2\n')
        def remote(host, user, command):
            if ' -B -c ' in command:
                return self.remote(host, user, command)
            return self.commit
        with patch.object(closure, 'git', return_value=self.commit):
            with self.assertRaises(ValueError):
                closure.safe_sync(self.root, self.root, self.server, remote)

    def test_marker_hashes_source_instead_of_trusting_label(self):
        code = self.root / 'AdaRES'
        code.mkdir()
        (code / 'model.py').write_text('weight = 1\n', encoding='utf-8')
        commit = self.commit_all()
        (code / '.codex_source_commit').write_text(commit)
        server = dict(self.server, remote_code_root=str(code))
        integrity.verify_marker(self.root, commit, server, self.remote)
        (code / 'model.py').write_text('weight = 2\n')
        with self.assertRaises(ValueError):
            integrity.verify_marker(self.root, commit, server, self.remote)

    def test_marker_manifest_batches_are_bounded(self):
        records = [('directory/' + str(i) + '.py', 'a' * 40) for i in range(500)]
        remote = Mock(return_value='{"ok":true}')
        with patch.object(integrity, 'marker_manifest', return_value=records), \
                patch.object(integrity.subprocess, 'check_output', return_value=b'weight = 1\n'):
            integrity.verify_marker(self.root, self.commit, self.server, remote)
        self.assertGreater(remote.call_count, 1)
        self.assertTrue(all(len(call.args[2].encode()) < 16000 for call in remote.call_args_list))

    def test_marker_checks_work_without_new_pathlib_api(self):
        self.legacy_path_api = True
        code = self.root / 'AdaRES'
        code.mkdir()
        (code / 'model.py').write_text('weight = 1\n', encoding='utf-8')
        commit = self.commit_all()
        (code / '.codex_source_commit').write_text(commit)
        server = dict(self.server, remote_code_root=str(code))
        integrity.verify_marker(self.root, commit, server, self.remote)
        (code / 'model.py').write_text('weight = 2\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            integrity.verify_marker(self.root, commit, server, self.remote)

    def test_config_mapping_checks_work_without_new_pathlib_api(self):
        self.legacy_path_api = True
        path = self.root / 'configs/test.yaml'
        path.write_text('root: /remote/data\nwidth: 4\n', encoding='utf-8')
        self.verify([('/local/data', '/remote/data')])
        path.write_text('root: /remote/data\nwidth: 5\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            self.verify([('/local/data', '/remote/data')])

    def test_marker_accepts_yaml_formatting_but_rejects_value_changes(self):
        self.legacy_path_api = True
        code = self.root / 'AdaRES'
        code.mkdir()
        config = code / 'config.yaml'
        config.write_text('width: 4\nroot: /data\n', encoding='utf-8')
        commit = self.commit_all()
        (code / '.codex_source_commit').write_text(commit)
        server = dict(self.server, remote_code_root=str(code))
        config.write_text('root: "/data"\n\nwidth: 4\n', encoding='utf-8')
        integrity.verify_marker(self.root, commit, server, self.remote)
        config.write_text('root: "/data"\n\nwidth: 5\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            integrity.verify_marker(self.root, commit, server, self.remote)

    def test_marker_accepts_python_crlf_but_rejects_code_changes(self):
        self.legacy_path_api = True
        code = self.root / 'AdaRES'
        code.mkdir()
        model = code / 'model.py'
        model.write_bytes(b'weight = 1\nother = 2\n')
        commit = self.commit_all()
        (code / '.codex_source_commit').write_text(commit)
        server = dict(self.server, remote_code_root=str(code))
        model.write_bytes(b'weight = 1\r\nother = 2\r\n')
        integrity.verify_marker(self.root, commit, server, self.remote)
        model.write_bytes(b'weight = 2\r\nother = 2\r\n')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            integrity.verify_marker(self.root, commit, server, self.remote)


if __name__ == '__main__':
    unittest.main()
