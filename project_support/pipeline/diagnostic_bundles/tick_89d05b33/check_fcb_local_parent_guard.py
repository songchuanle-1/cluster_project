"""Exercise only the real local mutation guard with transport denied."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, importlib.util, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent;OP=HERE/'fcb_operational_prepare'
CID='hierarchy-fine-coarse-complete-bipartite-composition'

class DeniedTransport:
    def __init__(self):self.calls=0
    def __call__(self,*args,**kwargs):self.calls+=1;raise AssertionError('No transport permitted in this local check')
    request=__call__
    run=__call__

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_GUARD_EXECUTION');return
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
    c=next(c for c in u.read(ROOT/'pipeline/research_work.json')['candidates'] if c['id']==CID)
    assert c['stage']=='validation' and c['code_commit']=='d4d062ef075abfe7cde93d4b4347ce146572762f'
    assert c['source_parent_commit']=='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
    p=u.read(OP/'preparation.json')
    assert sha(OP/'preparation.json')==c['execution_adapter']['preparation']['sha256']
    for n,h in p['prepared_file_hashes'].items():
        f=(OP/n).resolve();assert f.is_relative_to(OP.resolve()) and sha(f)==h
    assert sha(OP/'adapter_release.json')==c['execution_adapter']['release']['sha256']
    active=HERE/'fcb_execution';assert not active.exists()
    before=sha(ROOT/'pipeline/research_work.json');primary=u.git(ROOT/'Cluster','rev-parse','HEAD').decode().strip();assert primary==u.SOURCE
    spec=importlib.util.spec_from_file_location('fcb_parent_guard_current',OP/'adapter.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    transport=DeniedTransport();adapter=module.Adapter(transport=transport)
    caught=None
    try:adapter.guard(required_seconds=60,gpu=0,mutation=True)
    except Exception as error:caught=error
    guard();u.primary_protection(b);u.lifecycle_protection(b);assert sha(ROOT/'pipeline/research_work.json')==before
    expected=isinstance(caught,module.Refused) and any(x in str(caught).lower() for x in ('parent','aoc','primary'))
    result={'owner':EXPECTED,'observed_at':datetime.now(timezone.utc).isoformat(),'command':'python -B pipeline/diagnostic_bundles/tick_89d05b33/check_fcb_local_parent_guard.py --execute-root','candidate_id':CID,'code_commit':c['code_commit'],'required_parent_commit':c['source_parent_commit'],'observed_primary_commit':primary,'AOC_admission_receipt_present':(ROOT/'pipeline/admissions/M222-AOC.json').exists(),'transport_calls':transport.calls,'active_execution_directory_created':active.exists(),'exception_class':type(caught).__name__ if caught else None,'exception':str(caught) if caught else None,'operational_preparation':u.ref(OP/'preparation.json'),'scope':'Actual current root owner/config local mutation guard only, transport explicitly denied. No prepare/stage/remote/GPU/Torch/native/resource/profile/queue or source operation.'}
    if not expected or transport.calls!=0 or active.exists():
        result['status']='UNEXPECTED_LOCAL_GUARD_RESULT';u.save(HERE/'fcb_local_parent_guard_unexpected.json',result);raise AssertionError('Actual local parent guard did not yield the expected pre-transport refusal')
    result['status']='EXPECTED_UNPROMOTED_PARENT_LOCAL_REFUSAL';u.save(HERE/'fcb_local_parent_guard_observation.json',result)
    print(json.dumps({'status':result['status'],'exception':result['exception'],'transport_calls':transport.calls,'primary':primary}))

if __name__=='__main__':main()
