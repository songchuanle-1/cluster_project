"""Actual SFC primitive-wrapper and failure-finally AST controls, opaque stdlib only."""
from pathlib import Path
from types import SimpleNamespace
import ast,hashlib,json

B=Path(__file__).resolve().parent
W=B/'sfc_native_prepare/worker.py'
t=ast.parse(W.read_text(encoding='utf-8'))
smoke=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='smoke')
nested={n.name:n for n in ast.walk(smoke) if isinstance(n,ast.FunctionDef)}
names=('observed_stack','observed_select','observed_copy','observed_mean')
parts=[nested[n] for n in names]
recovery=next(n for n in smoke.body if isinstance(n,ast.Try) and 'installations' in ast.unparse(n))
checks=[]
def ck(c,s):
    assert c,s
    checks.append(s)
class Index:
    def __init__(self,values):self.values=values
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return self.values
class Opaque:
    def __eq__(self,other):return SimpleNamespace(all=lambda:True)
def make_env():
    calls=[];state={};returns={n:object() for n in ('stack','select','copy','mean')}
    def original(kind):
        def f(*args,**kwargs):
            calls.append((kind,args,kwargs));returns[kind]=object();return returns[kind]
        return f
    env={'state':state,'original_stack':original('stack'),'original_select':original('select'),'original_copy':original('copy'),
         'torch':None,'fingerprint':lambda torch,value:'opaque','summary':lambda value:{'finite':True},'lite_watch':lambda *x:None}
    exec(compile(ast.fix_missing_locations(ast.Module(parts,[])),'actual_SFC_wrappers_only','exec'),env)
    return env,calls,returns
env,calls,ret=make_env()
ck(env['observed_stack']([object()],dim=0) is ret['stack'],'outside context stack exact original return')
ck(env['observed_select'](object(),0,Index([0])) is ret['select'],'outside context select exact original return')
ck(env['observed_copy'](object(),0,Index([0]),object()) is ret['copy'],'outside context copy exact original return')
ck([x[0] for x in calls]==['stack','select','copy'],'outside context original methods called once only')

env,calls,ret=make_env();old=object();rp={'sources':[0,1],'receivers':[0],'counts':[2],'source_receivers':[0,0]}
ctx={'phase':'mean_ready','current_state_ref':old,'rounds':[rp],'round_index':0,'mean_count':0,'record':{'mean_calls':[],'primitive_calls':[]}}
env['state']['sfc_context']=ctx
def original_mean(actual_old,actual_plan):
    ck(actual_old is old and actual_plan is rp,'actual mean original arguments preserved')
    env['observed_select'](actual_old,0,Index(rp['sources']))
    calls.append(('mean',(actual_old,actual_plan),{}));return ret['mean']
env['original_mean']=original_mean
ck(env['observed_mean'](old,rp) is ret['mean'],'active mean returns original object without recomputation')
ck([x[0] for x in calls]==['select','mean'] and ctx['mean_count']==1 and ctx['phase']=='cell','actual donor gather and mean once; phase advances')
before=len(calls)
try:env['observed_mean'](object(),rp)
except AssertionError:ck(len(calls)==before,'wrong old-state/phase rejected before original mean')
else:raise AssertionError('wrong old-state accepted')

env,calls,ret=make_env();old=object();gelu=object()
ctx={'phase':'state_write','current_state_ref':old,'GELU_ref':gelu,'rounds':[rp],'round_index':0,'state_write_count':0,
     'pending_round':{},'record':{'round_calls':[],'primitive_calls':[]}}
env['state']['sfc_context']=ctx
ck(env['observed_copy'](old,0,Index([0]),gelu) is ret['copy'],'actual state replacement returns original copy object')
ck(len(calls)==1 and calls[0][0]=='copy' and ctx['current_state_ref'] is ret['copy'] and ctx['state_write_count']==1 and ctx['phase']=='final_scatter','single functional update and phase barrier; no copy replay')
ctx.update(phase='final_copy',final_level=0,destinations=[[0],[],[]],final_source_ref=gelu,final_flat_outputs=[])
ck(env['observed_copy'](Opaque(),0,Index([0]),gelu) is ret['copy'] and len(calls)==2 and ctx['final_flat_outputs'][0] is ret['copy'],'final scatter once and exact original result retained')

class ControlFailure(Exception):pass
class Owner:
    def __init__(self):object.__setattr__(self,'fail_replacement',None)
    def __setattr__(self,k,v):
        if v is self.fail_replacement:raise ControlFailure('partial install sentinel')
        object.__setattr__(self,k,v)
for partial_install in (False,True):
    owner=Owner();a,b,ra,rb=(object() for _ in range(4));owner.stack=a;owner.select=b
    if partial_install:owner.fail_replacement=rb
    class Inherited:
        def method(self):return 'original'
    instance=Inherited();instance.method=lambda:'temporary'
    removed=[];writer_events=[]
    def train(*args):raise ControlFailure('native train sentinel, no training executed')
    state={'temporary':True}
    ev={'installations':[(owner,'stack',ra),(owner,'select',rb)],'global_replacements':[(owner,'stack',a),(owner,'select',b)],
        'replacements':[(instance,'method')],'hooks':[SimpleNamespace(remove=lambda:removed.append(True))],'state':state,
        'writer':SimpleNamespace(flush=lambda:writer_events.append('flush'),close=lambda:writer_events.append('close')),
        'train':SimpleNamespace(train=train),'torch':SimpleNamespace(cuda=SimpleNamespace(synchronize=lambda:None)),
        'TwoNativeBatches':lambda v:v,'loader':None,'model':None,'optimizer':None,'scheduler':None,'cfg':None,'logger':None}
    try:exec(compile(ast.fix_missing_locations(ast.Module([recovery],[])),'actual_install_try_finally_only','exec'),ev)
    except ControlFailure:pass
    else:raise AssertionError('sentinel failure absent')
    ck(owner.stack is a and owner.select is b,'global primitive replacements restored after '+('partial-install failure' if partial_install else 'train failure'))
    ck('method' not in vars(instance) and instance.method()=='original','instance override restored to inherited original')
    ck(removed==[True] and state=={} and writer_events==['flush','close'],'hooks/state/writer finally cleanup preserved')

proof={'status':'ACTUAL_SFC_PRIMITIVE_OBSERVER_WRAPPER_AND_FAILURE_FINALLY_AST_STDLIB_VALIDATED_NOT_TORCH',
       'actual_checks':len(checks),'checks':checks,
       'tested_AST_sha256':hashlib.sha256('\n'.join(ast.dump(n,include_attributes=False) for n in parts+[recovery]).encode()).hexdigest(),
       'scope':'Actual four callback definitions and exact installation try/finally AST only, opaque stdlib stand-ins. Outside-context one-call delegation, active actual mean/select/copy return identity/phase and wrong-state refusal, partial-install/train exception restoration. No Torch/global real Tensor monkeypatch, learned operator/forward/backward/native/resource/root execution, old suite or new numerical gate.'}
if __name__=='__main__':print(json.dumps(proof,indent=2,allow_nan=False))
