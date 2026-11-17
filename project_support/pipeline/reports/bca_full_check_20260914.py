"""Bounded native full TRAIN check using prior fixed data/checkpoint."""
from pathlib import Path
source=Path("/tmp/cps_admission_20260914/cps_full_check_20260914.py").read_text()
source=source.replace('work = Path("/tmp/cps_admission_20260914")',
                      'work = Path("/tmp/bca_admission_20260914")')
source=source.replace('name = base + "_cps"','name = base + "_bca"')
source=source.replace('details["cps_eligible_pairs"]','details["bca_valid_masks"]')
source=source.replace('k.startswith("cps_")','k.startswith("bca_")')
source=source.replace('cps={k:', 'bca={k:')
exec(compile(source,"<bca-native-full-check>","exec"))
