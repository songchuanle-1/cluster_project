"""Audit completed research before applying a new explicit GPU0-only resource policy."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
 tmp=p.with_name(p.name+'.45ebfinal.tmp')
 with tmp.open('x',encoding='utf8') as f:
  if isinstance(x,str):f.write(x)
  else:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
  f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def main():
 owner=guard();assert not (HERE/'close_resource_change_intent.json').exists()
 semantic=HERE/'cts_actual_four_result_review.json';peer=HERE/'cts_four_actual_results_independent_review.json'
 assert sha(semantic)=='a33c0fe74f0e2860aa2f9fb0b7fe066aad27a4ee34e7937c06c7b62001a33121' and read(semantic)['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION'
 assert sha(peer)=='5d2f0716ca790ab6e2fdde9026950b89c637ea61067442a515e48f8ace1e0652' and read(peer)['material_concerns']==[]
 archive=read(HERE/'exact_terminal_archive_result.json');assert {x['id']:x['state'] for x in archive['results']}=={'M213-BFC':'crashed','M212-BCR':'done_earlystop'}
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();before=read(HERE/'protected_assets_before.json')
  for n in ['experiments/M206-CGCA.json','experiments/M211-BTC.json','admissions/M211-BTC.json','admissions/M212-BCR.json','admissions/M213-BFC.json']:
   assert sha(ROOT/'pipeline'/n)==before['protected_ledgers'][n]
  assert subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'rev-parse','HEAD'],text=True).strip()=='48fc302c3c02ffef0b241be3593c386b6b65a72e'
  assert subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'diff','--cached','--name-only'])==b''
  assert subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'status','--porcelain=v1','--untracked-files=all','-z']).hex()==before['status_hex']
  assert all(sha(ROOT/'Cluster'/p)==h for p,h in before['files'].items())
  q=monitor.load_queue(str(ROOT));assert not any(t.get('status') in ['running','claiming'] for ts in q['gpu_queues'].values() for t in ts)
  assert not any(monitor.load_running(str(ROOT)).values()) and not (ROOT/'pipeline/admissions/M214-CTS.json').exists()
  path=ROOT/'pipeline/research_work.json';work=read(path);old=copy.deepcopy(work)
  c=next(x for x in work['candidates'] if x.get('experiment_id')=='M214-CTS')
  c.update(native_status='ACTUAL_TRAIN2_AND_ORIGINAL_RESOURCE_PAIR_PASSED_INDEPENDENTLY_REVIEWED',native_smoke_status='ACTUAL_TWO_STEP_PASSED',resource_status='ACTUAL_ORIGINAL_PROTOCOL_PASSED',resource_profile_status='ACTUAL_ORIGINAL_PROTOCOL_PASSED',native_execution_code_commit='4e80006047d5cb3dcdfb9c1102e02c33f354a07d',admission_status='NOT_YET_ADMITTED',
   next_action='Preserve exact four actual CTS GPU0 results from tick45eb and both semantic reviews; user now explicitly forbids GPU1. Close original immutable snapshot, apply authorized GPU0-only policy, acquire fresh owner and separately bind current GPU0 admission/ff/FIFO dispatch guards to immutable historical test owner45eb. Do not relabel/reexecute old raw or use GPU1. Current source4e8 remains exact9A child48fc; no ff/receipt/queue/launch occurred yet.')
  for p in [semantic,peer,HERE/'exact_terminal_archive_result.json',*(HERE/'cts_execution'/(m+'_'+t+'_execution.json') for m in ['smoke','resources'] for t in ['champion','candidate'])]:
   item=ref(p)
   if item not in c['evidence']:c['evidence'].append(item)
  bfc=next(x for x in work['candidates'] if x.get('experiment_id')=='M213-BFC');bfc['checkpoint_best_miou']=0.4992169439792633
  for p in [HERE/'bfc_crash_diagnosis.json',HERE/'bfc_checkpoint_readonly_evidence_r2.json',HERE/'bfc_checkpoint_readonly_summary.json',HERE/'bfc_resume_plan.md']:
   item=ref(p)
   if item not in bfc['evidence']:bfc['evidence'].append(item)
  bfc['next_action']='Preserve original BFC crash and verified epoch19 last checkpoint; exact checkpoint best .4992169439792633 is distinct from rounded terminal-log .499. Diagnose failing data tensor overlap, then complete concrete source-compatible recovery plan and BFC-specific human resume authorization. Only GPU0 is now allowed; do not use GPU1, cold restart or borrow HAP/M206 grants. This hold never blocks CTS.'
  bec=next(x for x in work['candidates'] if x.get('experiment_id')=='M215-BEC');source_path=HERE/'bec_r1_version_operation/isolated_source_version.json';source=read(source_path)
  assert sha(source_path)=='617203db75c05528e4d0a58b94309edb6b86888bcb91f3a73cf5fc18e1bc089e' and source['code_commit']=='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563' and source['parent_commit']=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
  bec['prepared_revision_source_version']={'revision':1,'code_commit':source['code_commit'],'parent_commit':source['parent_commit'],'evidence':ref(source_path),'native_resources':'NOT_RUN','scope':'New compatible R1 isolated source only; candidate original9b and its actual raw version remain unchanged until new reviewed execution binding.'}
  for p in [HERE/'bec_r1_cpu_trace_evidence.json',HERE/'bec_r1_prepare/preparation.json',HERE/'bec_r1_implementation_independent_review.json',source_path]:
   item=ref(p)
   if item not in bec['evidence']:bec['evidence'].append(item)
   if item not in bec['revision_history'][-1]['evidence']:bec['revision_history'][-1]['evidence'].append(item)
  work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':c['id'],'kind':'native_smoke','result':'passed',
   'command':"python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/review_cts.py --project D:/project/cluster_project --execution-dir D:/project/cluster_project/pipeline/diagnostic_bundles/tick_45eb3b04/cts_execution --output D:/project/cluster_project/pipeline/diagnostic_bundles/tick_45eb3b04/cts_actual_four_result_review.json",
   'observation':'Real CTS two original TRAIN loss/backward/optimizer steps and four actual matched arms passed unchanged semantic checker and independent review; original counted9.761811532G below10G. Not efficacy or admission. BCR earlystop27 and BFC dataloader crash canonically archived. BEC native two steps succeeded but resource JIT bool index_fill failed; R1 preregistered and CPU minimal trace repair supported. User then revoked GPU1, so no old-bound ff/admit/launch; safe immutable-snapshot handoff to GPU0-only policy.',
   'evidence':[ref(semantic),ref(peer)]}
  work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=c['next_action']
  assert len(work['candidates'])==141
  with (HERE/'close_resource_change_intent.json').open('x',encoding='utf8') as f:json.dump({'token':owner['token'],'work_before_sha256':sha(path),'user_latest_instruction':'不用gpu1','scope':'Metadata/report closure only; no new GPU, ff, queue or launch. Apply GPU0-only SERVERS after old receipt released, never modify old context.'},f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  save(path,work)
  p=ROOT/'pipeline/codex_memory.md';memory=p.read_text('utf8');lines=memory.splitlines()
  def line(prefix,value):
   indexes=[i for i,x in enumerate(lines) if x.startswith(prefix)];assert len(indexes)==1;lines[indexes[0]]=value
  line('- 最新接管',f'- 最新接管{owner["token"]}；actual owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner["generated_at"]}/原deadline{owner["deadline_at"]}不延长。本轮实测后用户明确不用gpu1，立即停止后续GPU1操作；先审计收尾旧不变snapshot，再应用GPU0-only新策略/新owner，不重标历史raw。')
  line('- 最新人类资源','- 最新直接人类资源指令2026-10-26：不用gpu1。后续仅server4physicalGPU0，立即约束全部动作；本轮旧snapshot/SERVERS仍d527[0,1]只为审计收尾，释放后manual改allowed[0]+留授权/decision，再新begin。旧90f882等只解释当时合法历史，不是未来GPU1许可。M206暂停保持，调度不改。')
  line('- M213-BFC正式training','- M213-BFC原run在TRAIN20/50 step3832/4686共享DataLoader scatter overlap RuntimeError中断，canonical crashed archiveb91b3ba11671451bb28f39dc3cc3f2c7。科学source48fc/原receipt812454/launch/log均保留，非BFC机制否定；原日志max.499为3dp。CPU核last.pth SHA24b3424f… epoch19/optimizer+scheduler/best.4992169439792633/noimprove4；完整1151tensor finite，640optstate/5group/maxstep89034。RNG/sampler/失败输入未复现，不能称续3833；原native恢复仍需具体兼容source计划及BFC专属人类授权，不借其他grant，不自动恢复。')
  line('- M212-BCR tested/admitted','- M212-BCR原run native earlystop27/patience10/best.4995，canonical archive5d060afca23d43deb4ae63525c00ff3d，未超M95.5020；原scientific11a/receiptb853/public48fc下8源/YAML/launch保持，无重启。')
  line('- 采集','- 本轮45eb初严格running observer遇原PID缺失即停止，随后两次独立只读确认两PID均不存在/原日志不再更新，完整log本远hash相同。BFC crash20、BCR nativeearlystop27已精确canonical finalize_task归档，未伪造deathwatch第三tick、未发信号；0running/0ready/M206paused。')
  line('- 当前2running/0ready','- 当前原BFC/BCR均已归档、0running/0ready，CTS四真臂已通过待GPU0-only新owner准入，BEC原两smoke成功但资源JIT失败、R1已注册CPU最小复现及私有True→1单行修复已完成；M206waiting但paused/dispatch_hold/resume_authorizedfalse，不用GPU1。')
  memory='\n'.join(lines)+'\n';memory=memory.split('\n## Last Tick')[0]+'''
## Last Tick
- 本轮45eb真实观察发现BFC/BCR均终态：精确原log+两PID稳定不存在+空context证据后调用canonical finalize_task，BFC crashed20（dataset/scatter错误）、BCR nativeearlystop27/.4995。原source/receipt/launch/全部日志及M206暂停保留，无第三monitor凑计数。
- CTS GPU0四实际臂均terminalrc0，2TRAIN loss9.547047615/13.908418655、common843/04231同初始和2batch配对，3W列原loss非零grad+update、1136/1156 distinctrows及64/60多轮真实覆盖。原82da语义审a33c+独审5d2f均通过，9.761811532G≤10G；效果/新颖/纯TRAIN峰值未知，尚无标准收据/ff/queue/启动。
- BEC GPU1在用户撤回前合法执行四臂：两smoke各2步finite成功，resourcecandidate JIT aten::index_fill(bool)内部assert rc1，原四raw全部保留、checker拒绝，无资源数值/PASS/queue。R1注册3fa782，CPU390ac50复现True失败/int1成功且三组bool mask一致；私有R1包2ef488仅一标量True→1，独审972c47通过，隔离源026c0c4单父4e8/9A/clean由617203db实证。原9b/2d/322不改、新源仅准备未native；后续仅GPU0。
- BFC CPU完整last19核验与恢复计划已保存，但失败sample/根因/clone修复未知；checkpoint best.49921694与rounded log.499分开。恢复授权未造、不自动restart，CTS独立推进。
- 最新用户不用gpu1立即生效，当前没有任何GPU1新运行；停止旧45eb双卡绑定的ff/admit/dispatch，先按原context审计report/finish，随后manual apply SERVERS[0]与授权decision并新begin。原05:52:30仍作为本次操作stop，不用新owner延长工作时间，不修改旧snapshot/deadline/raw。
- 0新候选/0模型训练启动/0准入/0主线提交或ff；CTS已测源4e8仍child48fc；BEC仅R1私有修复/兼容源保存待证据。141IDs、28用户status/bytes/index及其他历史保护；两终态归档为真实新变更，不伪称10账全不变。七段memory/真实attempt/六段report后核实际FINALIZED/released；释放后不补写本报告。
'''
  assert memory.count('\n## ')==7 and len(memory.splitlines())<120;save(p,memory)
  notes={'actions':[
   '本轮原snapshot2running后严格running观测遇原PID消失；独立两次精确原PID/ownlog与完整日志hash确认BFC20数据加载崩溃、BCR27自然早停best.4995。受审canonical finalize_task精确归档两原run，未伪造deathwatch第三tick/发信号/重启，M206暂停保持。',
   'CTS在实际GPU0使用原YAML/seed/2TRAIN数据与M95配对，4真臂terminalrc0；原loss9.547047615/13.908418655、finite backward/optimizer、3列原lossgrad/update和3distinct多轮覆盖实测，原语义+独立审核通过。原count9.761811532G/10G，15%memory条件未触发，效果未知，尚未准入启动。',
   'BEC原GPU1两smoke真2step成功，资源candidate JIT bool index_fill内部assert失败，四raw保留且标准checker拒绝；R1注册后CPU最小复现True失败/int1成功、mask逐元素一致，私有修复仅一literal，原模型/协议/handlers/数据/阈值不改，未假签native/resourcePASS。',
   'BFC固定完整last19已CPU读取校验，best.4992169439792633/noimprove4/optim+scheduler状态明确，未调用GPU或恢复，失败输入和修复未知；恢复方案保存，不借HAP/M206授权。',
   '最新直接用户不用gpu1立即生效。此后无GPU1计算/训练，原先合法历史raw不重标。旧snapshot/owner/资源哈希保持只审计收尾；释放后manual应用GPU0-only资源策略并新begin，再用历史CTS GPU0实证和fresh GPU0部署门继续。'],
   'decisions':['遵守资源撤回：不在旧双卡快照下执行原待ff/admit/dispatch，不修改快照/原deadline，不重标历史raw；先完整收尾再新资源快照。仍以本次原05:52:30操作stop，不用新owner延时。','BFC runtime故障不否定机制，BEC profiler兼容失败不作10G超标或训练负收益；均保留原失败，独立CTS可在GPU0继续。']}
  save(HERE/'resource_handoff_report_notes.json',notes)
  save(HERE/'resource_handoff_persisted.json',{'token':owner['token'],'user_instruction':'不用gpu1','old_snapshot_unchanged':True,'no_new_gpu1_work':True,'new_admissions':0,'new_launches':0,'next':'Finish old lease, apply manual GPU0-only policy then fresh begin; preserve original stop05:52:30.'})
  print(json.dumps({'status':'OLD_SNAPSHOT_AUDIT_READY_FOR_RESOURCE_HANDOFF','memory_lines':len(memory.splitlines())}))
 finally:lock.close()
if __name__=='__main__':main()
