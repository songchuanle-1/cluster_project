"""Small isolated CRE orchestration metadata checks; not native or old suites."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,contextlib,copy,hashlib,importlib.util,io,json,sys,tempfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];BASE=ROOT/'pipeline/diagnostic_bundles/tick_05f6addd/aef_operational_prepare'
checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.__new__','socket.connect','socket.bind','socket.getaddrinfo'):raise AssertionError('No actual process/network action: '+event)
 if event=='import' and args and str(args[0]).split('.')[0]=='torch':raise AssertionError('No Torch')
def funcs(source):
 out={}
 def visit(nodes,prefix=''):
  for n in nodes:
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):out[prefix+n.name]=ast.dump(n,include_attributes=False)
   elif isinstance(n,ast.ClassDef):visit(n.body,prefix+n.name+'.')
 visit(ast.parse(source).body);return out

def main():
 sys.addaudithook(audit)
 for name in ('adapter.py','remote_ops.py'):
  source=(HERE/name).read_text('utf8');compile(source,str(HERE/name),'exec');ck('compile_'+name,True)
  original=(BASE/name).read_text('utf8').replace('hierarchy-parent-antisymmetric-edge-flux','hierarchy-cross-root-directed-edge-broadcast').replace('56b2a96dc48cc8a88f0f7105527ef448113b1060','7ed9373db335d44c884133da3eced3fca03ad29a').replace('M216-AEF','M217-CRE').replace('AEF','CRE').replace('aef','cre')
  ck('all_function_AST_exact_after_only_namespace_literals_'+name,funcs(original)==funcs(source))
 spec=importlib.util.spec_from_file_location('isolated_cre_adapter',HERE/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 ck('CRE_source_runtime_currentGPU0',m.CANDIDATE=='hierarchy-cross-root-directed-edge-broadcast' and m.COMMIT=='7ed9373db335d44c884133da3eced3fca03ad29a' and m.EXPECTED_RUNTIME_COMMIT=='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563' and set(m.GPU_UUIDS)=={0})
 ck('actual_native_final_SHA_binding',isinstance(m.PREPARATION_SHA,str) and len(m.PREPARATION_SHA)==64 and isinstance(m.TEMPLATE_SHA,str) and len(m.TEMPLATE_SHA)==64 and sha(m.FROZEN/'preparation.json')==m.PREPARATION_SHA and sha(m.FROZEN/'manifest_template.json')==m.TEMPLATE_SHA)
 prep=json.loads((m.FROZEN/'preparation.json').read_text('utf8'));template=json.loads((m.FROZEN/'manifest_template.json').read_text('utf8'))
 ck('native_exact_CRE_version',prep['candidate_id']==m.CANDIDATE and prep['source_commit']==m.COMMIT and template['candidate_id']==m.CANDIDATE and template['code_commit']==m.COMMIT)
 ck('ten_execution_fields_null',all(template[k] is None for k in ['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']))
 class NoTransport:
  calls=0
  def call(self,*args,**kwargs):self.calls+=1;raise AssertionError('No transport expected')
 transport=NoTransport()
 with tempfile.TemporaryDirectory(prefix='cre_metadata_',dir=HERE) as tmp:
  r=Path(tmp);(r/'pipeline').mkdir();a=m.Adapter(root=r,origin=r,frozen=m.FROZEN,transport=transport)
  for method in ('probe','prepare'):
   for gpu in (1,False):
    try:getattr(a,method)(gpu)
    except m.Refused:ck(method+'_reject_'+repr(gpu)+'_before_guard',True)
    else:raise AssertionError('Invalid physicalGPU admitted')
  try:a._release_details()
  except m.Refused:ck('missing_static_release_refused_before_other_metadata',True)
  else:raise AssertionError('Missing static release admitted')
  import yaml
  (r/'SERVERS.yaml').write_text(yaml.safe_dump({'servers':{'server-4':{'allowed_gpus':[0]}}}),encoding='utf8')
  (r/'pipeline/running.json').write_text(json.dumps({'server-4':{'0':'M215-BEC'}}),encoding='utf8')
  try:a._local_idle(0)
  except m.Refused:ck('registered_BEC_busy_refuses_before_transport',True)
  else:raise AssertionError('Busy0 admitted')
  auth={'path':'software.json','sha256':'0'*64};candidate={'id':m.CANDIDATE,'experiment_id':'M217-CRE','code_commit':m.COMMIT,'goal_sha256':m.GOAL,'authorization':auth,'config':'cre_software','stage':'validation'};a._frozen_details=lambda:({}, {'config':'cre_software'})
  (r/'pipeline/research_work.json').write_text(json.dumps({'candidates':[candidate]}),encoding='utf8');a._candidate_ready(auth);ck('new_CRE_without_revision_eligible_schema',True)
  candidate['revision_history']=[{'revision':1}];(r/'pipeline/research_work.json').write_text(json.dumps({'candidates':[candidate]}),encoding='utf8')
  try:a._candidate_ready(auth)
  except m.Refused:ck('foreign_BEC_R1_or_other_revision_branch_not_inherited',True)
  else:raise AssertionError('Foreign revision admitted')
 ck('zero_actual_transport',transport.calls==0)
 ck('no_active_or_production_release',not any((HERE/n).exists() for n in ['adapter_release.json','native_manifest.json','execution_binding.json','execution_lease.json']))
 ck('Torch_not_imported','torch' not in sys.modules)
 report={'status':'SMALL_CRE_METADATA_AST_REFUSAL_SOFTWARE_CHECKS_PASSED_NOT_NATIVE','recorded_at':datetime.now(timezone.utc).isoformat(),'checks_count':len(checks),'checks':checks,'source_hashes':{n:sha(HERE/n) for n in ['adapter.py','remote_ops.py']},'scope':'Only compile/AST/import and isolated temporary metadata/invalid-GPU methods with NoTransport. No actual project guard or adapter entry, process/network/Torch/Git/SSH/GPU/native/shared action. Not old33/38/41/61/98 suites.','actual_execution':'NOT_RUN','material_concerns':[]}
 out=HERE/'metadata_validation.json'
 with out.open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'checks':len(checks),'report':str(out),'sha256':sha(out),'actual_execution':'NOT_RUN'}))
if __name__=='__main__':main()
