"""Independent actual BFC production-plan/forward list-stub/static integration audit.
No model/module/torch import or local tensor execution.
"""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import argparse
import ast
import datetime
import hashlib
import json
import math
import sys

ROOT=Path('D:/project/cluster_project')
TICK=ROOT/'pipeline/diagnostic_bundles/tick_ab7e46d4'
PREP=TICK/'new_candidate_prepare'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=PREP/'staged_repository/framework/model/Quard_model'/(NAME+'_bfc')
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
CID='hierarchy-parent-butterfly-token-composition'
EXP='M213-BFC'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text('utf-8-sig'))
ref=lambda p:{'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
dump=lambda n:ast.dump(n,include_attributes=False)
parse=lambda p:ast.parse(Path(p).read_text('utf-8-sig'))
checks=[]
def ck(value,label):
    assert value,label
    checks.append(label)
def cls(tree,name):return next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
def method(tree,name,fun):return next(n for n in cls(tree,name).body if isinstance(n,ast.FunctionDef) and n.name==fun)

def oracle(centers,parents,supported):
    """Block partition matching oracle; deliberately no XOR or source helper calls."""
    groups=[]
    for p in sorted(set(parents[i] for i,v in enumerate(supported) if v)):
        ids=sorted([i for i,v in enumerate(supported) if v and parents[i]==p],key=lambda i:tuple(centers[i])+(i,))
        n=len(ids);m=math.ceil(math.log2(n)) if n>1 else 0
        bits=list(range(m))+list(reversed(range(max(0,m-1))))
        groups.append((p,ids,bits))
    rounds=[]
    for t in range(max([len(bits) for _,_,bits in groups]+[0])):
        pairs=[]
        for p,ids,bits in groups:
            if t>=len(bits):continue
            bit=bits[t];step=2**bit
            for first in range(0,len(ids),2*step):
                for offset in range(step):
                    a=first+offset;b=first+step+offset
                    if b<len(ids):pairs.append((p,bit,ids[a],ids[b]))
        rounds.append(pairs)
    return groups,rounds

def audit_plan(plan,centers,parents,supported,slots):
    groups,rounds=oracle(centers,parents,supported)
    assert [(g['parent'],list(g['order']),list(g['bits'])) for g in plan['groups']]==groups
    assert [list(q) for q in plan['rounds']]==rounds
    assert list(plan['singleton_ids'])==[ids[0] for _,ids,_ in groups if len(ids)==1]
    active={i for i,v in enumerate(supported) if v};states={i:{i} for i in active}
    pair_count=0
    for pairs in plan['rounds']:
        consumed=[];old=deepcopy(states);new=deepcopy(states)
        for p,bit,a,b in pairs:
            assert a in active and b in active and a!=b and parents[a]==parents[b]==p
            consumed.extend((a,b));new[a]=old[a]|old[b];new[b]=old[a]|old[b];pair_count+=1
        assert len(consumed)==len(set(consumed))
        assert all(new[i]==old[i] for i in active-set(consumed))
        states=new
    for p,ids,_ in groups:
        assert all(states[i]==set(ids) for i in ids)
    assert all(0<=i<len(parents)<=slots for i in active)
    return groups,rounds,pair_count

def zeros(shape):
    return 0.0 if not shape else [zeros(shape[1:]) for _ in range(shape[0])]
def shapeof(x):
    return () if not isinstance(x,list) else (len(x),)+ (shapeof(x[0]) if x else ())
class ListValue:
    """Only a Python list/control-flow surrogate; no Tensor/autograd/device claim."""
    def __init__(self,data,dtype='float',device='stdlib',requires_grad=False,shape=None):
        self.data=deepcopy(data);self.shape=tuple(shape) if shape is not None else shapeof(self.data)
        self.dtype=dtype;self.device=device;self.requires_grad=requires_grad
    @property
    def ndim(self):return len(self.shape)
    def __len__(self):return self.shape[0]
    def numel(self):return math.prod(self.shape)
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return deepcopy(self.data)
    def __getitem__(self,item):
        if isinstance(item,tuple):
            rows,cols=item;assert isinstance(rows,slice) and isinstance(cols,slice) and self.ndim==2
            data=[r[cols] for r in self.data[rows]]
            return ListValue(data,self.dtype,self.device,shape=(len(range(self.shape[0])[rows]),len(range(self.shape[1])[cols])))
        return ListValue(self.data[item],self.dtype,self.device,shape=self.shape[1:])
    def index_select(self,dim,index):
        assert dim==0
        return ListValue([self.data[i] for i in index.data],self.dtype,self.device,shape=(len(index.data),)+self.shape[1:])
    def index_copy(self,dim,index,value):
        assert dim==0 and len(index.data)==len(value.data) and len(set(index.data))==len(index.data)
        data=deepcopy(self.data)
        for i,row in zip(index.data,value.data):data[i]=deepcopy(row)
        return ListValue(data,self.dtype,self.device,shape=self.shape)
    def new_zeros(self,shape):return ListValue(zeros(tuple(shape)),self.dtype,self.device,shape=shape)
class ListTorch:
    long='long';bool='bool'
    def tensor(self,value,dtype,device):return ListValue(value,dtype,device)
    def cat(self,values,dim):
        assert dim==-1 and len({len(v.data) for v in values})==1
        return ListValue([sum([v.data[i] for v in values],[]) for i in range(len(values[0].data))],device=values[0].device,shape=(len(values[0].data),sum(v.shape[1] for v in values)))
    def zeros_like(self,value):return value.new_zeros(value.shape)
    def stack(self,values,dim):
        assert dim==0 and values
        return ListValue([v.data for v in values],device=values[0].device,shape=(len(values),)+values[0].shape)
def pairmap(row,c=2):
    left,right=row[:c],row[c:]
    return [left[i]+2*right[i]+1 for i in range(c)]+[3*left[i]-right[i]-2 for i in range(c)]
def nonlinearity(v):return v*v/(1+abs(v))
class Mix:
    def __init__(self,zero=False):self.calls=[];self.zero=zero
    def __call__(self,value):
        self.calls.append(deepcopy(value.data))
        return ListValue([[0.0]*len(row) if self.zero else pairmap(row) for row in value.data],device=value.device,shape=value.shape)
class Activation:
    def __init__(self):self.calls=[]
    def __call__(self,value):
        self.calls.append(deepcopy(value.data))
        return ListValue([[nonlinearity(x) for x in row] for row in value.data],device=value.device,shape=value.shape)
def forward_oracle(features,centers,parents,supported,zero=False):
    groups,rounds=oracle(centers,parents,supported);state=deepcopy(features);c=len(features[0]) if features else 2
    for pairs in rounds:
        old=deepcopy(state);new=deepcopy(state)
        for _,_,a,b in pairs:
            mixed=[0.0]*(2*c) if zero else [nonlinearity(x) for x in pairmap(old[a]+old[b],c)]
            new[a],new[b]=mixed[:c],mixed[c:]
        state=new
    for _,ids,_ in groups:
        if len(ids)==1:state[ids[0]]=[0.0]*c if zero else [nonlinearity(x) for x in pairmap(features[ids[0]]+[0.0]*c,c)[:c]]
    return [state[i] if i<len(supported) and supported[i] else [0.0]*c for i in range(len(features))]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preparation-sha',required=True);args=parser.parse_args()
    ck(sha(PREP/'preparation.json')==args.preparation_sha=='8512a69de3d5fcdd32523bbf966833485f3e17329235881de7aa0bd5adbe4501','frozen preparation external SHA exact')
    prep=read(PREP/'preparation.json')
    ck(len(prep['prepared_file_hashes'])==16 and all((PREP/k).resolve().is_relative_to(PREP.resolve()) and sha(PREP/k)==v for k,v in prep['prepared_file_hashes'].items()),'all16 frozen preparation map paths/hash exact')
    source9={k:v for k,v in prep['prepared_file_hashes'].items() if k.startswith('staged_repository/')}
    ck(len(source9)==9 and sum(k.endswith('.py') for k in source9)==8 and sum(k.endswith('.yaml') for k in source9)==1,'exact8 model sources plus one nativeYAML')
    helper=MODEL/'middle_butterfly.py';tree=parse(helper)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_butterfly_plan')
    ns={'math':math};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(helper)+':actual_plan','exec'),ns);production=ns['build_butterfly_plan']
    forward=method(tree,'ParentButterflyTokenComposition','forward')
    exec(compile(ast.Module(body=[forward],type_ignores=[]),str(helper)+':actual_forward_list_stub','exec'),dict(ns,torch=ListTorch()),ns2:={})
    actual_forward=ns2['forward']
    def run_case(centers,parents,supported,slots,zero=False):
        original=deepcopy((centers,parents,supported));plan=production(centers,parents,supported,slots)
        groups,rounds,pair_count=audit_plan(plan,centers,parents,supported,slots)
        assert original==(centers,parents,supported)
        values=[[float(i+1),-(i+2)/3] for i in range(slots)]
        f=ListValue([values],shape=(1,slots,2));mix=Mix(zero);act=Activation()
        self=SimpleNamespace(channels=2,max_middle_tokens=slots,mix=mix,activation=act)
        out=actual_forward(self,f,[ListValue(centers,shape=(len(parents),3))],[ListValue(parents,'long')],[ListValue(supported,'bool')])
        assert out.shape==(1,slots,2) and out.data==[forward_oracle(values,centers,parents,supported,zero)]
        assert f.data==[values] and original==(centers,parents,supported)
        assert len(mix.calls)==len(rounds)+(1 if plan['singleton_ids'] else 0)==len(act.calls)
        assert sum(len(x) for x in mix.calls)==pair_count+len(plan['singleton_ids'])
        return {'n_supported':sum(supported),'parent_groups':len(groups),'rounds':len(rounds),'pair_rows':pair_count,'singleton_rows':len(plan['singleton_ids']),'slots':slots}
    valid=[]
    for n in range(129):
        centers=[[(i%5)*1.0,((n-i)%7)*1.0,(i%3)*1.0] for i in range(n)]
        valid.append({'n':n,**run_case(centers,[42]*n,[True]*n,n+3)})
    ck(len(valid)==129,'actual production plan and extracted forward list-surrogate executed for every n0..128')
    ck(all(valid[n]['n_supported']==n for n in range(129)),'every n independently checks block-partition pair oracle/disjoint old-state matching/full final parent reachability/originalID scatter')
    special=[]
    for n in (1,2,3,5,6,7,9,13,31,64,65,128):
        special.append({'case':'all_duplicate_coordinates_ID_tie','n':n,**run_case([[0.0,0.0,0.0]]*n,[7]*n,[True]*n,n+2)})
    centers=[[float((i*7)%11),float(i%3),0.0] for i in range(24)];parents=[11 if i%3==0 else 3 if i%3==1 else 99 for i in range(24)];support=[i not in (0,4,6,8,15,18,22) for i in range(24)]
    special.append({'case':'multiple_parent_gaps_true_support_holes_and_padding',**run_case(centers,parents,support,29)})
    special.append({'case':'all_unsupported_internal_and_batch_padding',**run_case(centers,parents,[False]*24,29)})
    for n in (0,1,2,3,5,8,13,64):
        special.append({'case':'zero_map_degenerate_delta0_original_outer_skip_compatible','n':n,**run_case([[float(i),0.0,0.0] for i in range(n)],[0]*n,[True]*n,n+2,True)})
    ck(len(special)==22,'actual helper/forward meaningful duplicate-ID-tie/multi-parent/support/padding/empty/singleton/zero-map cases executed')
    # Independent multi-batch control: each parent occupies disjoint input coordinates/IDs.
    v1=[[1.0,2.0],[3.0,4.0],[5.0,6.0],[7.0,8.0],[9.0,10.0]]
    v2=[[10.0,9.0],[8.0,7.0],[6.0,5.0],[4.0,3.0],[2.0,1.0]]
    c1=[[3.0,0.0,0.0],[1.0,0.0,0.0],[2.0,0.0,0.0]]
    c2=[[1.0,0.0,0.0],[1.0,0.0,0.0],[0.0,0.0,0.0],[5.0,0.0,0.0]]
    inp=ListValue([v1,v2],shape=(2,5,2));self=SimpleNamespace(channels=2,max_middle_tokens=5,mix=Mix(),activation=Activation())
    out=actual_forward(self,inp,[ListValue(c1,shape=(3,3)),ListValue(c2,shape=(4,3))],[ListValue([9,9,9],'long'),ListValue([6,6,7,7],'long')],[ListValue([True]*3,'bool'),ListValue([True,False,True,True],'bool')])
    assert out.data==[forward_oracle(v1,c1,[9,9,9],[True]*3),forward_oracle(v2,c2,[6,6,7,7],[True,False,True,True])] and inp.data==[v1,v2]
    ck(True,'actual extracted forward multi-batch independent geometry/support state reset and original-ID inverse outputs match independent oracle')
    empty=actual_forward(SimpleNamespace(channels=2,max_middle_tokens=5,mix=Mix(),activation=Activation()),ListValue([],shape=(0,5,2)),[],[],[])
    ck(empty.shape==(0,5,2) and empty.data==[],'actual extracted forward zero-batch branch Python control flow executed with list stub')
    invalid=[
      ('maxbool',[[0.,0.,0.]],[0],[True],True),('maxnegative',[],[],[],-1),('maxfloat',[],[],[],1.0),
      ('maxprefix',[[0.,0.,0.]],[0],[True],0),('coords_short',[],[0],[True],1),('support_short',[[0.,0.,0.]],[0],[],1),
      ('coord_dim2',[[0.,0.]],[0],[True],1),('coord_dim4',[[0.,0.,0.,0.]],[0],[True],1),
      ('coord_nan',[[float('nan'),0.,0.]],[0],[True],1),('coord_inf',[[0.,float('inf'),0.]],[0],[True],1),
      ('coord_bool',[[False,0.,0.]],[0],[True],1),('coord_string',[['0',0.,0.]],[0],[True],1),
      ('parent_negative',[[0.,0.,0.]],[-1],[True],1),('parent_float',[[0.,0.,0.]],[0.0],[True],1),
      ('parent_bool',[[0.,0.,0.]],[True],[True],1),('support_int',[[0.,0.,0.]],[0],[1],1)]
    refused=[]
    for label,coords,parents,supported,slots in invalid:
        try:production(coords,parents,supported,slots)
        except (ValueError,TypeError):refused.append(label)
        else:raise AssertionError('invalid plan accepted:'+label)
    ck(len(refused)==16,'actual production function rejects16 distinct invalid scalar contract cases')
    # Static integration, source and registered-parameter contracts.
    hp=parse(MODEL/'hier_postprocess.py');bh=parse(BASE/'hier_postprocess.py');dec=parse(MODEL/'dec.py');bd=parse(BASE/'dec.py')
    for name in ('__init__.py','backbone.py','loss.py','network.py','sample_model.py'):
        ck((MODEL/name).read_bytes()==(BASE/name).read_bytes(),'original copied '+name+' byte exact')
    config_path=next(k for k in source9 if k.endswith('.yaml'));baseyaml=ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml')
    ck((PREP/config_path).read_bytes()==baseyaml.read_bytes(),'original nativeYAML byte exact; only filename/package resolver changes')
    for name in ('C2F_ClusterAttn_Lite','C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT'):
        ck(dump(cls(hp,name))==dump(cls(bh,name)),'original complete '+name+' AST exact')
    for c,f in [('PointCloudPartitioner','partition_points'),('PointCloudPartitioner','cluster_layer'),('SharedClusterBank','build_cluster_feats')]:
        ck(dump(method(hp,c,f))==dump(method(bh,c,f)),'original '+c+'.'+f+' AST exact')
    base_init=method(bh,'C2F_ClusterAttn_CTF','__init__');new_init=method(hp,'C2F_ClusterAttn_CTF','__init__')
    ck([dump(v) for v in new_init.body[:len(base_init.body)]]==[dump(v) for v in base_init.body],'original complete3FFN/3LN constructor statement sequence precedes BFC addition unchanged')
    text=(MODEL/'hier_postprocess.py').read_text('utf-8-sig')
    ck('self.cluster_ffn[1] = nn.Identity()' in text and 'with torch.random.fork_rng(devices=[]):' in text and 'self.middle_butterfly = ParentButterflyTokenComposition(d_model, self.cluster_layer_nums[1])' in text and 'refined = cf + self.middle_butterfly(' in text,'registered middle replacement/original cfskip/local CPU RNG fork design control present')
    ck('per_layer_coords[2]' in text and 'self.partitioner.middle_parent_ids is not self.cluster_ids_list[2]' in text and 'point_to_mid = ids1[ids0]' in text and 'torch.bincount(point_to_mid, minlength=Kmid) > 0' in text,'exact original middle coordinate cache/current parent identity/true point support composition')
    htext=(MODEL/'middle_butterfly.py').read_text('utf-8-sig')
    ck('self.mix = nn.Linear(2 * channels, 2 * channels)' in htext and 'self.activation = nn.GELU()' in htext and 'features.detach()' not in htext and 'pair_input = torch.cat((state.index_select(0, left),' in htext and htext.index('mixed = self.activation(self.mix(pair_input))')<htext.index('state = state.index_copy(0, left') and '.index_copy_' not in htext,'one shared2C→2C/GELU and all paired outputs computed before functional two-sided writes; features not detached')
    ck(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='nn' for n in ast.walk(cls(tree,'ParentButterflyTokenComposition')))==2,'helper registers only one Linear and GELU, no extra readout/gate/residual/parameters')
    for c in ('ThreeLayerMLP','CrossAttentionLayer','SelfAttentionLayer','FFN','MLP','Decoder_layer','DEC'):
        ck(dump(cls(dec,c))==dump(cls(bd,c)),'original decoder '+c+' AST exact')
    ck(dump(method(dec,'Encoder_layer','__init__'))==dump(method(bd,'Encoder_layer','__init__')),'original Encoder constructor including RNG consumers unchanged')
    dectext=(MODEL/'dec.py').read_text('utf-8-sig')
    ck(dectext.count('self.cluster_att.middle_positions = self.cluster_bank.middle_positions')==1 and dectext.count('inst_feats = inst_feats +')==1,'one current-bank cache transfer and original single inst feature update path')
    for p in MODEL.glob('*.py'):compile(parse(p),str(p),'exec')
    ck('torch' not in sys.modules and not any(k.startswith('torch.') for k in sys.modules),'no torch/model/module import, framework Tensor or native/GPU execution in audit')
    report={'schema_version':1,'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'mdc_review','candidate_id':CID,'experiment_id':EXP,'status':'ACTUAL_STDLIB_PRODUCTION_TOPOLOGY_FORWARD_LIST_STUB_AND_STATIC_INTEGRATION_VALIDATED_NATIVE_NOT_RUN','material_concerns':[],
      'preparation':ref(PREP/'preparation.json'),'code_commit':None,'base_reference_commit':'11a811618179ab1ddc0cee299194667413b7fdb9','staged_source_hashes':source9,
      'source_files':{k.removeprefix('staged_repository/'):v for k,v in source9.items()},
      'executable_proof':{'audit_script':ref(Path(__file__)),'actual_python_argv':[sys.executable,'-B',str(Path(__file__)), '--preparation-sha',args.preparation_sha],'actual_functions_extracted':['build_butterfly_plan','ParentButterflyTokenComposition.forward'],'source':ref(helper),'model_torch_imported':False,'framework_Tensor_or_native_execution':False,'actual_invocation_complete':True,'actual_stdout_verdict':'Printed only after all assertions and report write completed; caller process rc0 independently observable.'},
      'actual_stdlib_cases':{'every_valid_n':{'range':[0,128],'cases':len(valid),'coverage':valid},'meaningful_special_cases':special,'multi_batch_cases':1,'empty_batch_cases':1,'invalid_plan_cases_refused':refused,'comparison':'Actual extracted production pure function and exact forward body with only scalar/list-value functional index-select/copy stubs. Compared to independent block-partition matching and simultaneous plain-list two-output toy-map oracle, not copied XOR construction. No actual GELU, parameter math, CUDA/Tensor/autograd behavior inferred.','per_round_row_ownership':'All pairs disjoint; both outputs consume same old-stage states; unmatched rows retain old state. Not strict-own-exclusive context.','potential_reachability':'Each supported final node graph reaches all original same-parent supported IDs and no other parent/unsupported/padding IDs; not proof of nonzero learned weights, injectivity, entropy or task usefulness.','bound':'n65..128 tests general helper contract with explicit max>=n; current native middleK64 does not instantiate these sizes. Native tensor edgecase coverage is UNKNOWN.'},
      'integration_review':{'original5copied_sources_exact':True,'originalYAML_exact':True,'original_raw_partition_bank_CSORT_HCG_AST_preserved':True,'middle_original_skip_retained':True,'new_module_registered':'one shared nn.Linear(2C,2C) + original nn.GELU','original_middle_FFN_removed':'nn.Identity after original3FFN/3LN constructor sequence','common_RNG':'Local fork_rng CPU constructor design only; actual full common parameters/buffers/loader/CUDA RNG pairing NOT_RUN; random-sequence reuse correlation not ruled out.','grad_graph':'Source features remain undetached and paired outputs use functional index_copy. List stubs do not prove Tensor/autograd/nonzero gradient behavior.','single_inst_path_preserved':True,'parameter_inference':{'new_operator':262656,'old_middle_FFN':525568,'delta':-262912,'expected_total_model':157221178,'expected_named_tensors':845,'actual_inventory':'NOT_RUN'}},
      'future_native_protocol':{'status':'NOT_RUN','fixed_originalTRAIN2_required':True,'actual_nonpower2_n3_multistage_required':True,'four_W_quadrant_finite_nonzero_original_loss_gradients_and_slice_updates_required':True,'missing_coverage':'INCONCLUSIVE_NO_RESAMPLE_OR_AUXILIARY_BACKWARD','same_resource_protocol_and_common_batch_pairing_required':True,'FLOPs_latency_VRAM_efficacy':'UNKNOWN'},
      'independent_logical_checks_passed':len(checks),'check_labels':checks,'limits':['This proof is source/static/stdlib control flow only, not native Tensor/device/FP32/GELU/autograd/registered inventory or resource/accuracy PASS.','Zero-map degeneration used a list surrogate, not actual learned operator; no synthetic native claim.','No literature novelty or whole-history equivalence proof; nearest-route scope stays in frozen research_boundary_and_protocol.json.','No current GPU/process/queue/ledger/Git/source mutation performed; protected BTC0/BCR1/M206 pause remain outside this audit.'],
      'next_action':'Root may bind this reviewed frozen9 for ordinary isolated local versioning while preserving public primary11a/index28/protected runs. Actual native pair/resources and canonical admission remain separate future gates.'}
    out=TICK/'bfc_topology_review.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(out),'sha256':sha(out),'material_concerns':[],'valid_n_cases':129,'special_cases':22,'invalid_refusals':16,'logical_checks':len(checks),'torch_imported':False},ensure_ascii=False))
if __name__=='__main__':main()
