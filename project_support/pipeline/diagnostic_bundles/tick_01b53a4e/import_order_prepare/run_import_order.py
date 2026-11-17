"""Default disabled root-only single CPU import-order control. No native replay."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,base64,hashlib,json,os,shlex,subprocess,sys
HERE=Path(__file__).resolve().parent;TICK=HERE.parent;ROOT=Path('D:/project/cluster_project')
sys.path.insert(0,str(TICK))
from anchor import guard
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
    data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    with (HERE/name).open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
    if not args.execute_root:print('DISABLED_NO_TRANSPORT_OR_CPU_CONTROL_EXECUTION');return
    owner=guard();assert owner['token']=='01b53a4e60c941719a2eb3bea379789b' and sys.dont_write_bytecode
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>290
    assert not any((HERE/n).exists() for n in ['import_order_intent.json','import_order_actual_result.json']),'Do not replay existing/partial CPU control'
    child=HERE/'cpu_order_child.py';controller=HERE/'remote_order_controller.py'
    assert sha(child)=='c7c54a557b1f072fd8aca02a8b808720755ef5d49c59f5a7a8e9ce497851a6e3' and sha(controller)=='6bf6d33df64e5aff6c1755652998a6fa11501cc6f82460c1ae029d8d0683f4ba'
    payload=('BOUND_OWNER='+repr(owner)+'\nCHILD_SOURCE_BASE64='+repr(base64.b64encode(child.read_bytes()).decode())+'\nCHILD_SOURCE_SHA256='+repr(sha(child))+'\n'+controller.read_text('utf-8'))
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','songcl@192.168.1.115',
        shlex.join(['bash','-lc',"source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python -B -"])]
    save('import_order_intent.json',{'owner':owner,'recorded_at':datetime.now(timezone.utc).isoformat(),'child_sha256':sha(child),'controller_sha256':sha(controller),'command':command,'scope':'Fixed two-order CPU dependency import control; no native/model/data/checkpoint/installation/cache cleanup','original_failures':'pipeline/diagnostic_bundles/tick_0f02aaa2/native_import_failures_independent_review.json'})
    guard()
    try:r=subprocess.run(command,input=payload,text=True,encoding='utf-8',capture_output=True,timeout=290)
    except subprocess.TimeoutExpired as error:
        save('import_order_actual_result.json',{'status':'CPU_ORDER_TRANSPORT_TIMEOUT_UNCERTAIN_NO_REPLAY','owner':owner,'error':str(error),'native_PASS':False});raise
    markers=[]
    for line in r.stdout.splitlines():
        if line.startswith('IMPORT_ORDER_PAIR='):markers.append(line[len('IMPORT_ORDER_PAIR='):])
    observation=json.loads(markers[0]) if len(markers)==1 else None
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':owner,'returncode':r.returncode,'observation':observation,'stdout':r.stdout,'stderr':r.stderr,'native_PASS':False,'scope':'This is CPU control evidence only; no four-arm/native/resource PASS or candidate rejection.'}
    save('import_order_actual_result.json',result)
    print(json.dumps({'returncode':r.returncode,'pair_status':observation.get('status') if observation else None,'result_sha256':sha(HERE/'import_order_actual_result.json'),'native_PASS':False}))
if __name__=='__main__':main()
