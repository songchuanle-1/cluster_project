"""One upstream pure-Lark constructor control; no torch, model, build or cache write."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import os,sys,json,ast,hashlib,importlib.metadata
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
path=Path('/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/pccm/core/parsers.py')
source=path.read_bytes();tree=ast.parse(source);grammar=None;kwargs=None
versions={}
for name in ['lark','lark-parser','pccm','spconv','torch','numpy']:
 try:versions[name]=importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError:versions[name]='NOT_INSTALLED_AS_THIS_DISTRIBUTION_NAME'
out={'python':sys.executable,'python_version':sys.version,'versions':versions,'pccm_parser_source':str(path),'pccm_parser_source_sha256':hashlib.sha256(source).hexdigest(),'torch_imported':False,'model_or_data_loaded':False,'GPU_queries_or_work':False,'library_or_cache_mutation':False,'status':'PREPARING_FIXED_PACKAGE_GRAMMAR_CONTROL'}
for node in tree.body:
 if isinstance(node,ast.Assign):
  names=[x.id for x in node.targets if isinstance(x,ast.Name)]
  if '_ARG_WITH_ATTR_GRAMMAR' in names:grammar=ast.literal_eval(node.value)
  if '_ARG_WITH_ATTR_PARSER' in names:
   call=node.value;assert isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='Lark'
   assert len(call.args)==1 and isinstance(call.args[0],ast.Name) and call.args[0].id=='_ARG_WITH_ATTR_GRAMMAR'
   kwargs={};omitted={}
   for keyword in call.keywords:
    try:kwargs[keyword.arg]=ast.literal_eval(keyword.value)
    except (ValueError,TypeError):omitted[keyword.arg]=ast.dump(keyword.value)
   assert set(omitted)=={'transformer'},'Only the native user-transformer object may be omitted from this grammar compilation control'
   out['original_constructor_line']=node.lineno;out['omitted_native_constructor_kwargs']=omitted
   out['scope_difference']='Original package grammar and literal parser options only. Native user-transformer construction is omitted; no parse or full pccm import equivalence is claimed.'
assert isinstance(grammar,str) and isinstance(kwargs,dict)
assert kwargs.get('cache',False) is False,'No grammar-cache writes authorized'
out.update(original_constructor_kwargs=kwargs,grammar_sha256=hashlib.sha256(grammar.encode()).hexdigest(),grammar_length=len(grammar))
print('LARK_ONLY_CONTROL_INITIAL='+json.dumps(out),flush=True)
try:
 import lark
 from lark import Lark
 out['lark_module']=lark.__file__
 parser=Lark(grammar,**kwargs)
 out.update(status='ORIGINAL_GRAMMAR_WITHOUT_USER_TRANSFORMER_LARK_CONSTRUCTION_PASSED_WITHOUT_TORCH',parser_type=type(parser).__module__+'.'+type(parser).__qualname__)
except BaseException as error:
 out.update(status='ORIGINAL_GRAMMAR_WITHOUT_USER_TRANSFORMER_LARK_CONSTRUCTION_FAILED_WITHOUT_TORCH',error_type=type(error).__name__,error=str(error))
 frames=[];tb=error.__traceback__
 while tb is not None:
  frames.append({'file':tb.tb_frame.f_code.co_filename,'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno});tb=tb.tb_next
 out['exception_frames']=frames
out['torch_imported']='torch' in sys.modules
print('LARK_ONLY_CONTROL_RESULT='+json.dumps(out),flush=True)
'''
def main():
    guard();assert not (HERE/'lark_only_control_r1_intent.json').exists() and not (HERE/'lark_only_control_r1_result.json').exists(),'No replay'
    with (HERE/'lark_only_control_r1_intent.json').open('x',encoding='utf8') as f:json.dump({'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'purpose':'Single original pccm grammar constructor without importing torch/pccm/model; isolate upstream dependency chain. No native PASS or code/cache fix.'},f,ensure_ascii=False,indent=2);f.write('\n')
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/home/songcl/.conda/envs/project_cluster/bin/python -B -'],input=PROGRAM,capture_output=True,text=True,encoding='utf8',timeout=30)
    markers=[line.removeprefix('LARK_ONLY_CONTROL_RESULT=') for line in r.stdout.splitlines() if line.startswith('LARK_ONLY_CONTROL_RESULT=')]
    out={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'returncode':r.returncode,'observation':json.loads(markers[0]) if len(markers)==1 else None,'stdout':r.stdout,'stderr':r.stderr,'native_PASS':False}
    guard()
    with (HERE/'lark_only_control_r1_result.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'returncode':r.returncode,'observation':out['observation'],'stderr':r.stderr[-1200:],'sha256':sha(HERE/'lark_only_control_r1_result.json')},ensure_ascii=False))
if __name__=='__main__':main()
