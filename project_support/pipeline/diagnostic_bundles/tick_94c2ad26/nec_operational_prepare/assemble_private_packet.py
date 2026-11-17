"""Private child authoring only. Default NOP; not a native or promotion entry."""
import argparse,ast,copy,datetime,hashlib,io,json,os,pathlib,re,tokenize
R=pathlib.Path('D:/project/cluster_project');T=R/'pipeline/diagnostic_bundles/tick_94c2ad26';O=pathlib.Path(__file__).resolve().parent;N=T/'nec_native_prepare';OLD=R/'pipeline/diagnostic_bundles/tick_d94467a9/lft_operational_compatible_prepare'
C='6bc36adfe42764aac2209e6600fb3a783e2fa374';B='4457a46f9075f61e83340aa0f0af87d5bf4e986c';CID='hierarchy-coupled-node-edge-state-composition';EXP='M228-NEC'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
ref=lambda p:{'path':pathlib.Path(p).relative_to(R).as_posix(),'sha256':sha(p)}
def author_guard():
 a=ast.parse((T/'anchor.py').read_text());v={q.targets[0].id:ast.literal_eval(q.value) for q in a.body if isinstance(q,ast.Assign) and len(q.targets)==1 and isinstance(q.targets[0],ast.Name) and q.targets[0].id in ['EXPECTED','CHECKS']};x=v['EXPECTED'];o=read(R/'pipeline/headless/.foreground.lockdir/owner.json');m=read(R/'pipeline/execution_mode.json')
 assert {k:o.get(k) for k in x}==x and m['mode']=='foreground' and m['target_thread_id']==x['thread_id']
 assert os.environ.get('CODEX_THREAD_ID') and os.environ['CODEX_THREAD_ID']!=x['thread_id']
 assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(x['deadline_at'])
 for name,h in v['CHECKS'].items():assert sha(R/name)==h,name
 return x,v['CHECKS']
def write(name,data):
 author_guard();p=O/name;assert p.resolve().is_relative_to(O.resolve())
 with p.open('xb') as f:f.write(data if isinstance(data,bytes) else data.encode('utf-8'));f.flush()
