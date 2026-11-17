"""Current root-only original AOC operation wrapper; default performs no action."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,sys

TICK=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_5f3e6c7b')
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard
import record_utils as u
ADAPTER=ROOT/'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_operational_prepare/adapter.py'
EXE=TICK/'aoc_execution'
BASELINE=TICK/'post_pes_terminal_baseline.json'
BASELINE_SHA='510c2b227c5ee02ae4554699a33faa06ec0e8e758fb08e2c8c94950672ba199d'
PINS={
 'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_operational_prepare/preparation.json':'e45e2db8fad383005eea4757acd9a6aa259d060f20103785cde5f6f9b5bd7fce',
 'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_operational_prepare/adapter.py':'49f67604d5eacd06960d1cd635488b3df6e2f4b47a1a29b67ea89ec91184cc26',
 'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_operational_prepare/adapter_release.json':'63017e16a2a5676451b91d385900b243805dfb8cbac6c48f101ebec2db8764f6',
 'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_native_prepare/preparation.json':'9cf931d5f788cf1e545c22a1aea017c181d52e05e40391411cc315b1b7600a40'}

def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,value):
    guard();data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
    with Path(p).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',nargs='?',choices=['prepare-stage','run'])
    parser.add_argument('--execute-root',action='store_true')
    parser.add_argument('--mode',choices=['smoke','resources'])
    parser.add_argument('--target',choices=['champion','candidate'])
    args=parser.parse_args()
    if not args.execute_root:print('DEFAULT_READ_ONLY_NO_AOC_OPERATION');return
    assert args.operation is not None
    if args.operation=='run':assert args.mode is not None and args.target is not None
    else:assert args.mode is None and args.target is None
    guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
    assert sha(BASELINE)==BASELINE_SHA
    baseline=read(BASELINE);assert baseline['owner']==EXPECTED and baseline['head']=='9c42fdc4e9168acec18980d782ee9c163e043bb7'
    for name,h in PINS.items():assert sha(ROOT/name)==h,name
    u.primary_protection(baseline);u.lifecycle_protection(baseline)
    label='prepare_stage' if args.operation=='prepare-stage' else args.mode+'_'+args.target
    intent=TICK/('aoc_'+label+'_wrapper_intent.json');output=TICK/('aoc_'+label+'_wrapper_result.json')
    failure=TICK/('aoc_'+label+'_wrapper_failure.json')
    assert not any(p.exists() for p in (intent,output,failure)),'Existing wrapper attempt: preserve original artifacts and reconcile, never replay'
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(baseline);u.lifecycle_protection(baseline)
        save(intent,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
             'operation':args.operation,'mode':args.mode,'target':args.target,'physical_gpu':0,
             'post_pes_terminal_baseline':ref(BASELINE),'original_adapter':ref(ADAPTER),
             'partial_policy':'Original request/status/reconcile only; no blind replay, alternate GPU, source edit or restart.'})
        spec=importlib.util.spec_from_file_location('current_original_aoc_adapter',ADAPTER)
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
        guard();u.primary_protection(baseline);u.lifecycle_protection(baseline)
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
