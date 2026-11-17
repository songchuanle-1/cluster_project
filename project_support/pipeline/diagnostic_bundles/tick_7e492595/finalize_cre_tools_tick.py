"""Root-only once record of existing CRE tools, actual resource refusals and current BEC progress."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,re,sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='7e4925958fa041fab72b22b0d2a0b0ea';BASE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563';SOURCE='7ed9373db335d44c884133da3eced3fca03ad29a'
CRE='hierarchy-cross-root-directed-edge-broadcast';AEF='hierarchy-parent-antisymmetric-edge-flux';BEC='hierarchy-cross-level-bipartite-edge-composition';CURRENT={CRE,AEF,BEC}
ONCE=['tools_finalize_before.json','tools_finalize_intent.json','tools_finalize_result.json','tools_finalize_memory_before.md','tools_finalize_preflight_source.json','report_notes.json']
EXPECTED={'cre_native_prepare/preparation.json':'1b669c0d0d5fe2c3364f8167a88a58189e3ace8424214fddaefe19711d6b0502','cre_operational_prepare/preparation.json':'54c199622d965858de862ffae056915bf94d7f8ac86db9bd4ffc716b9d36fc4a','cre_native_preparation_independent_review.json':'3ea7fcc4b542db8df99765abec78f82f43b15d794ed6edd039afb01c6750260d','cre_operational_preparation_independent_review.json':'b202f3ece5846f65504ad390fd3f9eea462fb8118409c06822ef185b19eadfb2','cre_catalogue_result.json':'f72e5bf2ff81e84977d5af84e53e3b1dd354966adcf44b1bdbca314ac4222ba4','cre_actual_local_guard.json':'bea155add9bdb3988cdf67f986488bfd76209e62cb861a75d773c67f8352b501','cre_catalogue_and_guard_independent_review.json':'64d566a5b537831e71a9d5692cf090bc25c3090d048ba37fecdb4a8b6ddfd913','bec_training_progress_observation.json':'d40c8f3e1c23082103b2a54b61b4459f844082fc98e552cf08e89148ff91d760','aef_actual_local_guard.json':'fb1793713c4ca5ef5e530457af658b4e88948c27e6f23056805f30285467ffc4','bec_and_aef_current_review.json':'9a47551a45a84c4e906f852045d005120191fb3d092d56239f9728693987852c','held_boundary_check.json':'57a929f518ae036f2c79983e8de038e622459fe4e3f5eec6e70810c5be36b99e','protected_assets_before.json':'0600921f1d7d19c5dbfc11893c3d731552dc9390f7dff5044528d46649e0b3bd'}
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def exclusive(p,data):
 with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def replace(p,data):
 temp=p.with_name(p.name+'.'+TOKEN+'.cre_tools_finalize.tmp');exclusive(temp,data);os.replace(temp,p)
def others(w):return {c['id']:c for c in w['candidates'] if c['id'] not in CURRENT}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute-root',action='store_true');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_RECORDING');return
 owner=guard();assert owner['token']==TOKEN and os.environ.get('GIT_OPTIONAL_LOCKS')=='0' and sys.dont_write_bytecode
 assert not any((HERE/n).exists() for n in ONCE),'Existing or partial finalizer output; reconcile read-only, never replay'
 for name,digest in EXPECTED.items():assert sha(HERE/name)==digest,name
 cat=read(HERE/'cre_catalogue_result.json');cg=read(HERE/'cre_actual_local_guard.json');ag=read(HERE/'aef_actual_local_guard.json');actualpeer=read(HERE/'cre_catalogue_and_guard_independent_review.json');obs=read(HERE/'bec_training_progress_observation.json');progresspeer=read(HERE/'bec_and_aef_current_review.json');held=read(HERE/'held_boundary_check.json')
 assert cat['owner_token']==TOKEN and cat['candidate_id']==CRE and cat['code_commit']==SOURCE and cat['status']=='REVIEWED_STATIC_CRE_CATALOGUE_ANCHORED_NATIVE_NOT_RUN' and cat['active_execution_created'] is False and cat['other142_candidates_unchanged'] and cat['all14_lifecycle_ledgers_unchanged'] and cat['primary28_status_bytes_index_and026c_unchanged']
 assert actualpeer['candidate_id']==CRE and actualpeer['code_commit']==SOURCE and actualpeer['material_concerns']==[] and actualpeer['anchors']['actual_catalogue_result']==ref(HERE/'cre_catalogue_result.json') and actualpeer['anchors']['actual_local_guard']==ref(HERE/'cre_actual_local_guard.json')
 for d,cid in [(cg,CRE),(ag,AEF)]:
  assert d['kind']=='resource_check' and d['result']=='blocked' and d['candidate_id']==cid and d['owner']=={k:owner[k] for k in d['owner']} and len(d['owner'])==6
  assert d['actual_local_guard_events']==[{'physical_gpu':0,'refused':True,'reason':'Selected GPU has registered running task'},{'physical_gpu':1,'refused':True,'reason':'Explicit physical GPU0 is required'}]
  assert all(d[k]==0 for k in ['transport_calls','Popen_calls','network_calls','GPU_queries','GPU1_queries']) and d['Torch_imported'] is False and d['active_execution_created'] is False and d['native_TRAIN2']==d['resources']=='NOT_RUN' and d['native_PASS_or_receipt_queue_created'] is False and d['material_concerns']==[] and d['hardware_evidence']==ref(HERE/'bec_training_progress_observation.json')
 assert cg['static_catalogue_result']==ref(HERE/'cre_catalogue_result.json') and obs['owner_token']==TOKEN and obs['native_TRAIN_growth'] is True
 first,last=obs['observations'];assert first['train_progress']==[17,50,3996,4686] and last['train_progress']==[17,50,4005,4686]
 assert all((x['pid'],x['start_ticks'],x['runtime_HEAD'],x['gpu_contexts'])==(1558071,'64444390',BASE,'1558071, 19768') for x in [first,last])
 assert progresspeer['material_concerns']==[] and progresspeer['actual_progress_checks_count']==18 and progresspeer['AEF_actual_local_resource_check_verified'] is True
 assert held['material_concerns']==[] and held['new_action'] is False and held['user_decision'] is False and len(held['held_records'])==10 and held['due_ID_check']['all_ten_due'] is True and all(x['same_entire_canonical_record_as4c'] and x['same_reference_manifest_as4c'] for x in held['held_records']) and held['authorization_boundary']['added_changed_removed']==[]
 ctx=read(ROOT/'pipeline/headless/.tick_context.json');assert ctx['research_work']['creation_budget']==0
 line=next(x for x in ctx['preflight']['monitor_output'].splitlines() if '_ctf_hcg_csort_bec]' in x);m=re.search(r'Best=([0-9.]+) (\d+)/(\d+) no_improve=(\d+)/(\d+) gpu=(\d+)',line);assert m and m.groups()==('0.5001','17','50','2','10','0')
 pf={'generated_at':ctx['generated_at'],'source_context':ref(ROOT/'pipeline/headless/.tick_context.json'),'monitor_line':line,'scope':'Original begin preflight, not later root TRAIN samples'};pfb=encoded(pf)
 partial={'best_mIoU_4dp':m.group(1),'epoch':17,'max_epochs':50,'no_improve':2,'patience':10,'gpu':0,'observed_at':ctx['generated_at'],'source':{'path':(HERE/'tools_finalize_preflight_source.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(pfb).hexdigest()},'not_final_efficacy':True}
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();pre=snapshot();baseline=read(HERE/'protected_assets_before.json');assert all(pre[k]==baseline[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
  assert len(pre['candidate_digests'])==143 and set(pre['candidate_digests'])==set(baseline['candidate_digests']) and all(v==baseline['candidate_digests'][k] for k,v in pre['candidate_digests'].items() if k!=CRE),'Only already verified CRE catalogue may differ before finalization'
  wp=ROOT/'pipeline/research_work.json';mp=ROOT/'pipeline/codex_memory.md';work=read(wp);out=copy.deepcopy(work);assert len(work['candidates'])==143 and sha(wp)==cat['work_sha256']
  cre=next(c for c in out['candidates'] if c['id']==CRE);aef=next(c for c in out['candidates'] if c['id']==AEF);bec=next(c for c in out['candidates'] if c['id']==BEC)
  assert cre['stage']=='validation' and cre['code_commit']==SOURCE and cre['source_parent_commit']==BASE and cre.get('native_execution_code_commit') is None and cre['native_status']==cre['resource_status']=='NOT_RUN' and not cre.get('revision_history')
  assert cre['worker_preparation']['preparation']==ref(HERE/'cre_native_prepare/preparation.json') and cre['execution_adapter']['preparation']==ref(HERE/'cre_operational_prepare/preparation.json') and cre['execution_adapter']['release']==cat['release']
  assert sha(ROOT/cat['release']['path'])==cat['release']['sha256'] and (ROOT/cat['release']['path']).read_bytes()==(HERE/'cre_operational_prepare/release_template.json').read_bytes() and not (HERE/'cre_execution').exists()
  assert aef['stage']=='validation' and aef['code_commit']=='56b2a96dc48cc8a88f0f7105527ef448113b1060' and aef.get('native_execution_code_commit') is None and aef['native_status']==aef['resource_status']=='NOT_RUN'
  assert bec['stage']=='training' and bec['code_commit']==bec['native_execution_code_commit']==BASE and bec['training_status']=='running'
  now=datetime.now(timezone.utc).isoformat()
  for candidate,gfile,check in [(cre,'cre_actual_local_guard.json',cg),(aef,'aef_actual_local_guard.json',ag)]:
   candidate.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(candidate.get('resource_check')),'prior_current_resource_check':copy.deepcopy(candidate.get('current_resource_check'))})
   candidate['resource_check']=ref(HERE/gfile);candidate['current_resource_check']={'kind':'resource_check','result':'blocked','physical_gpu':0,'recorded_at':check['recorded_at'],'evidence':ref(HERE/gfile),'hardware_evidence':ref(HERE/'bec_training_progress_observation.json'),'scope':'Actual current root local refusal with separate root hardware samples; zero new hardware query/native test, no new exclusive slot hold.'}
   candidate['next_action']='Reuse existing reviewed version-bound native/op tools only after genuine authorized idleGPU0 and fresh owner/context/unaltered deadline/assets/UUID/three locks. Original BEC stays running; noGPU1/eviction/old-binding replay. If primary advances first, package unchanged candidate source compatibly and test that exact version before a new binding.'
   for entry in [ref(HERE/gfile),ref(HERE/'bec_and_aef_current_review.json')]:
    if entry not in candidate['evidence']:candidate['evidence'].append(entry)
  cre.setdefault('preparation_history',[]).append({'recorded_at':now,'reason':'Existing source reserve now has independently reviewed static native/op capability; no actual native execution.','prior_preparation_scope':copy.deepcopy(cre.get('preparation_scope'))})
  cre['preparation_scope']='Source7ed singleparent026c plus static reviewed native1b669/op54c199; original frozen c760 code-null mother and prior isolated proof remain unchanged. Native/resources not executed, activebinding absent; release is static catalogue only.'
  for entry in [ref(HERE/'cre_catalogue_result.json'),ref(HERE/'cre_catalogue_and_guard_independent_review.json')]:
   if entry not in cre['evidence']:cre['evidence'].append(entry)
  bec.setdefault('training_progress_history',[]).append(copy.deepcopy(bec.get('training_progress_observation')))
  bec['training_progress_observation']={'first':first['train_progress'],'last':last['train_progress'],'pid':1558071,'start_ticks':'64444390','observed_at':last['observed_at'],'evidence':ref(HERE/'bec_training_progress_observation.json'),'independent_review':ref(HERE/'bec_and_aef_current_review.json'),'preflight_partial_metrics':partial}
  bec['current_resource_check']={'result':'original_training_running','physical_gpu':0,'observed_at':last['observed_at'],'evidence':ref(HERE/'bec_training_progress_observation.json'),'scope':'Root bounded original source/process/TRAIN/context evidence, not continuous exclusivity or pureTRAIN peak.'}
  for entry in [ref(HERE/'bec_training_progress_observation.json'),ref(HERE/'bec_and_aef_current_review.json')]:
   if entry not in bec['evidence']:bec['evidence'].append(entry)
  if work.get('held_boundary_review'):out.setdefault('held_boundary_review_history',[]).append(copy.deepcopy(work['held_boundary_review']))
  out['held_boundary_review']=ref(HERE/'held_boundary_check.json')
  if work.get('tick_attempt'):out.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
  out['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CRE,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+(HERE/'check_cre_actual_guard.py').as_posix()+' --execute-root','observation':'Current root version/static catalogue/owner policy guards passed; prepare0 refused original registered BEC, prepare1 refused unauthorizedGPU1 before transport. Zero process/network/Torch/newGPU query/active artifacts; separate current root BEC samples show17/50 growth. CRE static tooling/software evidence is not native/resource PASS.','evidence':[ref(HERE/'cre_actual_local_guard.json'),ref(HERE/'cre_catalogue_and_guard_independent_review.json'),ref(HERE/'bec_and_aef_current_review.json')],'other_existing_resource_check':ref(HERE/'aef_actual_local_guard.json')}
  out['updated_at']=now;out['next_action']='Continue exact original BEC1558071/source026c on soleGPU0. Existing AEF and CRE now have complete reviewed tools; reuse them on genuine fresh idle authorizedGPU0, preserving sibling-parent compatibility and all unmeasured native/resource limits. No new candidate/source/revision/admission/queue/launch or old-task recovery.'
  assert len(out['candidates'])==143 and set(c['id'] for c in out['candidates'])==set(c['id'] for c in work['candidates']) and others(out)==others(work)
  memory_old=mp.read_bytes();parts={};key=None
  for text in memory_old.decode('utf8').splitlines():
   if text.startswith('## '):key=text;parts[key]=[]
   elif key:parts[key].append(text)
  headers=['## Goal And Phase','## Champion And Baseline','## Active Hypotheses','## Closed Or Failed Directions','## Running And Queue','## Open Questions And Risks','## Last Tick'];assert set(parts)==set(headers)
  parts[headers[0]][0]='- 当前7e4925958fa041fab72b22b0d2a0b0ea，actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T00:10:56.011432+00:00/deadline01:10:56.011432+00:00原值保持。'
  parts[headers[2]]=[('- CRE原隔离source7ed9373db335d44c884133da3eced3fca03ad29a/父026c/9A/clean及c760母本null保持；本轮完成受审native1b669/16map/12diag/10active null、op54c199/7map/19小metadata软件检查，独审3ea7/b202。root静态catalogue f72e/模板bytecopy1765和实际NoTransport guard bea155均不等nativePASS，无manifest/lease/active/远端。stagevalidation，native/resources仍NOT_RUN。' if x.startswith('- CRE实际隔离source') else x.replace('- 新M217-CRE唯一储备：','- 既有M217-CRE储备：')) for x in parts[headers[2]]]
  parts[headers[2]].append('- CRE未来必须用自己694507协议和新worker实测original M95/CRE两TRAIN loss/backward/optimizer、真实root边/mean/ancestor synthesis/HCG-inst、实际common集合和原资源；不能借AEF/BEC旧raw或静态软件代测。原resources整AST保持，prepare仍核current0/026c/UUID/三锁/1020s窗口/原deadline/no-replay。')
  parts[headers[3]]=[('- 旧10本轮DUE，只做bounded canonical record/ref签名与授权目录filename/mtime/size比较，57a929f5对4c139adf全同；无正文/655目标/旧grant/checkpoint读取，无新增恢复或修订授权，不重开/重测。' if x.lstrip('- ').startswith('旧10') else x) for x in parts[headers[3]]]
  parts[headers[4]][0]='- 当前1个确认训练：M215-BEC source026c，GPU0原PID1558071/start64444390；本轮root TRAIN17/50 3996→4005/4686、sole context19768MiB，d40c8f3e观测/18项peer9a47551a；源8/YAML/receipt/R1digest/唯一三账保持，不声称持续独占。'
  parts[headers[4]]=[('- 本轮begin原始监控截至00:10:56Z：BEC partial Best=.5001、17/50、no_improve2/10；原行证据另存tools_finalize_preflight_source，不是后续TRAIN样本新验证值或最终效果。M95.5020/目标.5100/gap.0080不变。' if x.startswith('- 本轮begin原始监控') else '- CTS维持unknown终态/M206paused+dispatch_hold+resumefalse不计ready，GPU1禁用；当前0ready，AEF+CRE都有受审静态工具但均未原生测试/准入/入队，原BEC继续，BFC不恢复。' if x.startswith('- CTS已unknown') else '- AEF当前guard fb179371与CRE新guard bea155均真root NoTransport：0 registered busy/1 unauthorized，零transport/Popen/network/Torch/新GPU查询/active；物理占用依据另采本轮BEC d40c样本，不把metadata拒绝说成硬件idle测试。' if x.startswith('- AEF本轮') else x) for x in parts[headers[4]]]
  parts[headers[5]].append('- 两个现成候选工具可静态跨tick复用，但执行需fresh真实owner/未延deadline/资产/白名单/空GPU0/三锁；CRE7ed与AEF56都是026c子版本，任何先行primary推进后，另一候选须新兼容版本并真测，旧packet只留历史，不假定跨兄弟ff或重标签raw。')
  parts[headers[6]]=['- begin一次canonical监控/goal/已有派发；原BEC健康17/50增长、无新终态/运维故障，仅GPU0。creation0只推进既有CRE工具，现有AEF完整工具仅复用，不造新候选/源版本/模型修订。','- native1b669/op54c199与独审3ea7/b202全部静态冻结，19小metadata/AST/非法GPU拒绝检查不是旧61/98套件或native；root仅一次静态catalogue与真实NoTransport bea155，0计算/transport/activebinding。','- tick_attempt为CRE实际resource_check/blocked（同时保存AEF当前fb179），既有BEC当前观测d40c/peer9a4另记；旧10due仅57a metadata同4c不解锁、不催问，不读655/grant/checkpoint正文。','- 本轮0newcandidate/sourcecommit/revision/admission/queue/launch；仅现有CRE/AEF/BEC研究记录+held全局manifest与七段memory/notes更新，其他140/14账/primary026c/28status+bytes/index保持。report/finish/postflight由root实际执行，不预签其成功。']
  memory='# Codex Research Memory\n\n'+'\n'.join(h+'\n'+'\n'.join(parts[h]).strip()+'\n' for h in headers)+'\n';assert len(memory.splitlines())<120 and memory.count('\n## ')==7
  notes={'actions':['原BEC1558071/start64444390/source026c在唯一GPU0真实TRAIN17/50 3996→4005，sole19768MiB；root观测d40c与当前18项peer9a4核源8/YAML/收据/R1digest/三账，未动原进程或GPU1。','完成既有CRE版本7ed专属native/op静态工具，native1b669/op54c199、独审3ea7/b202；19小软件metadata/AST/拒绝检查，非原生/FP32/资源PASS。原c760模型/6945协议与原AEF工具不改。','root静态catalogue f72e/release模板1765精确bytecopy与实际NoTransport bea155成功；prepare0忙/1未授权，零transport/process/network/Torch/新GPU查询/active；AEF本轮同scope fb179另存。','旧10到期仅57a有界record/ref字符串和授权目录metadata比较，对4c全部同；不读655/旧grant/checkpoint正文，不重开旧路线或借timer恢复M206/BFC。'], 'decisions':['0新候选/源commit/模型revision/准入/入队/训练launch；CRE保持validation、native/resourcesNOT_RUN，resource_checkblocked不增加exclusivehold；AEF现成工具待空卡，原BEC继续。','00:10:56 preflight partial Best.5001/17of50/noimprove2与稍后TRAIN增长分开；M95.5020/目标.5100/gap.0080不变，无新champion或完整效果结论。','CRE7ed与AEF56同父026c；若main先推进，另一版本须兼容打包并实际测试，保留旧proof，不跨兄弟ff/重标旧raw。原resources整函数与科学阈值不动，未测common/梯度/FP32/资源/准确率仍未知。','仅既有CRE/AEF/BEC与held全局证据、七段memory/notes可变，其他140/14账/primary28/index/026c保持；root另按实际执行report/finish，不预报postflight/lease释放成功，无新增权限请求。']}
  wb,mb,nb=encoded(out),memory.encode('utf8'),encoded(notes);work_before=sha(wp);memory_before=sha(mp)
  bd={'owner_token':TOKEN,'recorded_at':now,'work_sha256':work_before,'memory_sha256':memory_before,'protected_snapshot':pre,'before_current_candidates':{c['id']:c for c in work['candidates'] if c['id'] in CURRENT},'held_boundary_before':work.get('held_boundary_review')}
  intent={'owner_token':TOKEN,'recorded_at':now,'scope':'Existing CRE tools/current3candidates progress-resource and heldglobal only; no lifecycle/source/native mutation','work_before_sha256':work_before,'memory_before_sha256':memory_before,'proposed_work_sha256':hashlib.sha256(wb).hexdigest(),'proposed_memory_sha256':hashlib.sha256(mb).hexdigest(),'partial_policy':'Never replay/rollback; reconcile exact journal and bytes.'}
  result={'owner_token':TOKEN,'recorded_at':now,'candidate_count':143,'new_candidates':0,'new_source_commits':0,'new_model_revisions':0,'new_admissions':0,'new_queue_tasks':0,'new_training_launches':0,'CRE_source_commit':SOURCE,'CRE_stage':'validation','CRE_native_resources':'NOT_RUN','other140_candidates_unchanged':True,'all14_lifecycle_ledgers_unchanged':True,'primary026c_protected28_status_bytes_index_unchanged':True,'held10_metadata_no_unlock':True,'memory_lines':len(memory.splitlines()),'work_sha256':hashlib.sha256(wb).hexdigest(),'memory_sha256':hashlib.sha256(mb).hexdigest(),'report_notes':{'path':(HERE/'report_notes.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(nb).hexdigest()},'postflight_or_finish_preclaimed':False}
  # Precompose every payload before any private journal or shared write.
  bb,ib,rb=encoded(bd),encoded(intent),encoded(result)
  guard();assert sha(wp)==work_before and sha(mp)==memory_before and not any((HERE/n).exists() for n in ONCE)
  exclusive(HERE/'tools_finalize_before.json',bb);exclusive(HERE/'tools_finalize_memory_before.md',memory_old);exclusive(HERE/'tools_finalize_preflight_source.json',pfb);exclusive(HERE/'tools_finalize_intent.json',ib)
  guard();assert sha(wp)==work_before and sha(mp)==memory_before
  replace(wp,wb);replace(mp,mb);exclusive(HERE/'report_notes.json',nb)
  post=snapshot();assert all(post[k]==pre[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
  assert read(wp)==out and others(read(wp))==others(work) and mp.read_bytes()==mb
  assert set(post['candidate_digests'])==set(pre['candidate_digests']) and all(v==pre['candidate_digests'][k] for k,v in post['candidate_digests'].items() if k not in CURRENT)
  guard();exclusive(HERE/'tools_finalize_result.json',rb)
  print(json.dumps({'status':'EXISTING_CRE_TOOLS_AND_CURRENT_RESOURCE_PROOFS_RECORDED_NOT_NATIVE_PASS','result':ref(HERE/'tools_finalize_result.json'),'memory_lines':len(memory.splitlines())},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
