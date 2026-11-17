STAGE_PATH='/data/songcl/Project/Cluster_project/pipeline/hap_5c5688ff'
import json,sys,os,subprocess
from pathlib import Path
sys.path.insert(0,STAGE_PATH)
import native_runtime as runtime
assert 'torch' not in sys.modules
query=['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits']
r={'status':'PENDING','native_worker_entered':False,'training_forwards':0,'optimizer_steps':0,'process_pid':os.getpid(),'before_contexts':subprocess.check_output(query,text=True,timeout=10).strip()}
try:
 r['guard_before']=runtime.acquire(Path(STAGE_PATH)/'execution_lease.json')
 r['status']='ACQUIRED_NO_COMPUTE'
except BaseException as error:
 r.update(status='REFUSED',error_type=type(error).__name__,error=str(error))
finally:
 r['owned_handles_before_release']=len(runtime.HANDLES)
 runtime.release()
 r['owned_handles_after_release']=len(runtime.HANDLES)
 r['torch_imported']='torch' in sys.modules
 r['gorilla_imported']='gorilla' in sys.modules
 r['after_contexts']=subprocess.check_output(query,text=True,timeout=10).strip()
 r['self_cuda_context_observed']=any(line.split(',')[0].strip()==str(os.getpid()) for line in r['after_contexts'].splitlines())
 r['no_cuda_work_observed']=not r['torch_imported'] and not r['gorilla_imported'] and not r['self_cuda_context_observed']
 assert r['no_cuda_work_observed'] and r['owned_handles_after_release']==0
 runtime.save('prelaunch_guard_result.json',r)
 print(json.dumps(r))
