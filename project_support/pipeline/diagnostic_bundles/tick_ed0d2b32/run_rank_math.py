"""One CPU analysis using all fixed readouts, not selected favorable cases."""
import shlex
from ops import guard,save,run,advance,evidence,tick,OUT,STAGE,HOST,SSH
RID='hierarchical-nonlocal-channel-rank-audit'
guard(180)
assert tick.load(OUT/'rank_m95/native_rank_capture_result.json')['passed']
advance([OUT/'rank_dimension_control_prereg.md',OUT/'rank_math.py'],candidate_id=RID,
    next_action='Execute48CPUfloat64Jacobians on all24fixedreadouts,including predeclared fixedDCT rankmatched negativecontrol;not whole-network deficit inference.')
stage=STAGE+'/rank_m95'
r=run(['scp',*SSH,str(OUT/'rank_math.py'),'songcl@'+HOST+':'+stage+'/rank_math.py'])
assert r.returncode==0,r.stderr
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/rank_math.py')+' --root '+shlex.quote(stage))
r=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['bash','-lc',command])],120)
save('rank_math_execution.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
assert r.returncode==0,r.stderr
f=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/rank_math_result.json',str(OUT/'rank_math_result.json')])
assert f.returncode==0,f.stderr
advance([OUT/'rank_math_result.json',OUT/'rank_math_execution.json'],candidate_id=RID,
    gate_result='Conditionalmodule rank/nativegradient projections measured on all24readouts;not efficacy,harm or novelty;native exactcontrols retained.',
    next_action='Pre-register a task-relevant matched native cross-coarse channel intervention versus rank-matched control before selecting any structural mechanism;do not equate rank2 with whole-network failure or admit a newgate.')
print(r.stdout)
