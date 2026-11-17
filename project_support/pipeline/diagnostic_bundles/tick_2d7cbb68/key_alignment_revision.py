"""One preregistered connection repair,not attention-temperature tuning."""
import ast
import copy
from datetime import datetime,timezone
import shutil
from ops import *
owner=guard(600)
prior=OUT/'native_coarse/native_coarse_result.json'
old=tick.load(prior)
assert old['execution_completed'] and old['controls_passed']
current=next(c for c in old['coarse_conditions'] if c['condition']=='coarse_attention')
uniform=next(c for c in old['coarse_conditions'] if c['condition']=='uniform_coarse_mean')
revision={'revision':1,'failure_scope':'implementation',
 'reason':'Prototype compares original point queries against independently FFN-refined coarse keys. Native entropy2.04991269/ln8 and own-coarse probabilities.127-.135 show weak coarse discrimination;loss+0.0001196265 resembles uniformmean+0.0001214743. These are risk signals,not trained harm.',
 'change':'Move ONLY attention keys to the pre-CTF coarse bank,which is an aggregation of the same point feature basis as the query. Keep refined coarse VALUES,point queries,all heads/scales/sqrtD,fine/middle,fusion and original loss unchanged.',
 'prediction':'Same-prefix controls compare raw-bank keys against original refined-key prototype,uniformmean and cyclic value mismatch;measure physical own-coarse alignment,entropy,actual task masks/loss and supervision. No minimum pretraining loss gain or retuned temperature.',
 'preregistered_at':datetime.now(timezone.utc).isoformat(),'failure_evidence':[evidence(prior)],
 'result':'pending','evidence':[]}
save('key_alignment_revision1_protocol.json',revision)
advance([OUT/'key_alignment_revision1_protocol.json'],stage='validation',revision_history=[revision],
 next_action='Execute fixed one-connection raw-key revision versus original refined keys in the same native capture;retain adverse results without admission')
module=ast.parse((OUT/'coarse_cross_attention.py').read_text())
fn=next(n for n in module.body if isinstance(n,ast.FunctionDef))
fn.args.args.append(ast.arg(arg='key_features'))
fn.args.defaults.append(ast.Constant(None))
changed=0
for n in ast.walk(fn):
    if isinstance(n,ast.Assign) and len(n.targets)==1 and ast.unparse(n.targets[0])=='keys':
        n.value=ast.parse('(coarse if key_features is None else key_features).reshape(batch,-1,heads,width)',mode='eval').body
        changed+=1
assert changed==1
ast.fix_missing_locations(module)
label='raw_key_revision1'
local=OUT/label
local.mkdir(exist_ok=False)
(local/'coarse_cross_attention_r1.py').write_text(ast.unparse(module)+'\n',encoding='utf-8')
tree=ast.parse((OUT/'native_coarse/native_coarse.py').read_text())
counts={'import':0,'keys':0,'conditions':0,'raw':0,'name':0}
class Repair(ast.NodeTransformer):
    def visit_ImportFrom(self,node):
        if node.module=='coarse_cross_attention':
            node.module='coarse_cross_attention_r1';counts['import']+=1
        return node
    def visit_Assign(self,node):
        self.generic_visit(node)
        if len(node.targets)==1 and ast.unparse(node.targets[0])=='coarse':
            counts['raw']+=1
            return [node,*ast.parse("raw_coarse=held['core_args'][3][-1]\nassert raw_coarse.shape==coarse.shape").body]
        return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='coarse_readback':
            node.keywords.append(ast.keyword(arg='key_features',value=ast.parse("None if mode=='coarse_attention_refined_key' else raw_coarse",mode='eval').body))
            counts['keys']+=1
        return node
    def visit_For(self,node):
        self.generic_visit(node)
        if ast.unparse(node.target)=='mode':
            node.iter=ast.parse("('own_coarse_identity','coarse_attention_refined_key','coarse_attention','uniform_coarse_mean','cyclic_key_value_mismatch')",mode='eval').body
            counts['conditions']+=1
        return node
    def visit_Constant(self,node):
        if node.value=='native_coarse_result.json':
            counts['name']+=1;return ast.Constant('native_raw_key_result.json')
        return node
tree=Repair().visit(tree)
assert counts=={k:1 for k in counts},counts
ast.fix_missing_locations(tree)
(local/'native_raw_key.py').write_text(ast.unparse(tree)+'\n',encoding='utf-8')
shutil.copyfile(ROOT/'pipeline/diagnostic_bundles/tick_ce9bc689/trace_m95_1/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(OUT/'native_coarse/native_manifest.json'))
stage=STAGE+'/'+label
manifest.update(stage=stage,key_alignment_revision=evidence(OUT/'key_alignment_revision1_protocol.json'))
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','native_raw_key.py','coarse_cross_attention_r1.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
sc=run(['scp',*SSH,*[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')],'songcl@192.168.1.115:'+stage+'/'])
assert sc.returncode==0,sc.stderr
guard(500)
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_raw_key.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(900,int(remaining)-120))
save('raw_key_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
pull=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/native_raw_key_result.json',str(local/'native_raw_key_result.json')])
assert pull.returncode==0,pull.stderr
value=tick.load(local/'native_raw_key_result.json')
revision.update(result='inconclusive',evidence=[evidence(local/'native_raw_key_result.json')])
advance([local/'native_raw_key_result.json',local/'native_manifest.json',local/'native_raw_key.py',local/'coarse_cross_attention_r1.py',OUT/'raw_key_execution.json'],revision_history=[revision],
 gate_result='Raw-key connection control complete='+str(value.get('execution_completed'))+';interpretation/diagnosis pending;no new model or admission')
summary=[]
for c in value.get('coarse_conditions',[]):
    summary.append({k:v for k,v in c.items() if k in ('condition','message_max_change','mask_max_change','native_loss_delta','matching_identical','identity_passed','attention_entropy_mean','own_coarse_probability_per_expression','message_gradient_norm','coarse_gradient_norm')})
print(json.dumps({'execution_completed':value.get('execution_completed'),'controls_passed':value.get('controls_passed'),'conditions':summary,'error':value.get('error'),'native_forwards':value['native_forwards'],'native_backwards':value['native_backwards'],'suffix_replays':value['suffix_replays'],'criterion_replays':value['criterion_replays']},ensure_ascii=False))
