"""Stdlib-only execution of HVD production tensor functions with a small shim.

This checks source identity, topology and moment arithmetic. It does not import
Torch, instantiate/train a model, check gradients, load data or measure resources.
"""
from pathlib import Path
import ast, copy, hashlib, json, random
import author_guard as ag
ag.author_guard()
HERE=ag.HERE
ROOT=ag.ROOT
manifest=json.loads((HERE/'source_manifest.json').read_text(encoding='utf-8'))
STAGE=HERE/'staged_repository'
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=STAGE/'framework/model/Quard_model'/(BASE+'_hvd')
OLD=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/new_candidate_prepare/staged_repository/framework/model/Quard_model'/(BASE+'_wfc')
checks=[]
def record(name,condition):
    if not condition: raise AssertionError(name)
    checks.append({'name':name,'passed':True})
def close(a,b):
    return abs(a-b) <= 1e-10 * max(1,abs(a),abs(b))
def equal_rows(a,b):
    return len(a)==len(b) and all(len(x)==len(y) and all(close(u,v) for u,v in zip(x,y)) for x,y in zip(a,b))

class FT:
    def __init__(self,rows):
        self.rows=[list(row) for row in rows]
        self.shape=(len(self.rows),len(self.rows[0]) if self.rows else 0)
    def new_zeros(self,shape): return FT([[0.0]*shape[1] for _ in range(shape[0])])
    def new_ones(self,shape): return FT([[1.0]*shape[1] for _ in range(shape[0])])
    def index_add(self,dim,labels,values):
        assert dim==0 and len(labels)==values.shape[0]
        rows=copy.deepcopy(self.rows)
        for index,src in zip(labels,values.rows):
            for channel,value in enumerate(src): rows[index][channel]+=value
        return FT(rows)
    def index_select(self,dim,labels):
        assert dim==0
        return FT([self.rows[index] for index in labels])
    def clamp_min(self,value):return FT([[max(x,value) for x in row] for row in self.rows])
    def square(self):return FT([[x*x for x in row] for row in self.rows])
    def binary(self,other,fn):
        assert self.shape[0]==other.shape[0]
        return FT([[fn(x,other.rows[i][j if other.shape[1]>1 else 0]) for j,x in enumerate(row)] for i,row in enumerate(self.rows)])
    def __sub__(self,other):return self.binary(other,lambda x,y:x-y)
    def __add__(self,other):return self.binary(other,lambda x,y:x+y)
    def __truediv__(self,other):return self.binary(other,lambda x,y:x/y)
class TorchShim:
    @staticmethod
    def cat(items,dim):
        assert dim==-1
        assert len({x.shape[0] for x in items})==1
        return FT([sum([list(x.rows[row]) for x in items],[]) for row in range(items[0].shape[0])])
    @staticmethod
    def zeros_like(value):return value.new_zeros(value.shape)

