"""Close only at the real deadline boundary; do not infer scientific admission."""
from datetime import datetime, timezone
import json
import subprocess
import sys
from ops import ROOT, OUT, ID, NAME, TOKEN, SKILL, guard, evidence, tick, now

owner, _ = guard(20)
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
assert 20 < remaining <= 180, 'The real near-deadline disposition is not yet applicable'
static = tick.load(OUT / 'independence_and_wiring_r1.json')
directory = ROOT / 'Cluster/framework/model/Quard_model' / (NAME + '_pce')
assert all(tick.digest(directory / name) == value for name, value in static['model_sources'].items())
assert tick.digest(ROOT / static['config']['path']) == static['config']['sha256']
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(c for c in work['candidates'] if c['id'] == ID)
assert candidate['stage'] == 'validation' and candidate['scientific_admission'] is False
if work.get('design_cycle'):
    work.setdefault('design_cycle_history', []).append(work['design_cycle'])
work['design_cycle'] = {'stop_reason': 'tick_deadline_near', 'attempted_ids': [ID],
    'evidence': [evidence(OUT / 'analysis.json')], 'resume_condition': candidate['next_action'],
    'observed_at': now(), 'actual_remaining_seconds': remaining}
tick.save(ROOT / 'pipeline/research_work.json', work)
notes = tick.load(OUT / 'report_notes.json')
notes['decisions'].append('真实截止前剩余约' + str(round(remaining)) + '秒，按tick_deadline_near保留已推进的PCE validation候选续做；不宣称路线穷尽、外部阻塞、科学准入或已训练。本记录保存时finish尚未执行。')
tick.save(OUT / 'report_notes.json', notes)
result = subprocess.run([sys.executable, '-B', str(SKILL / 'foreground_tick.py'), 'cluster_project',
    'report', '--token', TOKEN, '--notes', str(OUT / 'report_notes.json')])
assert result.returncode == 0
result = subprocess.run([sys.executable, '-B', str(SKILL / 'foreground_tick.py'), 'cluster_project',
    'finish', '--token', TOKEN])
raise SystemExit(result.returncode)
