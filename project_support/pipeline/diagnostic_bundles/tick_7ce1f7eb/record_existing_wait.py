"""Root-only once record of known existing resource wait; no native/static rebuild or held review."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,re,sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='7ce1f7eb75114a98a169f9ff9b6bbb06';BASE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
AEF='hierarchy-parent-antisymmetric-edge-flux';CRE='hierarchy-cross-root-directed-edge-broadcast';BEC='hierarchy-cross-level-bipartite-edge-composition';CURRENT={AEF,CRE,BEC}
EXPECTED={'bec_training_progress_observation.json':'a1c8182e598ebf0e1e86e184da083b3ec43154f99f2fdfd1f5b130af9de2dcb1','aef_actual_local_guard.json':'79b642b8724629f0c5aeb031829a8657004ba407bfcadbd7ed34e747854bae61','cre_actual_local_guard.json':'da0a5b2fed64c18e53ffe1c81e73966067ff1fe013da61a6a9cae460da31a925','protected_assets_before.json':'2ef3c5a5828350de9bdfa96608a985263060448e4239a648493435f16809cf71'}
ONCE=['wait_record_before.json','wait_record_intent.json','wait_record_result.json','wait_record_memory_before.md','wait_record_preflight_source.json','report_notes.json']
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def exclusive(p,data):
 with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def replace(p,data):
 tmp=p.with_name(p.name+'.'+TOKEN+'.wait_record.tmp');exclusive(tmp,data);os.replace(tmp,p)
def others(w):return {c['id']:c for c in w['candidates'] if c['id'] not in CURRENT}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute-root',action='store_true');ap.add_argument('--peer-sha256');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_RECORDING');return
 owner=guard();assert owner['token']==TOKEN and os.environ.get('GIT_OPTIONAL_LOCKS')=='0' and sys.dont_write_bytecode
 assert isinstance(args.peer_sha256,str) and re.fullmatch('[0-9a-f]{64}',args.peer_sha256) and sha(HERE/'actual_current_review.json')==args.peer_sha256,'Actual current independent peer SHA required'
 assert not any((HERE/n).exists() for n in ONCE),'Partial/existing recorder output: reconcile read-only, never replay'
 for name,digest in EXPECTED.items():assert sha(HERE/name)==digest,name
 peer=read(HERE/'actual_current_review.json');obs=read(HERE/'bec_training_progress_observation.json');ag=read(HERE/'aef_actual_local_guard.json');cg=read(HERE/'cre_actual_local_guard.json')
 assert peer['owner_token']==TOKEN and peer['material_concerns']==[] and peer['new_action'] is False and peer['user_decision'] is False
 assert peer['anchors']['observation']==ref(HERE/'bec_training_progress_observation.json') and peer['anchors']['AEFguard']==ref(HERE/'aef_actual_local_guard.json') and peer['anchors']['CREguard']==ref(HERE/'cre_actual_local_guard.json')
 assert obs['owner_token']==TOKEN and obs['native_TRAIN_growth'] is True;first,last=obs['observations']
 assert first['train_progress']==[21,50,2993,4686] and last['train_progress']==[21,50,3002,4686]
 assert all((x['pid'],x['start_ticks'],x['runtime_HEAD'],x['gpu_contexts'])==(1558071,'64444390',BASE,'1558071, 19768') for x in [first,last])
 for cid,d in [(AEF,ag),(CRE,cg)]:
  assert d['candidate_id']==cid and d['kind']=='resource_check' and d['result']=='blocked' and len(d['owner'])==6 and d['owner']=={k:owner[k] for k in d['owner']}
  assert d['actual_local_guard_events']==[{'physical_gpu':0,'refused':True,'reason':'Selected GPU has registered running task'},{'physical_gpu':1,'refused':True,'reason':'Explicit physical GPU0 is required'}]
  assert all(d[k]==0 for k in ['transport_calls','Popen_calls','network_calls','GPU_queries','GPU1_queries']) and d['Torch_imported'] is False and d['active_execution_created'] is False and d['native_TRAIN2']==d['resources']=='NOT_RUN' and d['native_PASS_or_receipt_queue_created'] is False and d['hardware_evidence']==ref(HERE/'bec_training_progress_observation.json')
 ctx=read(ROOT/'pipeline/headless/.tick_context.json');assert ctx['research_work']['creation_budget']==0
 line=next(x for x in ctx['preflight']['monitor_output'].splitlines() if '_ctf_hcg_csort_bec]' in x);m=re.search(r'Best=([0-9.]+) (\d+)/(\d+) no_improve=(\d+)/(\d+) gpu=(\d+)',line);assert m and m.groups()==('0.5001','21','50','6','10','0')
 pf={'generated_at':ctx['generated_at'],'source_context':ref(ROOT/'pipeline/headless/.tick_context.json'),'monitor_line':line,'scope':'Original begin preflight, separate from later actual TRAIN samples'};pfb=encoded(pf)
 partial={'best_mIoU_4dp':'0.5001','epoch':21,'max_epochs':50,'no_improve':6,'patience':10,'gpu':0,'observed_at':ctx['generated_at'],'source':{'path':(HERE/'wait_record_preflight_source.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(pfb).hexdigest()},'not_final_efficacy':True}
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();before=snapshot();baseline=read(HERE/'protected_assets_before.json');assert all(before[k]==baseline[k] for k in ['head','index_empty','status_hex','files','protected_ledgers','candidate_digests'])
  wp=ROOT/'pipeline/research_work.json';mp=ROOT/'pipeline/codex_memory.md';work=read(wp);out=copy.deepcopy(work);assert len(work['candidates'])==143
  selected={c['id']:c for c in out['candidates'] if c['id'] in CURRENT};assert set(selected)==CURRENT
  for cid,source,gfile,check in [(AEF,'56b2a96dc48cc8a88f0f7105527ef448113b1060','aef_actual_local_guard.json',ag),(CRE,'7ed9373db335d44c884133da3eced3fca03ad29a','cre_actual_local_guard.json',cg)]:
   c=selected[cid];assert c['stage']=='validation' and c['code_commit']==source and c.get('native_execution_code_commit') is None and c['native_status']==c['resource_status']=='NOT_RUN' and not c.get('blocker_kind')
   c.setdefault('resource_check_history',[]).append({'recorded_at':datetime.now(timezone.utc).isoformat(),'prior_resource_check':copy.deepcopy(c.get('resource_check')),'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
   c['resource_check']=ref(HERE/gfile);c['current_resource_check']={'kind':'resource_check','result':'blocked','physical_gpu':0,'recorded_at':check['recorded_at'],'evidence':ref(HERE/gfile),'hardware_evidence':ref(HERE/'bec_training_progress_observation.json'),'scope':'Current root local NoTransport refusals; hardware samples collected separately, no new physical-idle query/native test/exclusive hold.'}
   c['next_action']='Reuse existing reviewed immutable tools only after genuine authorized idleGPU0 and fresh root owner/context/original deadline/source/assets/UUID/three locks. Current original BEC continues; noGPU1, eviction, new tool duplication or old-binding replay. If main moves first, package/test unchanged source on a compatible actual parent.'
   for entry in [ref(HERE/gfile),ref(HERE/'bec_training_progress_observation.json'),ref(HERE/'actual_current_review.json')]:
    if entry not in c['evidence']:c['evidence'].append(entry)
  bec=selected[BEC];assert bec['stage']=='training' and bec['code_commit']==bec['native_execution_code_commit']==BASE and bec['training_status']=='running'
  bec.setdefault('training_progress_history',[]).append(copy.deepcopy(bec.get('training_progress_observation')))
  bec['training_progress_observation']={'first':first['train_progress'],'last':last['train_progress'],'pid':1558071,'start_ticks':'64444390','observed_at':last['observed_at'],'evidence':ref(HERE/'bec_training_progress_observation.json'),'independent_review':ref(HERE/'actual_current_review.json'),'preflight_partial_metrics':partial}
  bec['current_resource_check']={'result':'original_training_running','physical_gpu':0,'observed_at':last['observed_at'],'evidence':ref(HERE/'bec_training_progress_observation.json'),'scope':'Bounded root original process/source/TRAIN/context samples, not continuous exclusivity or pureTRAIN peak.'}
  for entry in [ref(HERE/'bec_training_progress_observation.json'),ref(HERE/'actual_current_review.json')]:
   if entry not in bec['evidence']:bec['evidence'].append(entry)
  if work.get('tick_attempt'):out.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
  out['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CRE,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+(HERE/'check_cre_actual_guard.py').as_posix()+' --execute-root','observation':'Known current wait: original BEC active on soleGPU0; existing CRE prepare0 busy/1 unauthorized before any transport. Separate root samples show21/50 TRAIN growth. Zero new hardware query/Torch/native/active; no static package or held re-review.','evidence':[ref(HERE/'cre_actual_local_guard.json'),ref(HERE/'bec_training_progress_observation.json'),ref(HERE/'actual_current_review.json')],'other_existing_resource_check':ref(HERE/'aef_actual_local_guard.json')}
  now=datetime.now(timezone.utc).isoformat();out['updated_at']=now;out['next_action']='Continue exact original BEC on soleGPU0 with original patience10; AEF/CRE reuse complete reviewed tools on genuine fresh allowed idle only. No new candidate/tool/source/revision/native/admission/queue/launch or protected-task recovery.'
  assert len(out['candidates'])==143 and set(c['id'] for c in out['candidates'])==set(c['id'] for c in work['candidates']) and others(out)==others(work)
  for k in ['held_boundary_review','held_boundary_review_history']:assert out.get(k)==work.get(k),'No new held/global pointer change when old10 notdue'
  memory_old=mp.read_bytes();parts={};key=None
  for text in memory_old.decode('utf8').splitlines():
   if text.startswith('## '):key=text;parts[key]=[]
   elif key:parts[key].append(text)
  headers=['## Goal And Phase','## Champion And Baseline','## Active Hypotheses','## Closed Or Failed Directions','## Running And Queue','## Open Questions And Risks','## Last Tick'];assert set(parts)==set(headers)
  parts[headers[0]][0]='- 当前7ce1f7eb75114a98a169f9ff9b6bbb06，actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T02:11:32.801863+00:00/deadline03:11:32.801863+00:00原值保持。'
  parts[headers[2]]=[x.replace('本轮完成受审native1b669','此前完成受审native1b669').replace('追加本轮actual result_evidence','追加94f历史actual result_evidence').replace('现真实四臂独审后','94f真实四臂独审后') for x in parts[headers[2]]]
  parts[headers[3]]=[('- 旧10本轮NOTdue，不重复复核或改全局held manifest；57a929f5只保留上轮到期metadata同4c历史引用，不新读655目标/旧grant/checkpoint正文，无新增恢复/修订授权，不重开或重测。' if x.lstrip('- ').startswith('旧10') else x) for x in parts[headers[3]]]
  parts[headers[4]][0]='- 当前1个确认训练：M215-BEC source026c，GPU0原PID1558071/start64444390；本轮root TRAIN21/50 2993→3002/4686、sole context19768MiB，a1c8182e观测/当前MD peer；源8/YAML/receipt/R1digest/唯一三账保持，非持续独占声明。'
  parts[headers[4]]=[('- 本轮begin原始监控截至02:11:32Z：BEC partial Best=.5001、21/50、no_improve6/10；原行另存wait_record_preflight_source，与稍后TRAIN样本分开，不是最终效果。原patience10不改，未实际早停不判失败。M95.5020/目标.5100/gap.0080保持。' if x.startswith('- 本轮begin原始监控') else '- AEF当前guard79b642b8与CRE当前guardda0a5b2f仅复用原冻结工具；0 registered busy/1 unauthorized、零transport/Popen/network/Torch/新GPU查询/active，物理占用依据本轮原BEC a1c8样本，不把metadata拒绝当新idle检测。' if x.startswith('- AEF当前guard') or x.startswith('- AEF本轮') else x) for x in parts[headers[4]]]
  parts[headers[6]]=['- begin一次canonical监控/goal/已有派发；原BEC21/50健康增长，best缓存.5001/noimprove6of10，未有新终态/运维故障，不抢跑自然早停。仅GPU0，M206继续用户暂停不计ready。','- 已有AEF native78f7/op965e/release8913与CRE native1b669/op54c199/release1765全静态复用，实际native/resources均NOT_RUN；本轮只两次current NoTransport busy0/拒1与原BEC新样本，不造新工具/测试/静态review。','- 旧10NOTdue，不新review或改变held全局指针，保留57a历史即可。143 IDs、其他140/14账/primary026c/28status+bytes/index不变；0新candidate/source/revision/native/admission/queue/launch。','- tick_attempt是CRE真实resource_check/blocked，两候选都只等唯一GPU0真实可用后fresh owner/原deadline/资产/UUID/三锁；已知健康资源等待建议DONT_NOTIFY。root另实际执行report/finish，不预签postflight或lease释放成功。']
  memory='# Codex Research Memory\n\n'+'\n'.join(h+'\n'+'\n'.join(parts[h]).strip()+'\n' for h in headers)+'\n';assert len(memory.splitlines())<120 and memory.count('\n## ')==7
  notes={'actions':['原BEC1558071/start64444390/source026c在唯一GPU0真实TRAIN21/50 2993→3002、sole19768MiB；本轮root观测与MD当前peer核源/队列/收据/R1等，未动原进程或GPU1。','AEF/CRE两原冻结driver本轮NoTransport只读/本地守卫：prepare0 registered busy、1 unauthorized，零transport/process/network/Torch/新GPU查询/active；不重建或复审静态工具、不将其写成原生资源PASS。'], 'decisions':['begin缓存Best.5001/21of50/noimprove6of10截至02:11:32，与稍后真实TRAIN增长分开，原patience10保持；未实际早停不判失败，无新champion或最终效果。','143现有IDs保持，creation0，无新candidate/source/tool/revision/native/admission/queue/launch；仅AEF/CRE当前resource和BEC进度、七段memory/notes改变，旧10NOTdue不新review或改全局指针，其他140/14账/primary026c/28/index保持。','两个现成工具仅待唯一GPU0真正释放后fresh owner/原deadline/UUID/资产/三锁；原AEF/CRE sibling兼容边界、native/resourcesNOT_RUN与所有未知保持，不重放旧lease或借旧raw。已知健康等待建议DONT_NOTIFY，无新增权限请求。','report/finish/postflight由root依据实际执行结果另收尾，记录脚本不预签完成或lease释放。']}
  wb,mb,nb=encoded(out),memory.encode('utf8'),encoded(notes);before_work=sha(wp);before_mem=sha(mp)
  bd={'owner_token':TOKEN,'recorded_at':now,'work_sha256':before_work,'memory_sha256':before_mem,'protected_snapshot':before,'before_current_candidates':{c['id']:c for c in work['candidates'] if c['id'] in CURRENT},'unchanged_held_boundary_review':work.get('held_boundary_review')}
  intent={'owner_token':TOKEN,'recorded_at':now,'scope':'Only current existing3candidate progress/resource, memory/notes; held global and lifecycle/source unchanged','before_work_sha256':before_work,'before_memory_sha256':before_mem,'proposed_work_sha256':hashlib.sha256(wb).hexdigest(),'proposed_memory_sha256':hashlib.sha256(mb).hexdigest(),'partial_policy':'No automatic retry/rollback; reconcile exact journal and bytes.'}
  result={'owner_token':TOKEN,'recorded_at':now,'candidate_count':143,'new_candidates':0,'new_sources':0,'new_model_revisions':0,'new_native_tests':0,'new_admissions':0,'new_queue_tasks':0,'new_launches':0,'other140_candidates_unchanged':True,'all14_lifecycle_ledgers_unchanged':True,'primary026c_28status_bytes_index_unchanged':True,'held_global_pointers_unchanged':True,'memory_lines':len(memory.splitlines()),'work_sha256':hashlib.sha256(wb).hexdigest(),'memory_sha256':hashlib.sha256(mb).hexdigest(),'notes':{'path':(HERE/'report_notes.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(nb).hexdigest()},'notification_recommendation':'DONT_NOTIFY','postflight_or_finish_preclaimed':False}
  # Every payload is serialized before the first private journal/shared write.
  bb,ib,rb=encoded(bd),encoded(intent),encoded(result)
  guard();assert sha(wp)==before_work and sha(mp)==before_mem and not any((HERE/n).exists() for n in ONCE)
  exclusive(HERE/'wait_record_before.json',bb);exclusive(HERE/'wait_record_memory_before.md',memory_old);exclusive(HERE/'wait_record_preflight_source.json',pfb);exclusive(HERE/'wait_record_intent.json',ib)
  guard();assert sha(wp)==before_work and sha(mp)==before_mem
  replace(wp,wb);replace(mp,mb);exclusive(HERE/'report_notes.json',nb)
  after=snapshot();assert all(after[k]==before[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
  assert read(wp)==out and others(read(wp))==others(work) and mp.read_bytes()==mb
  assert set(after['candidate_digests'])==set(before['candidate_digests']) and all(v==before['candidate_digests'][k] for k,v in after['candidate_digests'].items() if k not in CURRENT)
  guard();exclusive(HERE/'wait_record_result.json',rb)
  print(json.dumps({'status':'KNOWN_EXISTING_RESOURCE_WAIT_RECORDED_NO_NEW_NATIVE_OR_TOOLS','result':ref(HERE/'wait_record_result.json'),'memory_lines':len(memory.splitlines())},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
