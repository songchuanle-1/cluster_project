"""Reuse the frozen resource-only probe with this tick's verified lease."""
import hashlib
import importlib.util
from pathlib import Path

TOKEN = 'ca3da4afb0164e3cbe2b74056a31635d'
BUNDLE = Path(__file__).resolve().parent
SOURCE = BUNDLE.parent / 'resource_recheck_a247e0f3dc214741ae85f7c2f69598e6/run_probe.py'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'a3306db89f6c7067c01b2236e3ecb9c7e1863e96462b3b4c752e8a8aae7b242f'
spec = importlib.util.spec_from_file_location('frozen_resource_probe', SOURCE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
probe.TOKEN = TOKEN
probe.BUNDLE = BUNDLE


if __name__ == '__main__':
    probe.main()
