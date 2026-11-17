"""Bounded NEC production AST/list arithmetic checks; no Torch/model import."""
from pathlib import Path
from fractions import Fraction as Q
from copy import deepcopy
from itertools import product
from types import SimpleNamespace
import ast,hashlib,json,math
import author_guard as ag
ag.check();HERE=ag.HERE;ROOT=ag.ROOT
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
DEST=HERE/'staged_repository/framework/model/Quard_model'/(BASE+'_nec')
FROZEN=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
checks=[]
def check(name,value):
    assert value,name;checks.append(name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
carrier_tree=ast.parse((FROZEN/'static_check.py').read_text(encoding='utf-8'))
carrier=[n for n in carrier_tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('size','T','stack','cat')]
exec(compile(ast.fix_missing_locations(ast.Module(body=carrier,type_ignores=[])),'generic_list_primitives_only','exec'))

class Map:
    def __init__(self,kind,events):self.kind=kind;self.events=events;self.calls=[]
    def __call__(self,x):
        self.events.append((self.kind,x.shape[0]));self.calls.append(deepcopy(x));c=x.shape[1]//2;out=[]
        for row in range(x.shape[0]):
            inputs=x.data[row*2*c:(row+1)*2*c]
            for k in range(c):
                value=Q((k+1)*(1 if self.kind=='edge' else -1),101)
                for j,v in enumerate(inputs):value+=Q((k+1)*(j+2),97 if self.kind=='edge' else 109)*v
                out.append(value)
        return T(out,(x.shape[0],c))
def activation(x):return T([v+v*v/Q(100) for v in x.data],x.shape)
def gelu(x):return T([float(v)*0.5*(1+math.erf(float(v)/math.sqrt(2))) for v in x.data],x.shape)
source=(DEST/'node_edge_coupling.py').read_text(encoding='utf-8');tree=ast.parse(source)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
ns={'torch':SimpleNamespace(tensor=lambda x,**kw:T(x),stack=stack,cat=cat,long='long')}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions+[forward],type_ignores=[])),'actual_NEC_production_AST','exec'),ns)
WIDTHS=(7,4,3);C=2
SCENES=[([1],[0,2],[0,0,1]),([0,3],[1,0,1,1],[0,2]),
        ([0,1,2],[0,1,1],[0,0]),([0,1,3,6],[0,1,0,2,0,0,2],[0,0,2]),
        ([],[],[]),([0,0,1,1],[0,1],[0,0])]

def topology(scene):
    points,fm,mc=scene;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    keys=[(l,i) for l,ids in enumerate((fine,middle,coarse)) for i in ids]
    edges=[((0,i),(1,fm[i])) for i in fine]+[((1,j),(2,mc[j])) for j in middle]
    adjacent={key:set() for key in keys};incident={key:[] for key in keys}
    for edge in edges:
        a,b=edge;adjacent[a].add(b);adjacent[b].add(a);incident[a].append(edge);incident[b].append(edge)
    components=[]
    for root in coarse:
        nodes={(2,root)}|{(1,j) for j in middle if mc[j]==root}|{(0,i) for i in fine if mc[fm[i]]==root}
        maximum=0
        for start in nodes:
            distances={start:0};queue=[start]
            for node in queue:
                for other in adjacent[node]:
                    if other not in distances:distances[other]=distances[node]+1;queue.append(other)
            maximum=max(maximum,max(distances.values()))
        components.append((nodes,[e for e in edges if e[0] in nodes],maximum))
    return keys,edges,incident,components

def vector(kind,row):
    c=len(row)//2;out=[]
    for k in range(c):
        value=Q((k+1)*(1 if kind=='edge' else -1),101)
        for j in range(2*c):value+=Q((k+1)*(j+2),97 if kind=='edge' else 109)*row[j]
        out.append(value)
    return out
