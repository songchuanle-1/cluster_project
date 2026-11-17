"""Real source AST, stdlib plan, hook-stub and disabled-entry checks only."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import math
import subprocess
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/project/cluster_project')
OLD = ROOT/'pipeline/diagnostic_bundles/tick_7dcc29e8/btc_operational_prepare/native'
SOURCE = HERE.parent/'new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr'
checks = {}
worker_text = (HERE/'worker.py').read_text(encoding='utf-8')
runtime_text = (HERE/'native_runtime.py').read_text(encoding='utf-8')
worker = ast.parse(worker_text)
runtime = ast.parse(runtime_text)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def same_function(tree, previous, name):
    return ast.dump(function(tree, name), include_attributes=False) == ast.dump(function(previous, name), include_attributes=False)


for path in (HERE/'worker.py', HERE/'native_runtime.py'):
    compile(path.read_text(encoding='utf-8'), str(path), 'exec')
checks['actual_two_sources_compile_without_import'] = True
previous_worker = ast.parse((OLD/'worker.py').read_text(encoding='utf-8'))
previous_runtime = ast.parse((OLD/'native_runtime.py').read_text(encoding='utf-8'))
checks['resources_complete_AST_exact_original_BTC_PSNC_protocol'] = same_function(worker, previous_worker, 'resources')
checks['seven_runtime_functions_AST_exact_original'] = all(same_function(runtime, previous_runtime, n) for n in ('sha', 'verify', 'observe', 'acquire', 'release', 'fingerprint', 'save'))
checks['runtime_early_disabled_real_source_bound_no_active_execution'] = all(s in runtime_text for s in ('DRAFT_EXECUTION_DISABLED = True', "CANDIDATE_COMMIT = '11a811618179ab1ddc0cee299194667413b7fdb9'", "SOURCE_PREPARATION_SHA256 = 'faf3494d13c5026b21e1d235dab311cc4f9a9d88b9653c4726a5ccbdc8958615'")) and runtime_text.index('require_promoted_version()\n') < runtime_text.index('import fcntl') < runtime_text.index("MANIFEST =")
checks['BCR_exact_identity_GPU0_parent00e_and_prefix'] = all(s in runtime_text for s in ('hierarchy-parent-bidirectional-complement-recurrence', 'M212-BCR', 'ctf_hcg_csort_bcr', "STAGE.name == 'bcr_'", 'PHYSICAL_GPU == 0', "version['parent_commit'] == '00e2b18c6b8d568a64edb496e6979d766440883c'"))
checks['main_acquire_before_native_setup_and_original_TRAIN2'] = worker_text.index("result['before']=acquire(args.lease)") < worker_text.index('torch,gorilla,cfg,model,qualified,train,optimizer,scheduler=setup') and 'train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)' in worker_text and 'torch.autograd.grad(' not in worker_text and 'loss.backward(' not in worker_text
checks['exact_common_exclusions_preserve_middle_LN'] = "excluded = ('dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.middle_complement.')" in worker_text and 'retain middle LayerNorm' in worker_text

# Execute the actual isolated pure plan and worker descriptor functions only.
pure = {'math': math}
source_ast = ast.parse((SOURCE/'middle_complement.py').read_text(encoding='utf-8'))
for tree, name in ((source_ast, 'build_complement_plan'), (worker, 'complement_plan_observation')):
    exec(compile(ast.Module(body=[function(tree, name)], type_ignores=[]), name, 'exec'), pure)
case_sizes = []
for centers, parents, support, width in [
    ([], [], [], 0), ([[0., 0., 0.]], [0], [True], 3),
    ([[1., 0., 0.], [0., 0., 0.]], [0, 0], [True, True], 2),
    ([[2., 0., 0.], [0., 0., 0.], [1., 0., 0.]], [0]*3, [True]*3, 4),
    ([[0., 0., 0.]]*5, [3]*5, [True]*5, 5),
    ([[float(i), 0., 0.] for i in range(7)], [2, 9, 2, 9, 2, 9, 2], [True, True, False, True, True, True, False], 9),
]:
    plan = pure['build_complement_plan'](centers, parents, support, width)
    groups, sequence = pure['complement_plan_observation'](plan)
    case_sizes.append([g['n'] for g in groups])
    for group in groups:
        order = group['order']; parent = group['parent']; actual = [e for e in sequence if e['parent']==parent]
        assert sum(e['map']=='scan' for e in actual)==2*(len(order)-1)
        assert sum(e['map']=='readout' for e in actual)==1
        readout = next(e for e in actual if e['map']=='readout')
        for i, row in enumerate(readout['row_source_ids']):
            assert row == {'own':[order[i]], 'left':sorted(order[:i]), 'right':sorted(order[i+1:])}
        for entry in actual:
            if entry['map']=='scan':
                assert entry['destination'] not in entry['output_source_ids']
checks['six_actual_production_plans_match_observer_descriptor_and_slice_oracle'] = True

# Callback execution uses simple Python vectors/matrices. It is not tensor or autograd testing.
class Tensor:
    def __init__(self, data):
        self.data = copy.deepcopy(data); self.device = 'stub'; self.requires_grad = True
    @property
    def shape(self):
        return (len(self.data), len(self.data[0])) if self.data and isinstance(self.data[0], list) else (len(self.data),)
    def detach(self): return self
    def new_zeros(self, size): return Tensor([0.0]*size)
    def index_select(self, dim, ids):
        assert dim == 0
        return Tensor([self.data[i] for i in ids])
    def __getitem__(self, key):
        if isinstance(key, tuple):
            first, second = key
            if isinstance(first, slice): return Tensor([row[second] for row in self.data[first]])
            return Tensor(self.data[first][second]) if isinstance(second, slice) else Tensor(self.data[first][second])
        return Tensor(self.data[key])


class Features:
    def __init__(self, rows): self.rows=rows
    def new_zeros(self, size): return Tensor([0.0]*size)
    def __getitem__(self, key):
        if isinstance(key, tuple): return Tensor(self.rows[key[0]][key[1]])
        return Tensor(self.rows[key])


class Torch:
    long = 'long'
    @staticmethod
    def tensor(value, **kwargs): return list(value)
    @staticmethod
    def stack(values): return Tensor([x.data for x in values])


def fingerprint(unused, value): return json.dumps(value.data, separators=(',', ':'))
def summary(value): return {'shape':list(value.shape), 'finite':True}
watched=[]
def watch(value, record, key): watched.append(key)
smoke_node = function(worker, 'smoke')
callbacks = {n.name:n for n in ast.walk(smoke_node) if isinstance(n, ast.FunctionDef)}
env={'torch':Torch, 'fingerprint':fingerprint, 'summary':summary, 'watch':watch,
     'att':SimpleNamespace(middle_complement=SimpleNamespace(channels=2)), 'state':{}}
for name in ('expected_piece','map_pre','map_post','activation_post'):
    exec(compile(ast.Module(body=[callbacks[name]],type_ignores=[]),name,'exec'),env)
features=Features([[[1., 2.], [3., 4.], [5., 6.], [7., 8.]]])
plan=pure['build_complement_plan']([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.],[3.,0.,0.]],[0,0,0,1],[True]*4,4)
groups, sequence=pure['complement_plan_observation'](plan)
for entry in sequence: entry['batch']=0
values={}
for group in groups:
    values[(0,group['parent'],'left',group['order'][0])]=None
    values[(0,group['parent'],'right',group['order'][-1])]=None
context={'features':features,'sequence':sequence,'index':0,'values':values,'pending':None,'pending_activation':None,'record':{'map_calls':[]}}
env['state'].update(complement_context=context,forward_index=1)
counter=0
for entry in sequence:
    parent=entry['parent'];kind=entry['map']
    if kind=='scan':
        src=entry['source']; direction=entry['direction']
        previous=values[(0,parent,direction,src)]
        data=features[0,src].data+([0.,0.] if previous is None else previous.data)
        actual_input=Tensor(data)
    else:
        data=[]
        for token in entry['order']:
            row=features[0,token].data
            for direction in ('left','right'):
                value=values[(0,parent,direction,token)]
                row += [0.,0.] if value is None else value.data
            data.append(row)
        actual_input=Tensor(data)
    assert env['map_pre'](kind)(None,(actual_input,)) is None
    counter+=1
    linear=Tensor([10.+counter,20.+counter] if kind=='scan' else [[30.+counter,40.+counter] for _ in entry['order']])
    assert env['map_post'](kind)(None,(actual_input,),linear) is None
    if kind=='scan':
        actual_activation=Tensor([100.+counter,200.+counter])
        assert env['activation_post'](None,(linear,),actual_activation) is None
        stored=values[(0,parent,entry['direction'],entry['destination'])]
        assert stored is actual_activation and stored is not linear
assert context['index']==len(sequence) and context['pending'] is None and context['pending_activation'] is None
assert len(context['record']['map_calls'])==6  # n3:4scan+1readout; n1:1readout
checks['actual_scan_GELU_readout_hooks_stub_source_boundaries_consumed_original_activation'] = True

before_text=ast.unparse(callbacks['before_step']);after_text=ast.unparse(callbacks['after_step'])
checks['five_real_native_parameter_gradient_blocks_and_update_hashes'] = all(x in worker_text for x in ("'scan_token'","'scan_state'","'readout_own'","'readout_left'","'readout_right'")) and 'weight.grad[:, start:end]' in before_text and "info['finite'] and info['abs_max'] > 0" in before_text and "record['parameter_block_before_step_hash'][name] != record['parameter_block_after_step_hash'][name]" in after_text
checks['inconclusive_native_coverage_no_resampling_or_auxiliary_backward'] = all(x in worker_text for x in ('INCONCLUSIVE_COVERAGE', 'actual_depth_ge2_scan_calls', 'no replacement sample/seed', 'not a whole-mechanism rejection'))

# A real local stdlib subprocess reaches the runtime's own disabled error before fcntl/manifest/torch.
refusals=[]
probe="""import json,runpy,sys
sys.path.insert(0,str(__import__('pathlib').Path(sys.argv[1]).parent))
try:
 runpy.run_path(sys.argv[1],run_name='__main__')
