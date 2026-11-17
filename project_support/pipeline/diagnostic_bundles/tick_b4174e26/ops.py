"""Current owning-lease helpers for a CPU-only metric-geometry audit."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT=Path('D:/project/cluster_project');OUT=Path(__file__).resolve().parent
TOKEN='b4174e26acf345ae8f3196c62b37c864'
CID='fle-fixed-membership-metric-geometry-audit'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1'
STAGE='/data/songcl/Project/Cluster_project/pipeline/metric_geometry_b4174e26'
REMOTE_ROOT='/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b'

def guard():
    owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert tick.digest(ROOT/'pipeline/goal.json')=='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
    return owner

def save(name,value):guard();tick.save(OUT/name,value)
def evidence(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def run(args,timeout=90):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def ssh(program,host='192.168.1.115',timeout=90):
    result=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','songcl@'+host,
        shlex.join(['/usr/bin/python3','-B','-c',program])],timeout)
    assert result.returncode==0,result.stderr
    return json.loads(result.stdout)

if __name__=='__main__':
    guard();view=tick.load(ROOT/'pipeline/headless/.tick_model_view.json')
    assert view['design_bootstrap']['required'] and view['research']['due_count']==0
    work=tick.load(ROOT/'pipeline/research_work.json')
    assert not any(c['id']==CID for c in work['candidates'])
    work['candidates'].append({'id':CID,'stage':'diagnosis','kind':'point_path_robustness_diagnostic',
        'hypothesis':'With fine membership and feature values fixed,Euclidean-neighbor-order preserving geometry transforms preserve the exact admitted FLE exchange;test actual TRAIN geometries without claiming whole-hierarchy equivariance or task efficacy.',
        'matched_control':'Identity,reflection,axis permutation,power-of-two scale,fixed translation/orthonormal rotation plus one preregistered non-isometric negative fixture;original hierarchy membership held fixed,no source or feature change.',
        'next_action':'Execute cheapest exact-source CPU fixture,then eight frozen TRAIN scene geometry tests using native means/fine memberships;save counterexamples and tie margins without editing M203. No CUDA or new training.',
        'failure_scope':'inconclusive','preregistered_at':datetime.now(timezone.utc).isoformat(),
        'evidence':[evidence(OUT/'metric_prereg.md'),evidence(ROOT/'pipeline/diagnostic_bundles/tick_dbeca5d6/cpu_contracts_result.json')],
        'wake_paths':['pipeline/experiments/M203-FLE.json','SERVERS.yaml']})
    guard();tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'registered':CID,'stage':'diagnosis','new_training_models':0,'admissions':0}))
