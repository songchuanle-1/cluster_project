"""Reuse the exact reviewed read-only AEF observer in this current owner context."""
from pathlib import Path
from anchor import guard,ROOT
HERE=Path(__file__).resolve().parent
guard()
s=(ROOT/'pipeline/diagnostic_bundles/tick_d08825b5/observe_aef_final.py').read_text('utf8')
s='\n'.join(line for line in s.splitlines() if not line.startswith(" record['prior_readback_failure']="))+'\n'
s=s.replace('aef_training_progress_observation_final.json','aef_training_progress_observation.json')
with (HERE/'observe_aef.py').open('x',encoding='utf8') as f:f.write(s)
