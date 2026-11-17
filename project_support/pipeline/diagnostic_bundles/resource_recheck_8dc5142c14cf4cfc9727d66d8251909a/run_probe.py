"""Bind existing resource and five-hold closeout code to this owned lease."""
from datetime import datetime
import importlib.util
import re
from pathlib import Path

ROOT = Path('D:/project/cluster_project')
BUNDLE = Path(__file__).resolve().parent
TOKEN = BUNDLE.name.removeprefix('resource_recheck_')
assert re.fullmatch('[0-9a-f]{32}', TOKEN)
SOURCE = ROOT / 'pipeline/diagnostic_bundles/resource_recheck_a247e0f3dc214741ae85f7c2f69598e6/run_probe.py'
PERSIST = ROOT / 'pipeline/diagnostic_bundles/resource_recheck_ca3da4afb0164e3cbe2b74056a31635d/persist.py'
PERSIST_SHA256 = '31def10760c0b3f20dded8c524c5e7202202de294d81955470214c14f78cf432'
import hashlib
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'a3306db89f6c7067c01b2236e3ecb9c7e1863e96462b3b4c752e8a8aae7b242f'
assert hashlib.sha256(PERSIST.read_bytes()).hexdigest() == PERSIST_SHA256
spec = importlib.util.spec_from_file_location('frozen_current_resource_probe', SOURCE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
probe.TOKEN, probe.BUNDLE = TOKEN, BUNDLE
probe.guard()
context = probe.tick.load(ROOT / 'pipeline/headless/.tick_model_view.json')
assert context['mode'] == 'design' and context['research']['due_count'] == 5
result = probe.tick.load(BUNDLE / 'resource_result.json')
assert result['token'] == TOKEN and not result['ready_for_original_capture_guards']
before = probe.tick.load(BUNDLE / 'work_before.json')
primary = next(c for c in before['candidates'] if c['id'] == 'm95-hierarchical-mask-feature-path-audit')
assert datetime.fromisoformat(result['observed_at']) >= datetime.fromisoformat(primary['retry_after'])


if __name__ == '__main__':
    raise SystemExit('Evidence already captured; use persist_current.py without repeating the probe.')
