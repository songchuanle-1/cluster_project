"""Freeze the unexecuted native packet after its preparer's offline checks."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
NATIVE=HERE/'btc_operational_prepare/native'; TOKEN='7dcc29e8844245ec87b6d58eee6ec966'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker-sha',required=True);ap.add_argument('--runtime-sha',required=True);ap.add_argument('--offline-proof',required=True);args=ap.parse_args()
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    assert sha(NATIVE/'worker.py')==args.worker_sha and sha(NATIVE/'native_runtime.py')==args.runtime_sha
    proof=Path(args.offline_proof).resolve();assert proof.is_relative_to(HERE) and proof.is_file()
    for name in ['worker.py','native_runtime.py']:
        source=(NATIVE/name).read_text(encoding='utf-8');ast.parse(source);compile(source,str(NATIVE/name),'exec')
    manifest=read(HERE/'btc_manifest_skeleton.json')
    files=['worker.py','native_runtime.py','candidate.yaml','source_version_binding.json']+[p.relative_to(NATIVE).as_posix() for p in sorted((NATIVE/'candidate_model').glob('*.py'))]
    assert len(files)==12
    manifest['diagnostic_files']={name:sha(NATIVE/name) for name in files}
    assert all(manifest[k] is None for k in ['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'])
    save(NATIVE/'manifest_template.json',manifest)
    preparation={'schema_version':1,'candidate_id':manifest['candidate_id'],'experiment_id':'M211-BTC',
        'source_commit':manifest['code_commit'],'code_commit':manifest['code_commit'],'source_parent_commit':manifest['source_parent_commit'],
        'status':'VERSION_BOUND_PREPARED_FOR_FRESH_OWNED_BINDING_ONLY_NOT_RUN',
        'source_preparation_sha256':manifest['source_preparation_sha256'],'source_version_binding_sha256':sha(NATIVE/'source_version_binding.json'),
        'prepared_file_hashes':{name:sha(NATIVE/name) for name in sorted(files+['README.md','manifest_template.json'])},
        'offline_worker_checks':{'path':proof.relative_to(ROOT).as_posix(),'sha256':sha(proof)},
        'native':'NOT_RUN','resources':'NOT_RUN','active_binding_lease_created':False,
        'prepared_at':datetime.now(timezone.utc).isoformat(),
        'limits':'Offline source/protocol validation only. Real TRAIN2, FP32/autograd, true n>=3 coverage, common initialization and resource pair remain unexecuted; future fresh authorization/assets/idleGPU0/three locks mandatory. No GPU1 use.'}
    assert len(preparation['prepared_file_hashes'])==14
    save(NATIVE/'preparation.json',preparation)
    save(HERE/'btc_native_packet_freeze.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':manifest['candidate_id'],
        'manifest_template_sha256':sha(NATIVE/'manifest_template.json'),'native_preparation_sha256':sha(NATIVE/'preparation.json'),
        'diagnostic_file_count':12,'prepared_file_count':14,'worker_sha256':args.worker_sha,'runtime_sha256':args.runtime_sha,
        'native_or_resources_executed':False,'active_manifest_or_lease_created':False,'source_modified':False})
    print(json.dumps({'manifest_template_sha256':sha(NATIVE/'manifest_template.json'),'native_preparation_sha256':sha(NATIVE/'preparation.json'),'native':'NOT_RUN','resources':'NOT_RUN'}))
if __name__=='__main__':main()
