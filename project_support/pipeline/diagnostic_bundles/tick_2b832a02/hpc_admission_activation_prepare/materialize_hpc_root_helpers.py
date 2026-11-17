"""Private exact helper activation only. Default plan, no public/Git/remote work."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent.parent
ORIGIN=HERE/'hpc_admission_prepare_corrected'
DEST=HERE/'hpc_admission_execute'
PREP_SHA='c3f7189d81c2d019d6062d077a5aad540ba57c479c721947f13632d9e1a543b9'
SOURCE_REVIEW_SHA='06cc0da061f0d8644c5922bda87c402cc95c300c226a4103cc1ef8e8903a86cd'
FILES=['hpc_evidence.py','summarize_hpc_actual.py','fast_forward_tested_hpc.py','admit_hpc_queue.py','dispatch_hpc_once.py','evidence_bindings.json']
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,value):
    guard();data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
    with Path(p).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute-root',action='store_true');ap.add_argument('--peer-sha256');args=ap.parse_args()
    if not args.execute_root:print('PLAN_ONLY_NO_PRIVATE_COPY_OR_OTHER_MUTATION');return
    guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
    assert re.fullmatch(r'[0-9a-f]{64}',args.peer_sha256 or ''),'Exact actual independent review SHA required'
    assert sha(ORIGIN/'preparation.json')==PREP_SHA
    preparation=read(ORIGIN/'preparation.json')
    for name,want in preparation['prepared_file_hashes'].items():
        path=(ORIGIN/name).resolve();assert path.is_relative_to(ORIGIN.resolve()) and sha(path)==want
    source_review=HERE/'hpc_root_admission_preparation_independent_review.json';assert sha(source_review)==SOURCE_REVIEW_SHA and read(source_review)['material_concerns']==[]
    peer=HERE/'hpc_actual_independent_review.json';assert sha(peer)==args.peer_sha256
    actual=read(peer);assert actual['status']=='FOUR_ACTUAL_HPC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
    assert actual['candidate_id']=='hierarchy-tree-resolvent-nonlinear-composition' and actual['code_commit']=='6282263d805c1741234f97afc981a05aca2ad6e3' and actual['goal_sha256']=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85' and actual['material_concerns']==[]
    assert {(x['mode'],x['target']) for x in actual['raw_results']}=={(m,t) for m in ('smoke','resources') for t in ('champion','candidate')} and len(actual['raw_results'])==4
    for item in actual['raw_results']:
        path=(ROOT/item['execution_path']).resolve();assert path.parent==HERE/'hpc_execution' and sha(path)==item['execution_sha256']
        envelope=read(path);assert envelope['identity']['request_id']==item['request_id'] and envelope['result_sha256']==item['result_sha256']
        assert envelope['certainty']=='terminal' and envelope['returncode']==0 and envelope['result']['execution_completed'] is True
    payload={n:(ORIGIN/n).read_bytes() for n in FILES};original={n:hashlib.sha256(b).hexdigest() for n,b in payload.items()}
    flag=b'DRAFT_EXECUTION_DISABLED=True';assert payload['hpc_evidence.py'].count(flag)==1
    payload['hpc_evidence.py']=payload['hpc_evidence.py'].replace(flag,b'DRAFT_EXECUTION_DISABLED=False')
    assert read(ORIGIN/'evidence_bindings.json')=={'independent_review':None}
    payload['evidence_bindings.json']=(json.dumps({'independent_review':ref(peer)},indent=2)+'\n').encode('utf8')
    for name,data in payload.items():
        if name.endswith('.py'):compile(data,str(DEST/name),'exec')
    assert not DEST.exists() and not any((HERE/n).exists() for n in ('hpc_root_activation_intent.json','hpc_root_activation_result.json')),'Existing/partial activation is read-only reconcile, never replay'
    guard();save(HERE/'hpc_root_activation_intent.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'origin_preparation':ref(ORIGIN/'preparation.json'),'source_review':ref(source_review),'actual_review':ref(peer),'scope':'Private exact bytecopy helpers only; only common True->False and actual peer binding change. No summary, FF, admission, queue, SSH/GPU or shared operation.','original_file_hashes':original})
    guard();DEST.mkdir(exist_ok=False)
    for name,data in payload.items():
        guard()
        with (DEST/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    after={n:sha(DEST/n) for n in FILES}
    assert all(after[n]==original[n] for n in FILES if n not in ('hpc_evidence.py','evidence_bindings.json'))
    save(HERE/'hpc_root_activation_result.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'origin_preparation':ref(ORIGIN/'preparation.json'),'actual_review':ref(peer),'original_file_hashes':original,'activated_file_hashes':after,'exact_changes':['hpc_evidence.py DRAFT_EXECUTION_DISABLED=True -> False','evidence_bindings.json independent_review None -> exact current actual MD path/SHA'],'all_other_executable_bytes_identical':True,'no_public_source_shared_Git_SSH_GPU_native_operation':True})
    print(json.dumps(ref(HERE/'hpc_root_activation_result.json')))
if __name__=='__main__':main()
