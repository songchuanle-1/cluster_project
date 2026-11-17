"""Independent frozen CTS source/production-plan/forward list-stub audit, no Torch."""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import argparse,ast,datetime,hashlib,json,math,sys,csv,re
ROOT=Path('D:/project/cluster_project')
TICK=ROOT/'pipeline/diagnostic_bundles/tick_3824d9c9'
PREP=TICK/'new_candidate_prepare'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=PREP/'staged_repository/framework/model/Quard_model'/(NAME+'_cts')
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
CID='hierarchy-parent-cyclic-triadic-state-composition'
EXP='M214-CTS'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text('utf-8-sig'))
ref=lambda p:{'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
dump=lambda n:ast.dump(n,include_attributes=False)
parse=lambda p:ast.parse(Path(p).read_text('utf-8-sig'))
checks=[]
def ck(x,label):
    assert x,label
    checks.append(label)
def cls(t,n):return next(v for v in t.body if isinstance(v,ast.ClassDef) and v.name==n)
def method(t,c,n):return next(v for v in cls(t,c).body if isinstance(v,ast.FunctionDef) and v.name==n)
def depth(n):
    k=0;digits=n-1
    while digits>0:k+=1;digits//=3
    return k
def oracle(centers,parents,supported):
    groups=[]
    for parent in sorted(set(parents[i] for i,v in enumerate(supported) if v)):
        order=sorted([i for i,v in enumerate(supported) if v and parents[i]==parent],key=lambda i:tuple(centers[i])+(i,))
        offsets=[3**i for i in range(depth(len(order)))]
        groups.append((parent,order,offsets))
    rounds=[]
    for r in range(max([len(o) for _,_,o in groups]+[0])):
        rows=[]
        for parent,order,offsets in groups:
            if r>=len(offsets):continue
            d=offsets[r];plus=order[d:]+order[:d];minus=order[-d:]+order[:-d]
            for own,p,m in zip(order,plus,minus):
                p=None if p==own else p;m=None if m in (own,p) else m
                rows.append((parent,d,own,p,m))
        rounds.append(rows)
    return groups,rounds
def audit_plan(plan,centers,parents,supported,slots):
    groups,rounds=oracle(centers,parents,supported)
    assert [(g['parent'],list(g['order']),list(g['offsets'])) for g in plan['groups']]==groups
    assert [list(rows) for rows in plan['rounds']]==rounds
    assert list(plan['singleton_ids'])==[o[0] for _,o,_ in groups if len(o)==1]
    active={i for i,v in enumerate(supported) if v};states={i:{i} for i in active}
    zero_slots=0
    for rows in plan['rounds']:
        old=deepcopy(states);new=deepcopy(states);outputs=[]
        for parent,d,own,plus,minus in rows:
            ids=[i for i in (own,plus,minus) if i is not None]
            assert len(ids)==len(set(ids)) and all(i in active and parents[i]==parent for i in ids)
            new[own]=set().union(*(old[i] for i in ids));outputs.append(own)
            zero_slots+=(plus is None)+(minus is None)
        assert len(outputs)==len(set(outputs))
        assert all(new[i]==old[i] for i in active-set(outputs))
        states=new
    for parent,order,offsets in groups:
        n=len(order);k=len(offsets)
        assert all(states[i]==set(order) for i in order)
        assert n<=1 or 3**(k-1)<n<=3**k
    return groups,rounds,sum(len(r) for r in rounds),zero_slots
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

def triadmap(row,c=2):
    own,plus,minus=row[:c],row[c:2*c],row[2*c:]
    return [own[i]+2*plus[i]-3*minus[i]+i+1 for i in range(c)]
def nonlinearity(v):return v*v/(1+abs(v))
class Mix:
    def __init__(self,zero=False):self.calls=[];self.zero=zero
    def __call__(self,value):
        self.calls.append(deepcopy(value.data));c=value.shape[1]//3
        return ListValue([[0.0]*c if self.zero else triadmap(row,c) for row in value.data],device=value.device,shape=(value.shape[0],c))
class Activation:
    def __init__(self):self.calls=[]
    def __call__(self,value):
        self.calls.append(deepcopy(value.data))
        return ListValue([[nonlinearity(x) for x in row] for row in value.data],device=value.device,shape=value.shape)
def forward_oracle(features,centers,parents,supported,zero=False):
    groups,rounds=oracle(centers,parents,supported);state=deepcopy(features);c=2
    for rows in rounds:
        old=deepcopy(state);new=deepcopy(state)
        for parent,d,own,plus,minus in rows:
            values=old[own]+(old[plus] if plus is not None else [0.0]*c)+(old[minus] if minus is not None else [0.0]*c)
            new[own]=[0.0]*c if zero else [nonlinearity(x) for x in triadmap(values,c)]
        state=new
    for _,ids,_ in groups:
        if len(ids)==1:state[ids[0]]=[0.0]*c if zero else [nonlinearity(x) for x in triadmap(features[ids[0]]+[0.0]*(2*c),c)]
    return [state[i] if i<len(supported) and supported[i] else [0.0]*c for i in range(len(features))]
def main():
    arg=argparse.ArgumentParser();arg.add_argument('--preparation-sha',required=True);args=arg.parse_args()
    ck(sha(PREP/'preparation.json')==args.preparation_sha=='bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e','final source preparation exact external SHA')
    prep=read(PREP/'preparation.json');source9={k:v for k,v in prep['prepared_file_hashes'].items() if k.startswith('staged_repository/')}
    ck(len(prep['prepared_file_hashes'])==14 and all((PREP/k).resolve().is_relative_to(PREP.resolve()) and sha(PREP/k)==v for k,v in prep['prepared_file_hashes'].items()),'all14 frozen map paths/hash exact')
    ck(len(source9)==9 and sum(k.endswith('.py') for k in source9)==8 and sum(k.endswith('.yaml') for k in source9)==1,'exact8 independent source files plus nativeYAML')
    ck(prep['code_commit'] is None and prep['source_commit'] is None and prep['future_version_parent'] is None and prep['source_Git_version']=='NOT_CREATED','source/code/futureparent null; packaging deferred not falsely bound to BFC48fc')
    helper=MODEL/'middle_triad.py';at=parse(helper);function=next(n for n in at.body if isinstance(n,ast.FunctionDef) and n.name=='build_triadic_plan')
    ns={'math':math};exec(compile(ast.Module(body=[function],type_ignores=[]),str(helper)+':production_plan','exec'),ns);production=ns['build_triadic_plan']
    fnode=method(at,'ParentCyclicTriadicStateComposition','forward');space=dict(ns,torch=ListTorch());exec(compile(ast.Module(body=[fnode],type_ignores=[]),str(helper)+':forward_list_surrogate','exec'),space);forward=space['forward']
    def case(centers,parents,support,slots,zero=False):
        original=deepcopy((centers,parents,support));plan=production(centers,parents,support,slots);groups,rounds,rows,zero_slots=audit_plan(plan,centers,parents,support,slots)
        features=[[float(i+1),-(i+2)/3] for i in range(slots)];fv=ListValue([features],shape=(1,slots,2));mix=Mix(zero);act=Activation()
        obj=SimpleNamespace(channels=2,max_middle_tokens=slots,mix=mix,activation=act)
        output=forward(obj,fv,[ListValue(centers,shape=(len(parents),3))],[ListValue(parents,'long')],[ListValue(support,'bool')])
        assert output.shape==(1,slots,2) and output.data==[forward_oracle(features,centers,parents,support,zero)]
        assert fv.data==[features] and original==(centers,parents,support)
        assert len(mix.calls)==len(act.calls)==len(rounds)+(1 if plan['singleton_ids'] else 0)
        assert sum(len(v) for v in mix.calls)==rows+len(plan['singleton_ids'])
        return {'supported':sum(support),'groups':len(groups),'rounds':len(rounds),'receiver_rows':rows,'singleton_rows':len(plan['singleton_ids']),'private_zero_donor_slots':zero_slots,'slots':slots}
    valid=[]
    for n in range(129):
        valid.append({'n':n,**case([[float(i%5),float((n-i)%7),float(i%3)] for i in range(n)],[42]*n,[True]*n,n+3)})
    ck(len(valid)==129,'actual extracted production plan and actual forward list-surrogate for every n0..128')
    special=[]
    for n in (1,2,3,4,5,6,8,9,13,18,54,64,65,128):
        special.append({'case':'coordinate_ties_original_ID_and_alias_boundary','n':n,**case([[0.,0.,0.]]*n,[7]*n,[True]*n,n+2)})
    pp=[5]*2+[9]*6+[42]+[7]*5+[99]*3;cc=[[float((i*7)%11),float(i%3),0.] for i in range(len(pp))]
    special.append({'case':'mixed_parent2_6_alias_and_singleton_1_and_multiround','n':len(pp),**case(cc,pp,[True]*len(pp),22)})
    pp=[11 if i%3==0 else 3 if i%3==1 else 99 for i in range(24)];cc=[[float((i*7)%11),float(i%3),0.] for i in range(24)];vv=[i not in (0,4,6,8,15,18,22) for i in range(24)]
    special.append({'case':'sparse_true_support_holes_multiparent_padding',**case(cc,pp,vv,29)})
    special.append({'case':'all_unsupported_internal_and_padding',**case(cc,pp,[False]*24,29)})
    for n in (0,1,2,3,5,6,18,64):
        special.append({'case':'zero_map_delta0_source_skip_degenerate','n':n,**case([[float(i),0.,0.] for i in range(n)],[0]*n,[True]*n,n+2,True)})
    ck(len(special)==25,'actual production helper/forward25 meaningful alias/tie/support/parent/padding/zero-map cases executed')
    # Multi-batch scalar/list control.
    v1=[[1.,2.],[3.,4.],[5.,6.],[7.,8.],[9.,10.]];v2=list(reversed(v1));c1=[[3.,0.,0.],[1.,0.,0.],[2.,0.,0.]];c2=[[1.,0.,0.],[1.,0.,0.],[0.,0.,0.],[5.,0.,0.]]
    fv=ListValue([v1,v2],shape=(2,5,2));obj=SimpleNamespace(channels=2,max_middle_tokens=5,mix=Mix(),activation=Activation())
    output=forward(obj,fv,[ListValue(c1,shape=(3,3)),ListValue(c2,shape=(4,3))],[ListValue([9,9,9],'long'),ListValue([6,6,7,7],'long')],[ListValue([True]*3,'bool'),ListValue([True,False,True,True],'bool')])
    ck(output.data==[forward_oracle(v1,c1,[9]*3,[True]*3),forward_oracle(v2,c2,[6,6,7,7],[True,False,True,True])] and fv.data==[v1,v2],'actual forward multi-batch isolation/order/zero-slot/original-ID values match independent oracle')
    empty=forward(SimpleNamespace(channels=2,max_middle_tokens=5,mix=Mix(),activation=Activation()),ListValue([],shape=(0,5,2)),[],[],[])
    ck(empty.shape==(0,5,2) and empty.data==[],'actual forward zero-batch Python branch executed with list-value surrogate')
    invalid=[('maxbool',[[0.,0.,0.]],[0],[True],True),('maxnegative',[],[],[],-1),('maxfloat',[],[],[],1.0),('maxprefix',[[0.,0.,0.]],[0],[True],0),('coords_short',[],[0],[True],1),('support_short',[[0.,0.,0.]],[0],[],1),('coord_dim2',[[0.,0.]],[0],[True],1),('coord_dim4',[[0.,0.,0.,0.]],[0],[True],1),('coord_nan',[[float('nan'),0.,0.]],[0],[True],1),('coord_inf',[[0.,float('inf'),0.]],[0],[True],1),('coord_bool',[[False,0.,0.]],[0],[True],1),('coord_string',[['0',0.,0.]],[0],[True],1),('parent_negative',[[0.,0.,0.]],[-1],[True],1),('parent_float',[[0.,0.,0.]],[0.0],[True],1),('parent_bool',[[0.,0.,0.]],[True],[True],1),('support_int',[[0.,0.,0.]],[0],[1],1)]
    rejected=[]
    for label,centers,parents,support,slots in invalid:
        try:production(centers,parents,support,slots)
        except (ValueError,TypeError):rejected.append(label)
        else:raise AssertionError('Invalid metadata accepted:'+label)
    ck(len(rejected)==16,'actual production helper16 distinct invalid scalar contract cases refused')
    # Inference-only dense channel MAC upper bound for any partition of at most64 supported middle IDs.
    work=[0]+[valid[n]['receiver_rows']+valid[n]['singleton_rows'] for n in range(1,65)]
    dp=[0]*65
    for total in range(1,65):dp[total]=max(work[n]+dp[total-n] for n in range(1,total+1))
    ck(dp[64]==256 and valid[64]['rounds']==4,'independent finite partition DP nativeK64 receiver-row upperbound256/fourrounds, inference not profiling')
    hp=parse(MODEL/'hier_postprocess.py');bh=parse(BASE/'hier_postprocess.py');dec=parse(MODEL/'dec.py');bd=parse(BASE/'dec.py')
    for name in ('__init__.py','backbone.py','loss.py','network.py','sample_model.py'):ck((MODEL/name).read_bytes()==(BASE/name).read_bytes(),'original copied '+name+' byte exact')
    cfg=next(k for k in source9 if k.endswith('.yaml'))
    ck((PREP/cfg).read_bytes()==(ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml')).read_bytes(),'original nativeYAML exact bytecopy, no config tuning')
    for name in ('C2F_ClusterAttn_Lite','C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT'):ck(dump(cls(hp,name))==dump(cls(bh,name)),'whole original '+name+' AST unchanged')
    for cl,met in [('PointCloudPartitioner','partition_points'),('PointCloudPartitioner','cluster_layer'),('SharedClusterBank','build_cluster_feats')]:ck(dump(method(hp,cl,met))==dump(method(bh,cl,met)),'original '+cl+'.'+met+' AST unchanged')
    oldinit=method(bh,'C2F_ClusterAttn_CTF','__init__');newinit=method(hp,'C2F_ClusterAttn_CTF','__init__')
    ck([dump(x) for x in newinit.body[:len(oldinit.body)]]==[dump(x) for x in oldinit.body],'complete original3FFN/3LN constructor statement order remains before new operator')
    htext=(MODEL/'hier_postprocess.py').read_text('utf-8-sig');helpertext=helper.read_text('utf-8-sig')
    ck('self.cluster_ffn[1] = nn.Identity()' in htext and 'with torch.random.fork_rng(devices=[]):' in htext and 'self.middle_triad = ParentCyclicTriadicStateComposition(d_model, self.cluster_layer_nums[1])' in htext and 'refined = cf + self.middle_triad(' in htext,'registered replacement/CPUfork/original middle cfskip; no extra residual')
    ck('per_layer_coords[2]' in htext and 'self.partitioner.middle_parent_ids is not self.cluster_ids_list[2]' in htext and 'point_to_mid = ids1[ids0]' in htext and 'torch.bincount(point_to_mid, minlength=Kmid) > 0' in htext,'true-support/current-original-ID cache semantics retained')
    ck('self.mix = nn.Linear(3 * channels, channels)' in helpertext and 'self.activation = nn.GELU()' in helpertext and 'features.detach()' not in helpertext and '.index_copy_' not in helpertext and helpertext.index('mixed = self.activation(self.mix(torch.cat(fields, dim=-1)))')<helpertext.index('state = state.index_copy(0, own_ids, mixed)'),'one shared3C→C/GELU, all OLD-state fields before write, no detached feature path or in-place scatter')
    ck(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='nn' for n in ast.walk(cls(at,'ParentCyclicTriadicStateComposition')))==2,'helper registers only one Linear/GELU, no additional gate/QKV/readout/newparameters')
    for name in ('ThreeLayerMLP','CrossAttentionLayer','SelfAttentionLayer','FFN','MLP','Decoder_layer','DEC'):ck(dump(cls(dec,name))==dump(cls(bd,name)),'original decoder '+name+' AST unchanged')
    ck(dump(method(dec,'Encoder_layer','__init__'))==dump(method(bd,'Encoder_layer','__init__')),'original Encoder constructor RNG consumers unchanged')
    dectext=(MODEL/'dec.py').read_text('utf-8-sig');ck(dectext.count('self.cluster_att.middle_positions = self.cluster_bank.middle_positions')==1 and dectext.count('inst_feats = inst_feats +')==1,'current cache transfer and original one inst update unchanged')
    for path in MODEL.glob('*.py'):compile(parse(path),str(path),'exec')
    ck('torch' not in sys.modules and not any(k.startswith('torch.') for k in sys.modules),'no framework torch/model imports, tensors, GPU or autograd in independent invocation')
    pat=re.compile(r'triad|dilat|cyclic|ternary|(^|[^a-z])ring([^a-z]|$)|circular|stencil|conv1d',re.I)
    selectedhits=[]
    for row in read(ROOT/'pipeline/research_work.json')['candidates']:
        projected={k:row.get(k) for k in ('id','experiment_id','stage','title','mechanism','mechanism_scope') if row.get(k) is not None}
        if any(pat.search(str(v)) for v in projected.values()):selectedhits.append(projected)
    with (ROOT/'pipeline/experiments.csv').open(encoding='utf-8-sig',newline='') as stream:
        csvhits=[{'id':row['id'],'config':row['config']} for row in csv.DictReader(stream) if pat.search(row['id']) or pat.search(row['config'])]
    protocol=PREP/'native_protocol.md'
    report={'schema_version':1,'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'mdc_review','candidate_id':CID,'experiment_id':EXP,'status':'CTS_FROZEN_SOURCE_AND_ACTUAL_STDLIB_TOPOLOGY_FORWARD_LIST_STUB_INDEPENDENTLY_VALIDATED_NATIVE_NOT_RUN','material_concerns':[],'preparation':ref(PREP/'preparation.json'),'code_commit':None,'source_commit':None,'future_version_parent':None,'base_reference_commit':prep['base_reference_commit'],'version_status':'DEFERRED_NOT_CREATED','staged_source_hashes':source9,'source_files':{k.removeprefix('staged_repository/'):v for k,v in source9.items()},'closest_scope':ref(TICK/'triadic_neighbor_boundary_review.json'),'native_protocol':ref(protocol),
      'executable_proof':{'audit_script':ref(Path(__file__)),'actual_python_argv':[sys.executable,'-B',str(Path(__file__)),'--preparation-sha',args.preparation_sha],'actual_extracted_functions':['build_triadic_plan','ParentCyclicTriadicStateComposition.forward'],'source':ref(helper),'actual_invocation_complete':True,'torch_imported':False,'framework_Tensor_or_native_execution':False,'scope':'Actual pure production function and forward Python control flow with scalar/list functional gather/index_copy and deliberately asymmetric toy3-input map/nonlinearity; no actual torch Tensor/GELU/parameter/FP32/autograd evidence.'},
      'actual_stdlib_cases':{'every_valid_n':{'range':[0,128],'cases':valid},'valid_n_count':129,'special_cases':special,'special_count':25,'multibatch_cases':1,'zero_batch_cases':1,'invalid_scalar_refusals':rejected,'invalid_count':16,'independent_oracle':'Rotated ordered-ID lists and integer base3 digit-depth oracle, distinct real own/+/- sources, synchronous old-state support propagation and independent plain-list numeric toy-map reference. No production modulo-loop copy reused in oracle.','all_final_parent_reachability':True,'unique_receivers_per_round':True,'overlapping_input_donors_allowed':True,'same_row_alias_replaced_by_private_zero':True,'cross_parent_or_unsupported_or_padding_sources':False,'limit':'Potential source graph coverage only; alln65..128 are helper generality tests beyond nativeK64. No learned nonzero-dependency/injectivity/task usefulness claim.'},
      'static_integration':{'frozen8source_originalYAML_exact':True,'5_original_copied_sources_exact':True,'original_partition_rawbank_CSORT_HCG_classes_AST_unchanged':True,'original_skip_LN_finecoarse_and_one_inst_path_retained':True,'common_constructor':'Original3FFN/3LN created in original sequence, then middleFFN Identity; only new operator inside CPU fork_rng. Pairing/loader/full-buffer/CUDA RNG behavior UNKNOWN; random stream reuse correlations not ruled out.','no_new_gate_QKV_language_route_residual_or_injection':True,'feature_graph':'Undetached original features and functional gather/scatter in source; list surrogate cannot prove actual Tensor/autograd behavior.','inferred_parameters':{'new':196864,'old_middle_FFN':525568,'delta':-328704,'full_model_expected':157155386,'named_parameter_tensors_expected':845,'actual_inventory':'NOT_RUN'}},
      'inferred_cost_only':{'native_middle_cap':64,'max_receiver_rows_including_singleton_boundary':dp[64],'max_global_rounds':4,'any_partition_DP':dp,'C':256,'denseLinear_MAC_per_row':3*256*256,'denseLinear_MAC_upperbound_per_one_hierarchy_batch':dp[64]*3*256*256,'old_middleFFN_denseLinear_MAC_for64':64*8*256*256,'upperbound_delta_denseMAC':dp[64]*3*256*256-64*8*256*256,'scope':'Source/finite-DP bound under original denseLinear MAC convention only, not total model FLOPs/profile or native measurement; excludes CPU sort/tolist/gather/synchronization/activation etc. Actual original protocol10G/medianP90/VRAM conditions still require a real same-input pair.'},
      'bounded_closest_scope_search':{'fields':['id','experiment_id','stage','title','mechanism','mechanism_scope'],'CSV_fields':['id','config'],'patterns':['triad','dilat','cyclic','ternary','ring','circular','stencil','conv1d'],'actual_selected_metadata_hits':selectedhits,'actual_CSV_hits':csvhits,'limit':'Finite declaration search, not all historical source or literature novelty proof. Explicit dense3tap dilated circular Conv1D-family; M205 one-hop sector-depthwise and BFC disjoint-pair differences only as scoped798a. BFC already fullparent; no new-coverage/causality/accuracy claim, no old hold/branch reopened.'},
      'future_native_protocol':{'original_TRAIN2_seed_YAML_pretrain_loader':True,'actual_3_distinct_real_inputs_multiround_dilation_r_ge1_required':True,'original_loss_gradient_and_update_blocks':['W_own','W_plus','W_minus'],'all3_blocks_each_step_finite_nonzero_plus_slice_update':True,'per_call_or_row_zero_gradients':'LEGAL when hook records finite; no blanket nonzero requirement','alias_zero_singleton_padding':'Record real counts; if absent NOT_EXERCISED, not a new mandatory native sample gate.','missing_frozen_path_coverage':'INCONCLUSIVE_NO_RESAMPLE_NO_EXTRA_AUXILIARY_BACKWARD','common_initialization_and_batch_pairing':'Future actual measurement required; no full-state/RNG equality inferred fromfork','native_Tensor_autograd_FP32':'NOT_RUN','resources':'NOT_RUN','efficacy':'UNKNOWN'},
      'independent_logical_checks_passed':len(checks),'check_labels':checks,'author_static_evidence':{'path':'static_validation.json','sha256':sha(PREP/'static_validation.json'),'author_assertions':264384,'interpretation':'Author own scalar/source assertions, not264384 experiments; preserved and not rerun here.'},
      'limits':['No Git version created or future main parent selected. Base11a is a reference only, not a fabricated CTS source commit or requirement to create a sibling of waitingBFC48fc.','No actual tensor/device/precision/GELU/gradient/resource/accuracy tested; semantic effects remain unknown.','Original BFC actual native has priority if a card naturally frees; no current GPU query, queue/process/shared/source/Git writes.','Only this external review/script written; original frozen package and old hold/proofs untouched.'],
      'next_action':'Root may register the one actually source-tested CTS reserve with explicit version-packaging/native/resource pending. Keep public main and both actual runs/M206 pause untouched; choose real future source parent only when compatible actual native readiness exists. Later native validation and admission remain independent.'}
    output=TICK/'cts_topology_review.json';assert not output.exists();output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(output),'sha256':sha(output),'material_concerns':[],'valid_n_cases':129,'special_cases':25,'invalid_refusals':16,'logical_checks':len(checks),'native_actual':'NOT_RUN','code_commit':None},ensure_ascii=False))
if __name__=='__main__':main()
