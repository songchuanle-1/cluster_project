"""Persist actual GPU0-only admission/launch outcome without changing any run."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys,subprocess
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'tick_45eb3b04'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
 temp=p.with_name(p.name+'.e245final.tmp')
 with temp.open('x',encoding='utf8') as f:
  if isinstance(x,str):f.write(x)
  else:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
  f.flush();os.fsync(f.fileno())
 os.replace(temp,p)
def main():
 owner=guard();assert not (HERE/'final_persist_intent.json').exists()
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor;import closure
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();before=read(HERE/'protected_assets_before.json');q=monitor.load_queue(str(ROOT))
  task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M214-CTS');assert str(task['gpu'])=='0' and task['code_commit']=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
  closure.admission(ROOT,task);dispatch=read(HERE/'cts_dispatch_result.json');verified=dispatch['verified_native_progress'] is True
  assert task['status']=='waiting' and task.get('pid') is None and not verified
  calls=read(HERE/'cts_dispatch_transport_calls.json');assert calls and not any(x['canonical_native_launch_request'] for x in calls)
  wait_path=HERE/'gpu0_wait_observation.json';wait=read(wait_path)
  assert wait['token']==owner['token'] and wait['observation']['physical_gpu']==0 and wait['observation']['GPU1_queried'] is False
  assert wait['observation']['gpu_contexts']=='3381194, 10694' and int(wait['observation']['gpu_inventory'].split(',')[2])==10743
  assert all(str(t.get('gpu'))!='1' for ts in q['gpu_queues'].values() for t in ts if t.get('status') in ['running','claiming'])
  head=subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'rev-parse','HEAD'],text=True).strip();assert head==task['code_commit']
  assert subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'diff','--cached','--name-only'])==b''
  assert subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'status','--porcelain=v1','--untracked-files=all','-z']).hex()==before['status_hex']
  assert all(sha(ROOT/'Cluster'/p)==h for p,h in before['files'].items())
  for n in ['experiments/M206-CGCA.json','experiments/M211-BTC.json','experiments/M212-BCR.json','experiments/M213-BFC.json','admissions/M211-BTC.json','admissions/M212-BCR.json','admissions/M213-BFC.json','experiments.csv']:
   assert sha(ROOT/'pipeline'/n)==before['protected_ledgers'][n],n
  work_path=ROOT/'pipeline/research_work.json';work=read(work_path);c=next(x for x in work['candidates'] if x.get('experiment_id')=='M214-CTS')
  c.update(stage='deployment',training_status='waiting',deployment_status='ADMITTED_WAITING_GPU0_BUSY_NO_LAUNCH',efficacy='UNKNOWN',resource_wait={'evidence':ref(wait_path),'server':'server-4','physical_gpu':0,'occupied_mib':10743,'observed_context':'3381194, 10694','identity':'UNKNOWN_NOT_PROBED','next_check':'Fresh canonical selectedGPU0 occupation/source/admission checks before a future dispatch; no new GPU1 use.'},next_action='CTS is technically admitted and FIFO waiting on server4 physicalGPU0 only. Actual canonical dispatch saw busyGPU0 and made zero Popen requests; saved result is terminal no-launch, not an uncertain training process. Preserve this original attempted dispatch and its postwrite filename-collision error; do not replay its helper. Future canonical queue dispatch may start only after fresh GPU0 UUID/no-context/idle/assets/locks/current policy checks pass. No eviction, other-card fallback or GPU1 computation. BEC R1 waits independently for GPU0/new exact026c-bound native gates.')
  paths=[HERE/'cts_dispatch_result.json',HERE/'cts_admission_queue_result.json',ROOT/'pipeline/admissions/M214-CTS.json',ROOT/'pipeline/authorizations/server4_gpu0_only_20261026.json',wait_path]
  for p in paths:
   item=ref(p)
   if item not in c['evidence']:c['evidence'].append(item)
  bec=next(x for x in work['candidates'] if x.get('experiment_id')=='M215-BEC')
  bec['next_action']='Keep original9b two native smoke successes and original bool index_fill JIT resource failure plus registeredR1 negative history. CPU compatibility/singleliteral repair and isolated026c(parent4e8) are prepared, not native-resource PASS. User now allows only server4GPU0; prepare a fresh0-only R1 source-bound packet and run actual original fixed paired native/resource gates when GPU0 is genuinely idle, never useGPU1 or relabel old raw.'
  work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':c['id'],'kind':'resource_check','result':'blocked',
   'command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_e245536a/cts_promotion_execute/dispatch_cts.py --execute-root',
   'observation':'Actual current GPU0-only admission and FIFO task were created using immutable old45eb CTS0 native evidence. One canonical dispatch made only a selectedGPU0 inventory query, found10743MiB busy, issued zero Popen/sync/launch, and saved waiting/verifiedfalse result. A subsequent duplicate result filename writer raised FileExistsError; actual task/transport/read-onlyNVML reconcile prove known no-launch, no retry. GPU1 was never queried/used. Efficacy UNKNOWN.',
   'evidence':[ref(p) for p in paths]}
  now=datetime.now(timezone.utc).isoformat();work['updated_at']=now;work['next_action']=c['next_action']
  assert len(work['candidates'])==141
  with (HERE/'final_persist_intent.json').open('x',encoding='utf8') as f:json.dump({'token':owner['token'],'work_before_sha256':sha(work_path),'scope':'Audit metadata after actual verified CTS0 launch; partial journal means no replay.'},f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  save(work_path,work)
  memory_path=ROOT/'pipeline/codex_memory.md';m=memory_path.read_text('utf8');lines=m.splitlines()
  def line(prefix,value):
   places=[i for i,x in enumerate(lines) if x.startswith(prefix)];assert len(places)==1;lines[places[0]]=value
  line('- 最新接管',f'- 最新接管{owner["token"]}，actual target/thread01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner["generated_at"]}/实际deadline{owner["deadline_at"]}。因人类GPU1撤回先合法finish45eb、manual资源0后新begin；本次操作stop仍05:52:30，不用新lease延时。finish以实际receipt为准。')
  line('- 最新直接人类资源','- 最新直接人类不用gpu1已应用：SERVERS SHA2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1仅server4physical[0]/max1；authorizations/server4_gpu0_only_20261026.json SHA94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09。旧GPU1 grant仅历史合法依据，不再授权未来GPU1计算；M206暂停/其他allowed[]/调度Disabled保持。')
  line('- M214-CTS validation','- M214-CTS已技术准入、FIFO waiting GPU0，精确source4e80006047d5cb3dcdfb9c1102e02c33f354a07d/单父48fc与原9A/YAML。receipt pipeline/admissions/M214-CTS.json SHA5416d5e…；当前无PID/无launch，实际GPU0占10743MiB，等待真空闲。历史45eb GPU0四真臂/a33c/5d2f保持原owner/版本，只current部署门更新，不重标或重跑历史。')
  line('- 采集','- 采集2026-10-26T13:47:46.634601+08:00：selected GPU0 UUID958e，NVML10743MiB/util1/context3381194:10694MiB，归属用途未知、未探/proc/发信号。当前canonical一次派发0Popen，CTS仍waiting/noPID；未sync或launch。没有查询/使用GPU1。BFC原20轮crash、BCR27/.4995早停已归档，当前CTS效果未知。')
  line('- 当前原BFC/BCR','- 当前0running、1ready CTS waiting GPU0资源；另M206waiting但paused/dispatch_hold/resume_authorizedfalse不计ready。BEC R1隔离026c child4e8/CPU兼容修复已准备，实际R1 native/resource未跑；原BFC checkpoint19保留待具体恢复计划/人类授权。GPU1禁止。')
  line('- 前b5dc/521已见','- 历史b5dc/521曾见未知PID1565126额外占卡且最小归属读取PermissionError；历史f15/509两次NVML未列该PID，不等于证明其退出/归属。本轮新0-only只核被授权GPU0，不读或计算GPU1，不重复身份探查/发信号。')
  m='\n'.join(lines)+'\n';m=m.split('\n## Last Tick')[0]+f'''
## Last Tick
- 旧45eb四真臂及两原terminal已完整report/finish/FINALIZED/released；新用户不用gpu1后manual授权94075与SERVERS2583实际仅[0]，本轮e245新snapshot容量1。TEST_OWNER45eb/旧raw不改，CURRENT_OWNER e245/current0部署分开，原05:52:30操作stop保留。
- 复用同源4e8、当时合法GPU0真实2TRAIN+资源/a33c/独审5d2f，当前owner下只exact9A ff48fc→4e8，28status+bytes/index空保持；生成真实标准摘要/技术收据M214、canonical admission+budget/FIFO/一次_process_queue。其selectedGPU0 inventory10743MiB忙，仅查询/0Popen/0sync/0launch，仍waiting无PID，不是原生进度通过。
- CTS仅server4GPU0等待资源，原数据/seed1999/epochs50/maxiters70/YAML保持，训练效果未知。1准入/1queue/0新训练启动。随后wrapper duplicate result writer FileExistsError已据原result/transport/只读NVML核定known no-launch，不重跑helper；没有GPU1查询或任务。
- BEC原9b两smoke已成功但resource JIT bool index_fill失败；R1已注册/CPU精确兼容/单True→1+隔离026c(父4e8)独立保存，不旧raw重标，新native/资源仍NOT_RUN，后续仅GPU0空槽。BFC原last19完整CPU元信息/失败保留，根因/输入未复现，未自动resume；M206暂停、BCR终态不动。
- 0新候选/141IDs；当轮只CTS准入部署及BEC next_action更新，原终态账/admission/28用户文件保护。原新建准备预算不强凑候选，只有GPU0且CTS已占用，不为填buffer重跑旧hold/655/旧测试。
- 六段报告与七段memory留档后核实际FINALIZED/released和lock/pending消失；释放后不回写。后续监测只报告新结果/故障/必要用户动作。
'''
  assert m.count('\n## ')==7 and len(m.splitlines())<120;save(memory_path,m)
  notes={'actions':[
   '响应直接用户不用gpu1：旧45eb已按旧不变snapshot完整收尾，再manual更新server4 allowed[0]/每卡1和新授权记录94075、SERVERS2583；新begin容量1，历史GPU1 raw保持原时间/版本，不再GPU1计算。',
   '当前owner/current0策略与历史TEST_OWNER45eb的CTS0实证明确分离，同源4e8四臂/a33c/5d2f未重标或重跑。当前技术核验只exact9A本地ff48fc→4e8、原28status/bytes/index保护、3标准摘要/收据/canonical admission+budget均实际通过。',
   'CTS按FIFO只GPU0一次canonical派发，selectedGPU0查询见10743MiB占用，0Popen/0sync/0launch，仍waiting/noPID。后置phase_result重复同名文件报错，已按原result+transport+新NVML核对known no-launch，没有重放；未假称原生进度或启动成功。',
   'BEC原profiler兼容失败及原raw保留，注册R1 CPU测试/私有单literal修复/隔离026c源准备不代新版native资源PASS；原BFC数据加载crash/last19恢复缺口和BCR正常earlystop27/.4995、M206pause保持。',
   '本轮1技术准入/1队列/0新训练启动、0新候选，未用新owner延长本次05:52:30操作stop；只有GPU0获准但被实际context占用，不挤占、不改调度或自动恢复其他实验。'],
   'decisions':['最新GPU0-only约束立即并已持久生效；CTS已就绪排队，待GPU0真正空闲后canonical新观测派发，不重放本轮一次helper。BEC R1同卡等待新source-bound原生门；原BFC仍先定位失败输入/具体恢复方案，不自动重启或借旧授权。']}
  save(HERE/'report_notes.json',notes)
  save(HERE/'final_persisted.json',{'token':owner['token'],'CTS_task':task,'verified_native_progress':False,'only_GPU0':True,'memory_lines':len(m.splitlines()),'new_admissions':1,'new_launches':0,'postflight':'NOT_YET_CALLED'})
  print(json.dumps({'status':'CTS_GPU0_ADMITTED_WAITING_BUSY_NO_LAUNCH_AUDIT_READY','memory_lines':len(m.splitlines())}))
 finally:lock.close()
if __name__=='__main__':main()
