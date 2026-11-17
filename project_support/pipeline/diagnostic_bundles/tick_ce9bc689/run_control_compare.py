"""Run source-bound CPU analysis only on preregistered captured controls."""
import argparse
import shlex
from ops import guard,save,run,advance,OUT,STAGE,HOST,SSH

p=argparse.ArgumentParser()
p.add_argument('--kind',choices=['sparse','aligned'],required=True)
a=p.parse_args()
guard(100)
uploaded=run(['scp',*SSH,str(OUT/'compare_controls.py'),'songcl@'+HOST+':'+STAGE+'/compare_controls_'+a.kind+'.py'])
assert uploaded.returncode==0,uploaded.stderr
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(STAGE+'/compare_controls_'+a.kind+'.py')+' --root '+shlex.quote(STAGE)+' --kind '+a.kind)
r=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['bash','-lc',command])],120)
save(a.kind+'_control_comparison_execution.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
assert r.returncode==0,r.stderr
name=a.kind+'_control_comparison.json'
fetch=run(['scp',*SSH,'songcl@'+HOST+':'+STAGE+'/'+name,str(OUT/name)])
assert fetch.returncode==0,fetch.stderr
advance([OUT/name,OUT/(a.kind+'_control_comparison_execution.json')],
    gate_result='Coordinate-aware '+a.kind+' measurement recorded;no automatic training admission.')
print(r.stdout)
