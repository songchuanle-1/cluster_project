"""Root-only actual-result binding copy; default does not read results or write."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, re, sys

TICK=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_a6e82f44')
sys.path.insert(0,str(TICK))
from anchor import ROOT, EXPECTED, guard
SOURCE=TICK/'elc_promotion_prepare'
DEST=TICK/'elc_admission_active'
EXE=TICK/'elc_execution'
SOURCE_SHA=None
MANIFEST_SHA='f183e9ee95aaf18a765d205dea55747569bdec42f1db3e2d69175989803790c9'
LEASE_SHA='5455778b1e5e67070ca4edddbd834c0c5cb2c8dab453f077f58193cf790046a3'
CID='hierarchy-undirected-edge-state-line-graph-composition'
CODE='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
BASE='c9be548699cd66bf68badff9ae6198a03eafa142'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
STATUS='FOUR_ACTUAL_ELC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
PAIRS=(('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate'))
FILES=('elc_evidence.py','summarize_elc_actual.py','fast_forward_tested_elc.py','admit_elc_queue.py','dispatch_elc_once.py','source_bindings.json')

def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write_new(p,data):
    guard()
    with Path(p).open('xb') as f:
        f.write(data);f.flush();__import__('os').fsync(f.fileno())

def check_actual(peer_sha):
    guard()
    peer_path=TICK/'elc_actual_independent_review.json'
    assert sha(peer_path)==peer_sha,'Independent review bytes differ from explicit root SHA'
    peer=read(peer_path)
    assert peer['status']==STATUS and peer['material_concerns']==[]
    assert peer['candidate_id']==CID and peer['code_commit']==CODE and peer['goal_sha256']==GOAL
    assert len(peer['raw_results'])==4 and {(v['mode'],v['target']) for v in peer['raw_results']}==set(PAIRS)
    assert sha(EXE/'native_manifest.json')==MANIFEST_SHA and sha(EXE/'execution_lease.json')==LEASE_SHA
    m=read(EXE/'native_manifest.json');b=read(EXE/'execution_binding.json');lease=read(EXE/'execution_lease.json')
    assert b['owner']==EXPECTED and set(b['owner'])==set(EXPECTED)
    assert b['candidate_id']==m['candidate_id']==CID and b['code_commit']==m['code_commit']==CODE
    assert b['runtime_code_commit']==m['runtime_code_commit']==BASE
    assert b['native_manifest_sha256']==lease['native_manifest_sha256']==MANIFEST_SHA and b['execution_lease_sha256']==LEASE_SHA
    assert m['current_token']==lease['token']==EXPECTED['token'] and m['goal_sha256']==GOAL
    assert m['physical_gpu']==b['physical_gpu']==lease['physical_gpu']==0 and m['allowed_gpus']==[0,1]
    assert m['gpu_uuid']==b['gpu_uuid']==lease['gpu_uuid']=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
    for key in ('context_sha256','pending_sha256','deadline_at'):
        assert m[key]==lease[key]==EXPECTED[key]
    raw_refs=[];request_ids=[]
    for mode,target in PAIRS:
        p=EXE/(mode+'_'+target+'_execution.json');q=EXE/(mode+'_'+target+'_request.json')
        envelope=read(p);request=read(q);raw=envelope['result']
        item=next(x for x in peer['raw_results'] if (x['mode'],x['target'])==(mode,target))
        assert item['execution_path']==ref(p)['path'] and item['execution_sha256']==sha(p)
        assert item['request_id']==request['request_id']==envelope['identity']['request_id']
        assert item['result_sha256']==envelope['result_sha256']
        assert hashlib.sha256(json.dumps(raw,indent=2,allow_nan=False).encode()).hexdigest()==envelope['result_sha256']
        assert envelope['certainty']=='terminal' and envelope['returncode']==0 and raw['execution_completed'] is True
        assert all(envelope['identity'].get(k)==v for k,v in request.items() if k not in ('mode','target'))
        expected={'candidate_id':CID,'code_commit':CODE,'goal_sha256':GOAL,'mode':mode,'target':target,
                  'current_token':EXPECTED['token'],'physical_gpu':0,'native_manifest_sha256':MANIFEST_SHA,
                  'context_sha256':EXPECTED['context_sha256'],'pending_sha256':EXPECTED['pending_sha256'],
                  'deadline_at':EXPECTED['deadline_at'],'stage':b['stage'],'gpu_uuid':b['gpu_uuid']}
        assert all(raw.get(k)==v for k,v in expected.items())
        request_ids.append(request['request_id']);raw_refs.append(ref(p))
    assert len(set(request_ids))==4
    return ref(peer_path),raw_refs

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute-root',action='store_true')
    ap.add_argument('--source-preparation-sha256')
    ap.add_argument('--peer-sha256','--independent-review-sha256',dest='independent_review_sha256',default=None)
    args=ap.parse_args()
    if not args.execute_root:
        print('DEFAULT_READ_ONLY_NO_BINDING_COPY_OR_PROMOTION');return
    assert isinstance(args.independent_review_sha256,str) and re.fullmatch('[0-9a-f]{64}',args.independent_review_sha256),'Actual peer SHA argument required'
    global SOURCE_SHA
    SOURCE_SHA=args.source_preparation_sha256
    assert isinstance(SOURCE_SHA,str) and re.fullmatch('[0-9a-f]{64}',SOURCE_SHA)
    guard();assert sys.dont_write_bytecode
    assert sha(SOURCE/'preparation.json')==SOURCE_SHA
    original=read(SOURCE/'preparation.json')
    assert original['draft_execution_disabled'] is True and original['prepared_for_owner']==EXPECTED
    for name,h in original['prepared_file_hashes'].items():assert sha(SOURCE/name)==h
    peer,raws=check_actual(args.independent_review_sha256)
    source_bindings=read(SOURCE/'source_bindings.json')
    assert source_bindings['code_commit']==CODE and source_bindings['parent_commit']==BASE
    assert source_bindings['native_preparation']['sha256']==read(EXE/'execution_binding.json')['frozen_preparation_sha256']
    assert source_bindings['manifest_template']['sha256']==read(EXE/'execution_binding.json')['frozen_template_sha256']
    files={name:(SOURCE/name).read_bytes() for name in FILES}
    text=files['elc_evidence.py'].decode('utf8')
    assert text.count('DRAFT_EXECUTION_DISABLED=True')==1
    files['elc_evidence.py']=text.replace('DRAFT_EXECUTION_DISABLED=True','DRAFT_EXECUTION_DISABLED=False',1).encode('utf8')
    evidence={'independent_review':peer,'actual_raw_results':raws,'actual_four_result_review':None,
              'scope':'Actual four terminal result identities and SHA-bound independent review are bound. Local summary/standards, source promotion, receipt, queue and launch have not been created by this binder.'}
    files['evidence_bindings.json']=encoded(evidence)
    recorded=datetime.now(timezone.utc).isoformat()
    metadata={'owner':EXPECTED,'recorded_at':recorded,'status':'ACTUAL_FOUR_RESULT_HELPER_BINDING_ONLY_NOT_ADMISSION',
              'source_preparation':ref(SOURCE/'preparation.json'),'manifest':ref(EXE/'native_manifest.json'),
              'independent_review':peer,'raw_results':raws,'allowed_changes':['Common DRAFT True->False','Actual evidence binding JSON'],
              'prepared_file_hashes':{n:hashlib.sha256(v).hexdigest() for n,v in files.items()},
              'standards_receipt_queue_source_or_launch_written':False}
    files['activation_binding.json']=encoded(metadata)
    intent=TICK/'elc_active_binding_intent.json';result=TICK/'elc_active_binding_result.json'
    assert not DEST.exists() and not intent.exists() and not result.exists(),'Existing/partial activation is never replayed or overwritten'
    # All bytes are composed before the exclusive journal and destination creation.
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();assert not DEST.exists() and not intent.exists() and not result.exists()
        assert sha(SOURCE/'preparation.json')==SOURCE_SHA
        write_new(intent,encoded({'owner':EXPECTED,'recorded_at':recorded,'source_preparation':ref(SOURCE/'preparation.json'),
                  'manifest':ref(EXE/'native_manifest.json'),'independent_review':peer,'raw_results':raws,
                  'operation':'One private reviewed binding copy only','partial_replay_forbidden':True}))
        guard();DEST.mkdir(exist_ok=False)
        for name,data in files.items():write_new(DEST/name,data)
        assert all(sha(DEST/n)==h for n,h in metadata['prepared_file_hashes'].items())
        write_new(result,encoded({'owner':EXPECTED,'recorded_at':recorded,'destination':str(DEST),
                  'binding':ref(DEST/'activation_binding.json'),'summary_source_admission_queue_launch_performed':False}))
        print(json.dumps({'status':'PRIVATE_ACTIVE_COPY_READY_NO_PROMOTION_PERFORMED','binding':ref(DEST/'activation_binding.json'),'result':ref(result)}))
    finally:lock.close()

if __name__=='__main__':main()
