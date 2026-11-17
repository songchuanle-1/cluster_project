"""Compare saved original trace pairs using CPU only."""
import argparse
import shlex
from ops import guard,save,run,ssh,advance,tick,OUT,STAGE,HOST,SSH

p=argparse.ArgumentParser()
p.add_argument('--model',choices=['m95','fle'],required=True)
a=p.parse_args()
guard(100)
uploaded=run(['scp',*SSH,str(OUT/'compare_trace.py'),'songcl@'+HOST+':'+STAGE+'/compare_'+a.model+'.py'])
assert uploaded.returncode==0,uploaded.stderr
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(STAGE+'/compare_'+a.model+'.py')+' --root '+shlex.quote(STAGE)+' --model '+a.model)
r=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['bash','-lc',command])],100)
save(a.model+'_trace_comparison_execution.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
assert r.returncode==0,r.stderr
fetched=run(['scp',*SSH,'songcl@'+HOST+':'+STAGE+'/'+a.model+'_trace_comparison.json',str(OUT/(a.model+'_trace_comparison.json'))])
assert fetched.returncode==0,fetched.stderr
advance([OUT/(a.model+'_trace_comparison.json'),OUT/(a.model+'_trace_comparison_execution.json')],
    next_action='Use localized first equalinput/differentoutputboundary for exactsavedinput operator control;no kernelcause,tolerancechange or training.')
print(r.stdout)
