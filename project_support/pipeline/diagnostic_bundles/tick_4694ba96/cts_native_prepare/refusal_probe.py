"""Local stdlib-only disabled entry refusal probe. No remote/native execution."""
import builtins,json,runpy,sys
from pathlib import Path
here=Path(__file__).resolve().parent
name=sys.argv[1]
assert name in ('worker.py','native_runtime.py')
seen=[]
original_import=builtins.__import__
def guarded_import(module,*args,**kwargs):
    if module.split('.')[0] in {'torch','fcntl','pynvml','numpy','gorilla','yaml'}:
        seen.append({'forbidden_import':module});raise AssertionError('Forbidden pre-refusal import '+module)
    return original_import(module,*args,**kwargs)
def audit(event,args):
    if event in ('subprocess.Popen','socket.connect','socket.bind'):
        seen.append({'forbidden_event':event});raise AssertionError(event)
    if event=='open':
        value=str(args[0])
        if 'native_manifest.json' in value or 'execution_lease' in value:
            seen.append({'forbidden_open':value});raise AssertionError('No execution materials may be opened')
builtins.__import__=guarded_import
sys.addaudithook(audit)
sys.path.insert(0,str(here))
try:
    runpy.run_path(str(here/name),run_name='__main__')
except RuntimeError as exc:
    assert str(exc)=='CTS native preparation is execution-disabled; a fresh reviewed operational bundle and lease are required'
    assert seen==[] and 'torch' not in sys.modules
    print(json.dumps({'entry':name,'refused':True,'message':str(exc),'forbidden_events':seen,'torch_imported':False}))
else:raise AssertionError('Disabled entry did not refuse')