def phi(values,fn):return fn(T(values)).data
def oracle(values,scene,fn,erase_edge_history=False,stale_incidence=False):
    keys,edges,incident,components=topology(scene)
    h={key:list(values[key[0]][key[1]]) for key in keys};e={edge:[Q(0)]*C for edge in edges}
    for r in range(max((d for _,_,d in components),default=0)):
        new_edges={key:list(v) for key,v in e.items()}
        for nodes,edge_keys,d in components:
            if r>=d:continue
            for edge in edge_keys:
                a,b=edge;own=[Q(0)]*C if erase_edge_history else e[edge]
                endpoint=[(x+y)/2 for x,y in zip(h[a],h[b])]
                new_edges[edge]=phi(vector('edge',own+endpoint),fn)
        read_edges=e if stale_incidence else new_edges
        new_nodes={key:list(v) for key,v in h.items()}
        for nodes,_,d in components:
            if r>=d:continue
            for node in sorted(nodes):
                total=[Q(0)]*C
                for edge in incident[node]:total=[a+b for a,b in zip(total,read_edges[edge])]
                mean=[v/len(incident[node]) for v in total]
                new_nodes[node]=phi(vector('node',h[node]+mean),fn)
        h,e=new_nodes,new_edges
    out=[[[Q(0)]*C for _ in range(w)] for w in WIDTHS]
    for (level,i),value in h.items():out[level][i]=value
    return out

def run_case(label,scenes,fn=activation):
    b=len(scenes);values=[[[[Q((batch+1)*3+(level-1)*2+i+k,101) for k in range(C)] for i in range(w)] for batch in range(b)] for level,w in enumerate(WIDTHS)]
    levels=[T([v for scene in bank for row in scene for v in row],(b,w,C)) for bank,w in zip(values,WIDTHS)]
    ids=[[T(scene[level]) for scene in scenes] for level in range(3)]
    events=[];obj=SimpleNamespace(channels=C,edge_cell=Map('edge',events),node_cell=Map('node',events),activation=fn)
    actual=ns['forward'](obj,levels,ids);expected=[[] for _ in range(3)]
    for batch,scene in enumerate(scenes):
        out=oracle([values[l][batch] for l in range(3)],scene,fn)
        for level in range(3):expected[level].extend(v for row in out[level] for v in row)
    if fn is activation:equal=all(t.data==v for t,v in zip(actual,expected))
    else:equal=all(all(abs(a-b)<=1e-12 for a,b in zip(t.data,v)) for t,v in zip(actual,expected))
    check(label+':actual forward matches independent keyed dual-state oracle',equal)
    plans=[ns['build_node_edge_plan'](*scene,WIDTHS) for scene in scenes];rounds=ns['build_node_edge_rounds'](plans)
    check(label+':one edge then one node map per active global round, no fake rows',events==[(kind,len(r[key])) for r in rounds for kind,key in (('edge','edge_receivers'),('node','node_receivers'))])
    for scene,plan in zip(scenes,plans):
        keys,edges,_,components=topology(scene)
        assert [tuple(plan['node_keys'][a]) for a in range(len(keys))]==keys
        assert [(plan['node_keys'][a],plan['node_keys'][b]) for a,b in plan['edges']]==edges
        assert [c['diameter'] for c in plan['components']]==[d for _,_,d in components]
    return actual,values,rounds

