"""CPU-only analysis of the exact two native captures."""
import shlex
from ops import guard,save,run,advance,OUT,STAGE,HOST,SSH
guard(100)
r=run(['scp',*SSH,str(OUT/'compare_stride.py'),'songcl@'+HOST+':'+STAGE+'/compare_stride.py'])
assert r.returncode==0,r.stderr
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(STAGE+'/compare_stride.py')+' --root '+shlex.quote(STAGE))
r=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['bash','-lc',command])],120)
save('native_stride_comparison_execution.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
assert r.returncode==0,r.stderr
f=run(['scp',*SSH,'songcl@'+HOST+':'+STAGE+'/native_stride_comparison.json',str(OUT/'native_stride_comparison.json')])
assert f.returncode==0,f.stderr
advance([OUT/'native_stride_comparison.json',OUT/'native_stride_comparison_execution.json'],
    gate_result='Finite actualnative selecteddescriptor/index comparison recorded;not efficacy or unique backendcause.',
    next_action='Conclude bounded reproducibility audit with observed limits;exact savedprefix/nativeflags controls required for subsequent mainline causal tests,not an indefinite kernel investigation.')
print(r.stdout)
