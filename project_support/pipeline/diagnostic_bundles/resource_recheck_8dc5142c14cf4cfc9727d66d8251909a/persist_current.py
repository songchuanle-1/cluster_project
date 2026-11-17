"""Reuse the unchanged hashed five-candidate closeout; no scientific retest."""
import runpy
from run_probe import BUNDLE, PERSIST, probe

probe.guard()
assert not (BUNDLE / 'persistence.json').exists()
runpy.run_path(str(PERSIST), run_name='__main__')
