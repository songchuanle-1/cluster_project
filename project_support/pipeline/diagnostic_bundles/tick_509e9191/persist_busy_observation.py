"""Persist one actual busy resource check; no native, model, source or queue action."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='509e919168b1426b8ebfab88075116e2';CTS='hierarchy-parent-cyclic-triadic-state-composition';BEC='hierarchy-cross-level-bipartite-edge-composition'
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
 owner=guard();assert not any((HERE/n).exists() for n in ['busy_persist_intent.json','busy_observation_persisted.json','codex_memory_before_finalization.md'])
 model=read(ROOT/'pipeline/headless/.tick_model_view.json')
 assert model['experiment_first']['enabled'] and model['research']['reserve_budget']==model['research']['creation_budget']==0
 assert model['queue']['running_count']==2 and model['queue']['ready_waiting_count']==0 and model['changes']['new_terminal_ids']==[]
 obs_path=HERE/'active_runs_progress_observation.json';obs=read(obs_path)
 assert sha(obs_path)=='5b719ec61d2a8d077c1417a93eeae48c11f82296ec4ad7c32f22e8cb5cdbb754' and obs['owner_token']==TOKEN
 assert len(obs['observations'])==2 and all(x['native_TRAIN_growth'] for x in obs['summary'])
 for sample in obs['observations']:
  for task in sample['tasks']:
   contexts=[int(line.split(',')[0].strip()) for line in task['gpu_contexts'].splitlines() if line.strip()]
   assert contexts==[task['pid']] and 1565126 not in contexts
   assert task['read_only'] and not task['signals_sent'] and task['errors']==[]
 review_path=HERE/'progress_and_resource_independent_review.json';review=read(review_path)
 assert sha(review_path)=='f71a74e64dc541f899deff7e89a9e21a38e4a81701dada2503434a198d709dd9'
 assert review['anchors']['actual_progress']==ref(obs_path) and review['material_concerns']==[]
 assert review['new_action'] is False and review['user_decision'] is False
 held_path=HERE/'held_boundary_check.json';held=read(held_path)
 assert held['new_action'] is False and held['user_decision'] is False
 assert not (HERE/'cts_execution').exists() and not (HERE/'bec_execution').exists()
 last=obs['observations'][-1];tasks={t['id']:t for t in last['tasks']};assert set(tasks)=={'M213-BFC','M212-BCR'}
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
   'previous_additional_process_exit_owner_purpose':'UNKNOWN_NOT_REQUERIED','evidence':[ref(obs_path),ref(review_path)],
   'scope':'Both original registered training tasks occupy the two allowed physical GPUs. Prior extraPID absent in these two samples is not proof of process exit or an idle card; no new native execution.'}
  for c in work['candidates']:
   if c['id'] in [CTS,BEC]:
    assert c['stage']=='validation' and c['native_execution_code_commit'] is None and c['native_status']=='NOT_RUN_BOTH_REGISTERED_GPUS_BUSY'
    c.setdefault('resource_wait_history',[]).append(copy.deepcopy(c.get('resource_wait',{})));c['resource_wait']=copy.deepcopy(wait)
    add(c,[obs_path,review_path])
   elif c['id'] in RUNNING:
    t=tasks[RUNNING[c['id']]];assert c['experiment_id']==t['id'];add(c,[obs_path,review_path])
    c['latest_runtime_observation']={'evidence':ref(obs_path),'independent_review':ref(review_path),'shared_runtime_commit':t['runtime_HEAD'],
     'admitted_source_unchanged':c['code_commit'],'previous_additional_gpu_pid':1565126,'previous_additional_pid_observed':False,
     'scope':'Original PID/start/argv/cwd/log/model8/YAML/UUID and native TRAIN growth preserved. Prior extra PID not listed in these samples; no exit/ownership or continuous exclusivity inference.'}
  permitted={CTS,BEC}|set(RUNNING)
  assert [c for c in work['candidates'] if c['id'] not in permitted]==[c for c in old['candidates'] if c['id'] not in permitted]
  work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CTS,'kind':'resource_check','result':'blocked',
   'command':"python -B -X utf8 'D:/project/cluster_project/pipeline/diagnostic_bundles/tick_509e9191/observe_active_runs.py'",
   'observation':'Actual two-sample original BFC19:4004→4011/BCR27:4479→4484 TRAIN growth; PID/start/source8/YAML/argv/cwd/log/UUID preserved. Both authorized cards remain physically occupied by original registered jobs, so CTS/BEC native computation is blocked. ExtraPID1565126 not listed in either sample; ownership/exit unknown. No new native binding, model/data backward or resource experiment.',
   'evidence':[ref(obs_path),ref(review_path)]}
  work['updated_at']=datetime.now(timezone.utc).isoformat()
  work['next_action']='Preserve original BFC/BCR jobs, both complete CTS/BEC preparation catalogs/checkers and all held boundaries. Execute real paired native checks only when an authorized card is genuinely idle and fresh owner/UUID/assets/three-lock/version/binding guards pass. No new source/preparation/admission from a busy observation.'
  guard()
  with (HERE/'busy_persist_intent.json').open('x',encoding='utf8') as f:
   json.dump({'token':TOKEN,'helper_sha256':sha(Path(__file__)),'research_work_before_sha256':sha(work_path),'memory_before_sha256':sha(ROOT/'pipeline/codex_memory.md'),
    'scope':'Once-only four existing observation updates. Partial journal requires readonly reconciliation, never replay.'},f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  save(work_path,work)
  memory_path=ROOT/'pipeline/codex_memory.md';memory=memory_path.read_text('utf8')
  with (HERE/'codex_memory_before_finalization.md').open('xb') as f:f.write(memory_path.read_bytes())
  lines=memory.splitlines()
  def replace_line(prefix,text):
   positions=[i for i,line in enumerate(lines) if line.startswith(prefix)];assert len(positions)==1;lines[positions[0]]=text
  replace_line('- 最新接管',f'- 最新接管{TOKEN}；actual owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner["generated_at"]}/原deadline{owner["deadline_at"]}不延长。前f15b FINALIZED/released及lock/pending消失后begin，本轮finish以实际receipt为准，不预签。')
  stamp=datetime.fromisoformat(last['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
  replace_line('- 采集',f'- 采集{stamp}上海：BFC原219369/start56265957 GPU0 Train19/50 4004→4011；BCR原1215422/start51717921 GPU1 Train27/50 4479→4484，分母各4686。源8/YAML77e/argv-cwd-fd1/UUID与public48fc/科学BCR11a保持，proof5b719ec6…及本轮独审。两样本每卡仅列各原PID；当前best未测，不外推长期独占/空卡。')
  replace_line('- 本轮旧9',f'- 本轮旧9到期，仅一次有界metadata复核{ref(held_path)["path"]} SHA{sha(held_path)}；旧8canonical记录/声明path-hash字符串和授权目录metadata及M206暂停语义无新动作，未读或重探655正文/旧grant正文/checkpoint body，不重开路线/增加修订。')
  memory='\n'.join(lines)+'\n'
  memory=memory.split('\n## Last Tick')[0]+'''
## Last Tick
- 本轮509e snapshot2running/0ready，现有储备CTS/BEC共2，reserve_budget0/creation_budget0；due11包含旧9，无新终态/operationalissue，begin已查进展并尝试已有合格队列，M206paused不计ready。
- 真实两样本原BFC19:4004→4011/BCR27:4479→4484均增长；原PID/start/8源/YAML/argv-cwd-fd1/UUID/公共48fc保持。NVML仅列各原任务，总used19775/19751MiB；1565126未列，owner/exit未知，不重探身份，不推断空卡。
- 实际resource_check blocked，授权两卡被原任务占用。CTS/BEC源/静态工具/只读结果checker原件复用，未重复14非法入口或61/98套件，无新工具/模型/native/resource数据检查/绑定/准入/queue/启动。
- 旧9到期仅有界metadata复核无新授权/动作，8旧记录和声明655路径hash字串/授权目录metadata/M206暂停保持；未读655正文/旧grant正文/checkpoint body，不触发修订或恢复。
- 0新候选/0新工具/0模型修订/0Git提交/0准入/0queue/0启动/0新训练终态；141IDs、主48fc/index空/28status+bytes/10运行归档账保持，仅四既有候选观察更新。两储备下一步是真正空卡+fresh完整门后原YAML固定TRAIN2/资源，通过后才收据入队/核真实步数。
- 例行健康且仍无新可行动事项，无需用户确认或通知；七段memory/真实blocked attempt/Chinese notes/六段report后原token finish核FINALIZED/released及lock/pending消失，释放后不回写。
'''
  assert memory.count('\n## ')==7 and len(memory.splitlines())<120
  save(memory_path,memory)
  notes={'actions':[
   '实际会话与target一致，前f15b已FINALIZED/released且lock/pending消失；本轮begin查进展并尝试派发已有合格队列，2running/0ready、储备2但reserve/creation预算0，无新终态或operationalissue。',
   '实际两样本BFC GPU0第19/50轮4004→4011、BCR GPU1第27/50轮4479→4484均增长，原PID/start/8源/YAML77e/argv-cwd-log/UUID保持，public48fc与BCR科学11a分开。当前best未测，不从cursor推断。',
   '两次NVML每卡只列各原训练，总used19775/19751MiB；1565126未被列出不证明退出或长期独占，其owner/用途未知且未重探。两授权GPU仍被原任务占用，本轮真实resource_check blocked，未创建native绑定或新GPU任务。',
   '旧9到期仅有界metadata复核，无新授权/动作；旧8canonical记录及声明655path-hash字符串、授权目录metadata、M206暂停语义保持。未读/stat/hash655正文、旧grant正文/checkpointbody或重跑旧诊断；报告位于本轮held_boundary_check.json。',
   '既有CTS/BEC本地准备与结果检查器已齐，未重复原软件套件或localguard非法入口；0新候选/工具/模型修订/Git提交/准入/queue/启动/训练终态，只更新四既有观察，保留28/index/主48fc/10账和其他137候选。'],
   'decisions':['无新研究或资源策略决策；保持现有授权/暂停/调度。下一步等授权卡真正空闲再做fresh完整guard与原生YAML两步/backward/资源实测，实测通过后才准入入队。仍无新可行动事项，保持静默。']}
  save(HERE/'report_notes.json',notes)
  guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
  save(HERE/'busy_observation_persisted.json',{'token':TOKEN,'result':'BLOCKED_REGISTERED_GPUS_BUSY','progress':ref(obs_path),'independent_review':ref(review_path),'held_metadata_review':ref(held_path),
   'memory_lines':len(memory.splitlines()),'new_candidates':0,'new_admissions':0,'new_launches':0,'native_resources':'NOT_RUN','postflight':'NOT_YET_CALLED'})
  print(json.dumps({'status':'BUSY_RESOURCE_OBSERVATION_PERSISTED_NO_NEW_ACTION','memory_lines':len(memory.splitlines()),'native_resources':'NOT_RUN'}))
 finally:lock.close()
if __name__=='__main__':main()
