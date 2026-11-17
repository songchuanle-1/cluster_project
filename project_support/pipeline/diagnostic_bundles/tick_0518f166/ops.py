"""Owning-lease helpers for a finite CPU operator diagnostic."""
from datetime import datetime,timezone
import json,os,shlex,subprocess,sys
from pathlib import Path
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT=Path('D:/project/cluster_project');OUT=Path(__file__).resolve().parent
TOKEN='0518f166a2e74c9e868f75ad6b0bf8ee';CID='fle-cutoff-tie-far-donor-continuity-audit'
GOAL='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1'
STAGE='/data/songcl/Project/Cluster_project/pipeline/cutoff_continuity_0518f166'
REMOTE_ROOT='/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b'
def guard():
    owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert tick.digest(ROOT/'pipeline/goal.json')==GOAL
    return owner
def save(name,value):
    guard()
    with (OUT/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False)
def evidence(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def run(args,timeout=90):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def ssh(program,host='192.168.1.115',timeout=90):
    response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','songcl@'+host,shlex.join(['/usr/bin/python3','-B','-c',program])],timeout)
    assert response.returncode==0,response.stderr
    return json.loads(response.stdout)
if __name__=='__main__':
    guard();view=tick.load(ROOT/'pipeline/headless/.tick_model_view.json')
    assert view['design_bootstrap']['required'] and view['research']['due_count']==0
    work=tick.load(ROOT/'pipeline/research_work.json')
    assert not any(c['id']==CID for c in work['candidates'])
    work['candidates'].append({'id':CID,'stage':'diagnosis','kind':'fixed_leaf_operator_continuity_diagnostic',
        'hypothesis':'Exact K32 cutoff tie fallback can create finite far-donor dependency absent under either sign of arbitrarily small exact cutoff perturbation,even with identical zero cutoff-donor content.',
        'matched_control':'One40point dyadic leaf;recipient/cutoff zero,farthest donor one;five preregistered perturbation magnitudes/both signs,constant features,tie-preserving motion/translation,exact Fraction ranks,NumPy and CPU autograd.',
        'next_action':'Execute frozen CPU source-level continuity controls now onserver4withCUDAhidden;retain both precisions and every result. No checkpoint,neural network,sourcechange,epsilonrepair or training.',
        'failure_scope':'inconclusive','preregistered_at':datetime.now(timezone.utc).isoformat(),
        'evidence':[evidence(OUT/'continuity_prereg.md'),evidence(OUT/'continuity_cpu.py')],
        'wake_paths':['pipeline/experiments/M203-FLE.json','SERVERS.yaml']})
    guard();tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'registered':CID,'stage':'diagnosis','new_training_models':0}))
