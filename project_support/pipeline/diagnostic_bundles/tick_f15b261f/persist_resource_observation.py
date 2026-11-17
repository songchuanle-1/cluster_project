"""Persist actual blocked resource observation; no model/queue/GPU operations."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='f15b261f91d845788f9187e85e699762'
CTS='hierarchy-parent-cyclic-triadic-state-composition';BEC='hierarchy-cross-level-bipartite-edge-composition'
RUNNING={'hierarchy-parent-butterfly-token-composition':'M213-BFC','hierarchy-parent-bidirectional-complement-recurrence':'M212-BCR'}
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
 temporary=p.with_name(p.name+'.'+TOKEN+'.tmp')
 with temporary.open('x',encoding='utf8') as f:
  if isinstance(x,str):f.write(x)
  else:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
  f.flush();os.fsync(f.fileno())
 os.replace(temporary,p)
def add(c,paths):
 for p in paths:
  item=ref(p)
  if item not in c.setdefault('evidence',[]):c['evidence'].append(item)
def main():
 owner=guard()
 assert not any((HERE/n).exists() for n in ['resource_persist_intent.json','resource_observation_persisted.json','codex_memory_before_finalization.md'])
 model=read(ROOT/'pipeline/headless/.tick_model_view.json')
 assert model['research']['reserve_budget']==model['research']['creation_budget']==0
 assert model['queue']['running_count']==2 and model['queue']['ready_waiting_count']==0 and model['changes']['new_terminal_ids']==[]
 obs_path=HERE/'active_runs_progress_observation.json';obs=read(obs_path)
 assert sha(obs_path)=='3fdb1207c6e6171b6850445554307bfbabb1955cb9a72dbf1e148b115ba52995' and obs['owner_token']==TOKEN
 assert len(obs['observations'])==2 and all(x['native_TRAIN_growth'] for x in obs['summary'])
 for sample in obs['observations']:
  for task in sample['tasks']:
   contexts=[int(line.split(',')[0].strip()) for line in task['gpu_contexts'].splitlines() if line.strip()]
   assert contexts==[task['pid']] and 1565126 not in contexts
   assert task['read_only'] and not task['signals_sent'] and task['errors']==[]
 last=obs['observations'][-1];tasks={t['id']:t for t in last['tasks']}
 assert set(tasks)=={'M213-BFC','M212-BCR'}
 guard_paths={CTS:HERE/'cts_actual_local_guard_integration.json',BEC:HERE/'bec_actual_local_guard_integration.json'}
 hashes={CTS:'755139ea68c2231bc97be3375076c9b113069d5362afdb59e50a1f99d731e311',BEC:'076c8af7b47dcb7df9ac89c8478aaa9cbde2c1781cc100455fbb840e2f625777'}
 for cid,p in guard_paths.items():
  d=read(p);assert sha(p)==hashes[cid] and d['candidate_id']==cid and d['current_owner_token']==TOKEN
  assert d['actual_transport_calls']==0 and d['subprocess_or_network_audit_events']==[] and not d['torch_imported']
  assert d['native_execution']==d['resources']=='NOT_RUN' and not d['active_binding_manifest_lease_or_execution_directory_created']
  assert all(d['refusals']['registered_gpu'+str(g)+'_busy']=='Selected GPU has registered running task' for g in [0,1])
 review_path=HERE/'progress_and_guard_independent_review.json';review=read(review_path)
 assert sha(review_path)=='3953731926a279d54669a3a83d059dea015621e571de048ca1707c3849599a76'
 assert review['new_action'] is False and review['user_decision'] is False
 assert review['anchors']['actual_progress']==ref(obs_path)
 assert review['resource_context_change']['currently_listed_in_either_of_two_samples_on_either_card'] is False
 assert review['resource_context_change']['process_exit_or_termination_proven'] is False
 assert review['resource_context_change']['actionable_idle_GPU_available'] is False
 assert not (HERE/'cts_execution').exists() and not (HERE/'bec_execution').exists()
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();before=read(HERE/'protected_assets_before.json')
  assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
  work_path=ROOT/'pipeline/research_work.json';work=read(work_path);old=copy.deepcopy(work)
  assert len(work['candidates'])==len(before['candidate_digests'])==141
  wait={'allowed_server':'server-4','allowed_physical_gpus':[0,1],'observed_at':last['observed_at'],
   'observed_tasks':{str(t['gpu']):{'id':t['id'],'pid':t['pid'],'start_ticks':t['start_ticks'],'contexts_raw':t['gpu_contexts'],'inventory_raw':t['gpu_inventory']} for t in tasks.values()},
   'previous_additional_pid':1565126,'previous_additional_pid_observed_in_current_samples':False,
   'previous_additional_process_exit_owner_purpose':'UNKNOWN_NOT_REQUERIED',
   'evidence':[ref(obs_path),ref(review_path)],
   'scope':'Both registered tasks remain physically busy. The prior extra PID is absent from both current NVML samples, not proof of process exit or GPU idle. No new GPU work.'}
  for c in work['candidates']:
   if c['id'] in guard_paths:
    assert c['stage']=='validation' and c['native_execution_code_commit'] is None
    c.setdefault('resource_wait_history',[]).append(copy.deepcopy(c.get('resource_wait',{})))
    c['resource_wait']=copy.deepcopy(wait);c['native_status']='NOT_RUN_BOTH_REGISTERED_GPUS_BUSY'
    c['execution_adapter']['actual_current_local_guard']=ref(guard_paths[c['id']])
    add(c,[obs_path,guard_paths[c['id']],review_path])
    if c['id']==BEC:
     old_text='Actual current local guard passes but both registered cards are busy, with persistent unknownPID1565126 also present; preserve all jobs.'
     new_text='Actual current local guard passes but both registered cards are busy; previous extraPID1565126 is absent from both current NVML samples, with process exit and ownership unknown; preserve all jobs.'
     assert c['next_action'].count(old_text)==1;c['next_action']=c['next_action'].replace(old_text,new_text)
   elif c['id'] in RUNNING:
    t=tasks[RUNNING[c['id']]];assert c['experiment_id']==t['id']
    add(c,[obs_path,review_path])
    c['latest_runtime_observation']={'evidence':ref(obs_path),'independent_review':ref(review_path),'shared_runtime_commit':t['runtime_HEAD'],
     'admitted_source_unchanged':c['code_commit'],'previous_additional_gpu_pid':1565126,'previous_additional_pid_observed':False,
     'scope':'Original PID/start/argv/cwd/log/model8/YAML/UUID and actual TRAIN growth preserved. Prior extra PID absent in these samples; no ownership/exit inference or process operation.'}
  permitted=set(guard_paths)|set(RUNNING)
  assert [c for c in work['candidates'] if c['id'] not in permitted]==[c for c in old['candidates'] if c['id'] not in permitted]
  work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CTS,'kind':'resource_check','result':'blocked',
   'command':"python -B -X utf8 'D:/project/cluster_project/pipeline/diagnostic_bundles/tick_f15b261f/observe_active_runs.py'",
   'observation':'Actual two-sample native TRAIN growth BFC16:2317→2325/BCR25:3514→3519; original processes, source/YAML and UUID preserved. Both registered cards are physically occupied. Actual CTS/BEC local prepare0/1 refused before transport, no active binding/native/resource experiment. Prior extraPID1565126 absent in both samples, owner/exit unknown; no identity requery or signals.',
   'evidence':[ref(obs_path),ref(guard_paths[CTS]),ref(review_path)]}
  work['updated_at']=datetime.now(timezone.utc).isoformat()
  work['next_action']='Retain both prepared CTS/BEC source-bound catalogs/checkers and original BFC/BCR training. Real paired native checks require a genuinely idle authorized card and new fresh owner/UUID/assets/three-lock/binding validation. No new preparation budget or admission/queue/native PASS is inferred from observation.'
  guard()
  with (HERE/'resource_persist_intent.json').open('x',encoding='utf8') as f:
   json.dump({'token':TOKEN,'helper_sha256':sha(Path(__file__)),'work_before_sha256':sha(work_path),'memory_before_sha256':sha(ROOT/'pipeline/codex_memory.md'),
    'scope':'Once-only four existing candidate observation updates; partial intent requires read-only reconciliation, never replay.'},f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  save(work_path,work)
  memory_path=ROOT/'pipeline/codex_memory.md';memory=memory_path.read_text('utf8')
  with (HERE/'codex_memory_before_finalization.md').open('xb') as f:f.write(memory_path.read_bytes())
  lines=memory.splitlines()
  def replace_line(prefix,text):
   indexes=[i for i,line in enumerate(lines) if line.startswith(prefix)];assert len(indexes)==1;lines[indexes[0]]=text
  replace_line('- 最新接管',f'- 最新接管{TOKEN}；actual owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner["generated_at"]}/原deadline{owner["deadline_at"]}不延长。前521 FINALIZED/released及lock/pending消失后begin，本轮finish以实际receipt为准，不预签。')
  stamp=datetime.fromisoformat(last['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
  replace_line('- 采集',f'- 采集{stamp}上海：BFC原219369/start56265957 GPU0 Train16/50 2317→2325；BCR原1215422/start51717921 GPU1 Train25/50 3514→3519，分母各4686。源8/YAML77e/argv-cwd-fd1/UUID与public48fc/科学BCR11a保持，proof3fdb1207…及本轮独审。两样本每卡仅列各原PID；当前best未测，不外推长期独占/空卡。')
  replace_line('- 前b5dc已通知', '- 前b5dc/521已见未知PID1565126占两卡，最小归属读取PermissionError历史保留；本轮两次NVML均未列该PID，仅见各原训练，总used GPU0/1为19775/19751MiB。是否退出/owner/用途仍UNKNOWN；未再探身份、读其他项目或发信号。两原任务仍忙，无新用户动作。')
  memory='\n'.join(lines)+'\n';memory=memory.replace('- 本轮521 BEC新版本绑定','- 前521 BEC新版本绑定').replace('- 本轮BEC实际localguard24c8719a','- 前521 BEC实际localguard24c8719a')
  memory=memory.replace('本轮对应版本native/operational静态包','前521对应版本native/operational静态包')
  memory=memory.split('\n## Last Tick')[0]+'''
## Last Tick
- 本轮f15b snapshot2running/0ready、已备储备2、reserve_budget0/creation_budget0、due仅CTS/BEC，旧9不due，无新终态或operationalissue；begin已查进展并尝试已有合格派发，M206paused不计ready。
- 实际两样本原BFC16:2317→2325/BCR25:3514→3519均增长，原身份/源/YAML/UUID保持；前额外1565126未列当前两次NVML，总used19775/19751MiB，未推断其退出/归属，未重复探查/干预。
- current CTSguard755139ea/BECguard076c8af7验证实际owner/context/原deadline/rawUUID/静态源锚，prepare0/1 registeredbusy beforetransport；0process/network/Torch/active，真实resource_check blocked，不是模型失败/native PASS。
- 两准备包及结果checker已完备、无新增本地实现待办；保留4e8/9b兄弟源与48fc主线、原null历史和原协议，后续真空卡+fresh完整门后原生TRAIN2/资源实测，通过才准入/入队/核真实步数。不重跑旧软件套件、旧9/655/grant/checkpoint正文。
- 0新候选/0新工具准备/0模型修订/0Git提交/0准入/0queue/0启动/0训练终态；141IDs、公共HEAD48fc/index空/28status+bytes和10运行归档账保护，仅四既有候选观察与资源状态更新。
- 例行进度健康且仍无可行动资源，无需新增确认或重复通知；七段memory/真实blocked attempt/Chinese notes/六段report后原token finish核FINALIZED/released及lock/pending消失，释放后不回写。
'''
  assert memory.count('\n## ')==7 and len(memory.splitlines())<120
  save(memory_path,memory)
  notes={'actions':[
   '核实际会话归属、前521已FINALIZED/released且无遗留lock/pending；本轮begin完成观测和已有合格队列派发尝试。2running/0ready、储备CTS/BEC共2但reserve/creation预算均0，旧9不due，无新终态/operationalissue。',
   '本轮只读两样本确认原BFC GPU0 Train16/50 2317→2325、BCR GPU1 Train25/50 3514→3519，原PID/start/argv/cwd/log/源8/YAML77e/UUID保持；public48fc与BCR科学11a分别记录，当前best未测。',
   '当前两次NVML仅列各原训练PID；上轮额外1565126本轮未见，总used19775/19751MiB。其是否退出/owner/用途未知，历史PermissionError保留，无身份重探/权限绕过/信号。两原训练仍占卡，不能由额外PID未列推断空卡。',
   '复用现有CTS/BEC静态包，在当前owner/context/原deadline/source/白名单下实际local prepare0/1均beforetransport registeredbusy拒绝；0transport/process/network/Torch/active，原生数据/backward/资源实验仍NOT_RUN。',
   '持久化真实blocked resource_check与两候选等待/两原训练观察，保留历史证据及全部其他候选/主线/运行归档账；无新候选/新工具/模型修订/提交/准入/queue/启动/终态。'],
   'decisions':['现有准备已齐且本轮创建预算0；真实原生检查等待授权卡实际空闲及fresh完整门，不占用原训练。例行进度仍健康，无需新增授权或用户动作，保持静默通知。']}
  save(HERE/'report_notes.json',notes)
  guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
  save(HERE/'resource_observation_persisted.json',{'token':TOKEN,'result':'BLOCKED_REGISTERED_GPUS_BUSY','evidence':ref(obs_path),'independent_review':ref(review_path),
   'memory_lines':len(memory.splitlines()),'new_candidates':0,'new_admissions':0,'new_launches':0,'native_resources':'NOT_RUN','postflight':'NOT_YET_CALLED'})
  print(json.dumps({'status':'RESOURCE_OBSERVATION_PERSISTED_BLOCKED_NO_NEW_ACTION','memory_lines':len(memory.splitlines()),'native_resources':'NOT_RUN'}))
 finally:lock.close()
if __name__=='__main__':main()
