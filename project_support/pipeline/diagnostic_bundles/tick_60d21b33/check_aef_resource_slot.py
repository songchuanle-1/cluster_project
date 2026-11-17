"""Root-only local resource check. It never queries hardware or creates AEF execution state."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path('D:/project/cluster_project')
TICK=Path(__file__).resolve().parent
EXPECTED_OWNER={'token':'60d21b3324c94445b26d2ecb24a3ba65','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-26T16:09:41.027895+00:00','deadline_at':'2026-10-26T17:09:41.027895+00:00','context_sha256':'062a6fc0ddeba051336890fe88f3d2d0382d2036f7afc139f368da2568334c23','pending_sha256':'c3ef64975c4c76f8c4febbcdc09867e2c133dbd465aab18a834238cafcf98cb4'}
OBSERVATION_SHA='4974189d8a32ce4a0588aedb8599314090f2adc150914a53d52cad31b2282d4b'
COMMIT='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
CID='hierarchy-parent-antisymmetric-edge-flux'
UUID0='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
CONFIG='configs/Quard/ctf_hcg_csort_bec/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bec.yaml'

def need(value,message):
    if not value:raise RuntimeError(message)
def read(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def no_compute_or_transport(event,args):
    if event in ('subprocess.Popen','os.system','os.posix_spawn','os.spawn','socket.__new__','socket.connect','socket.bind','socket.getaddrinfo'):
        raise RuntimeError('NO_TRANSPORT_OR_PROCESS: '+event)
    if event=='import' and args and str(args[0]).split('.')[0]=='torch':raise RuntimeError('NO_TORCH')

def owner_guard():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    need({k:owner.get(k) for k in EXPECTED_OWNER}==EXPECTED_OWNER,'Current original six-field owner mismatch')
    mode=read(ROOT/'pipeline/execution_mode.json')
    need(mode.get('mode')=='foreground' and mode.get('target_thread_id')==owner['thread_id']==os.environ.get('CODEX_THREAD_ID'),'Only actual foreground root may execute; never override identity')
    need(datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED_OWNER['deadline_at']),'Original deadline expired')
    need(sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256'],'Current context/pending mismatch')
    need(sha(ROOT/'pipeline/goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85','Goal changed')
    need(sha(ROOT/'SERVERS.yaml')=='2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1','GPU0-only resource registry changed')
    need(sha(ROOT/'pipeline/authorizations/server4_gpu0_only_20261026.json')=='94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09','Current resource scope changed')
    import yaml
    server=yaml.safe_load((ROOT/'SERVERS.yaml').read_text('utf-8'))['servers']['server-4']
    need(server['allowed_gpus']==[0] and server['max_tasks_per_gpu']==1,'Only physicalGPU0 is authorized')
    return owner

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
    if not args.execute_root:
        print(json.dumps({'status':'DISABLED_UNLESS_EXPLICIT_ACTUAL_ROOT','actual_resource_check':'NOT_RUN','transport':0,'hardware_query':0,'native_execution':'NOT_RUN'}));return
    sys.addaudithook(no_compute_or_transport)
    owner=owner_guard()
    op=TICK/'bec_training_progress_observation.json';need(sha(op)==OBSERVATION_SHA,'This tick actual hardware observation changed')
    obs=read(op);samples=obs.get('observations');need(obs.get('owner_token')==owner['token'] and isinstance(samples,list) and len(samples)==2,'Missing two current-owner actual observations')
    queue=read(ROOT/'pipeline/queue.json');rows=[x for ts in queue['gpu_queues'].values() for x in ts];bec=[x for x in rows if x.get('id')=='M215-BEC'];need(len(bec)==1,'Original BEC queue identity changed');bec=bec[0]
    need(all(bec.get(k)==v for k,v in {'status':'running','pid':1558071,'gpu':'0','server':'server-4','code_commit':COMMIT,'config':CONFIG,'launch_verified':True,'launch_verification':'training_progress'}.items()),'BEC no longer canonical verified GPU0 occupancy; do not infer current hardware state')
    mappings=[(server,str(gpu),eid) for server,gpus in read(ROOT/'pipeline/running.json').items() for gpu,eid in gpus.items()]
    need(mappings==[('server-4','0','M215-BEC')],'Current registered occupancy changed')
    for sample in samples:
        when=datetime.fromisoformat(sample['observed_at']);need(datetime.fromisoformat(owner['generated_at'])<=when<=datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at']),'Actual sample is not from this original owner window')
        need(sample['id']=='M215-BEC' and sample['pid']==1558071 and sample['start_ticks']=='64444390' and sample['runtime_HEAD']==COMMIT,'Observed process/version mismatch')
        need(sample['argv']==['python','tools/train.py',CONFIG,'--gpu_ids','0','--num_gpus','1'] and sample['fd1']==bec['log'],'Observed original BEC argv/log mismatch')
        need(sample['errors']==[] and sample['GPU1_queried'] is False and sample['signals_sent'] is False,'Actual evidence contains error or out-of-scope action')
        inventory=[x.strip() for x in sample['gpu_inventory'].split(',')];need(inventory[0]=='0' and inventory[1]==UUID0,'Actual observation is not physicalGPU0/UUID0')
        contexts=[x.strip() for x in sample['gpu_contexts'].splitlines() if x.strip()];need(len(contexts)==1 and contexts[0].split(',')[0].strip()=='1558071' and int(contexts[0].split(',')[1])>0,'Actual saved hardware evidence does not show original BEC occupancy')
        need(len(sample['actual_model8_hashes'])==8 and all(sha(ROOT/'Cluster'/path)==digest for path,digest in sample['actual_model8_hashes'].items()),'Actual original BEC source8 mismatch')
    first,last=samples;need(first['train_progress'][:2]==last['train_progress'][:2] and first['train_progress'][2]<last['train_progress'][2] and obs['native_TRAIN_growth'] is True,'No actual current native progress')
    work=read(ROOT/'pipeline/research_work.json');aef=next(c for c in work['candidates'] if c['id']==CID)
    need(aef.get('experiment_id')=='M216-AEF' and aef.get('native_execution_code_commit') is None,'AEF actual native state changed; reconcile instead')
    need(not any(x.get('id')=='M216-AEF' for x in rows),'AEF already queued; no inferred preparation result')
    owner_guard()
    need('torch' not in sys.modules,'Torch unexpectedly imported')
    result={'kind':'resource_check','result':'blocked','candidate_id':CID,'experiment_id':'M216-AEF','recorded_at':datetime.now(timezone.utc).isoformat(),'owner':owner,'physical_gpu':0,'allowed_gpus':[0],'blocker':'Current GPU0 registered M215-BEC and this tick root-saved actual GPU0 process/context occupancy; no authorized idle slot for AEF native.','hardware_evidence':ref(op),'actual_hardware_observed_at':[x['observed_at'] for x in samples],'registered_task':{'id':'M215-BEC','pid':1558071,'gpu':0,'code_commit':COMMIT},'AEF_native_execution':'NOT_RUN','AEF_native_tool_availability':'NOT_ASSERTED; this is a local resource check, not an AEF adapter or preparation PASS.','software_scope':'Only current root identity/policy/local canonical state and exact root-saved actual observation inspected. No new hardware query or physical test.','hardware_availability_claim':'No new live hardware query; saved actual samples show occupiedGPU0 and current canonical metadata still reserves it. Metadata alone is not hardware-idle proof.','transport_calls':0,'subprocess_calls':0,'network_calls':0,'GPU_queries':0,'GPU1_queries':0,'Torch_imported':False,'standard_PASS_receipt_queue_written':False,'new_action':False,'user_decision':False,'material_concerns':[]}
    out=TICK/'aef_resource_slot_check.json'
    with out.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps({'path':str(out),'sha256':sha(out),'result':'blocked','native_execution':'NOT_RUN','transport':0}))

if __name__=='__main__':main()
