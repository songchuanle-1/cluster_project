"""ELC callback identity/phase controls only; no Torch or worker imports."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,json

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
WORKER=HERE/'elc_native_prepare/worker.py'
tree=ast.parse(WORKER.read_text('utf8'));names=('observed_stack','observed_select','observed_mean','observed_copy','observed_incident')
functions=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(functions)==len(names)
class Token:
    def __init__(self,label,rows=1,channels=1,ids=None,zero=False):
        self.label=label;self.shape=(rows,channels);self.ids=ids;self.zero=zero;self.requires_grad=False
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return list(self.ids)
    def __getitem__(self,key):return Token(self.label+':'+repr(key))
    def __eq__(self,other):return SimpleNamespace(all=lambda:self.zero and other==0)
calls=[];checks=[];state={};serial=0
def ck(cond,label):assert cond,label;checks.append(label)
def fresh(kind,rows=1):
    global serial
    serial+=1;return Token(kind+str(serial),rows)
def original_stack(values,*args,**kwargs):
    out=fresh('stack',len(values));calls.append(('stack',values,out));return out
def original_select(tensor,dim,index,*args,**kwargs):
    out=fresh('select',len(index.ids));calls.append(('select',tensor,out));return out
def original_copy(tensor,dim,index,source,*args,**kwargs):
    out=fresh('copy',tensor.shape[0]);calls.append(('copy',tensor,out));return out
def summary(value):return {'finite':True,'shape':list(value.shape)}
ns={'state':state,'torch':object(),'copy':copy,'original_stack':original_stack,'original_select':original_select,
    'original_copy':original_copy,'fingerprint':lambda torch,value:value.label,'summary':summary,'lite_watch':lambda *args:None,
    'att':SimpleNamespace(edge_line_graph=SimpleNamespace(channels=1))}
exec(compile(ast.Module(functions,[]),str(WORKER)+'::only_five_callback_defs','exec'),ns)
stack,select,mean,write,incident=(ns[n] for n in names)
def record():return {'primitive_calls':[],'mean_calls':[],'incident_mean_calls':[],'round_calls':[]}
def refused(call,label):
    before=len(calls)
    try:call()
    except AssertionError:ck(len(calls)==before,label+': refuses before original delegation')
    else:raise AssertionError(label+': invalid phase/identity accepted')

# Outside active context, every primitive returns the distinct original result.
for name,call in [('stack',lambda:stack([Token('row')])),('select',lambda:select(Token('old'),0,Token('idx',ids=[0]))),
                  ('copy',lambda:write(Token('old'),0,Token('idx',ids=[0]),Token('source')))]:
    before=len(calls);out=call();ck(len(calls)==before+1 and out is calls[-1][2],name+': transparent once-return outside active context')

# Exact child/parent initialization stacks; no source operator is re-evaluated.
norm=[Token('fine'),Token('mid'),Token('coarse')]
ctx={'phase':'initial_children','edge_rows':[(0,(0,2),(1,3)),(0,(1,3),(2,1))],'normalized':norm,'stack_count':0,'record':record()}
state['elc_context']=ctx
child=[norm[0][0,2],norm[1][0,3]];parent=[norm[1][0,3],norm[2][0,1]]
out=stack(child);ck(out is ctx['child_stack_ref'] is calls[-1][2] and ctx['phase']=='initial_parents','child stack original identity and phase')
out=stack(parent);ck(out is ctx['parent_stack_ref'] is calls[-1][2] and ctx['phase']=='initialize' and ctx['stack_count']==2,'parent stack original identity and initialize phase')
refused(lambda:stack(child),'stack after initialization')

# Adjacent-edge mean delegates once and observes each actual OLD bucket gather.
old=Token('OLD',3);rp={'receivers':[0,1,2],'counts':[2,2,2],
    'endpoint_buckets':[{'degree':1,'edges':[0,1,2],'receiver_rows':[0,1,2]},
                        {'degree':3,'edges':[0,1,2],'receiver_rows':[0,1,2]}]}
ctx={'phase':'mean_ready','current_state_ref':old,'rounds':[rp],'round_index':0,'mean_count':0,'record':record()};state['elc_context']=ctx
def original_mean(value,plan):
    out=fresh('mean',len(plan['receivers']));calls.append(('mean',value,out))
    for bucket in plan['endpoint_buckets']:select(value,0,Token('bucket',ids=bucket['edges']))
    return out
ns['original_mean']=original_mean
before=len(calls);out=mean(old,rp)
ck(out is ctx['mean_ref'] and ctx['phase']=='cell' and ctx['mean_count']==1,'adjacent mean original return object and cell phase')
ck(len(calls)==before+3 and [c[0] for c in calls[before:]]==['mean','select','select'],'one original adjacent mean and one select per bucket')
ck(all(c[1] is old for c in calls[before:]),'all endpoint gathers from exact same OLD state')
ck(ctx['record']['mean_calls'][0]['returned_original_object_unchanged'] and not ctx['record']['mean_calls'][0]['mean_replayed_by_observer'],'actual mean record truth follows delegation')
ctx['phase']='mean_ready';refused(lambda:mean(Token('stale',3),rp),'adjacent mean stale state')
ctx['phase']='cell';refused(lambda:mean(old,rp),'adjacent mean wrong phase')

# A real captured GELU object goes into one functional copy; OLD is not replaced in place.
gelu=Token('actualGELU',3);ctx.update(phase='state_write',GELU_ref=gelu,state_write_count=0,pending_round={})
before=len(calls);out=write(old,0,Token('receivers',ids=[0,1,2]),gelu)
ck(len(calls)==before+1 and out is calls[-1][2] is ctx['current_state_ref'] and out is not old,'state copy once, actual new original return retained')
ck(ctx['phase']=='incident_ready' and ctx['round_index']==ctx['state_write_count']==1,'last actual round advances to incident mean')
refused(lambda:write(old,0,Token('idx',ids=[0,1,2]),gelu),'copy without correct write phase')

# Final mean uses the same final edge state at both endpoints; it is not replayed.
plan={'incident':[[0],[0,1],[1]],'edges':[(0,1),(1,2)]}
final=Token('finaledge',2);ctx={'phase':'incident_ready','current_state_ref':final,'plans_ref':[plan],'incident_count':0,
    'node_count':3,'record':record(),'round_index':1,'positions':[[0],[1],[2]],'destinations':[[2],[3],[1]],
    'final_level':0,'final_flat_outputs':[]};state['elc_context']=ctx
def original_incident(value,plans):
    out=fresh('incident',3);calls.append(('incident',value,out))
    select(value,0,Token('incident_sources',ids=[0,0,1,1]));return out
ns['original_incident']=original_incident
before=len(calls);out=incident(final,ctx['plans_ref'])
ck(len(calls)==before+2 and [c[0] for c in calls[before:]]==['incident','select'],'one original incident mean and original edge gather')
ck(out is ctx['node_state_ref'] is calls[before][2] and ctx['phase']=='final_scatter' and ctx['incident_count']==1,'incident original object returned unchanged for node scatter')
ck(ctx['incident_sources']==[0,0,1,1] and ctx['record']['incident_mean_calls'][0]['incident_counts']==[1,2,1],'final edge identities shared at both endpoint incidences')
refused(lambda:incident(final,ctx['plans_ref']),'second incident mean')
ctx['phase']='incident_ready';refused(lambda:incident(Token('wrongfinal',2),ctx['plans_ref']),'incident stale final carrier');ctx['phase']='final_scatter'
for level in range(3):
    before=len(calls);src=select(out,0,Token('positions',ids=ctx['positions'][level]));answer=write(Token('zero',5,zero=True),0,Token('destination',ids=ctx['destinations'][level]),src)
    ck(len(calls)==before+2 and answer is calls[-1][2] is ctx['final_flat_outputs'][-1],'final level'+str(level)+' gather/copy returns originals once')
ck(ctx['phase']=='complete' and ctx['final_level']==3,'all three actual scatters complete before context removal')

# Reuse earlier tested failure-finally behavior only after exact AST equality.
def train_try(source):
    smoke=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='smoke')
    return next(n for n in ast.walk(smoke) if isinstance(n,ast.Try) and any(isinstance(c,ast.For) and isinstance(c.iter,ast.Name) and c.iter.id=='installations' for c in n.body))
oldsource=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare/worker.py'
new_try=train_try(WORKER.read_text('utf8'));prior_try=train_try(oldsource.read_text('utf8'))
ck(ast.dump(new_try,include_attributes=False)==ast.dump(prior_try,include_attributes=False),'global installation/finally body exactly matches earlier failure-tested SFC AST; no old failure suite rerun')
proof={'status':'ELC_ACTUAL_CALLBACK_AST_ONCE_RETURN_PHASE_STDLIB_CHECKED_NOT_TORCH','actual_checks':len(checks),'checks':checks,
    'tested_worker_sha256':hashlib.sha256(WORKER.read_bytes()).hexdigest(),
    'tested_callback_AST_sha256':hashlib.sha256(ast.dump(ast.Module(functions+[new_try],[]),include_attributes=False).encode()).hexdigest(),
    'prior_failure_finally_proof':'pipeline/diagnostic_bundles/tick_928313fd/sfc_primitive_observer_independent_software.json',
    'scope':'Only five actual callback defs and AST equality of installation/finally. Distinct opaque original return stand-ins exercise two initialization stacks, multi-bucket OTHER mean, functional state write, final incident mean and3scatters; invalid phase/stale carrier refuses before delegation. No production mean/Linear/GELU/Torch/Tensor descriptor/CUDA/autograd/backward/native/root entry or old suite execution, no synthetic native result or new scientific gate.'}
if __name__=='__main__':print(json.dumps(proof,indent=2,allow_nan=False))
