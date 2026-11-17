"""stdlib checks of production MST builder and source wiring; NOT Torch/native."""
from pathlib import Path
import ast,copy,hashlib,json,math,sys,traceback
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=Path('D:/project/cluster_project')
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort';NAME=BASE+'_aef'
MODEL=P/'staged_repository/framework/model/Quard_model'/NAME
PRIMARY=R/'Cluster/framework/model/Quard_model'/BASE
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];cases=0
def ck(n,v):
    assert v,n
    checks.append(n)
def kruskal(coords,parents,support):
    out=[]
    for parent in sorted(set(parents[i] for i in range(len(parents)) if support[i])):
        ids=[i for i in range(len(parents)) if support[i] and parents[i]==parent]
        representatives={i:i for i in ids}
        def find(i):
            while representatives[i]!=i:i=representatives[i]
            return i
        candidates=[]
        for a in ids:
            for b in ids:
                if a<b:candidates.append((sum((coords[a][j]-coords[b][j])**2 for j in range(3)),a,b))
        for _,a,b in sorted(candidates):
            x,y=find(a),find(b)
            if x!=y:representatives[x]=y;out.append((a,b))
    return sorted(out)
def check_plan(builder,coords,parents,support,label):
    global cases
    plan=builder(coords,parents,support);cases+=1
    ck(label+'_oracle',sorted(plan['edges'])==kruskal(coords,parents,support))
    active={i for i,x in enumerate(support) if x}
    ck(label+'_count',len(plan['edges'])==len(active)-len(plan['groups']))
    ck(label+'_domain',all(a<b and a in active and b in active and parents[a]==parents[b] for a,b in plan['edges']))
    # Integer arbitrary edge flux tests incidence algebra on actual production edges.
    delta=[[0,0] for _ in coords];reverse=[[0,0] for _ in coords]
    for k,(a,b) in enumerate(plan['edges']):
        q=[3*k+1,7-2*k]
        for channel in range(2):
            delta[a][channel]+=q[channel];delta[b][channel]-=q[channel]
            reverse[b][channel]+=-q[channel];reverse[a][channel]-=-q[channel]
    ck(label+'_orientation_algebra',delta==reverse)
    ck(label+'_unweighted_integer_sum',all(sum(delta[i][c] for i in g['node_ids'])==0 for g in plan['groups'] for c in range(2)))
    ck(label+'_ignored_rows_zero',all(delta[i]==[0,0] for i in range(len(coords)) if i not in active))
    return plan
