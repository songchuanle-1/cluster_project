"""Record the user's latest permanent GPU1 instruction under the owned lease."""
from datetime import datetime,timezone
import copy
import json
import shutil
from pathlib import Path
import subprocess
from run import BUNDLE,ROOT,TOKEN,guard,tick
guard()
before=tick.load(BUNDLE/'goal_snapshot.json')
after=tick.load(ROOT/'pipeline/goal.json')
comparison=copy.deepcopy(after)
confirmation=comparison['constraints'].pop()
assert comparison==before and len(after['constraints'])==22
assert confirmation.startswith('[USER-ALLOCATION CONFIRMED 2026-10-16]')
assert not (BUNDLE/'resource_confirmation_record.json').exists()
shutil.copy2(ROOT/'pipeline/goal.json',BUNDLE/'goal_confirmed.json')
result=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',
    'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
    'cluster_project','manual','User confirms all future work on server3 GPU1.',
    'Pin all future training and GPU diagnostics to server3 GPU1.',
    'Latest explicit user instruction supersedes conditional fallback. Same pinned hostname/GPU UUID now at192.168.1.120. Other21constraints/all11bans and scientific fields unchanged; server4/server6 new dispatch disabled, existing jobs preserved; no scheduler change.',
    str(BUNDLE/'user_resource_confirmation.json')+'; '+str(BUNDLE/'address_repair.json')],
    text=True,encoding='utf-8',capture_output=True,timeout=30)
assert result.returncode==0,result.stderr
decision=Path(result.stdout.rsplit('->',1)[1].strip())
assert decision.is_file() and decision.parent==ROOT/'pipeline/decisions'
tick.save(BUNDLE/'resource_confirmation_record.json',{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'prior21constraints_and_all_other_fields_unchanged':True,'constraint_count':22,
    'goal_sha256':tick.digest(ROOT/'pipeline/goal.json'),
    'confirmed_goal_snapshot_sha256':tick.digest(BUNDLE/'goal_confirmed.json'),
    'decision':{'path':decision.relative_to(ROOT).as_posix(),'sha256':tick.digest(decision)},
    'future_server':'server-3','physical_gpu':1,'new_training_started':False,'scheduler_changes':0})
print(json.dumps({'future_server':'server-3','gpu':1,'all_future_training_and_gpu_diagnostics':True,
    'goal22constraints':True,'other_science_unchanged':True,'decision':str(decision)},indent=2))
