"""Current registered-slot check and one prepared AEF catalogue handoff.
No GPU/model/source/queue/experiment operation; missing CTS remains canonical pending.
"""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,importlib.util,json,os,sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'tick_150c2902';PREP=OLD/'new_candidate_prepare'
OP=ROOT/'pipeline/diagnostic_bundles/tick_faccbed6/bec_r1_operational_prepare'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CTS='hierarchy-parent-cyclic-triadic-state-composition';BEC='hierarchy-cross-level-bipartite-edge-composition';AEF='hierarchy-parent-antisymmetric-edge-flux'
TOKEN='01d2f5482cb54841a4ca285805401771'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def data(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def save(p,x):
 with Path(p).open('xb') as f:f.write(data(x));f.flush();os.fsync(f.fileno())
def replace(p,b):
 t=p.with_name(p.name+'.'+TOKEN+'.aef.tmp')
 with t.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def main():
 owner=guard();assert owner['token']==TOKEN
 assert not (HERE/'aef_registration_intent.json').exists() and not (HERE/'bec_registered_slot_check.json').exists(),'Existing phase requires reconciliation, not replay'
 assert sha(PREP/'preparation.json')=='9d6a03ba72c37b518d54f072400a4ecb3b042783b9e74e1d32a5169cfc50d990'
 assert sha(PREP/'candidate_record.json')=='3898be398097d819ce8029112d6cd361bc97f462c57eadf9c7aacf4b161794f0'
 assert sha(OLD/'aef_source_topology_independent_review.json')=='27d6266fd98dcafd64b8351f7bc8143dad44d5c9a6a15d86f19fb408b6786aca'
 p=read(PREP/'preparation.json')
 for n,h in p['prepared_file_hashes'].items():assert sha(PREP/n)==h,n
 for n in ['aef_frozen_handoff_check.json','aef_preparation_reuse_review.json']:
  assert (HERE/n).is_file()
 reuse=read(HERE/'aef_preparation_reuse_review.json');assert reuse['material_concerns']==[]
 exit_proof=read(HERE/'cts_exit_readonly_evidence.json');assert exit_proof['owner_token']==TOKEN and exit_proof['observation']['original_PID_present'] is False
 assert exit_proof['observation']['last_train_progress']==[14,50,1843,4686]
 baseline=read(HERE/'protected_assets_before.json');before=snapshot()
 assert all(before[k]==baseline[k] for k in ['head','index_empty','status_hex','files','protected_ledgers','candidate_digests'])
 q=read(ROOT/'pipeline/queue.json');t=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M214-CTS')
 assert t['pid']==3505065 and t['status']=='running' and str(t['gpu'])=='0'
 dw=read(ROOT/'pipeline/deathwatch.json');cts_key=Path(t['config']).stem
 assert dw['server-4'][cts_key]['missed']==2,'Preserve canonical consecutive-observation threshold; no forced third poll'
 ctx=read(ROOT/'pipeline/headless/.tick_context.json');assert ctx['experiment_first']['enabled'] is True
 assert ctx['research_work']['creation_budget']==1
 names=list(baseline['protected_ledgers']);registry={n:sha(ROOT/'pipeline'/n) for n in names}
 events=[];calls=[]
 def audit(event,args):
  if event=='subprocess.Popen' or event.startswith('socket.'):
   events.append(event);raise RuntimeError('NoTransport prohibits process/network')
 sys.addaudithook(audit)
 spec=importlib.util.spec_from_file_location('actual_R1_registered_slot_adapter',OP/'adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 class NoTransport:
  def call(self,*a,**k):calls.append(a[:1]);raise RuntimeError('NoTransport')
 adapter=module.Adapter(root=ROOT,origin=OP,frozen=OP/'native',transport=NoTransport(),execution_dir=str(HERE/'bec_r1_execution'))
 outcomes={}
 for gpu in (0,1):
  try:adapter.prepare(gpu)
  except module.Refused as e:outcomes[str(gpu)]={'refused':True,'reason':str(e)}
  else:raise AssertionError('Unexpected resource preparation success')
 assert outcomes['0']['reason']=='Selected GPU has registered running task',outcomes
 assert outcomes['1']['reason']=='Explicit physical GPU0 is required for R1',outcomes
 assert not calls and not events and 'torch' not in sys.modules and not (HERE/'bec_r1_execution').exists()
 guard();assert registry=={n:sha(ROOT/'pipeline'/n) for n in names}
 resource={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'candidate_id':BEC,'outcomes':outcomes,'resource_check_result':'blocked','reason':'Original CTS PID is absent; canonical deathwatch is only2/3 and still reserves GPU0. PhysicalGPU0 was observed idle in293136 evidence, so this is lifecycle-registration pending, not proof of real GPU busy. Do not force a third poll, restart CTS, or reuse a prior healthy observation.','CTS_exit_evidence':ref(HERE/'cts_exit_readonly_evidence.json'),'transport_calls':0,'process_network_events':events,'Torch_imported':False,'active_execution_directory_created':False,'native_R1':'NOT_RUN','resources_R1':'NOT_RUN','shared_ledgers_unchanged':True}
 save(HERE/'bec_registered_slot_check.json',resource)
 # All process/Git work for protection was done before the strict audit hook.
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();wp=ROOT/'pipeline/research_work.json';w=read(wp);out=copy.deepcopy(w)
  assert len(w['candidates'])==141 and AEF not in {x['id'] for x in w['candidates']}
  assert not any(x.get('experiment_id')=='M216-AEF' for x in w['candidates'])
  a=read(PREP/'candidate_record.json');assert a['id']==AEF and a['experiment_id']=='M216-AEF' and a['code_commit'] is a['source_commit'] is None
  assert a['native_status']==a['resource_status']=='NOT_RUN' and a['stage']=='implementation'
  now=datetime.now(timezone.utc).isoformat()
  a.update(created_at=now,registered_at=now,goal_sha256='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85',authorization=ctx['experiment_first']['authorization'],resource_authorization={'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'},preparation_scope='Original150c frozen software evidence retained; current registration only, no native/FP32/GPU/resource/efficacy PASS or source version.',next_action='Prepare an actual compatible isolated source version and native worker from these exact frozen9 files after canonical original CTS terminal confirmation. Then fresh soleGPU0 idle/UUID/assets/three-lock/current-owner/original-deadline checks and original M95/AEF TRAIN2+resources. BEC R1 remains nearer admission and has priority; no GPU1, eviction, resampling, threshold changes or old-held reopening.')
  for e in [ref(OLD/'aef_research_boundary_review.json'),ref(OLD/'aef_source_topology_independent_review.json'),ref(HERE/'aef_frozen_handoff_check.json'),ref(HERE/'aef_preparation_reuse_review.json')]:
   if e not in a['evidence']:a['evidence'].append(e)
  out['candidates'].append(a)
  c=next(x for x in out['candidates'] if x['id']==CTS);b=next(x for x in out['candidates'] if x['id']==BEC)
  c['training_status']='process_missing_pending_terminal_confirmation'
  c['runtime_issue']={'observed_at':exit_proof['observation']['observed_at'],'kind':'original_PID_absent_no_terminal_marker','pid':3505065,'last_train_progress':[14,50,1843,4686],'canonical_deathwatch':'2/3','cause':'UNKNOWN','evidence':ref(HERE/'cts_exit_readonly_evidence.json'),'no_restart_or_resume':True}
  c['next_action']='Original CTS3505065 is absent; own log stops TRAIN14/50 step1843 without terminal/exception marker. Preserve original code/admission/log/checkpoints; next ordinary canonical observation must confirm terminal threshold before exact archival. No forced extra deathwatch poll, automatic restart/resume or claim of healthy training.'
  for e in [ref(HERE/'cts_exit_readonly_evidence.json')]:
   if e not in c['evidence']:c['evidence'].append(e)
  b['current_resource_check']={'result':'blocked','kind':'registered_original_CTS_terminal_confirmation_pending','evidence':ref(HERE/'bec_registered_slot_check.json'),'physical_scope':'Prior current-tick GPU0 idle observation; no continuous exclusivity or real-busy claim.'}
  b['next_action']='Wait for next ordinary canonical CTS terminal confirmation (currently missing originalPID, deathwatch2/3), preserve its exact run. Then fresh physicalGPU0 idle/UUID/assets/three-lock binding and all original R1 four native/resource arms, only when enough original deadline remains (>1020s per run). No GPU1 or blind restart.'
  if ref(HERE/'bec_registered_slot_check.json') not in b['evidence']:b['evidence'].append(ref(HERE/'bec_registered_slot_check.json'))
  assert b['revision_history'][0]['result']=='pending' and b['native_execution_code_commit'] is None
  if w.get('tick_attempt'):out.setdefault('tick_attempt_history',[]).append(copy.deepcopy(w['tick_attempt']))
  out['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':BEC,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+Path(__file__).as_posix(),'observation':'Actual current R1 production prepare0 refused the original CTS registered reservation while originalPID is absent and canonical deathwatch2/3; prepare1 refused explicit GPU0-only scope. Zero transport/process/network/Torch/active state. PhysicalGPU0 idle evidence is kept separate, not fabricated busy. R1 native/resources NOT_RUN.','evidence':[ref(HERE/'bec_registered_slot_check.json')]}
  out['updated_at']=now;out['next_action']='Confirm original missing CTS terminal through next ordinary canonical observation, preserve its exact checkpoint/log/source; no restart. BEC R1 is first for actual native gates after safe release; AEF exact-source preparation is registered as the only new candidate and remains unversioned/native-unrun. OnlyGPU0; M206 paused.'
  unchanged=lambda z:{x['id']:x for x in z['candidates'] if x['id'] not in (CTS,BEC,AEF)}
  assert unchanged(out)==unchanged(w) and len(out['candidates'])==142
  oldmem=(ROOT/'pipeline/codex_memory.md').read_text('utf8')
  # Rebuild all seven sections, retaining unchanged project/history paragraphs.
  sections={};key=None
  for line in oldmem.splitlines():
   if line.startswith('## '):key=line;sections[key]=[]
   elif key:sections[key].append(line)
  headers=['## Goal And Phase','## Champion And Baseline','## Active Hypotheses','## Closed Or Failed Directions','## Running And Queue','## Open Questions And Risks','## Last Tick'];assert set(sections)==set(headers)
  sections[headers[0]][0]='- 当前01d2f5482cb54841a4ca285805401771，实际会话/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T14:05:55.958593+00:00/deadline15:05:55.958593+00:00原值保持。'
  active=sections[headers[2]]
  active=[line for line in active if not line.startswith('- 本轮仅currentowner')]
  active[0]='- M214-CTS原source/primary/runtime4e80006047d5cb3dcdfb9c1102e02c33f354a07d与receipt5416保持；原PID3505065本轮已不见，最近原日志TRAIN14/50 step1843，causeUNKNOWN，非正常完成/非机制失败。canonical2/3缺失待下一次确认，不自动重启/续训。'
  active += ['- M216-AEF（hierarchy-parent-antisymmetric-edge-flux）本轮唯一新登记，stageimplementation/code+source=null，未Git/部署/原生/FP32/资源/效果；沿用原150c截止前冻结9源码配置prep9d6a03/candidate3898be、独审27d626（21集成+46独立stdlib性质），本轮交接011e37/复用cd1a6无重跑旧suite。', '- AEF仅替middle FFN：同原父组detached几何MST，qij=GELU(W[xi,xj])-GELU(W[xj,xi])，同q以+/- incidence写两端；原LN/skip/fine/coarse/rawmean/CSORT/HCG/单inst保留。只实数unweighted token sum代数性质，不保RSTR π加权pointmean，不是Markov/旧RSTR修复或新增额度。理论参数−394240/实际资源未知。', '- AEF后续先实际兼容版本及native工具，再在BEC优先、唯一GPU0释放且fresh当前owner/idle/UUID/assets/三锁/原deadline充足时跑原M95/AEF固定TRAIN2和原资源；原seed/data/YAML/schedule不变，无新候选替名。']
  sections[headers[2]]=active
  sections[headers[4]]=['- 当前canonical仍登记CTS running，但本轮原PID已无，ownlog14/50 step1843无终态/异常关键字；证据tick_01d2f548/cts_exit_readonly_evidence.json SHA293136ca8c011e88b31307c948baa7ec4de82a9a051ab65f76e38e8932e32b41。canonical只reconcile到deathwatch2/3，不强行第三次归档，真实训练进度不再确认。', '- GPU0本轮只读观测41MiB/util0/无context，是该时间点物理idle，不等于canonical槽位已释放或后续独占。BEC真实current prepare0被原CTS登记占位拒绝，prepare1被明确0-only拒绝；0transport/Torch/process/network/active，不是GPU实忙或native PASS。', '- 当前0已确认训练、1登记待终态，0ready；M206仍waiting但paused/dispatch_hold/resume_authorized=false，GPU1禁止。AEF只新登记准备，R1未准入；BFC不恢复。', *[line for line in sections[headers[4]] if line.startswith('- pinned') or line.startswith('- 未知claim')]]
  sections[headers[5]]=['- CTS停止原因UNKNOWN；原ownlog末段无异常/正常结束标记，不推断OOM、外部kill、崩溃或模型失败。原checkpoint保留未做新恢复准备/授权，不借HAP等grant；本轮未执行任何GPU/恢复。', *[line for line in sections[headers[5]] if line.startswith('- 目标gap') or line.startswith('- 原CTS/')]]
  sections[headers[6]]=['- 旧150c因上游capacity中断，14:04恢复时已过原13:12deadline；核agents完成/相关本地writer0/141候选与12账全同，原token canonical abort为INCOMPLETE/released后才新begin。旧AEF prep/test/peer均原deadline前，旧原始声明/owner不改。', '- 本轮fresh snapshot creation/reserve1，只登记同一AEF一个prepared候选；0新源码修订/Git/准入/入队/训练启动。CTS新观测由旧healthy变为原PID缺失，canonical额外reconcile只到2/3，槽位保留。', '- 当前真实tick_attempt为BEC resource_check/blocked（registered原CTS终态确认pending，非硬件忙），AEF原软件证据仅按原时间复用，无伪造当前新native或重跑套件。', '- 原141中的139候选、全部12受保护账/primary4e8/28用户文件status+bytes/index空保持；只work中CTS/BEC证据与新增AEF、memory/notes改变。六段report/七段memory后canonical finish，最终以真实receipt/释放为准，释放后不回写。']
  mem='# Codex Research Memory\n\n'+'\n'.join(h+'\n'+'\n'.join(sections[h]).strip()+'\n' for h in headers)+'\n';assert len(mem.splitlines())<120 and mem.count('\n## ')==7
  notes={'actions':['安全释放已确认中断的旧150c原租约；原AEF冻结/独审在旧deadline前，当前接续同一候选，不延长或重造旧snapshot。','当前CTS原PID3505065缺失，ownlog停TRAIN14/50 step1843无终态或异常关键字；当前物理GPU0观测41MiB/0util/无context。canonical reconcile到deathwatch2/3，未强行第三次轮询归档，未重启/恢复/触碰checkpoint。','真实当前BEC生产prepare0因原CTS登记占位拒绝，prepare1因明确0-only拒绝；0transport/process/network/Torch/active，属于登记终态确认pending，非硬件实忙或native资源PASS。','本轮唯一登记M216-AEF：固定父组几何MST上的双向共享非线性反对称通量，原middle LN/skip及fine/coarse/rawmean/CSORT/HCG保持；复用旧136+850作者软件检查和21集成/46独立stdlib证明，不重跑旧套件，不代签Torch/FP32/梯度/资源/效果。','AEF code/source仍null、尚未Git或入队；本轮1候选登记，0native/GPU/版本提交/准入/派发/训练启动。原139其他候选与12账/28用户文件/index保护保持。'],'decisions':['CTS停止原因未知，保留原code/admission/log/checkpoint，待下一普通canonical观察确认第三次缺失后精确归档；不得把日志无异常写为正常完成或直接断言模型崩溃，不自动续训。','BEC R1优先等原登记槽位合法释放；再fresh GPU0 idle/UUID/assets/三锁且每run原deadline余量>1020秒才真实四臂。GPU1保持禁用，不驱逐或强改资源。','AEF是独立middle signedMST图，不是旧RSTR/PCE恢复/额外修订；实数unweighted sum与旧π加权门分开，原held失败/额度/门不改。','本轮按实际resource_check/blocked与单一prepared登记收尾，最终以canonical finish/FINALIZED released为准；无新增人工确认请求。']}
  wb,mb=data(out),mem.encode();data(notes)
  previous={'work_sha256':sha(wp),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
  save(HERE/'aef_registration_before.json',{'owner_token':TOKEN,'hashes':previous,'candidate_digests':before['candidate_digests'],'protected_ledgers':registry,'CTS_before':next(x for x in w['candidates'] if x['id']==CTS),'BEC_before':next(x for x in w['candidates'] if x['id']==BEC),'tick_attempt_before':w.get('tick_attempt')})
  save(HERE/'aef_registration_intent.json',{'owner_token':TOKEN,'recorded_at':now,'scope':'Only existing CTS/BEC runtime evidence + ONE prepared AEF + work tick_attempt/currentmemory','before':previous,'new_candidate':AEF})
  guard();assert sha(wp)==previous['work_sha256'] and registry=={n:sha(ROOT/'pipeline'/n) for n in names}
  replace(wp,wb);replace(ROOT/'pipeline/codex_memory.md',mb);save(HERE/'report_notes.json',notes)
  assert read(wp)==out and unchanged(read(wp))==unchanged(w) and registry=={n:sha(ROOT/'pipeline'/n) for n in names}
  assert all(sha(ROOT/'Cluster'/n)==h for n,h in baseline['files'].items())
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'candidate_count':142,'new_candidate_ids':[AEF],'other139_candidates_unchanged':True,'all12_lifecycle_ledgers_unchanged':True,'protected28_files_unchanged':True,'primary_source_not_modified':True,'CTS_state':'original_PID_absent_canonical_deathwatch2of3_pending','new_training_launches':0,'native_AEF':'NOT_RUN','native_BEC_R1':'NOT_RUN','memory_lines':len(mem.splitlines()),'work_sha256':sha(wp),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md'),'notes':ref(HERE/'report_notes.json')}
  save(HERE/'aef_registration_result.json',result);print(json.dumps({'status':'ONE_PREPARED_AEF_REGISTERED_CURRENT_RESOURCE_BLOCK_RECORDED','result':ref(HERE/'aef_registration_result.json'),'memory_lines':len(mem.splitlines())},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