except RuntimeError as e:
 assert 'BCR native preparation is execution-disabled' in str(e)
 assert 'torch' not in sys.modules and 'fcntl' not in sys.modules
 print(json.dumps({'own_disabled_error':str(e),'torch_imported':False,'fcntl_imported':False}))
else: raise AssertionError('Disabled draft did not refuse')
"""
for name in ('native_runtime.py','worker.py'):
    done=subprocess.run([sys.executable,'-B','-c',probe,str(HERE/name)],capture_output=True,text=True,encoding='utf-8',timeout=20)
    assert done.returncode==0,(name,done.stdout,done.stderr)
    refusals.append({'entry':name,'returncode':done.returncode,'observation':json.loads(done.stdout)})
checks['two_actual_stdlib_entry_refusals_before_manifest_fcntl_torch'] = True
assert all(checks.values()), checks
result={'schema_version':1,'status':'ACTUAL_AST_STDLIB_HOOK_STUB_AND_DISABLED_ENTRY_CHECKS_PASSED_NATIVE_NOT_RUN',
        'checks':checks,'logical_check_count':len(checks),'production_plan_case_group_sizes':case_sizes,
        'entry_refusals':refusals,'source_hashes':{n:digest(HERE/n) for n in ('worker.py','native_runtime.py')},
        'model_source_hashes':{n:digest(SOURCE/n) for n in ('middle_complement.py','hier_postprocess.py','dec.py')},
        'native_execution':'NOT_RUN','resources':'NOT_RUN','transport':'NOT_RUN',
        'scope':'Real function AST, actual extracted production stdlib plan, Python list/vector callback stubs, and real local stdlib refusal subprocesses only. No local torch/model import, Tensor/autograd/FP32 behavior, native TRAIN, GPU or SSH.',
        'unknowns':['actual native n>=3/depth2 coverage and scan/readout block gradients/updates','real Tensor/device/index/autograd/numerics','batch/common initialization pairing','actual latency/VRAM/FLOPs','efficacy']}
output=HERE/'static_validation.json'
with output.open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'path':str(output),'sha256':digest(output),'logical_checks':len(checks),'source_hashes':result['source_hashes']}))
