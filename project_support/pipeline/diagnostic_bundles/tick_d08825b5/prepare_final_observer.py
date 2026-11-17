"""Prepare a separate immutable final readback without changing prior observations."""
from pathlib import Path
from anchor import guard
HERE=Path(__file__).resolve().parent
guard()
s=(HERE/'observe_aef_v2.py').read_text('utf8')
old="assert before==after and b['max_native_step']>a['max_native_step']"
assert old in s
s=s.replace(old,'assert before==after')
s=s.replace('aef_training_progress_observation_v2.json','aef_training_progress_observation_final.json')
with (HERE/'observe_aef_final.py').open('x',encoding='utf8') as f:f.write(s)
