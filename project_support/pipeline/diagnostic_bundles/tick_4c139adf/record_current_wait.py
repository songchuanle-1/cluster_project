"""Record current observed progress/resource wait; never launch or rebuild tools."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='4c139adf5bcc40e98cd22bd716f79079'
AEF='hierarchy-parent-antisymmetric-edge-flux';BEC='hierarchy-cross-level-bipartite-edge-composition'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def exclusive(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def replace(p,b):
 t=p.with_name(p.name+'.'+TOKEN+'.observed_wait.tmp');exclusive(t,b);os.replace(t,p)
def main():
 assert sys.argv[1:]==['--execute-root'] and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
 owner=guard();assert owner['token']==TOKEN
 for name in ['record_intent.json','record_before.json','record_result.json','report_notes.json','preflight_bec_metric.json']:
  assert not (HERE/name).exists(),'Partial operation requires reconciliation; never replay'
 obs_path=HERE/'bec_training_progress_observation.json';resource_path=HERE/'aef_actual_local_guard.json'
 assert sha(obs_path)=='b97bffaee42149d93979c3507b65dfabb1a9dd2e5c2cf8ae8169de8f60ae7e36'
 assert sha(resource_path)=='2a44db27cf6b0daabc778015350af59e7ed0bd65becc256fe5b2670d2394ff92'
 obs=read(obs_path);resource=read(resource_path);peer_path=HERE/'bec_and_aef_current_review.json';held_path=HERE/'held_boundary_check.json'
 peer=read(peer_path);held=read(held_path)
 assert peer['material_concerns']==[] and peer['foreground_snapshot']['token']==TOKEN
 assert held['material_concerns']==[] and held['foreground_snapshot']['token']==TOKEN
 assert obs['owner_token']==TOKEN and obs['native_TRAIN_growth'] is True and resource['owner']['token']==TOKEN
 assert resource['result']=='blocked' and resource['transport_calls']==0 and resource['active_execution_created'] is False
 assert resource['native_TRAIN2']==resource['resources']=='NOT_RUN'
 first,last=obs['observations'];assert first['train_progress']==[10,50,526,4686] and last['train_progress']==[10,50,535,4686]
 ctx=read(ROOT/'pipeline/headless/.tick_context.json')
 line=next(x for x in ctx['preflight']['monitor_output'].splitlines() if '_ctf_hcg_csort_bec]' in x)
 assert 'Best=0.4803 10/50 no_improve=0/10 gpu=0' in line
 metric={'recorded_at':owner['generated_at'],'context_sha256':owner['context_sha256'],'original_monitor_line':line,'best_mIoU_4dp':'0.4803','epoch':10,'max_epochs':50,'no_improve':0,'patience':10,'scope':'Original begin cached monitor output, not a newer remote validation or final efficacy.'}
 metric_bytes=encode(metric);metric_ref={'path':(HERE/'preflight_bec_metric.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(metric_bytes).hexdigest()}
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();pre=snapshot();baseline=read(HERE/'protected_assets_before.json')
  for k in ['head','index_empty','status_hex','files','protected_ledgers','candidate_digests']:assert pre[k]==baseline[k],k
  wp=ROOT/'pipeline/research_work.json';mp=ROOT/'pipeline/codex_memory.md';work=read(wp);out=copy.deepcopy(work)
  a=next(x for x in out['candidates'] if x['id']==AEF);b=next(x for x in out['candidates'] if x['id']==BEC)
  assert a['stage']=='validation' and a['native_status']==a['resource_status']=='NOT_RUN' and a.get('native_execution_code_commit') is None
  assert b['stage']=='training' and b['training_status']=='running'
  now=datetime.now(timezone.utc).isoformat()
  a.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(a.get('resource_check')),'prior_current_resource_check':copy.deepcopy(a.get('current_resource_check'))})
  a['resource_check']=ref(resource_path)
  a['current_resource_check']={'result':'blocked','server':'server-4','physical_gpu':0,'recorded_at':resource['recorded_at'],'evidence':ref(resource_path),'hardware_evidence':ref(obs_path),'scope':'Current owner and reused frozen adapter passed local guards; registered BEC blocks prepare0, GPU1 rejected before transport. Separate fresh original BEC source/process/context samples; no native computation.'}
  for e in [ref(resource_path),ref(peer_path)]:
   if e not in a['evidence']:a['evidence'].append(e)
  b.setdefault('training_progress_history',[]).append(copy.deepcopy(b.get('training_progress_observation')))
  b['training_progress_observation']={'first':first['train_progress'],'last':last['train_progress'],'pid':last['pid'],'start_ticks':last['start_ticks'],'observed_at':last['observed_at'],'evidence':ref(obs_path),'independent_review':ref(peer_path),'preflight_partial_metrics':metric_ref}
  b['current_resource_check']={'result':'original_training_running','server':'server-4','physical_gpu':0,'observed_at':last['observed_at'],'evidence':ref(obs_path),'scope':'Bounded source/process/native TRAIN growth/context; no continuous exclusivity or pureTRAIN peak claim.'}
  for e in [ref(obs_path),ref(peer_path),metric_ref]:
   if e not in b['evidence']:b['evidence'].append(e)
  if out.get('held_boundary_review'):out.setdefault('held_boundary_review_history',[]).append(copy.deepcopy(out['held_boundary_review']))
  out['held_boundary_review']=ref(held_path)
  if out.get('tick_attempt'):out.setdefault('tick_attempt_history',[]).append(copy.deepcopy(out['tick_attempt']))
  out['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':AEF,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+(HERE/'check_aef_actual_guard.py').as_posix()+' --execute-root','observation':'Actual current owner with unchanged reviewed AEF packet: GPU0 prepare refused registered original BEC occupancy; GPU1 refused at entry. Zero transport/Popen/network/Torch/new GPU queries by guard, no active execution. Separate fresh root BEC source/process/context/native10of50 steps526to535 confirm progress. No new actionable fault or native/resource PASS.','evidence':[ref(resource_path),ref(peer_path)]}
  out['updated_at']=now
  others=lambda w:{x['id']:x for x in w['candidates'] if x['id'] not in (AEF,BEC)}
  assert len(out['candidates'])==142 and others(out)==others(work)
  memory_old=mp.read_bytes();memory=memory_old.decode('utf8')
  memory=memory.replace('- 当前05f6addd722d487fbdc663753af44b83，actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T18:03:58.499009+00:00/deadline19:03:58.499009+00:00原值保持。','- 当前4c139adf5bcc40e98cd22bd716f79079，actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T20:05:03.749915+00:00/deadline21:05:03.749915+00:00原值保持。')
  lines=memory.splitlines();updated=[]
  for text in lines:
   if text.startswith('- 当前1个确认训练：'):text=f"- 当前1个确认训练：M215-BEC source026c，server4GPU0原PID1558071/start64444390；{first['observed_at']}→{last['observed_at']}，TRAIN10/50 526→535/4686，sole context19760MiB；本轮观测b97bffae/独审{sha(peer_path)[:8]}，源8/YAML/队列/收据与mapping一致，非持续独占声明。"
   elif text.startswith('- 本轮begin原始监控截至'):text='- 本轮begin原始监控20:05:03Z：BEC partial Best=.4803、10/50、no_improve0/10；原行独立保存在本轮preflight_bec_metric.json，非双样本新验证值或最终效果。M95.5020/目标.5100/gap.0080保持。'
   elif text.startswith('- AEF本轮aef_actual_local_guard'):text='- AEF本轮actual guard2a44db27 resource_check/blocked：复用原05f6已审native78f7/op965e/release8913，不重建或重测静态工具；prepare0因registered BEC拒绝，prepare1因GPU1未授权拒绝，0transport/Popen/network/Torch/新GPU查询/active。另采本轮BEC b97b物理context与增长，AEF仍未实测/入队。'
   elif text.startswith('- 旧held候选本轮不复核'):text=f"- 旧10本轮due，仅bounded metadata/ref清单复核{sha(held_path)[:8]}；旧记录/禁用项/修订上限保持，无新恢复授权，不读655正文/旧grant/checkpoint体、不重开/重测。"
   updated.append(text)
  memory='\n'.join(updated)+'\n'
  prefix=memory.split('## Last Tick\n')[0]
  memory=prefix+'## Last Tick\n- 新begin一次canonical监控/goal/派发；无新终态/运维故障，原BEC TRAIN10/50继续增长，原GPU0唯一context与源/收据核实。\n- AEF仅fresh当前owner原工具资源拒绝检查，真实blocked；工具已完备无新本地缺口，等待唯一GPU0自然释放。未做新模型/源码/静态suite/native/资源计算或准入。\n- due旧10仅metadata/ref签名边界复核，不读旧655/grant/ckpt、不追加旧修订、恢复或授权请求。其他140候选、14生命周期账、primary026c/28status+bytes/index保持。\n- 本轮0新candidate/模型revision/sourcecommit/准入/入队/训练启动；没有新的可行动故障或需用户决定。记录/报告后按实际canonical postflight/receipt释放，本记录不预签收尾成功。\n'
  assert len(memory.splitlines())<120 and memory.count('\n## ')==7 and TOKEN in memory
  notes={'actions':['canonical begin无新终态/运维问题；原BEC在唯一GPU0真实TRAIN10/50 526→535，源8/YAML/进程/收据/登记/physical0 context核实。','AEF复用原受审native/op与静态release，当前owner实际prepare0拒绝registeredbusy、prepare1入口拒绝，0transport/Popen/network/Torch/AEF执行；资源检查blocked，原生及资源实测仍未运行。','due旧10仅当前metadata/ref边界复核，原记录与许可状态保持；0新候选/修订/sourcecommit/准入/入队/启动，其他140候选与14账、28用户文件和主线026c保持。'],'decisions':['BEC原训练继续；20:05Z缓存Best.4803/10of50/noimprove0与双样本进度分开，尚无最终效果或新champion。','AEF等待唯一GPU0自然释放后用现成工具做原YAML真实配对检查；不使用GPU1、不占用运行卡、不重建已备工具，无新用户动作。已知等待状态无实质新变化，保持静默；canonical收尾结果以实际receipt为准。']}
  wb,mb,nb=encode(out),memory.encode('utf8'),encode(notes)
  before={'owner_token':TOKEN,'work_sha256':sha(wp),'memory_sha256':sha(mp),'protected_snapshot':pre,'AEF_before':next(x for x in work['candidates'] if x['id']==AEF),'BEC_before':next(x for x in work['candidates'] if x['id']==BEC),'held_boundary_review_before':work.get('held_boundary_review'),'tick_attempt_before':work.get('tick_attempt')}
  intent={'owner_token':TOKEN,'recorded_at':now,'proposed_work_sha256':hashlib.sha256(wb).hexdigest(),'proposed_memory_sha256':hashlib.sha256(mb).hexdigest(),'scope':'AEF fresh observed resource wait, BEC progress, bounded held metadata pointer, seven-section memory. No source/lifecycle changes; partial operations must be reconciled without replay.'}
  result={'recorded_at':now,'owner_token':TOKEN,'native_resources_AEF':'NOT_RUN','tick_attempt':'resource_check/blocked','other140_candidates_unchanged':True,'protected14_ledgers_and28_files_primary026c_unchanged':True,'memory_lines':len(memory.splitlines()),'new_candidate_revision_sourcecommit_admission_queue_launch':0,'canonical_finish_claimed':False,'work_sha256':hashlib.sha256(wb).hexdigest(),'memory_sha256':hashlib.sha256(mb).hexdigest()}
  bb,ib,rb=encode(before),encode(intent),encode(result)
  guard();assert sha(wp)==before['work_sha256'] and sha(mp)==before['memory_sha256']
  exclusive(HERE/'record_before.json',bb);exclusive(HERE/'record_intent.json',ib);exclusive(HERE/'preflight_bec_metric.json',metric_bytes)
  guard();replace(wp,wb);replace(mp,mb);exclusive(HERE/'report_notes.json',nb)
  post=snapshot()
  for k in ['head','index_empty','status_hex','files','protected_ledgers']:assert post[k]==pre[k],k
  assert others(read(wp))==others(work) and read(wp)==out and mp.read_bytes()==mb
  exclusive(HERE/'record_result.json',rb)
  print(json.dumps({'status':'CURRENT_KNOWN_WAIT_RECORDED','result':ref(HERE/'record_result.json'),'memory_lines':len(memory.splitlines())}))
 finally:lock.close()
if __name__=='__main__':main()
