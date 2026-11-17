"""One fresh CPU-only import diagnosis. No model construction or native forward."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import sys,json,hashlib,marshal,builtins,importlib
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
            frames.append({'lineno':tb.tb_lineno,'lasti':frame.f_lasti,'bytecode_window_hex':frame.f_code.co_code[max(0,frame.f_lasti-10):frame.f_lasti+14].hex(),'code':code_info(frame.f_code),
                'local__len':describe(loc['_len']) if '_len' in loc else {'state':'ABSENT'},
                'local__len_is_code_list':loc.get('_len') is loc.get('code'),
                'local__len_is_pattern':loc.get('_len') is loc.get('pattern'),
                'frame_global_len':describe(frame.f_globals['len']) if 'len' in frame.f_globals else {'state':'ABSENT'},
                'frame_builtin_len':describe(frame.f_builtins.get('len')),
                'code_list_type':describe(loc.get('code')),'pattern_type':describe(loc.get('pattern'))})
        tb=tb.tb_next
    return frames
# Compile exact source to a fresh code object at each sample, never execute/replace it.
def fresh_disk_function_code():
    disk_module_code=compile(Path(sre_compile.__file__).read_bytes(),sre_compile.__file__,'exec',dont_inherit=True,optimize=sys.flags.optimize)
    for constant in disk_module_code.co_consts:
        if isinstance(constant,type(sre_compile._compile.__code__)) and constant.co_name=='_compile':
            return constant
    raise RuntimeError('Exact disk _compile code object absent')
original_snapshot=snapshot
def snapshot():
    out=original_snapshot();loaded=sre_compile._compile.__code__;disk_function_code=fresh_disk_function_code()
    out['disk_compiled_function_code']=code_info(disk_function_code)
    out['loaded_vs_disk_compiled']={'same_co_code':loaded.co_code==disk_function_code.co_code,'same_varnames':loaded.co_varnames==disk_function_code.co_varnames,'same_names':loaded.co_names==disk_function_code.co_names,'same_marshal_sha256':sha_bytes(marshal.dumps(loaded))==sha_bytes(marshal.dumps(disk_function_code))}
    return out
events=[];allowed_readonly_events=[]
def readonly_audit(event,args):
    if event=='open':
        mode=args[1];flags=args[2]
        write=False
        if isinstance(mode,str):
            for character in mode:
                if character=='w' or character=='a' or character=='x' or character=='+':write=True
        if isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):write=True
        if write:
            if str(args[0])=='/dev/null' and isinstance(flags,int) and not(flags & (os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                allowed_readonly_events.append({'event':event,'scope':'/dev/null only, no persistent file write','mode':mode,'flags':flags});return
            events.append({'event':event,'path':str(args[0])[:600]});raise RuntimeError('CPU_DIAGNOSTIC_READONLY_FENCE_WRITE')
    if event=='subprocess.Popen':
        executable=args[0];argv=args[1];cwd=args[2];env=args[3]
        if executable in ('uname','/bin/uname','/usr/bin/uname') and isinstance(argv,(list,tuple)) and len(argv)==2 and argv[0] in ('uname','/bin/uname','/usr/bin/uname') and argv[1]=='-p' and cwd is None and env is None:
            allowed_readonly_events.append({'event':event,'scope':'Exact read-only uname -p, no shell/build/model invocation','executable':executable,'argv':list(argv)});return
    if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','os.remove','os.rename','os.mkdir'):
        events.append({'event':event,'arguments':repr(args)[:800]});raise RuntimeError('CPU_DIAGNOSTIC_READONLY_FENCE_PROCESS_NETWORK_OR_WRITE')
sys.addaudithook(readonly_audit)
report={'status':'CPU_IMPORT_DIAGNOSTIC_IN_PROGRESS','observed_at':datetime.now(timezone.utc).isoformat(),
    'python':sys.executable,'hostname':socket.gethostname(),'root':ROOT,'sys_path':list(sys.path),
    'runtime_config':CONFIG,'runtime_config_sha256':sha_bytes(Path(CONFIG).read_bytes()),
    'sre_compile_path':sre_compile.__file__,'sre_compile_source_sha256':sha_bytes(Path(sre_compile.__file__).read_bytes()),
    'initial':snapshot(),'stages':[],'read_only_fence_events':events,'explicit_allowed_readonly_events':allowed_readonly_events,'original_native_forward_count':0,
    'model_instantiations':0,'optimizer_steps':0,'checkpoint_or_dataset_loaded':False,'CUDA_setup_deliberately_omitted':True,
    'GPU_queries_or_signals':False,'native_PASS':False}
def emit(label,value):
    sys.stdout.write(label+'='+json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');sys.stdout.flush()
# Emit the initial code comparison before importing train/torch, so it survives a collector fault.
emit('CRE_CPU_IMPORT_INITIAL',report['initial'])
def stage(name,action):
    item={'name':name,'before':snapshot()};report['stages'].append(item)
    emit('CRE_CPU_IMPORT_STAGE_BEGIN',{'name':name,'before':item['before']})
    try:action()
    except BaseException as error:
        # Preserve original failure frames FIRST; do not call traceback/linecache/regex formatting.
        item['status']='FAILED';item['error_type']=type(error).__name__;item['error']=str(error)
        report['status']='CPU_IMPORT_DIAGNOSTIC_FAILED_AT_STAGE';report['failed_stage']=name
        try:item['sre_compile_failure_frames']=traceback_frames(error)
        except BaseException as collector_error:item['frame_collector_error']={'type':type(collector_error).__name__,'message':str(collector_error)}
        try:item['after']=snapshot()
        except BaseException as collector_error:item['snapshot_collector_error']={'type':type(collector_error).__name__,'message':str(collector_error)}
        emit('CRE_CPU_IMPORT_FAILED_STAGE',item)
        return False
    item['status']='PASSED';item['after']=snapshot()
    assert item['after']['cuda_is_initialized'] in (False,'TORCH_NOT_IMPORTED')
    emit('CRE_CPU_IMPORT_STAGE_PASSED',{'name':name,'after':item['after']})
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
stages=[('import_tools_train_and_original_imports',import_native_prefix),('original_runtime_yaml_Config_fromfile',config_from_exact_file),('original_gorilla_seed1999',original_seed),('original_M95_module_and_natural_spconv_import',original_m95_import)]
index=0
while index<4:
    entry=stages[index]
    if not stage(entry[0],entry[1]):break
    index+=1
if index==4:report['status']='ALL_CPU_IMPORT_STAGES_PASSED_CUDA_SETUP_OMITTED_NOT_NATIVE_PASS'
try:report['final']=snapshot()
except BaseException as collector_error:report['final_snapshot_collector_error']={'type':type(collector_error).__name__,'message':str(collector_error)}
report['limitations']='This omits torch.cuda.set_per_process_memory_fraction/CUDA initialization and never constructs a model. Passing does not explain or repair the original failed GPU-worker import and is not native/resource evidence. Read-only fence permits only /dev/null RW and exact uname -p (platform discovery), no other child/build/write/network; other blocked actions are separately reported. Disk-source compile is code-object-only, not execution or a replacement.'
emit('CRE_CPU_IMPORT_DIAGNOSTIC',report)
