"""Run existing full-backward check on the captured native duplicate fixture."""
from pathlib import Path
source = Path("/tmp/cps_admission_20260914/cps_full_check_20260914.py").read_text()
source = source.replace('fixed / "fixed_batch.pth"', 'Path("/tmp/cps_duplicate_native_fixture_20260914.pth")')
source = source.replace('work / "full_check.json"', 'work / "duplicate_full_check.json"')
exec(compile(source, "<duplicate-native-full-check>", "exec"))
