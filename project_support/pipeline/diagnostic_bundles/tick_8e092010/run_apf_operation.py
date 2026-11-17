"""One explicit existing reviewed APF adapter operation, no retries."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,os
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
OP=ROOT/'pipeline/diagnostic_bundles/tick_8e092010/apf_compatible_prepare'
def save(path,value):
    guard()
    with path.open('x',encoding='utf8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['prepare','stage','run'])
    parser.add_argument('--mode',choices=['smoke','resources'])
    parser.add_argument('--target',choices=['champion','candidate'])
    args=parser.parse_args();guard()
    assert sha(OP/'preparation.json')=='4a8ec1410a739c9e09e5ea4c9847469f40480532eeb221d368c5878b95014b2e'
    assert sha(OP/'adapter_release.json')=='5cc5231d4f7734c8f77809542619be484ae920a8b002ca2fbf11ee7b919151b2'
    assert sha(OP/'native/preparation.json')=='2ab71fa083e77bddcb6183c4aca24a358d6c4a09ef42bb1b2c4942e6f7aca760'
    if args.operation=='run':assert args.mode and args.target;label=args.mode+'_'+args.target
    else:assert args.mode is None and args.target is None;label=args.operation
    intent=HERE/('apf_'+label+'_controller_intent.json');output=HERE/('apf_'+label+'_controller_result.json')
    assert not intent.exists() and not output.exists(),'Existing or partial operation; reconcile original request only, never replay'
    spec=importlib.util.spec_from_file_location('current_reviewed_apf_adapter',OP/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    adapter=module.Adapter();adapter.guard()
    save(intent,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'operation':args.operation,'mode':args.mode,'target':args.target,'adapter_release_sha256':sha(OP/'adapter_release.json'),
        'scope':'Exactly one explicit reviewed adapter method call; original safety/runtime/native gates unchanged. Any error preserves the original request for reconciliation, never retry.'})
    try:
        if args.operation=='prepare':result=adapter.prepare(0)
        elif args.operation=='stage':result=adapter.stage()
        else:result=adapter.run(args.mode,args.target)
    except Exception as error:
        save(output,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
            'operation':args.operation,'mode':args.mode,'target':args.target,'error_type':type(error).__name__,'error':str(error),
            'result':'ERROR_RECONCILE_ORIGINAL_REQUEST_NO_RETRY'})
        raise
    save(output,{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'operation':args.operation,'mode':args.mode,'target':args.target,'result':result})
    print(json.dumps({'operation':args.operation,'mode':args.mode,'target':args.target,'state':result.get('state'),
        'status':result.get('status'),'request_id':result.get('request_id'),
        'result_path':output.relative_to(ROOT).as_posix(),'sha256':sha(output)},ensure_ascii=False))
if __name__=='__main__':main()