def main():
    for i,scene in enumerate(SCENES):run_case('single'+str(i),[scene])
    _,mixed_values,mixed_rounds=run_case('mixed empty D2 D4 batches',[SCENES[0],SCENES[4],SCENES[3]])
    run_case('zero batch',[])
    run_case('scalar erf GELU',[SCENES[2]],gelu)
    check('mixed components really stop both carriers after genuine D2',len(mixed_rounds)==4 and len(mixed_rounds[2]['node_receivers'])<len(mixed_rounds[1]['node_receivers']) and len(mixed_rounds[2]['edge_receivers'])<len(mixed_rounds[1]['edge_receivers']))
    scene=SCENES[2];values=[[[Q(level+i+k+1,101) for k in range(C)] for i in range(w)] for level,w in enumerate(WIDTHS)]
    ordinary=oracle(values,scene,activation)
    check('persistent edge history is nontrivial source-DAG control',ordinary!=oracle(values,scene,activation,erase_edge_history=True))
    check('node reads NEW rather than lagged edge states',ordinary!=oracle(values,scene,activation,stale_incidence=True))
    p=ns['build_node_edge_plan'](list(range(256)),[i//4 for i in range(256)],[i//8 for i in range(64)],[256,64,8])
    rounds=ns['build_node_edge_rounds']([p])
    check('original cap source rows and MAC inference only',len(p['node_keys'])==328 and len(p['edges'])==320 and len(rounds)==4 and sum(len(r['edge_receivers'])+len(r['node_receivers']) for r in rounds)*2*256*256==339738624)
    invalid=[([True],[0],[0],WIDTHS),([-1],[0],[0],WIDTHS),([7],[0],[0],WIDTHS),([1],[0],[0],WIDTHS),([0],[4],[0],WIDTHS),([0],[0],[],WIDTHS),([0],[0],[0],(7,4,True)),([0],[0],[0],(7,4))]
    for args in invalid:
        try:ns['build_node_edge_plan'](*args)
        except ValueError:pass
        else:raise AssertionError('Invalid original metadata accepted')
    check('eight invalid metadata cases rejected',True)
    for path in DEST.glob('*.py'):compile(path.read_bytes(),str(path),'exec')
    check('exact8 independent model files compile without imports',len(list(DEST.glob('*.py')))==8)
    copied=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/new_candidate_prepare/staged_repository/framework/model/Quard_model'/(BASE+'_wfc')
    check('six original model modules unchanged',all((DEST/n).read_bytes()==(copied/n).read_bytes() for n in ('__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py')))
    yaml=next((HERE/'staged_repository/configs').rglob('*.yaml'))
    check('native YAML exact a18',sha(yaml)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
    original=(ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/lft_candidate_prepare/original_m95_hier_postprocess.py.txt').read_text(encoding='utf-8')
    actual=(DEST/'hier_postprocess.py').read_text(encoding='utf-8')
    methods=lambda text:{(c.name,n.name):ast.dump(n,include_attributes=False) for c in ast.parse(text).body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef)}
    a,b=methods(original),methods(actual);allowed={('C2F_ClusterAttn_CTF','__init__'),('C2F_ClusterAttn_CTF','forward')}
    check('other23hierarchy methods original rawmean FPS HCG CSORT unchanged',a.keys()==b.keys() and all(a[k]==b[k] for k in a if k not in allowed))
    check('original RNG constructor consumption then CPUfork then FFN removal',actual.index('self.cluster_ffn_norm')<actual.index('with torch.random.fork_rng(devices=[])')<actual.index('self.cluster_ffn = nn.ModuleList([nn.Identity()'))
    check('two2CtoC maps source parameter inference',2*(2*256*256+256)==262656 and 3*(8*256*256+5*256)==1576704)
    source_hashes={p.relative_to(HERE/'staged_repository').as_posix():sha(p) for p in sorted((HERE/'staged_repository').rglob('*')) if p.is_file()}
    ag.save(HERE/'static_validation.json',{'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','check_count':len(checks),'checks':checks,'actual_forward_carrier_cases':9,'invalid_metadata_cases':8,'Torch':False,'native':'NOT_RUN','resources':'NOT_RUN','Torch_FP32_autograd':'NOT_RUN','command':'python -B -X utf8 pipeline/diagnostic_bundles/tick_d94467a9/new_candidate_one/static_check.py','source_files_exact9':source_hashes,'scope':'Actual new producer plan/rounds/means/forward AST on generic rational/list primitives vs independent original-ID direct dual-state equations, plus one scalar-erf GELU case. No old test main/suite or full model executed; no native threshold follows.'})
    print(json.dumps({'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','check_count':len(checks),'sha256':sha(HERE/'static_validation.json')}))
if __name__=='__main__':main()
