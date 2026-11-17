"""One fresh CPU-only import diagnosis. No model construction or native forward."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import sys,json,hashlib,marshal,traceback,builtins,importlib
from pathlib import Path
from datetime import datetime,timezone
import sre_compile

ROOT='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
STAGE='/data/songcl/Project/Cluster_project/pipeline/cre_0f02aaa2_gpu0'
CONFIG=STAGE+'/runtime_config_smoke_champion/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml'
assert sys.executable=='/home/songcl/.conda/envs/project_cluster/bin/python'
os.chdir(ROOT)
sys.path[:]=[ROOT,ROOT+'/framework/lib',STAGE]+[p for p in sys.path if p not in ('',ROOT,ROOT+'/framework/lib',STAGE)]
def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def describe(value):
    try:r=repr(value)
    except BaseException as error:r='<repr failed: '+type(error).__name__+'>'
    return {'type':type(value).__module__+'.'+type(value).__qualname__,'callable':callable(value),'repr':r[:1200]}
def code_info(code):
    return {'name':code.co_name,'filename':code.co_filename,'firstlineno':code.co_firstlineno,
        'varnames':list(code.co_varnames),'bytecode_sha256':sha_bytes(code.co_code),'marshal_sha256':sha_bytes(marshal.dumps(code))}
def snapshot():
    fn=sre_compile._compile;torch=sys.modules.get('torch')
    return {'builtin_len':describe(builtins.len),'module_len':describe(sre_compile.__dict__['len']) if 'len' in sre_compile.__dict__ else {'state':'ABSENT'},
        'compile_function':describe(fn),'compile_code':code_info(fn.__code__),'compile_defaults':describe(fn.__defaults__),
        'cuda_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES'),'cuda_is_initialized':bool(torch.cuda.is_initialized()) if torch is not None else 'TORCH_NOT_IMPORTED'}
def traceback_frames(error):
    frames=[];tb=error.__traceback__
    while tb is not None:
        frame=tb.tb_frame
        if frame.f_code.co_name=='_compile' and frame.f_code.co_filename.endswith('sre_compile.py'):
            loc=frame.f_locals
            frames.append({'lineno':tb.tb_lineno,'code':code_info(frame.f_code),
                'local__len':describe(loc['_len']) if '_len' in loc else {'state':'ABSENT'},
                'local__len_is_code_list':loc.get('_len') is loc.get('code'),
                'local__len_is_pattern':loc.get('_len') is loc.get('pattern'),
                'frame_global_len':describe(frame.f_globals['len']) if 'len' in frame.f_globals else {'state':'ABSENT'},
                'frame_builtin_len':describe(frame.f_builtins.get('len')),
                'code_list_type':describe(loc.get('code')),'pattern_type':describe(loc.get('pattern'))})
        tb=tb.tb_next
    return frames
events=[]
def readonly_audit(event,args):
    if event=='open':
        mode=args[1];flags=args[2]
        write=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if write:
            events.append({'event':event,'path':str(args[0])[:600]});raise RuntimeError('CPU_DIAGNOSTIC_READONLY_FENCE_WRITE')
    if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','os.remove','os.rename','os.mkdir'):
        events.append({'event':event,'arguments':repr(args)[:800]});raise RuntimeError('CPU_DIAGNOSTIC_READONLY_FENCE_PROCESS_NETWORK_OR_WRITE')
sys.addaudithook(readonly_audit)
report={'status':'CPU_IMPORT_DIAGNOSTIC_IN_PROGRESS','observed_at':datetime.now(timezone.utc).isoformat(),
    'python':sys.executable,'hostname':socket.gethostname(),'root':ROOT,'sys_path':list(sys.path),
    'runtime_config':CONFIG,'runtime_config_sha256':sha_bytes(Path(CONFIG).read_bytes()),
    'sre_compile_path':sre_compile.__file__,'sre_compile_source_sha256':sha_bytes(Path(sre_compile.__file__).read_bytes()),
    'initial':snapshot(),'stages':[],'read_only_fence_events':events,'original_native_forward_count':0,
    'model_instantiations':0,'optimizer_steps':0,'checkpoint_or_dataset_loaded':False,'CUDA_setup_deliberately_omitted':True,
    'GPU_queries_or_signals':False,'native_PASS':False}
def stage(name,action):
    item={'name':name,'before':snapshot()};report['stages'].append(item)
    try:action()
    except BaseException as error:
        item.update(status='FAILED',error_type=type(error).__name__,error=str(error),after=snapshot(),
            traceback=traceback.format_exc(),sre_compile_failure_frames=traceback_frames(error))
        report.update(status='CPU_IMPORT_DIAGNOSTIC_FAILED_AT_STAGE',failed_stage=name)
        return False
    item.update(status='PASSED',after=snapshot())
    assert item['after']['cuda_is_initialized'] in (False,'TORCH_NOT_IMPORTED')
    return True
modules={}
def import_native_prefix():
    from tools import train
    import torch,gorilla,yaml
    from framework import resolve_network
    torch.set_num_threads(1)
    modules.update(train=train,torch=torch,gorilla=gorilla,yaml=yaml,resolve_network=resolve_network)
def config_from_exact_file():modules['cfg']=modules['gorilla'].Config.fromfile(CONFIG)
def original_seed():modules['gorilla'].set_random_seed(1999)
def original_m95_import():modules['m95']=importlib.import_module('framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort')
for name,action in [('import_tools_train_and_original_imports',import_native_prefix),('original_runtime_yaml_Config_fromfile',config_from_exact_file),('original_gorilla_seed1999',original_seed),('original_M95_module_and_natural_spconv_import',original_m95_import)]:
    if not stage(name,action):break
else:report['status']='ALL_CPU_IMPORT_STAGES_PASSED_CUDA_SETUP_OMITTED_NOT_NATIVE_PASS'
report['final']=snapshot()
report['limitations']='This omits torch.cuda.set_per_process_memory_fraction/CUDA initialization and never constructs a model. Passing does not explain or repair the original failed GPU-worker import and is not native/resource evidence. Read-only fence may make an import fail earlier if it attempts a child/build/write/network; that is separately reported.'
print('CRE_CPU_IMPORT_DIAGNOSTIC='+json.dumps(report,ensure_ascii=False,allow_nan=False),flush=True)
