"""Exercise real current local guard with transport/process/network forbidden."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
PACKET=HERE/'bcr_operational_prepare'; TOKEN='41eb62fa1d32436f859264a19b0d4049'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text())
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    paths=[ROOT/'pipeline/queue.json',ROOT/'pipeline/running.json',ROOT/'pipeline/research_work.json',ROOT/'SERVERS.yaml',ROOT/'pipeline/goal.json']
    before={str(p):sha(p) for p in paths}; execution=HERE/'bcr_execution';assert not execution.exists()
    transport_calls=[]; prohibited_events=[]
    class NoTransport:
        def call(self,*args,**kwargs):
            transport_calls.append({'args':str(args[:1])});raise AssertionError('Actual transport forbidden in local guard validation')
    def audit(event,args):
        if event=='subprocess.Popen' or event.startswith('socket.'):
            prohibited_events.append(event);raise AssertionError('Process/network forbidden: '+event)
    sys.addaudithook(audit)
    spec=importlib.util.spec_from_file_location('bcr_actual_guard',PACKET/'adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    adapter=module.Adapter(transport=NoTransport(),execution_dir=execution)
    guard=adapter.guard(gpu=0,mutation=True)
    assert guard['owner']==owner
    refusals={}
    try:adapter.prepare(0)
    except module.Refused as error:refusals['registered_GPU0_busy']=str(error)
    else:raise AssertionError('Busy prepare should be refused before transport/materialization')
    assert refusals['registered_GPU0_busy']=='Selected GPU has registered running task'
    try:adapter.guard(gpu=1,mutation=True)
    except module.Refused as error:refusals['GPU1_not_permitted']=str(error)
    else:raise AssertionError('GPU1 should be refused before transport')
    assert 'Only physical server4 GPU0' in refusals['GPU1_not_permitted']
    try:adapter.guard(required_seconds=999999,gpu=0,mutation=True)
    except module.Refused as error:refusals['unchanged_deadline_budget']=str(error)
    else:raise AssertionError('Insufficient unchanged deadline must be refused')
    assert refusals['unchanged_deadline_budget']=='Insufficient unchanged owner deadline'
    after={str(p):sha(p) for p in paths}
    assert before==after and not execution.exists() and not transport_calls and not prohibited_events and 'torch' not in sys.modules
    assert json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text())==owner
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_LOCAL_CURRENT_OWNER_GUARD_VALID_BUSY_PREPARE_REFUSED_NO_TRANSPORT',
        'candidate_id':module.CANDIDATE,'code_commit':module.COMMIT,'current_owner_token':TOKEN,'original_deadline_at':owner['deadline_at'],
        'guard_actual_current_owner_context_and_external_anchors_valid':True,'refusals':refusals,
        'actual_transport_calls':len(transport_calls),'subprocess_or_network_audit_events':prohibited_events,
        'torch_imported':False,'active_binding_manifest_lease_or_execution_directory_created':False,
        'goal_servers_queue_running_research_work_unchanged':before==after,'shared_artifact_hashes':after,
        'native_execution':'NOT_RUN','resources':'NOT_RUN','GPU1':'NOT_QUERIED_NOT_USED',
        'scope':'Only real current local guards evaluated; registered BTC blocks before any probe/remote/GPU/lease. This is no live hardware-idleness proof, native PASS or admission.'}
    path=HERE/'bcr_actual_local_guard_integration.json'
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'current_owner_valid':True,'transport_calls':0,'active_binding_created':False,'refusals':refusals},ensure_ascii=False))
if __name__=='__main__':main()
