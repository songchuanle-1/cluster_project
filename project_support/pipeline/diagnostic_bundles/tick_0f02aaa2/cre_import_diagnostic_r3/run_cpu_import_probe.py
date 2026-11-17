"""Default disabled. Root-only one narrowed-fence CPU import probe, never a native replay."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,shlex,subprocess,sys
HERE=Path(__file__).resolve().parent;TICK=HERE.parent;ROOT=Path('D:/project/cluster_project')
sys.path.insert(0,str(TICK))
from anchor import guard
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,value):
    data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    with (HERE/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
    if not args.execute_root:print('DISABLED_NO_CPU_PROCESS_TRANSPORT_OR_MUTATION');return
    owner=guard();assert owner['token']=='0f02aaa25b1a4f6e9d27cf8da33b8ca1' and sys.dont_write_bytecode
    failed=TICK/'cre_execution/smoke_champion_execution.json';assert sha(failed)=='998c15df671d2e12c0b8a2ce741f9fb35011e425c77683d192c817201d97081c'
    raw=json.loads(failed.read_text('utf8'));assert raw['certainty']=='terminal' and raw['returncode']==1 and raw['result']['optimizer_steps']==0
    assert raw['identity']['request_id']=='f11717294d4f4e82b66daa065b58c2ee'
    assert sha(TICK/'cre_initial_smoke_trace.json')=='71c7968b6b19437023e01d37e371ac9f4acc803419249d35ad5980f30787b095'
    assert not any((HERE/n).exists() for n in ['cpu_import_probe_intent.json','cpu_import_probe_result.json']),'Preserve/reconcile prior attempt, no replay'
    source=HERE/'remote_cpu_import_probe.py';assert sha(source)=='5300606764597c013d9a4735a3250c9d172d893f161fd78f005d95ea52a863d6'
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','songcl@192.168.1.115',
        shlex.join(['bash','-lc',"source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python -B -"])]
    write('cpu_import_probe_intent.json',{'owner':owner,'recorded_at':datetime.now(timezone.utc).isoformat(),'purpose':'Independent fresh read-only CPU import diagnosis only, no native retry','probe_sha256':sha(source),'command':command,'failed_request_id':raw['identity']['request_id']})
    guard()
    try:r=subprocess.run(command,input=source.read_text('utf8'),text=True,encoding='utf8',capture_output=True,timeout=120)
    except subprocess.TimeoutExpired as error:
        write('cpu_import_probe_result.json',{'status':'CPU_IMPORT_DIAGNOSTIC_TIMEOUT_UNCERTAIN_NO_REPLAY','owner':owner,'error':str(error),'native_PASS':False});raise
    markers=[line.removeprefix('CRE_CPU_IMPORT_DIAGNOSTIC=') for line in r.stdout.splitlines() if line.startswith('CRE_CPU_IMPORT_DIAGNOSTIC=')]
    observation=json.loads(markers[0]) if len(markers)==1 else None
    out={'status':'CPU_IMPORT_DIAGNOSTIC_RETURNED' if r.returncode==0 and observation else 'CPU_IMPORT_DIAGNOSTIC_REMOTE_OR_PARSE_FAILURE_NO_REPLAY',
        'owner':owner,'recorded_at':datetime.now(timezone.utc).isoformat(),'probe_sha256':sha(source),'returncode':r.returncode,
        'observation':observation,'stdout':r.stdout,'stderr':r.stderr,'native_PASS':False,'new_training_or_model_mutation':False}
    write('cpu_import_probe_result.json',out)
    print(json.dumps({'status':out['status'],'probe_status':observation.get('status') if observation else None,'failed_stage':observation.get('failed_stage') if observation else None,'result_sha256':sha(HERE/'cpu_import_probe_result.json'),'native_PASS':False}))
if __name__=='__main__':main()
