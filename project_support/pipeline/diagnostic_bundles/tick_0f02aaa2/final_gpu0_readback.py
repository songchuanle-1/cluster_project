"""Fresh permitted physical GPU0/lock probe only; no new worker or training."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
guard()
path=ROOT/'pipeline/diagnostic_bundles/tick_f395f943/hpc_operational_prepare/adapter.py'
assert sha(path)=='988439b555a4e7a4adbeb38453cf924de103706565b3c68addf4d6ced3c5979a'
spec=importlib.util.spec_from_file_location('original_hpc_readonly_final_probe',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
probe=m.Adapter().probe(0);guard()
out={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'physical_observation':probe,'scope':'Fresh physical0/source/lock readback only; this is no admission or future idle/launch permission. GPU1 not queried.'}
with (HERE/'final_gpu0_observation.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'sha256':sha(HERE/'final_gpu0_observation.json'),'physical_observation':probe},ensure_ascii=False))
