"""One preregistered protocol repair; retain the failed bank replay."""
import ast
import copy
from datetime import datetime, timezone
import shutil
from ops import *

owner=guard(600)
prior=OUT/'moment/native_moment_result.json'
failure=tick.load(prior)
assert failure['controls_passed'] is False and failure['native_backwards']==1
revision={'revision':1,'failure_scope':'implementation',
 'reason':'Reaggregating identical native FP32 points changed bank tokens1.9073486328125e-6, message2.86102294921875e-6 and suffix masks1.9073486328125e-5, exceeding frozen1e-6.',
 'change':'For native identity/suffix controls use the token tensors captured in that SAME forward. Keep actual GPU bank replay discrepancies as unpassed observations; verify moment-changing mean invariance independently with the actual aggregate function on CPU float64.',
 'prediction':'Captured-token message and suffix reconstruct original native outputs at unchanged1e-6; no assertion that reaggregated tokens do. GPU permutation invariance remains measured at original1e-6, not relabelled PASS.',
 'preregistered_at':datetime.now(timezone.utc).isoformat(),
 'failure_evidence':[evidence(prior)],'result':'pending','evidence':[]}
save('capture_revision1_protocol.json',revision)
advance([prior,OUT/'capture_revision1_protocol.json'],revision_history=[revision],next_action='Run one exact captured-token revision and CPU actual-aggregate moment control; preserve original failed replay and strict native permutation outcomes')
tree=ast.parse((OUT/'native_moment.py').read_text())
changes={'base':0,'controls':0,'cpu':0,'name':0}
class Repair(ast.NodeTransformer):
    def visit_Assign(self,node):
        self.generic_visit(node)
        target=ast.unparse(node.targets[0]) if len(node.targets)==1 else ''
        if target=='base_tokens':
            changes['base']+=1
            return ast.parse("replayed_tokens=source(x)\nr['original_gpu_bank_replay_max_change']=[error(a,b) for a,b in zip(replayed_tokens,tokens)]\nbase_tokens=clone(tokens)").body
        if target=='controls':
            assert isinstance(node.value,ast.Dict)
            keep=[i for i,k in enumerate(node.value.keys) if k.value!='token_reconstruction']
            node.value.keys=[node.value.keys[i] for i in keep]
            node.value.values=[node.value.values[i] for i in keep]
            changes['controls']+=1
        return node
    def visit_For(self,node):
        self.generic_visit(node)
        if ast.unparse(node.target)=='permutation':
            for child in ast.walk(node):
                if isinstance(child,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='perm_tokens' for t in child.targets):
                    break
            extra=ast.parse("""cpu_mean_checks=[]
for b in range(x.shape[0]):
    cid=ids[0][b].long().cpu()
    a=hierarchy.aggregate_cluster(x[b,:len(cid)].detach().cpu().double(),cid)
    z=hierarchy.aggregate_cluster(perm[b,:len(cid)].detach().cpu().double(),cid)
    cpu_mean_checks.append(error(a,z))
r.setdefault('cpu_float64_mean_checks',[]).append({'permutation':permutation,'max_error_per_expression':cpu_mean_checks,'strict1e_minus6':max(cpu_mean_checks)<=1e-6})
""").body
            index=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pm' for t in n.targets))
            node.body[index:index]=extra
            changes['cpu']+=1
        return node
    def visit_Constant(self,node):
        if node.value=='native_moment_result.json':
            changes['name']+=1
            return ast.Constant('native_moment_captured_result.json')
        return node
tree=Repair().visit(tree)
assert changes=={'base':1,'controls':1,'cpu':1,'name':1},changes
ast.fix_missing_locations(tree)
label='captured_revision1'
local=OUT/label
local.mkdir(exist_ok=False)
(local/'native_moment_captured.py').write_text(ast.unparse(tree)+'\n',encoding='utf-8')
shutil.copyfile(ROOT/'pipeline/diagnostic_bundles/tick_ce9bc689/trace_m95_1/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(OUT/'moment/native_manifest.json'))
stage=STAGE+'/'+label
manifest.update(stage=stage,capture_revision=evidence(OUT/'capture_revision1_protocol.json'))
manifest['diagnostic_files']={name:tick.digest(local/name) for name in ('native_runtime.py','native_moment_captured.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
result=run(['scp',*SSH,*[str(local/name) for name in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')],'songcl@192.168.1.115:'+stage+'/'])
assert result.returncode==0,result.stderr
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_moment_captured.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],900)
save('capture_revision1_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
pulled=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/native_moment_captured_result.json',str(local/'native_moment_captured_result.json')])
assert pulled.returncode==0,pulled.stderr
value=tick.load(local/'native_moment_captured_result.json')
revision.update(result='passed' if value.get('execution_completed') and value.get('controls_passed') else 'inconclusive',evidence=[evidence(local/'native_moment_captured_result.json')])
advance([local/'native_moment_captured_result.json',local/'native_manifest.json',local/'native_moment_captured.py',OUT/'capture_revision1_execution.json'],revision_history=[revision],gate_result='Captured-prefix protocol result='+revision['result']+';original GPU replay FAIL retained,task deficit not established')
print(json.dumps({k:v for k,v in value.items() if k not in ('before','after')},ensure_ascii=False))
