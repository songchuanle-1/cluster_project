"""Preserve the first deployment sample and take a final original-run readback."""
from pathlib import Path
import ast
from anchor import guard
HERE=Path(__file__).resolve().parent
guard();s=(HERE/'observe_cre.py').read_text('utf8');old='cre_training_progress_observation.json';assert s.count(old)==2
s=s.replace(old,'cre_training_progress_observation_final.json');ast.parse(s)
with (HERE/'observe_cre_final.py').open('x',encoding='utf8') as f:f.write(s)
