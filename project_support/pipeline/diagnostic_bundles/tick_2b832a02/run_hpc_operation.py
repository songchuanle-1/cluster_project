"""One explicit existing reviewed HPC adapter operation, no retries."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,os
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
OP=ROOT/'pipeline/diagnostic_bundles/tick_fd073f88/hpc_compatible_prepare'
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
    assert sha(OP/'preparation.json')=='789ccef52b93106b06c1039257436ea67a9415ee0d2d0e2fe98ebe0182d6beb4'
    assert sha(OP/'adapter_release.json')=='00146ccd8d15bbe604057e3594aa317f86f96d1dcc032d8aeaa2cb89579a266b'
    assert sha(OP/'native/preparation.json')=='ab13cba6418ab9ba733e2b0ecfbe203a220b4b472346623a3835ce11803593b3'
    if args.operation=='run':assert args.mode and args.target;label=args.mode+'_'+args.target
    else:assert args.mode is None and args.target is None;label=args.operation
    intent=HERE/('hpc_'+label+'_controller_intent.json');output=HERE/('hpc_'+label+'_controller_result.json')
    assert not intent.exists() and not output.exists(),'Existing or partial operation; reconcile original request only, never replay'
    spec=importlib.util.spec_from_file_location('current_reviewed_hpc_adapter',OP/'adapter.py')
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
