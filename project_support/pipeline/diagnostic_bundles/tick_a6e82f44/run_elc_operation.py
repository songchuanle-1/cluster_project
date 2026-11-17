"""Current root-only original ELC operation wrapper; default performs no action."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,sys

TICK=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_a6e82f44')
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard
import record_utils as u
ADAPTER=TICK/'elc_policy_compat_prepare/adapter.py'
EXE=TICK/'elc_execution'
BASELINE=None
BASELINE_SHA=None
PINS={'pipeline/diagnostic_bundles/tick_692b4575/elc_native_prepare/preparation.json': '28ec7b290cae00e50e30f28d9cef3d9d4ccc75cc3c4936cb15db1014a5d7cec9'}


def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,value):
    guard();data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
    with Path(p).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())

def protect_primary(baseline):
    guard();repo=ROOT/'Cluster'
    assert u.git(repo,'rev-parse','HEAD').decode().strip()==baseline['head']=='c9be548699cd66bf68badff9ae6198a03eafa142'
    assert u.git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==baseline['status_hex']
    assert not u.git(repo,'diff','--cached','--name-only','-z')
    index=Path(u.git(repo,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else repo/index
    assert sha(index)==baseline['index_sha256']
    assert all(sha(repo/n)==h for n,h in {**baseline['files'],**baseline['exact_tested_nine_source_paths']}.items())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',nargs='?',choices=['prepare-stage','run'])
    parser.add_argument('--execute-root',action='store_true')
    parser.add_argument('--preparation-sha256',required=False)
    parser.add_argument('--peer-sha256',required=False)
    parser.add_argument('--baseline')
    parser.add_argument('--baseline-sha256')
    parser.add_argument('--mode',choices=['smoke','resources'])
    parser.add_argument('--target',choices=['champion','candidate'])
    args=parser.parse_args()
    if not args.execute_root:print('DEFAULT_READ_ONLY_NO_ELC_OPERATION');return
    assert args.operation is not None
    if args.operation=='run':assert args.mode is not None and args.target is not None
    else:assert args.mode is None and args.target is None
    global BASELINE,BASELINE_SHA
    BASELINE=Path(args.baseline).resolve();BASELINE_SHA=args.baseline_sha256
    assert BASELINE.is_relative_to(TICK) and isinstance(BASELINE_SHA,str) and len(BASELINE_SHA)==64
    guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
    assert sha(BASELINE)==BASELINE_SHA
    baseline=read(BASELINE);assert baseline['owner']==EXPECTED and baseline['head']=='c9be548699cd66bf68badff9ae6198a03eafa142'
    for name,h in PINS.items():assert sha(ROOT/name)==h,name
    preparation=ADAPTER.with_name('preparation.json');assert sha(preparation)==args.preparation_sha256
    peer=TICK/'elc_policy_compat_independent_review.json';assert sha(peer)==args.peer_sha256
    assert read(peer).get('material_concerns',read(peer).get('concerns'))==[]
    assert read(ADAPTER.with_name('adapter_release.json'))==read(ADAPTER.with_name('release_template.json'))
    for name,h in read(preparation)['prepared_file_hashes'].items():assert sha(ADAPTER.parent/name)==h,name
    protect_primary(baseline);u.lifecycle_protection(baseline)
    label='prepare_stage' if args.operation=='prepare-stage' else args.mode+'_'+args.target
    intent=TICK/('elc_'+label+'_wrapper_intent.json');output=TICK/('elc_'+label+'_wrapper_result.json')
    failure=TICK/('elc_'+label+'_wrapper_failure.json')
    assert not any(p.exists() for p in (intent,output,failure)),'Existing wrapper attempt: preserve original artifacts and reconcile, never replay'
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();protect_primary(baseline);u.lifecycle_protection(baseline)
        save(intent,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
             'operation':args.operation,'mode':args.mode,'target':args.target,'physical_gpu':0,
             'protected_current_baseline':ref(BASELINE),'original_adapter':ref(ADAPTER),
             'partial_policy':'Original request/status/reconcile only; no blind replay, alternate GPU, source edit or restart.'})
        spec=importlib.util.spec_from_file_location('current_original_elc_adapter',ADAPTER)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        adapter=module.Adapter(execution_dir=EXE)
        if args.operation=='prepare-stage':
            binding=adapter.prepare(0);stage=adapter.stage()
            summary={'prepared_manifest_sha256':binding['native_manifest_sha256'],'stage_certainty':stage.get('certainty'),
                     'stage_verified':stage.get('verified'),'stage_execution':ref(EXE/'stage_execution.json')}
        else:
            actual=adapter.run(args.mode,args.target)
            summary={'certainty':actual.get('certainty'),'returncode':actual.get('returncode'),
                     'execution_completed':actual.get('result',{}).get('execution_completed'),
                     'result_sha256':actual.get('result_sha256'),
                     'original_execution':ref(EXE/(args.mode+'_'+args.target+'_execution.json'))}
        guard();protect_primary(baseline);u.lifecycle_protection(baseline)
        save(output,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
             'operation':args.operation,'mode':args.mode,'target':args.target,'summary':summary,
             'shared_source_queue_admission_or_launch_performed':False})
        print(json.dumps({'operation':args.operation,'mode':args.mode,'target':args.target,**summary,'wrapper_result':ref(output)},ensure_ascii=False))
    except BaseException as error:
        if not failure.exists():
            save(failure,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
                 'error_type':type(error).__name__,'error':str(error),'not_training_or_mechanism_classification':True,
                 'next_action':'Read exact original adapter request/execution/status/reconcile; never rerun the wrapper blindly.'})
        raise
    finally:lock.close()

if __name__=='__main__':main()
