"""Owning-lease helpers for finite saved-storage accounting."""
from datetime import datetime,timezone
import json,os,shlex,subprocess,sys
from pathlib import Path
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT=Path('D:/project/cluster_project');OUT=Path(__file__).resolve().parent
TOKEN='19aeaa5c23b8475ebe2148a0fdcf4e6b';CID='fle-backward-saved-neighbor-storage-audit'
GOAL='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1'
STAGE='/data/songcl/Project/Cluster_project/pipeline/saved_storage_19aeaa5c'
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
    work['candidates'].append({'id':CID,'stage':'diagnosis','kind':'finite_point_path_storage_diagnostic',
        'hypothesis':'The admitted zero-new-parameter FLE retains N*K*C floating donor storage for backward,including masked padded neighbor slots;parameter reduction does not eliminate activation storage.',
        'matched_control':'Actual unchanged K32/H8/C256/float32 source;N16/64/128singleleaf andN128in16leavesof8;deduplicated saved-storage hooks vsplain/source no_grad,identical output andfinite matchedgradient.',
        'next_action':'Execute preregistered finite CPU saved-storage accounting now withCUDAhidden andone thread;record underlying storage aliases and validity count. Do not claimGPUpeak orimplementmemoryrepair.',
        'failure_scope':'inconclusive','preregistered_at':datetime.now(timezone.utc).isoformat(),
        'evidence':[evidence(OUT/'saved_storage_prereg.md'),evidence(OUT/'saved_storage_cpu.py')],
        'wake_paths':['pipeline/experiments/M203-FLE.json','SERVERS.yaml']})
    guard();tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'registered':CID,'stage':'diagnosis','new_training_models':0}))
