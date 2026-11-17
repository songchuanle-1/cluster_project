"""Record one new static HPC prototype, compatible CRE preparation and exact AEF readback."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;HPC=HERE/'new_candidate_prepare'
CID='hierarchy-tree-resolvent-nonlinear-composition';CRE='hierarchy-cross-root-directed-edge-broadcast';AEF='hierarchy-parent-antisymmetric-edge-flux'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def atomic(p,v,text=False):
 guard();tmp=Path(str(p)+'.d088.final.tmp')
 with tmp.open('x',encoding='utf8') as f:f.write(v if text else json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 guard();os.replace(tmp,p)
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def protected(baseline):
 git=lambda *a:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
 assert git('rev-parse','HEAD').decode().strip()==baseline['head']
 assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==baseline['status_hex'] and not git('diff','--cached','--name-only','-z')
 for n,h in baseline['files'].items():assert sha(ROOT/'Cluster'/n)==h,n
 for n,h in baseline['protected_ledgers'].items():assert sha(ROOT/'pipeline'/n)==h,n
def main():
 guard();assert sha(HPC/'preparation.json')=='c94f9c289dbf92019d01d3674907a4765368fa3849160ff8268f7788f921a70c'
 peer=HERE/'hpc_source_topology_independent_review_final.json';assert sha(peer)=='0311d80df87c2e4f33767bea3ecc024b9dd95112aedf3719bd30efebf29f575e'
 review=read(peer);assert review['status']=='STATIC_HPC_SOURCE_TOPOLOGY_AND_INTEGRATION_REVIEWED_NOT_NATIVE_PASS' and review['material_concerns']==[]
 prep=read(HPC/'preparation.json');assert prep['candidate_id']==CID and prep['code_commit'] is None and prep['source_commit'] is None
 for n,h in prep['prepared_file_hashes'].items():assert sha(HPC/n)==h,n
 software=read(HPC/'static_validation.json');assert software['status']=='STDLIB_PRODUCTION_FUNCTION_CARRIER_AND_SOURCE_CHECKS_PASSED_NOT_NATIVE' and software['native']=='NOT_RUN' and software['resources']=='NOT_RUN' and software['torch_imported'] is False
 hpc=read(HPC/'candidate_record.json');assert hpc['id']==CID and hpc['stage']=='implementation' and hpc['experiment_id']=='M218-HPC' and hpc['code_commit'] is None
 assert len(prep['source_files'])==9 and not (ROOT/'Cluster'/hpc['config']).exists()
 final=HERE/'aef_training_progress_observation_final.json';assert sha(final)=='beeb75fe24e61772c65417ea8877d2d46dbf573f8feeebbdee5ce892316da926'
 live=read(final);assert live['returncode']==0;ob=live['observation'];samples=ob['samples'];assert samples[-1]['max_native_step']>samples[0]['max_native_step']
 guard_file=HERE/'cre_actual_current_guard.json';assert sha(guard_file)=='dfb0f6904f7d3005a6de06332076f5c4c80194cb7a0f4fcfc1eebcdcbbe71a71'
 cg=read(guard_file);assert cg['transport_calls']==0 and cg['active_binding_manifest_lease_created'] is False and cg['native_or_resources_executed'] is False
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();baseline=read(HERE/'protected_assets_before.json');protected(baseline)
  work=read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==143 and not any(c['id']==CID or c.get('experiment_id')=='M218-HPC' or Path(c.get('config','')).name==Path(hpc['config']).name for c in work['candidates'])
  context=read(ROOT/'pipeline/headless/.tick_context.json');assert context['research_work']['creation_budget']==1
  assert all(digest(c)==baseline['candidate_digests'][c['id']] for c in work['candidates'] if c['id']!=CRE)
  ae=next(c for c in work['candidates'] if c['id']==AEF);cre=next(c for c in work['candidates'] if c['id']==CRE)
  assert ae['stage']=='training' and ae['code_commit']=='56b2a96dc48cc8a88f0f7105527ef448113b1060' and cre['code_commit']=='d58576b396cfb54577652be972f3ffaffda508c9'
  now=datetime.now(timezone.utc).isoformat()
  save(HERE/'research_registration_intent.json',{'recorded_at':now,'owner':EXPECTED,'new_candidate_id':CID,'source_preparation':ref(HPC/'preparation.json'),'independent_source_review':ref(peer),'before_research_work_sha256':sha(ROOT/'pipeline/research_work.json'),'operation':'One permitted private implementation candidate plus existing CRE guard and AEF observation; no admission/queue/launch.'})
  decision=mon.log_decision(str(ROOT),'next_batch','如何补充现有层级point-feature储备而不打断GPU0训练？','登记一个HPC全树非线性组合原型；保留CRE兼容d585与当前AEF训练，原生与资源检查等待合法空槽。','HPC用原真实fine-middle-coarse森林的固定(I+L)逆算子包原3FFN，改变跨层信息流而非数值调参；仅stdlib生产函数载体/独立有理参考解与代码接线检查通过。无Torch/autograd/FP32/资源/效果结论，不重开RSTR/PCE。',json.dumps([ref(HPC/'preparation.json'),ref(peer),ref(HERE/'cre_catalogue_result.json'),ref(final)],ensure_ascii=False))
  hpc.update(registered_at=now,created_at=now,source_preparation=ref(HPC/'preparation.json'),source_status='FROZEN_PRIVATE9_STATIC_CHECKED_VERSION_PACKAGING_PENDING',queued=False,resource_authorization=cre['resource_authorization'],source_review_scope='Actual production function numeric/list carriers and AST/source integration only. No Torch/autograd/FP32/native/pairing/resources/efficacy or novelty PASS.',source_inference_parameters={'delta':0,'scope':'No new trainable constructor in source; actual full-model inventory is NOT_RUN.'},next_action='Preserve this frozen original9 prototype and negatives; package an actual compatible exact9 isolated version against then-current main and prepare version-bound native observers. Then use genuinely idle authorized GPU0 for original matched TRAIN2/resources before admission. Existing AEF continues; no GPU1, sibling ff, resampling, extra numerical gate or untested receipt.')
  for p in [HPC/'preparation.json',HPC/'candidate_record.json',HPC/'static_check.py',peer,Path(decision)]:
   e=ref(p)
   if e not in hpc['evidence']:hpc['evidence'].append(e)
  hpc['known_limits'].extend(['CPU metadata transfers are included in whole-call wall-clock latency; original fvcore unsupported/CPU Python work is not claimed fully counted.','Offdiagonal Jacobian is unmeasured without extra backward; no per-coordinate/per-call nonzero gate. Singleton real points still form a three-node path; no-edge=M95 is mathematical control, not a natural singleton claim.'])
  ae.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(ae.get('latest_native_training_progress'))})
  ae['latest_native_training_progress']={'recorded_at':ob['observed_at'],'epoch':5,'step':398,'steps_per_epoch':4686,'observed_steps':samples,'precise_native_validation':live['precise_native_validation'],'evidence':ref(final),'scope':'Partial original training, not terminal best/champion evidence. Source/runtime/PID/physicalGPU0 verified; no checkpoint body.'}
  for p in [HERE/'aef_training_progress_observation.json',HERE/'aef_training_progress_observation_v2.json',final]:
   e=ref(p)
   if e not in ae['evidence']:ae['evidence'].append(e)
  cre.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(cre.get('resource_check')),'prior_current_resource_check':copy.deepcopy(cre.get('current_resource_check'))})
  cre['resource_check']=ref(guard_file);cre['current_resource_check']={'kind':'resource_check','result':'blocked','server':'server-4','physical_gpu':0,'recorded_at':cg['recorded_at'],'evidence':ref(guard_file),'hardware_evidence':ref(final),'scope':'Actual compatible adapter local refusal: original AEF retains registered slot. Zero transport/active/native. Separate exact physicalGPU0 process readback, not new idle permission.'}
  for p in [guard_file,HERE/'cre_catalogue_result.json',final]:
   e=ref(p)
   if e not in cre['evidence']:cre['evidence'].append(e)
  work['candidates'].append(hpc)
  if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
  work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CID,'kind':'implementation_test','result':'passed','command':prep['static_check_command'],'observation':'Actual frozen HPC production-function stdlib carrier and independent Fraction small-forest oracle/source integration checks passed. This is only a software implementation result; all actual Torch/native/autograd/FP32/resources/pairing/efficacy remain NOT_RUN or UNKNOWN. CRE compatible exact9 d585 and static tool port completed, but original AEF occupies sole authorized GPU0.','evidence':[ref(HPC/'static_validation.json'),ref(HPC/'preparation.json'),ref(peer)]}
  work['last_event_tick']=EXPECTED['generated_at'];work['updated_at']=now;work['next_action']='Monitor exact original AEF PID759301/log on server4 GPU0. CRE d585-compatible tools are next native candidate once the same authorized slot is genuinely idle; HPC remains private implemented/unversioned reserve needing compatible source/tool packaging. No GPU1, task eviction, old-held reopening or extra permission for ordinary project work.'
  atomic(ROOT/'pipeline/research_work.json',work)
  for c in [ae,cre,hpc]:
   for e in c['evidence']:closure.artifact(ROOT,e)
  protected(baseline)
  old=(ROOT/'pipeline/codex_memory.md').read_text('utf8').splitlines();sections={};name=None
  for line in old:
   if line.startswith('## '):name=line[3:];sections[name]=[]
   elif name is not None:sections[name].append(line)
  sections['Goal And Phase'][0]='- 当前d08825b53af74c30b3473a41dde74321；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T06:11:40.278464Z/deadline07:11:40.278464Z原值不延长。'
  sections['Champion And Baseline']=[s.replace('M215-BEC本轮','M215-BEC上轮') for s in sections['Champion And Baseline']]
  active=[]
  for s in sections['Active Hypotheses']:
   if s.startswith('- CRE M217既有储备') or s.startswith('- CRE原c760'):continue
   active.append(s.replace('本轮真实四臂','上轮真实四臂').replace('本轮aef_execution','上轮aef_execution'))
  active.extend(['- CRE现有M217兼容source d58576b396cfb54577652be972f3ffaffda508c9/唯一父56，恰9A与原c760九文件逐字相同、isolated clean，实际proof1b9aac2e/独审96651ba3；主线/runtime仍AEF56，未promotion/sync/native/准入。旧7ed/父026c与c760 null保留历史，不跨兄弟ff。',
   '- CRE固定原root receiver+不同sender联合U/GELU定向vector消息→private equalmean，再D0/D1联合原fine/middle与ancestor root消息；原3LN/skip/raw/CSORT/HCG/单inst保持，替代3FFN。收益/新颖性未知。',
   '- 新CRE兼容native2cfa0d0a/op外包dd7f12b3/release模板bytecopycfb506af已外锚，独审bb92b636。原workerbcc611/6945协议/9源码与资源函数保留，runtime只版本声明适配56；32必要软件检查非native。10active仍null、native/resourcesNOT_RUN。',
   '- 当前CRE实际guard dfb0f690：prepare0因原AEF registered占用拒绝，prepare1本地拒绝；0transport/active/lease/manifest/native，不把静态release或当前guard当未来空卡许可。',
   '- 新增M218-HPC stableID hierarchy-tree-resolvent-nonlinear-composition，原fine→middle→coarse真支持森林A=I+L，S=A^-1；refined=raw+S F(LN/raw经S分析)，精确为S→原各层FFN→S的3bank组合。固定两层Schur上行/回代，无denseinverse/N²attention/新参数/新skip/调参；原LN/FFN/CSORT/HCG/唯一inst保持。',
   '- HPC prep c94f9c28/17map/8源+1原YAML，code/source/actualparent null；56仅未来兼容参考，选中native前按实际main另包装。source参数delta0仅源推断。36小forest+1双batch+8非法case/208软件断言（非208实验），生产函数AST载体vs独立Fraction oracle；独审0311d80d含34独立小forest检查，均非Torch/autograd/FP32/native/资源/效果。',
   '- HPC unsupported/pad两次identity保原FFN/skip；一个真实点仍是3层路径，不能说singleton自然退化M95。无边回M95仅数学control；S常量保持不等S F(SX)均值保持，不授RSTR/PCE修订或新数值门。CPU metadata代价/浮点/过平滑/泛化/创新均未测。'])
  sections['Active Hypotheses']=active
  sections['Closed Or Failed Directions']=[s.replace('本轮archive','上轮archive') for s in sections['Closed Or Failed Directions'] if not s.startswith('- 旧10 holds')]
  sections['Closed Or Failed Directions'].append('- 旧10 holds本轮NOTdue，授权/数值负证据/旧grant/checkpoint body未重读、不重开。143旧候选仅AEF/CRE更新，其余141保持；本轮新增HPC1。')
  sections['Running And Queue'][0]='- 唯一确认训练M216-AEF，server4 GPU0原PID759301/source-runtime56；上海14:41:48原生日志TRAIN5/50 389→398/4686。4次精确native validation best.41799527406692505/no_improve1，仅训练中部分结果；M95 champion.5020保持。0ready；M206仍暂停。储备CRE+HPC共2，均未native准入。'
  sections['Open Questions And Risks']=[s for s in sections['Open Questions And Risks'] if not s.startswith('- CRE旧7ed')]
  sections['Open Questions And Risks'].append('- CRE d585当前兼容工具已备但真实native/common-pairing/grad/resources未执行；HPC仅冻结私有未版本原型。未来source/main变化必须兼容重包装+实际native，不重标签旧raw。全部旧受保护恢复权限保持。')
  sections['Last Tick']=['- begin一次canonical监控/goal/已有派发；其new_terminal BEC是上轮已归档事件，本轮无新训练归档/停止/恢复。AEF实际5/50仍增长，0.4180是当前部分最佳，不作最终效果或失败判断。',
   '- 当前严格hostkey/hostname+原PID/cwd/source8/YAML/runtime56/NVML onlyGPU0验证，原生进度两次增长与精确own logger validation；不读checkpoint、不发信号。初版observer误假设/proc初始env必含CUDA字段而失败，负记录保留，V2/final改实际NVML0归属，非训练故障/模型修订。',
   '- 新CRE原图/原九字节仅兼容版本保存一次d585（父56）；实际独审+最小版本工具port完成；同原guard当前busy0拒绝/unauthorized1拒绝，未新GPU计算。',
   '- 本轮创建1个HPC原型，源与协议/真实stdlib生产函数软件检查+独审保留，native及资源NOT_RUN。0模型修订，1兼容sourcecommit（仅CRE），0主线ff/sync/准入/入队/训练启动；28/index/16账/其他141旧候选保持。',
   '- tick_attempt=HPC implementation_test/passed，严格仅软件作用域；当前两个储备继续就绪准备。GPU1禁用、M206暂停、其他项目与调度不动。root随后实际report/finish并核释放，不预签收尾。']
  names=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick'];lines=['# Codex Research Memory','']
  for name in names:lines.extend(['## '+name]+[s for s in sections[name] if s]+[''])
  assert len(lines)<120;atomic(ROOT/'pipeline/codex_memory.md','\n'.join(lines),text=True)
  notes={'actions':['2026-10-27上海14:17原AEF TRAIN4/50 1376→1384；14:41:48再读同PID/source/runtime/GPU0，TRAIN5/50 389→398/4686；4次精确native validation best0.41799527406692505/no_improve1，仅部分训练结果。无checkpoint body/信号，现有训练继续。','原CRE九文件逐字兼容包装为独立d585（父当前56），主线/index/28用户文件/16账不变。新native/op工具与原worker/协议/资源函数相容并独审；32软件检查只metadata/AST。生产静态release为受审模板bytecopy，无active binding或lease。','新compatibleCRE当前owner/source/授权/外锚实际本地guard：GPU0因原AEF登记占用拒绝，GPU1本地拒绝；0transport/native/GPU计算，不抢运行。','实现并登记唯一新增M218-HPC全树组合私有原型（S→原3FFN→S）；36小forest+1双batch+8非法case和独立小forest/接线检查通过。code/source/actualparent null，Tensor/FP32/autograd/native/resources/准确率未测。'],
   'decisions':['M95仍0.5020，目标0.5100/gap0.0080；AEF当前0.4180是第5轮训练中部分最佳，不否定该机制、不调参或提前停止。BEC上轮24/.5001正常终态保留，本轮无新训练完成。','优先CRE d585在唯一授权GPU0真正空闲时做原matched TRAIN2/resources，通过后同轮准入派发；HPC为第二储备，先按届时actualmain包装源与原生观测工具。不跨兄弟ff，不改数据/seed/schedule/原10G/原资源口径或旧held门。','HPC静态解性质不等Torch/FP32或效果，CPU元数据同步纳whole-call latency，不能声称Python全计入FLOPs；无offdiagonal Jacobian/逐坐标非零/均值新门，原RSTR/PCE负证据与修订上限保持。','保持server4 GPU0/max1，GPU1禁用、M206用户暂停和调度Disabled。两个储备未native准入，0新可运行waiting；本轮无需新增人工确认。']}
  save(HERE/'report_notes.json',notes)
  after_ids={c['id']:digest(c) for c in work['candidates']};changed=[k for k,v in baseline['candidate_digests'].items() if after_ids[k]!=v];assert set(changed)=={AEF,CRE};assert set(after_ids)-set(baseline['candidate_digests'])=={CID}
  save(HERE/'protected_assets_after.json',{'recorded_at':now,'primary_HEAD':baseline['head'],'source28_and_status_index_unchanged':True,'lifecycle16_unchanged':True,'old_candidate_count':143,'changed_old_candidates':changed,'unchanged_old_count':141,'new_candidate_ids':[CID],'total_candidates':144,'primary_ff_sync_admission_queue_launch':False,'CRE_source_save_only':True})
  print(json.dumps({'new_candidate':'M218-HPC','stage':'implementation','CRE':'compatible static tooling, native NOT_RUN','AEF_native_progress':samples[-1]['last_native_step'],'AEF_partial_best':live['precise_native_validation']['best'],'memory_lines':len(lines),'report_notes':ref(HERE/'report_notes.json'),'protected_assets_after':ref(HERE/'protected_assets_after.json')},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
