"""Private child MIC packet authoring. Default NOP, no native or pipeline entry."""
import argparse,ast,copy,datetime,hashlib,io,json,os,pathlib,re,tokenize
R=pathlib.Path('D:/project/cluster_project');T=R/'pipeline/diagnostic_bundles/tick_e2659f91';O=pathlib.Path(__file__).resolve().parent;N=T/'mic_native_prepare';OLD=R/'pipeline/diagnostic_bundles/tick_94c2ad26/nec_operational_prepare'
C='041b63579888f2143cb9f3a5216ec4cff4ee8046';B='4457a46f9075f61e83340aa0f0af87d5bf4e986c';CID='hierarchy-ancestry-mobius-interaction-composition';EXP='M229-MIC'
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
 proof=T/'mic_version_prepare/isolated_source_version.json';pv=read(proof)
 assert sha(proof)=='966a9b3ec74f5794ddc8b847febc2b3d592f90898645c8e72c96615026dc1d83' and pv['code_commit']==C and pv['parent_commit']==B and pv['diff_exact9A'] is True
 sourcepeer=T/'mic_actual_source_version_independent_review.json';assert sha(sourcepeer)=='8929a938428f2dd9b452d0e6294f8ea09f417f8556eaa9aecde24fa0cb079ecb' and read(sourcepeer)['material_concerns']==[]
 native=read(N/'preparation.json');template=read(N/'manifest_template.json')
 assert native['candidate_id']==CID and native['source_commit']==C and native['source_parent_commit']==B and native['draft_execution_disabled'] is True
 assert native['source_files']==pv['frozen_source_files'] and len(native['source_files'])==9
 for name,h in native['prepared_file_hashes'].items():assert sha(N/name)==h,name
 assert native['manifest_template']==ref(N/'manifest_template.json')
 assert all(template[k] is None for k in ['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'])
 old=read(OLD/'preparation.json');assert sha(OLD/'preparation.json')=='53fe96c2c0430a5330abe5872327bc470a1548775f292c25b52eadce7ab5c5fd'
 for name,h in old['prepared_file_hashes'].items():assert sha(OLD/name)==h,name
 plan=[('pipeline/diagnostic_bundles/tick_94c2ad26/nec_native_prepare',N.relative_to(R).as_posix()),(old['native_preparation']['sha256'],sha(N/'preparation.json')),(old['native_manifest_template']['sha256'],sha(N/'manifest_template.json')),('6bc36adfe42764aac2209e6600fb3a783e2fa374',C),('hierarchy-coupled-node-edge-state-composition',CID),('M228-NEC',EXP),('nec_remote_ops','mic_remote_ops'),('nec_execution','mic_execution'),('nec_','mic_'),('_nec','_mic'),('NEC','MIC')]
 generated={}
 for name in ['adapter.py','remote_ops.py']:
  text=port((OLD/name).read_text(),plan);compile(text,str(O/name),'exec');write(name,text);generated[name]=text
 launcher=port((OLD/'run_nec_operation.py').read_text(),plan);compile(launcher,str(O/'run_mic_operation.py'),'exec');write('run_mic_operation.py',launcher)
 assert 'DRAFT_EXECUTION_DISABLED = True' in generated['adapter.py']
 assert "GPU_UUIDS = {1:" in generated['adapter.py'] and 'choices=[1]' in generated['adapter.py']
 assert "PARENT_EXPERIMENT = 'M227-LFT'" in generated['adapter.py']
 assert 'running_source_files=' in launcher and 'record_utils' not in launcher
 for p,h in native['source_files'].items():assert sha(N/('candidate.yaml' if p.endswith('.yaml') else 'candidate_model/'+pathlib.PurePosixPath(p).name))==h,p
 provenance={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':owner,'actual_author_child_thread_id':os.environ['CODEX_THREAD_ID'],'root_thread_not_impersonated':True,'checks':checks,'status':'CHILD_AUTHOR_METADATA_CHECKED_NOT_ROOT_GUARD_PASS','reference_preparation':ref(OLD/'preparation.json'),'reference_adapter':ref(OLD/'adapter.py'),'reference_remote':ref(OLD/'remote_ops.py'),'reference_launcher':ref(OLD/'run_nec_operation.py'),'literal_plan':plan,'mapping_semantics':'Single longest-first STRING-token substitution only; no replacements rescanned, Python identifiers/control flow/schema names untouched.','function_AST_scope':'Whole adapter, remote and launcher ASTs differ only by declared STRING values; DRAFTTrue/selected1/currentpolicy/parentLFT4457/body and running18 working-source snapshots inherited unchanged.','source_version':ref(proof),'actual_source_version_independent_review':ref(sourcepeer),'no_Git_SSH_GPU_Torch_entry_or_shared_execution':True}
 save('port_provenance.json',provenance)
 release=copy.deepcopy(read(OLD/'release_template.json'));release.update(candidate_id=CID,experiment_id=EXP,code_commit=C,native_preparation_sha256=sha(N/'preparation.json'),manifest_template_sha256=sha(N/'manifest_template.json'),source_version_binding_sha256=native['source_version_binding']['sha256'],source_hashes={k:sha(O/k) for k in ['adapter.py','remote_ops.py']})
 save('release_template.json',release)
 write('README.md','# MIC disabled operational packet\n\nActual041b exact9 child4457 proof966a; original346a NULL/source protocola507 untouched. Native sibling mic_native_prepare is DRAFTTrue/10NULL. Same selectedphysical1/liveallowed0,1/max1 and parentM227-LFT technical receipt guard as reviewed NEC53fe. No LFT completion/effect gate. Readonly Adapter observation preserved, mutations refuse draft before transport/directory/binding.\n\nThis is not nativePASS or execution readiness. No adapter_release/lease/raw/summary/receipt/queue/remote directory created. The release_template is only an inert draft catalogue; cannot enable a DRAFTTrue worker or adapter. Future separately reviewed activation and fresh actual owner/source/assets/idle/UUID1/three locks required, no sharing/eviction/replay.\n\nrun_mic_operation.py defaults NOP. Root-only operation wrapper retains >1020s run margin, one exact request/intents and uncertain-status reconciliation, host-first strict key SSH. HEAD4457/index/status/user28/38life/work/memory and WFC/LFT running18 source working hashes are read before/after, no record_utils.git signature assumption. Original model/protocol/worker scientific gates are not changed here. No actual input/result is pre-signed.\n')
 validation={'status':'STATIC_MIC_STRING_NAMESPACE_VERSION_AND_DRAFT_GUARDS_VALIDATED_NOT_NATIVE_PASS','checks':['actual041b singleparent4457 proof966a','actualsourcepeer8929 and original346a/a507 refs','finalnative map/template/sourcebinding/source9 hashes','exact single-pass STRING metadata port only across3 executable sources','DRAFTTrue/nativeTrue/10NULL locally blocks mutation before artifacts/transport','selectedphysical1 and policy0,1/max1/UUID1/three locks unchanged','parentM227-LFT technical receipt identity/profile/gates/hash guard unchanged','readonly observation/host-first/no replay/request reconciliation unchanged','defaultNOP explicitroot wrapper plus main/user28/index/38life/running18 capture unchanged','Python source syntax only, no entry or oldsuite'],'actual_check_count':10,'native_TRAIN2':'NOT_RUN','resources':'NOT_RUN','current_physical_card_availability':'UNKNOWN_BY_AUTHOR_NO_QUERY','root_guard_invoked':False}
 save('static_validation.json',validation)
 prep=copy.deepcopy(old);prep.update(recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='STATIC_MIC_GPU1_OPERATIONAL_DRAFT_PREPARED_NOT_EXECUTED',candidate_id=CID,experiment_id=EXP,code_commit=C,source_commit=C,source_parent_commit=B,expected_runtime_code_commit=B,prepared_under_parent_owner=owner,actual_author_child_thread_id=os.environ['CODEX_THREAD_ID'],native_preparation=ref(N/'preparation.json'),native_manifest_template=ref(N/'manifest_template.json'),native_source_version_binding=native['source_version_binding'],source_preparation=pv['source_preparation'],native_protocol=pv['native_protocol'],isolated_source_version=ref(proof),actual_source_version_independent_review=ref(sourcepeer),reference_operational_preparation=ref(OLD/'preparation.json'),release_template=ref(O/'release_template.json'),root_launcher=ref(O/'run_mic_operation.py'),literal_port_provenance=ref(O/'port_provenance.json'),metadata_validation=ref(O/'static_validation.json'))
 prep['prepared_file_hashes']={p.relative_to(O).as_posix():sha(p) for p in sorted(O.iterdir()) if p.is_file()};save('preparation.json',prep)
 print(json.dumps({'preparation':ref(O/'preparation.json'),'native_preparation':ref(N/'preparation.json'),'adapter':ref(O/'adapter.py'),'remote':ref(O/'remote_ops.py'),'release_template':ref(O/'release_template.json'),'root_launcher':ref(O/'run_mic_operation.py'),'DRAFT':True,'selected_GPU':[1],'native_resources':'NOT_RUN'}))
if __name__=='__main__':main()