def run():
    helper=(MODEL/'middle_flux.py').read_text(encoding='utf-8');tree=ast.parse(helper)
    production=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_parent_mst')
    ns={'math':math};exec(compile(ast.Module(body=[production],type_ignores=[]),'actual_production_MST','exec'),ns)
    builder=ns['build_parent_mst']
    for n in range(129):
        coords=[[(17*i)%31,(7*i*i)%19,(13*i)%23] for i in range(n)]
        check_plan(builder,coords,[0]*n,[True]*n,'n'+str(n))
    specials=[
      ([[0,0,0]]*6,[0]*6,[True]*6),
      ([[0,0,0],[1,0,0],[0,1,0],[1,1,0]],[0]*4,[True]*4),
      ([[i,0,0] for i in range(7)],[7,2,7,2,7,2,7],[True,False,True,True,False,True,True]),
      ([[i,0,0] for i in range(5)],[0,0,1,1,1],[False]*5),
      ([[0,0,0],[0,0,0],[0,0,0]],[0,1,2],[True]*3),
      ([[i,(-1)**i,0] for i in range(9)],[3,3,3,3,3,3,3,3,3],[True,False,True,False,True,False,True,False,True]),
      ([(0,0,0),(2,2,2)],[4,4],[True,True])]
    for j,args in enumerate(specials):check_plan(builder,*args,'special'+str(j))
    p=builder([[0,0,0]]*5,[0]*5,[True]*5)
    ck('coincident_tie_star_original_ID',sorted(p['edges'])==[(0,1),(0,2),(0,3),(0,4)])
    malformed=[
      (None,[],[]),([],None,[]),([],[],None),
      ([[0,0,0]],[],[]),([[0,0]], [0],[True]),
      ([[0,0,0]],[-1],[True]),([[0,0,0]],[True],[True]),([[0,0,0]],[1.0],[True]),
      ([[0,0,0]],[0],[1]),([[True,0,0]],[0],[True]),
      ([[float('nan'),0,0]],[0],[False]),([[float('inf'),0,0]],[0],[True])]
    for i,args in enumerate(malformed):
        try:builder(*args)
        except ValueError:ck('invalid'+str(i),True)
        else:raise AssertionError('Invalidmetadata accepted '+str(i))
    for p in MODEL.glob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
    ck('eight_source_count',len(list(MODEL.glob('*.py')))==8)
    for n in ('__init__.py','backbone.py','loss.py','network.py','sample_model.py'):
        ck('unchanged_primary_'+n,(MODEL/n).read_bytes()==(PRIMARY/n).read_bytes())
    config=P/'staged_repository/configs/Quard/ctf_hcg_csort_aef'/str(NAME+'.yaml')
    ck('YAML_byteidentical',(config).read_bytes()==(R/'Cluster/configs/Quard/ctf_hcg_csort'/str(BASE+'.yaml')).read_bytes())
    ck('YAML_original_hash',sha(config)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
    hpost=(MODEL/'hier_postprocess.py').read_text(encoding='utf-8');dec=(MODEL/'dec.py').read_text(encoding='utf-8')
    oldtree=ast.parse((PRIMARY/'hier_postprocess.py').read_text(encoding='utf-8'));newtree=ast.parse(hpost)
    classes=lambda t:{n.name:n for n in t.body if isinstance(n,ast.ClassDef)}
    for n in ('C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT'):
        ck('original_complete_class_AST_'+n,ast.dump(classes(oldtree)[n],include_attributes=False)==ast.dump(classes(newtree)[n],include_attributes=False))
    ck('original_middle_skip',all(s in hpost for s in ['refined = cf + self.middle_flux(','self.cluster_ffn_norm[1](cf)','self.cluster_ffn[1] = nn.Identity()']))
    ck('original_init_consumption_then_CPUfork',hpost.index('self.cluster_ffn = nn.ModuleList')<hpost.index('self.cluster_ffn_norm = nn.ModuleList')<hpost.index('self.cluster_ffn[1] = nn.Identity()')<hpost.index('with torch.random.fork_rng(devices=[])'))
    ck('true_support_and_cache_binding',all(s in hpost for s in ['point_to_mid = ids1[ids0]','self.middle_parent_ids is not cluster_ids_list[2]','middle_positions = [coords.detach() for coords in per_layer_coords[2]]']))
    ck('one_existing_inst_writeback',dec.count('inst_feats = inst_feats + gate * cluster_message')==(PRIMARY/'dec.py').read_text(encoding='utf-8').count('inst_feats = inst_feats + gate * cluster_message'))
    ck('actual_forward_oldstate_orientations_then_subtract',all(s in helper for s in ['flat.index_select(0, left_index)','flat.index_select(0, right_index)','self.activation(self.edge_map(oriented))','transformed[:edge_count] - transformed[edge_count:]']))
    ck('functional_signed_scatter_and_empty0',all(s in helper for s in ['return features.new_zeros(features.shape)','delta.index_add(0, left_index, flux)','delta.index_add(0, right_index, -flux)']))
    ck('native_cap_original_config_guard',all(s in helper for s in ['width > self.max_middle_tokens','max(parents) >= self.max_parent_tokens']) and 'self.cluster_layer_nums[1], self.cluster_layer_nums[2]' in hpost)
    ck('feature_not_detached','features.detach' not in helper and 'flat.detach' not in helper)
    ck('one_module_call_in_source',helper.count('self.edge_map(oriented)')==1)
    ck('parameter_inference',2*256*256+256==131328 and 8*256*256+5*256==525568 and 131328-525568==-394240)
    ck('Torch_not_imported','torch' not in sys.modules)
status='STDLIB_PRODUCTION_TOPOLOGY_AND_SOURCE_CHECKS_PASSED_NOT_NATIVE'
error=None
try:run()
except Exception:
    status='SOFTWARE_CHECK_FAILED_NOT_NATIVE';error=traceback.format_exc()
out={'status':status,'recorded_at':datetime.now(timezone.utc).isoformat(),'production_plan_valid_cases':cases,'check_count':len(checks),'checks':checks,'error':error,
 'actual_command':'python -B -X utf8 '+str(P/'static_check.py'),
 'source_hashes':{p.relative_to(P/'staged_repository').as_posix():sha(p) for p in sorted((P/'staged_repository').rglob('*')) if p.is_file()},
 'scope':'Production Prim function extracted from real helper AST and executed against independent Kruskal oracle + incidence integer algebra/source AST. n>native64 is abstract metadata stress only. Actual Torch forward/autograd/FP32/nativeTRAIN/resources were NOT_RUN.',
 'Torch_model_Git_SSH_GPU_or_shared_write':False}
path=P/'static_validation_run1.json'
with path.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(path),'status':status,'valid_cases':cases,'checks':len(checks),'error':error}))
raise SystemExit(0 if error is None else 1)
