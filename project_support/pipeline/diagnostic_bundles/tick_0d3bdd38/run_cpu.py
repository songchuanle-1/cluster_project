"""Execute frozen CPU controls remotely with CUDA hidden,not on local workstation."""
import json,shlex
from ops import guard,save,run,OUT,STAGE
import foreground_tick as tick

guard(900)
for runner,output in [('cpu_contracts.py','cpu_contracts_result.json'),('interval_cpu_checks.py','interval_cpu_result.json')]:
    command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
             'conda activate project_cluster && CUDA_VISIBLE_DEVICES= python -B '+shlex.quote(STAGE+'/'+runner))
    response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],300)
    save(runner+'_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr})
    fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/'+output,str(OUT/'norm_revision2'/output)])
    save(runner+'_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr});assert fetch.returncode==0
    result=tick.load(OUT/'norm_revision2'/output)
    print(json.dumps({'runner':runner,'passed':result['passed'],'checks':len(result.get('checks',[])),'error':result.get('error')}))
    assert response.returncode==0 and result['passed'],response.stderr
