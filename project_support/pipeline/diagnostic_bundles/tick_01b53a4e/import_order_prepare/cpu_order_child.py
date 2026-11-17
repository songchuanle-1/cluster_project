"""One fixed CPU import-order condition, no model/data/CUDA setup."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys,json,hashlib,marshal,importlib,importlib.metadata,builtins,socket
from pathlib import Path
from datetime import datetime,timezone
import sre_compile

assert socket.gethostname()=='dl04-MS-7E06'
assert sys.executable=='/home/songcl/.conda/envs/project_cluster/bin/python'
CONDITION=sys.argv[1]
assert CONDITION in ('PCCM_FIRST','GORILLA_FIRST')
ROOT='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
REFERENCE_STAGE='/data/songcl/Project/Cluster_project/pipeline/cre_0f02aaa2_gpu0'
EXPERIMENT=Path('/data/songcl/Project/Cluster_project/pipeline/import_order_01b53a4e')
PRIVATE=Path(os.environ['IMPORT_ORDER_PRIVATE']).resolve()
assert PRIVATE==EXPERIMENT/CONDITION and PRIVATE.is_dir()
os.chdir(ROOT)
sys.path[:]=[ROOT,ROOT+'/framework/lib',REFERENCE_STAGE]+[p for p in sys.path if p not in ('',ROOT,ROOT+'/framework/lib',REFERENCE_STAGE)]
WHITELIST=('PYTHONPATH','PYTHONPYCACHEPREFIX','TORCH_COMPILE_DISABLE','TORCHDYNAMO_DISABLE','PYDEVD_USE_FRAME_EVAL')
def describe(value):
    try:representation=repr(value)
    except BaseException:representation='<repr unavailable>'
    return {'type':type(value).__module__+'.'+type(value).__qualname__,'callable':callable(value),'repr':representation[:600]}
def code_info(code):
    return {'filename':code.co_filename,'name':code.co_name,'firstlineno':code.co_firstlineno,
        'bytecode_sha256':hashlib.sha256(code.co_code).hexdigest(),'marshal_sha256':hashlib.sha256(marshal.dumps(code)).hexdigest(),
        'varnames':list(code.co_varnames),'names':list(code.co_names)}
def snapshot():
    loaded=sre_compile._compile.__code__;compiled=compile(Path(sre_compile.__file__).read_bytes(),sre_compile.__file__,'exec',dont_inherit=True,optimize=sys.flags.optimize)
    disk=None
    for constant in compiled.co_consts:
        if isinstance(constant,type(loaded)) and constant.co_name=='_compile':disk=constant;break
    assert disk is not None
    torch=sys.modules.get('torch');cuda=getattr(torch,'cuda',None);initialized=getattr(cuda,'is_initialized',None)
    observed_environment={}
    for key in WHITELIST:observed_environment[key]=os.environ.get(key)
    return {'torch_imported':torch is not None,'pccm_imported':'pccm' in sys.modules,'gorilla_imported':'gorilla' in sys.modules,
        'cuda_is_initialized':bool(initialized()) if callable(initialized) else 'CUDA_MODULE_NOT_READY',
        'sys_gettrace':describe(sys.gettrace()),'sys_getprofile':describe(sys.getprofile()),'sys_flags':repr(sys.flags),
        'whitelisted_environment':observed_environment,
        'builtin_len':describe(builtins.len),'sre_module_len':describe(sre_compile.__dict__['len']) if 'len' in sre_compile.__dict__ else {'state':'ABSENT'},
        'sre_compile_code':code_info(loaded),'disk_compiled_sre_code':code_info(disk),
        'loaded_vs_disk':{'code':loaded.co_code==disk.co_code,'varnames':loaded.co_varnames==disk.co_varnames,'names':loaded.co_names==disk.co_names,'marshal':marshal.dumps(loaded)==marshal.dumps(disk)}}
def exception_frames(error):
    rows=[];tb=error.__traceback__
    while tb is not None:
        frame=tb.tb_frame;entry={'filename':frame.f_code.co_filename,'function':frame.f_code.co_name,'lineno':tb.tb_lineno,
            'lasti':frame.f_lasti,'bytecode_sha256':hashlib.sha256(frame.f_code.co_code).hexdigest()}
        if frame.f_code.co_filename.endswith(('sre_compile.py','lark/visitors.py')):
            entry['selected_locals']={}
            for key in ('_len','self','x'):
                if key in frame.f_locals:entry['selected_locals'][key]=describe(frame.f_locals[key])
            entry['frame_global_len']=describe(frame.f_globals['len']) if 'len' in frame.f_globals else {'state':'ABSENT'}
            entry['frame_builtin_len']=describe(frame.f_builtins.get('len'))
        rows.append(entry);tb=tb.tb_next
    return rows

# A single generic private-directory write policy; no per-failure fence expansion.
write_events=[];helper_events=[];denials=[]
def resolved_path(value,dir_fd=None):
    if isinstance(value,int):
        target=os.readlink('/proc/self/fd/'+str(value))
        if target.endswith(' (deleted)'):target=target[:-10]
        return Path(target).resolve()
    path=Path(os.fsdecode(value))
    if not path.is_absolute() and dir_fd not in (None,-1):path=Path(os.readlink('/proc/self/fd/'+str(dir_fd)))/path
    return path.resolve()
def allowed_path(path):return path==PRIVATE or path.is_relative_to(PRIVATE)
def require_private(event,path):
    if not allowed_path(path):
        denials.append({'event':event,'path':str(path)});raise RuntimeError('PRIVATE_IMPORT_DIRECTORY_POLICY_REFUSED')
    if len(write_events)<60:write_events.append({'event':event,'path':str(path)})
def audit(event,args):
    if event=='open':
        mode=args[1];flags=args[2];write=False
        if isinstance(mode,str):
            for ch in mode:
                if ch=='w' or ch=='a' or ch=='x' or ch=='+':write=True
        if isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):write=True
        if write:
            path=resolved_path(args[0])
            if path==Path('/dev/null'):return
            require_private(event,path)
    elif event in ('os.remove','os.rmdir','os.mkdir','os.chmod','os.chown','os.utime','os.truncate'):
        position={'os.remove':1,'os.rmdir':1,'os.mkdir':2,'os.chmod':2,'os.chown':3,'os.utime':3}.get(event)
        fd=args[position] if position is not None and len(args)>position else None
        require_private(event,resolved_path(args[0],fd))
    elif event in ('os.rename','os.link'):
        require_private(event,resolved_path(args[0],args[2]));require_private(event,resolved_path(args[1],args[3]))
    elif event=='os.symlink':
        destination=resolved_path(args[1],args[2]);source=Path(os.fsdecode(args[0]))
        if not source.is_absolute():source=destination.parent/source
        require_private(event,source.resolve());require_private(event,destination)
    elif event in ('subprocess.Popen','os.posix_spawn'):
        executable=args[0];argv=args[1]
        if executable in ('uname','/bin/uname','/usr/bin/uname') and isinstance(argv,(tuple,list)) and len(argv)==2 and argv[0] in ('uname','/bin/uname','/usr/bin/uname') and argv[1]=='-p':
            helper_events.append({'event':event,'command':'uname -p'});return
        denials.append({'event':event,'executable':str(executable),'argv':repr(argv)[:400]});raise RuntimeError('NO_BUILD_INSTALL_OR_OTHER_CHILD_IN_CPU_IMPORT_CONTROL')
    elif event in ('os.system','socket.connect','socket.getaddrinfo'):
        denials.append({'event':event});raise RuntimeError('NO_NETWORK_OR_SHELL_IN_CPU_IMPORT_CONTROL')
sys.addaudithook(audit)

report={'condition':CONDITION,'started_at':datetime.now(timezone.utc).isoformat(),'python':sys.executable,'python_version':sys.version,
    'root':ROOT,'sys_path':list(sys.path),'private_directory':str(PRIVATE),'process_cache_paths':{'TMPDIR':os.environ.get('TMPDIR'),'MPLCONFIGDIR':os.environ.get('MPLCONFIGDIR'),'XDG_CACHE_HOME':os.environ.get('XDG_CACHE_HOME'),'XDG_CONFIG_HOME':os.environ.get('XDG_CONFIG_HOME')},
    'fixed_CPU_control_hashseed':'1999 on both conditions; process-only control, not a native model/loader seed modification or sweep',
    'initial':snapshot(),'phases':[],'private_write_events':write_events,'readonly_platform_helpers':helper_events,'policy_denials':denials,
    'model_instances':0,'native_forwards':0,'optimizer_steps':0,'dataset_or_checkpoint_loaded':False,'native_PASS':False}
modules={}
def complete_pccm():
    modules['pccm']=importlib.import_module('pccm')
    parsers=importlib.import_module('pccm.core.parsers')
    source=Path(parsers.__file__);parser=parsers._ARG_WITH_ATTR_PARSER;transformer=parser.options.transformer
    report['actual_original_parser']={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'grammar_sha256':hashlib.sha256(parsers._ARG_WITH_ATTR_GRAMMAR.encode()).hexdigest(),
        'parser':parser.options.parser,'start':parser.options.start,
        'transformer_type':type(transformer).__module__+'.'+type(transformer).__qualname__,
        'real_AttrArgTransformer_instance':isinstance(transformer,parsers.AttrArgTransformer),
        'manual_constructor_kwargs_omitted':False}
    assert report['actual_original_parser']['source_sha256']=='e004988c79f7d48a24d0ba66c8e5b600503815643275bf12beb430ca17ee491e'
    assert report['actual_original_parser']['real_AttrArgTransformer_instance']
def gorilla_import():modules['gorilla']=importlib.import_module('gorilla')
def torch_import():modules['torch']=importlib.import_module('torch')
if CONDITION=='PCCM_FIRST':steps=[('complete_original_pccm_and_real_transformer',complete_pccm),('gorilla',gorilla_import),('torch_explicit',torch_import)]
else:steps=[('gorilla',gorilla_import),('torch_explicit',torch_import),('complete_original_pccm_and_real_transformer',complete_pccm)]
index=0
while index<3:
    step=steps[index];item={'name':step[0],'before':snapshot()};report['phases'].append(item)
    try:step[1]()
    except BaseException as error:
        item.update(status='FAILED',error_type=type(error).__name__,error=str(error))
        try:item['exception_frames']=exception_frames(error)
        except BaseException as capture_error:item['collector_error']=type(capture_error).__name__+': '+str(capture_error)
        try:item['after']=snapshot()
        except BaseException as capture_error:item['snapshot_error']=type(capture_error).__name__+': '+str(capture_error)
        report['status']='CPU_IMPORT_ORDER_CONDITION_INCONCLUSIVE_POLICY' if denials else 'CPU_IMPORT_ORDER_CONDITION_FAILED'
        break
    item['status']='PASSED';item['after']=snapshot()
    if item['after']['cuda_is_initialized'] is True:
        report['status']='CPU_ONLY_SCOPE_VIOLATION_CUDA_INITIALIZED';break
    index+=1
if index==3:report['status']='COMPLETE_PCCM_REAL_TRANSFORMER_AND_GORILLA_TORCH_CPU_IMPORT_PASSED'
try:report['final']=snapshot()
except BaseException as capture_error:report['final_snapshot_error']=type(capture_error).__name__+': '+str(capture_error)
report['scope']='Fresh CPU process, original full pccm import including real AttrArgTransformer; fixed two-order control only. No tools.train/M95 model construction/full native equivalence, no CUDA setup, data or checkpoint. Private cache paths and fixed startup hashseed are explicit diagnostic conditions. Callbacks/compile switches only observed, never changed.'
print('IMPORT_ORDER_RESULT='+json.dumps(report,ensure_ascii=False,allow_nan=False),flush=True)