helper=(MODEL/'variance_decomposition.py').read_text(encoding='utf-8')
tree=ast.parse(helper)
actual_functions=[node for node in tree.body if isinstance(node,ast.FunctionDef)]
namespace={'torch':TorchShim}
exec(compile(ast.fix_missing_locations(ast.Module(body=actual_functions,type_ignores=[])),str(MODEL/'variance_decomposition.py'),'exec'),namespace)
plan=namespace['build_support_plan']
components=namespace['moment_components']
pack=namespace['pack_moment_rows']
record('all_actual_helper_functions_executed_or_bound',set(n.name for n in actual_functions)=={'build_support_plan','_group_mean','moment_components','pack_moment_rows'})
record('source_manifest_exact_nine',len(manifest['source_files'])==9)
record('model_exact_eight_python',len(list(MODEL.glob('*.py')))==8)
record('all_nine_source_hashes_match',all(ag.sha(STAGE/path)==digest for path,digest in manifest['source_files'].items()))
for path in MODEL.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'))
record('all_eight_python_sources_parse',True)
record('six_baseline_files_byte_exact',all((MODEL/name).read_bytes()==(OLD/name).read_bytes() for name in ('__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py')))
record('original_yaml_byte_exact',ag.sha(STAGE/manifest['config'])=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
record('source_and_parent_versions_remain_null',all(manifest[k] is None for k in ('code_commit','source_commit','source_parent_commit','actual_parent','future_version_parent')))
original=(ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/lft_candidate_prepare/original_m95_hier_postprocess.py.txt').read_text(encoding='utf-8')
old_tree=ast.parse(original)
new_tree=ast.parse((MODEL/'hier_postprocess.py').read_text(encoding='utf-8'))
def class_map(parsed):return {node.name:node for node in parsed.body if isinstance(node,ast.ClassDef)}
old_classes,new_classes=class_map(old_tree),class_map(new_tree)
record('all_non_ctf_classes_ast_identical',all(ast.dump(old_classes[name])==ast.dump(new_classes[name]) for name in old_classes if name!='C2F_ClusterAttn_CTF'))
record('all_module_functions_ast_identical',[ast.dump(n) for n in old_tree.body if isinstance(n,ast.FunctionDef)]==[ast.dump(n) for n in new_tree.body if isinstance(n,ast.FunctionDef)])
old_init=next(n for n in old_classes['C2F_ClusterAttn_CTF'].body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
new_init=next(n for n in new_classes['C2F_ClusterAttn_CTF'].body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
record('original_constructor_rng_prefix_preserved',[ast.dump(n) for n in old_init.body]==[ast.dump(n) for n in new_init.body[:len(old_init.body)]])
record('new_core_constructor_uses_cpu_fork_rng','with torch.random.fork_rng(devices=[]):' in ast.get_source_segment((MODEL/'hier_postprocess.py').read_text(encoding='utf-8'),new_init))
record('no_helper_query_or_child_map_dependence',not any(isinstance(n,ast.Name) and n.id in {'query','child_cluster_maps'} for n in ast.walk(tree)))
record('no_new_softmax_gates_dropout_or_attention',not any(isinstance(n,ast.Attribute) and n.attr in {'softmax','sigmoid','Dropout','MultiheadAttention'} for n in ast.walk(tree)))
record('no_new_dense_point_pair_operator',not any(isinstance(n,ast.Attribute) and n.attr in {'cdist','matmul','einsum','bmm'} for n in ast.walk(tree)))
p=plan([3,0,3],[1,99,99,3],[99,2,99,0],3,[5,5,4])
record('actual_plan_ignores_unsupported_holes',p=={'nodes':[[0,3],[1,3],[0,2]],'point_to_fine':[1,0,1],'fine_to_middle':[0,1],'middle_to_coarse':[1,0]})
record('actual_plan_empty_scene',plan([],[],[],0,[0,0,0])=={'nodes':[[],[],[]],'point_to_fine':[],'fine_to_middle':[],'middle_to_coarse':[]})
invalid_cases=[([-1],[0],[0],1,[1,1,1]),([1],[0],[0],1,[1,1,1]),([0],[],[0],1,[1,1,1]),([0],[-1],[0],1,[1,1,1]),([0],[0],[],1,[1,1,1]),([0],[0],[2],1,[1,1,1]),([0],[0],[0],2,[1,1,1]),([True],[0],[0],1,[1,1,1])]
failed=0
for args in invalid_cases:
    try:plan(*args)
    except ValueError:failed+=1
record('actual_plan_rejects_eight_invalid_true_paths',failed==len(invalid_cases))
values=FT([[0.0],[2.0],[4.0],[6.0],[10.0],[14.0],[18.0],[22.0]])
p0=[0,0,1,1,2,2,3,3];p1=[0,0,1,1];p2=[0,0]
s=components(values,p0,p1,p2,4,2,1)
record('fine_variance_actual_source',equal_rows(s[0].rows,[[1],[1],[4],[4]]))
record('middle_within_between_actual_source',equal_rows(s[1].rows,[[1],[4]]) and equal_rows(s[2].rows,[[4],[16]]))
record('coarse_within_between_actual_source',equal_rows(s[3].rows,[[12.5]]) and equal_rows(s[4].rows,[[42.25]]))
rows=pack([FT([[10],[20],[30],[40]]),FT([[50],[60]]),FT([[70]])],s,p1,p2)
record('actual_fine_topdown_pack',equal_rows(rows[0].rows,[[10,1,4,42.25],[20,1,4,42.25],[30,4,16,42.25],[40,4,16,42.25]]))
record('actual_middle_and_coarse_pack',equal_rows(rows[1].rows,[[50,1,4,42.25],[60,4,16,42.25]]) and equal_rows(rows[2].rows,[[70,12.5,42.25,0]]))
constant=components(FT([[7],[7],[7],[7]]),[0,0,1,1],[0,0],[0],2,1,1)
record('constant_features_zero_moments',all(all(x==0 for row in tensor.rows for x in row) for tensor in constant))
uneven=components(FT([[0],[0],[0],[4]]),[0,0,0,1],[0,0],[0],2,1,1)
record('higher_levels_use_equal_children_not_point_mass',equal_rows(uneven[2].rows,[[4]]))
a=components(FT([[-1],[1],[3],[5]]),[0,0,1,1],[0,0],[0],2,1,1)
b=components(FT([[0],[0],[4],[4]]),[0,0,1,1],[0,0],[0],2,1,1)
record('same_fine_means_different_native_dispersion_distinguishable',a[0].rows!=b[0].rows and a[2].rows==b[2].rows)
# Independent oracle: enumerate each root's hierarchical equal-child point law.
rr=random.Random(1999)
for trial in range(5):
    point_labels=[0,0,1,2,2,2,3,4,4]; fine_labels=[0,0,1,2,2]; mid_labels=[0,0,1]
    points=FT([[rr.uniform(-3,3),rr.uniform(-3,3)] for _ in point_labels])
    stats=components(points,point_labels,fine_labels,mid_labels,5,3,2)
    for root in range(2):
        mids=[i for i,x in enumerate(mid_labels) if x==root]
        weighted=[]
        for mid in mids:
            fines=[i for i,x in enumerate(fine_labels) if x==mid]
            for fine in fines:
                pp=[i for i,x in enumerate(point_labels) if x==fine]
                for index in pp: weighted.append((points.rows[index],1/len(mids)/len(fines)/len(pp)))
        for channel in range(2):
            mu=sum(row[channel]*weight for row,weight in weighted)
            variance=sum((row[channel]-mu)**2*weight for row,weight in weighted)
            assert close(variance,stats[3].rows[root][channel]+stats[4].rows[root][channel])
record('five_multichannel_cases_match_direct_hierarchical_distribution_oracle',True)
permutation=[8,3,0,7,4,2,6,1,5]
original_points=FT([[float(i),float(i*i)] for i in range(9)])
original_stats=components(original_points,point_labels,fine_labels,mid_labels,5,3,2)
permuted_stats=components(FT([original_points.rows[i] for i in permutation]),[point_labels[i] for i in permutation],fine_labels,mid_labels,5,3,2)
record('valid_point_permutation_equivariance_actual_source',all(equal_rows(x.rows,y.rows) for x,y in zip(original_stats,permuted_stats)))
record('genuine_zero_features_keep_topological_support',plan([0,1],[0,0],[0],2,[2,1,1])['nodes']==[[0,1],[0],[0]])
result={'schema_version':1,'candidate_id':manifest['candidate_id'],'experiment_id':manifest['experiment_id'],
 'test_kind':'stdlib_source_identity_topology_and_production_tensor_functions_with_small_shim',
 'torch_imported':False,'model_instantiated':False,'native_data_loaded':False,
 'native_backward':'NOT_RUN','full_forward':'NOT_RUN','resources':'NOT_RUN','efficacy':'UNKNOWN','novelty':'UNKNOWN',
 'production_helper_sha256':ag.sha(MODEL/'variance_decomposition.py'),
 'check_count':len(checks),'checks':checks,'passed':True,
 'limitations':'The small tensor shim checks the actual production statistic/packing functions in ordinary arithmetic; it supplies no Torch, autograd, device, AMP, full-model, resource or efficacy evidence.'}
ag.write_json(HERE/'static_validation.json',result)
print(json.dumps({'passed':True,'check_count':len(checks),'result_sha256':ag.sha(HERE/'static_validation.json')}))
