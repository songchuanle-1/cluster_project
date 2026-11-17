from pathlib import Path
source=Path("/tmp/cps_admission_20260914/cps_parity_ddp_20260914.py").read_text()
source=source.replace('work = Path("/tmp/cps_admission_20260914")',
                      'work = Path("/tmp/bca_admission_20260914")')
source=source.replace('name = base + "_cps"','name = base + "_bca"')
exec(compile(source,"<bca-parity>","exec"))
