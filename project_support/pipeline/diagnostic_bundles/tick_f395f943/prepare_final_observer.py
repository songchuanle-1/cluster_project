"""Separate immutable final readback; do not require a training line during validation."""
from pathlib import Path
from anchor import guard
HERE=Path(__file__).resolve().parent
guard()
s=(HERE/'observe_aef.py').read_text('utf8')
s=s.replace('size-24000','size-1200000')
s=s.replace("assert steps and not any(e in txt", "assert not any(e in txt")
s=s.replace("'last_native_step':steps[-1],'max_native_step':max(steps)","'last_native_step':steps[-1] if steps else None,'max_native_step':max(steps) if steps else None")
s=s.replace('aef_training_progress_observation.json','aef_training_progress_observation_final.json')
with (HERE/'observe_aef_final.py').open('x',encoding='utf8') as f:f.write(s)
