"""Read-only exact registered BTC process and short native progress observation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,time

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
TOKEN='3824d9c96f6343e09d60362b4a00495b'

def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text())
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    queue=json.loads((ROOT/'pipeline/queue.json').read_text())
    task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M211-BTC')
    assert task['status']=='running' and task['launch_verified'] is True and task['pid']==2784474 and str(task['gpu'])=='0'
    params={k:task[k] for k in ('pid','config','log')}
    payload='PARAMS='+repr(params)+'\nBTC_SOURCES='+repr({'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/__init__.py': '327bf439ad68108b0493d337a2097dc83626e71af869b2536408232f197eda62', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/backbone.py': '1eb4ac3483961e708c23b0abad396c181dbf38c56fcca559d88b9622af46bafd', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/dec.py': '294d1c40b4b5ca72e1adc3d158d90b3f9fe176351a41c9a4107458f48439ea22', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/hier_postprocess.py': 'ee308d8769e9e8e93cc7cea092ef1dc9c2832ababb5073ec9249094f4402a058', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/loss.py': 'c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/middle_tree.py': 'd64cae116d22dcbe9cc1ef954cb0cd61d0b52ebe231484d5c5ef8d00946ee8ec', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/network.py': '5a77eb852b3c6e5de2804d80a2c7a16504f1fd8a57aa94dc6045d9f35587625d', 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc/sample_model.py': 'b22319d5c3958a9a893cb6c2134dd7e124778610aba7e8b9c90647560c806999'})+'\nBTC_CONFIG_SHA='+repr('77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea')+'\n'+r'''
import socket,json,os,re,time,subprocess,hashlib
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
p=Path('/proc')/str(PARAMS['pid']); s=(p/'stat').read_text().rsplit(')',1)[1].split()
args=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v]
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
expected=['python','tools/train.py',PARAMS['config'],'--gpu_ids','0','--num_gpus','1']
assert args==expected and os.readlink(p/'cwd')==root
assert os.readlink(p/'fd/1')==PARAMS['log']
path=Path(PARAMS['log'])
with path.open('rb') as f: f.seek(max(0,path.stat().st_size-600000)); text=f.read().decode(errors='replace')
trains=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text))
assert trains
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert row.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert any(line.split(',')[0].strip()==str(PARAMS['pid']) for line in contexts.splitlines())
head=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip()
assert head=='11a811618179ab1ddc0cee299194667413b7fdb9'
actual_sources={p:hashlib.sha256((Path(root)/p).read_bytes()).hexdigest() for p in BTC_SOURCES};assert actual_sources==BTC_SOURCES
assert hashlib.sha256((Path(root)/PARAMS['config']).read_bytes()).hexdigest()==BTC_CONFIG_SHA
lines=text.replace('\r','\n').splitlines()
errors=[line for line in lines if any(k in line for k in ['Traceback','AttributeError','RuntimeError','Early stopping'])]
print(json.dumps({'pid':PARAMS['pid'],'start_ticks':s[19],'state':s[0],'argv':args,'cwd':root,'runtime_HEAD':head,'BTC_admitted_source_commit':'00e2b18c6b8d568a64edb496e6979d766440883c','BTC_native_model_sources_and_deployed_YAML_unchanged':True,
 'train_progress':[int(trains[-1][i]) for i in (1,2,3,4)],'log':str(path),'log_bytes':path.stat().st_size,
 'log_age_seconds':time.time()-path.stat().st_mtime,'gpu0':row,'gpu0_contexts':contexts,'errors':errors,
 'last_nonempty_lines':[line[-400:] for line in lines if line.strip()][-6:],
 'GPU1':'NOT_QUERIED_BY_THIS_GPU0_OBSERVER','read_only':True,'signals_sent':False}))
'''
    cmd=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -']
    observations=[]
    for i in range(2):
        if i:time.sleep(3)
        run=subprocess.run(cmd,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=40)
        if run.returncode:
            fail={'returncode':run.returncode,'stderr':run.stderr,'observations':observations,'signals_sent':False,'launch_retried':False}
            (HERE/'btc_observation_failure.json').write_text(json.dumps(fail,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            raise RuntimeError('Exact readonly observation failed; no process change or restart performed')
        observations.append({'observed_at':datetime.now(timezone.utc).isoformat(),'data':json.loads(run.stdout)})
    a,b=[o['data'] for o in observations]
    assert a['start_ticks']==b['start_ticks']=='47557208' and a['argv']==b['argv'] and not a['errors'] and not b['errors']
    increasing=(b['train_progress'][0],b['train_progress'][2])>(a['train_progress'][0],a['train_progress'][2])
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment':'M211-BTC','observations':observations,
            'same_exact_registered_process_and_native_TRAIN_growth':increasing,'start_identity_scope':'Exact original start47557208 first captured in tick_ddb531fb after verified launch, now unchanged across two observations; initial dispatch did not record start_ticks.',
            'no_BTC_relaunch_or_BTC_source_change_or_signal':True,'GPU1':'NOT_QUERIED_BY_THIS_BTC_OBSERVER'}
    path=HERE/'btc_progress_observation.json'
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'progress':[a['train_progress'],b['train_progress']],
                      'growth':increasing,'pid':task['pid'],'start_ticks':b['start_ticks'],'runtime_HEAD':b['runtime_HEAD']},ensure_ascii=False))

if __name__=='__main__':main()