def save(name,value):write(name,json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def port(source,plan):
 mp=dict(plan);rx=re.compile('|'.join(re.escape(k) for k in sorted(mp,key=len,reverse=True)));out=[]
 for q in tokenize.generate_tokens(io.StringIO(source).readline):
  if q.type==tokenize.STRING:
   try:v=ast.literal_eval(q.string)
   except (SyntaxError,ValueError):v=None
   if isinstance(v,str):
    nv=rx.sub(lambda m:mp[m.group()],v)
    if nv!=v:q=tokenize.TokenInfo(q.type,repr(nv),q.start,q.end,q.line)
  out.append(q)
 return tokenize.untokenize(out)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--assemble-private',action='store_true');a=ap.parse_args()
 if not a.assemble_private:print('DEFAULT_NOP_PRIVATE_AUTHOR_NO_ENTRY');return
 owner,checks=author_guard();assert not (O/'preparation.json').exists()
 proof=T/'nec_version_prepare/isolated_source_version.json';pv=read(proof)
 assert sha(proof)=='87453f6c78bf6acf061685f7492b2c25723c23d5d6ed5846ffd364f015807f6c' and pv['code_commit']==C and pv['parent_commit']==B and pv['diff_exact9A'] is True
 native=read(N/'preparation.json');template=read(N/'manifest_template.json')
 assert native['candidate_id']==CID and native['source_commit']==C and native['source_parent_commit']==B and native['draft_execution_disabled'] is True
 assert native['source_files']==pv['frozen_source_files'] and len(native['source_files'])==9
 for name,h in native['prepared_file_hashes'].items():assert sha(N/name)==h,name
 assert native['manifest_template']==ref(N/'manifest_template.json')
 assert all(template[k] is None for k in ['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'])
 old=read(OLD/'preparation.json');assert sha(OLD/'preparation.json')=='94e3583e2e53f2113284bd84970cd93e2a2d41fe0000f1391c3c0ef94666912e'
 for name,h in old['prepared_file_hashes'].items():assert sha(OLD/name)==h,name
 old_parent_config='configs/Quard/ctf_hcg_csort_wfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_wfc.yaml'
 new_parent_config='configs/Quard/ctf_hcg_csort_lft/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft.yaml'
 plan=[('pipeline/diagnostic_bundles/tick_d94467a9/lft_native_compatible_prepare',N.relative_to(R).as_posix()),(old['native_preparation']['sha256'],sha(N/'preparation.json')),(old['native_manifest_template']['sha256'],sha(N/'manifest_template.json')),('hierarchy-nonlinear-lifting-analysis-synthesis',CID),('hierarchy-wedge-factor-incidence-composition','hierarchy-nonlinear-lifting-analysis-synthesis'),('M227-LFT',EXP),('M226-WFC','M227-LFT'),(old_parent_config,new_parent_config),(old['code_commit'],C),(old['expected_runtime_code_commit'],B),('lft_remote_ops','nec_remote_ops'),('lft_execution','nec_execution'),('lft_','nec_'),('_lft','_nec'),('WFC94','LFT4457'),('parent94','parent4457'),('WFC','LFT'),('LFT','NEC')]
 generated={}
 for name in ['adapter.py','remote_ops.py']:
  text=port((OLD/name).read_text(),plan)
  if name=='adapter.py':
   assert text.count('DRAFT_EXECUTION_DISABLED = False')==1
   text=text.replace('DRAFT_EXECUTION_DISABLED = False','DRAFT_EXECUTION_DISABLED = True')
  compile(text,str(O/name),'exec');write(name,text);generated[name]=text
 launcher=port((OLD/'run_lft_operation.py').read_text(),plan)
 old_snapshot="user_files={n:sha(ROOT/'Cluster'/n) for n in baseline['files']},ledgers="
 new_snapshot="user_files={n:sha(ROOT/'Cluster'/n) for n in baseline['files']},running_source_files={n:sha(ROOT/'Cluster'/n) for group in ('WFC_source_paths','LFT_source_paths') for n in baseline[group]},ledgers="
 assert launcher.count(old_snapshot)==1;launcher=launcher.replace(old_snapshot,new_snapshot)
 compile(launcher,str(O/'run_nec_operation.py'),'exec');write('run_nec_operation.py',launcher)
 for p,h in native['source_files'].items():
  actual=N/('candidate.yaml' if p.endswith('.yaml') else 'candidate_model/'+pathlib.PurePosixPath(p).name);assert sha(actual)==h,p
 before=ast.parse((OLD/'adapter.py').read_text());after=ast.parse(generated['adapter.py'])
 fs=lambda a:{q.name:ast.dump(q,include_attributes=False) for q in ast.walk(a) if isinstance(q,ast.FunctionDef)}
 bf,af=fs(before),fs(after)
 provenance={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':owner,'actual_author_child_thread_id':os.environ['CODEX_THREAD_ID'],'root_thread_not_impersonated':True,'checks':checks,'status':'CHILD_AUTHOR_METADATA_CHECKED_NOT_ROOT_GUARD_PASS','reference_preparation':ref(OLD/'preparation.json'),'reference_adapter':ref(OLD/'adapter.py'),'reference_remote':ref(OLD/'remote_ops.py'),'literal_plan':plan,'explicit_non_STRING_change':{'file':'adapter.py','old':'DRAFT_EXECUTION_DISABLED = False','new':'DRAFT_EXECUTION_DISABLED = True','reason':'Mirror actual frozen NEC native DRAFTTrue, refuse mutation locally before directory/binding/transport; readonly unchanged.'},'mapping_semantics':'Single longest-first regular-expression substitution on STRING token values; replacements are not rescanned, preserving distinct candidate NEC and parent LFT roles. No NAME/identifier/schema substring replacement.','adapter_actual_function_AST_differences':[k for k in bf if bf[k]!=af[k]],'root_launcher_snapshot_addition':{'old':old_snapshot,'new':new_snapshot,'scope':'Read/hash all18 existing WFC/LFT working source paths before and after operation, in addition to HEAD/index/status/user28/lifecycle/work/memory. No record_utils.git call/signature dependency.'},'source_version':ref(proof),'no_Git_SSH_GPU_Torch_entry_or_shared_execution':True}
 save('port_provenance.json',provenance)
 release={'schema_version':1,'purpose':'Static draft module/version hash catalogue only; no execution activation/token/lease/GPU permission','candidate_id':CID,'experiment_id':EXP,'code_commit':C,'native_preparation_sha256':sha(N/'preparation.json'),'manifest_template_sha256':sha(N/'manifest_template.json'),'source_version_binding_sha256':native['source_version_binding']['sha256'],'source_hashes':{k:sha(O/k) for k in ['adapter.py','remote_ops.py']},'external_candidate_preparation_and_release_anchors_required':True,'fresh_owned_binding_and_live_idle_still_required':True,'explicit_selected_physical_GPU_capability':[1],'selection_scope':'Exact current allowed[0,1]/max1; only physicalGPU1 may be explicitly selected. No fallback/sharing/eviction/replay. Preserve protected WFC0/LFT1 original tasks and all foreign occupation; current availability unknown to author.','conditional_parent_promotion':{'expected_primary_HEAD':B,'required_technical_receipt':'pipeline/admissions/M227-LFT.json','profile':'experiment_first','training_completion_or_effect_requirement':False,'applies_to_mutations_only':True},'resource_policy':copy.deepcopy(old['release_template'] and read(OLD/'release_template.json')['resource_policy'])}
 save('release_template.json',release)
 text='# NEC guarded operational packet\n\nActual source6bc36 child4457 from root proof8745; original7592 source/protocol17ba unchanged. Native packet is sibling nec_native_prepare and must match exact hashes. This static capability only selects physicalGPU1 (logicalCUDA0); allowed0,1/max1 grant is unchanged. Native and operational DRAFTTrue are execution-disabled, operational_readyFalse. No card availability or native/resource PASS is asserted.\n\nThe original key/hostname-first host.115, owner6/current context+deadline, source/assets, selected UUID1, double idle, three gpu1 locks, durable exact requests and uncertain-status reconciliation/no replay remain inherited. Mutation prepare/stage/run additionally needs genuine M227-LFT technical receipt and actual parent main/runtime4457; no LFT completion or efficacy gate. Read-only Adapter probe/status/reconcile preserve original observation semantics.\n\nNo adapter_release, active manifest/lease, request or remote directory is created. Even static registration cannot enable this draft. A future separate reviewed activation packet must preserve this frozen6c52 native and op draft before any actual mutation; it must bind fresh current source/owner/idle/lease and exact release anchors. run_nec_operation.py defaults NOP; each --execute-root --operation prepare/stage/run invokes at most one original request. Run requires original >1020-second margin; mode smoke/resources target champion/candidate. Existing uncertainty must be reconciled, never replayed.\n\nWrapper snapshots HEAD4457/index/status/user28/38 lifecycle/work/memory and both original running18 source hashes. No dependence on record_utils.git signature. No model/science summaries/admission/queue/dispatch is authored here.\n'
 write('README.md',text)
 assert "GPU_UUIDS = {1:" in generated['adapter.py'] and 'choices=[1]' in generated['adapter.py']
 assert "PARENT_EXPERIMENT = 'M227-LFT'" in generated['adapter.py'] or 'PARENT_EXPERIMENT = "M227-LFT"' in generated['adapter.py']
 assert "hierarchy-nonlinear-lifting-analysis-synthesis" in generated['adapter.py']
 validation={'status':'STATIC_NEC_VERSION_NAMESPACE_AND_GUARDED_GPU1_METADATA_VALIDATED_NOT_NATIVE_PASS','checks':['native and operational DRAFTTrue locally refuse mutation; readonly observations preserved','actual root source6bc36-child4457 and frozen source9 map','actual final native map/template/sourcebinding hashes','single-pass STRING candidate/parent role port, preserved identifiers','selected physical1 only/livepolicy0,1/max1 unchanged','parent genuine M227-LFT technical receipt mutation-only, no efficacy/completion','original host-first strict key SSH/UUID1/three locks/deadline/source/request guards inherited','defaultNOP root wrapper and one original operation call, selected1 arguments inherited','running18 source working-hash snapshot added to user28/index/lifecycle guards','all prepared Python source compile only; no import/entry','10 active manifest fields NULL/no production static release'], 'actual_check_count':11,'native_TRAIN2':'NOT_RUN','resources':'NOT_RUN','current_physical_card_availability':'UNKNOWN_BY_AUTHOR_NO_QUERY','root_guard_invoked':False}
 save('static_validation.json',validation)
 prep={'schema_version':1,'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'STATIC_NEC_GPU1_OPERATIONAL_DRAFT_PREPARED_NOT_EXECUTED','candidate_id':CID,'experiment_id':EXP,'code_commit':C,'source_commit':C,'source_parent_commit':B,'expected_runtime_code_commit':B,'draft_execution_disabled':True,'operational_ready':False,'prepared_under_parent_owner':owner,'actual_author_child_thread_id':os.environ['CODEX_THREAD_ID'],'static_provenance_only_not_execution_binding':True,'native_preparation':ref(N/'preparation.json'),'native_manifest_template':ref(N/'manifest_template.json'),'native_source_version_binding':native['source_version_binding'],'source_preparation':pv['source_preparation'],'native_protocol':pv['native_protocol'],'isolated_source_version':ref(proof),'reference_operational_preparation':ref(OLD/'preparation.json'),'release_template':ref(O/'release_template.json'),'root_launcher':ref(O/'run_nec_operation.py'),'literal_port_provenance':ref(O/'port_provenance.json'),'metadata_validation':ref(O/'static_validation.json'),'selected_GPU_capability':[1],'live_resource_policy':{'allowed_gpus':[0,1],'max_tasks_per_gpu':1},'resource_authorization':release['resource_policy']['authorization'],'conditional_parent_promotion':release['conditional_parent_promotion'],'active_binding_manifest_lease':'NOT_CREATED','production_static_release':'NOT_CREATED; requires root exact-copy and external registered anchors','all_actual_execution':'NOT_RUN','native_TRAIN2':'NOT_RUN','resources':'NOT_RUN','efficacy':'UNKNOWN','scientific_admission':False,'independent_review':'EXTERNAL_PENDING_NOT_CIRCULARLY_MAPPED'}
 prep['prepared_file_hashes']={p.relative_to(O).as_posix():sha(p) for p in sorted(O.iterdir()) if p.is_file()};save('preparation.json',prep)
 print(json.dumps({'preparation':ref(O/'preparation.json'),'native_preparation':ref(N/'preparation.json'),'adapter':ref(O/'adapter.py'),'remote':ref(O/'remote_ops.py'),'release_template':ref(O/'release_template.json'),'root_launcher':ref(O/'run_nec_operation.py'),'selected_GPU':[1],'native_resources':'NOT_RUN'}))
if __name__=='__main__':main()
