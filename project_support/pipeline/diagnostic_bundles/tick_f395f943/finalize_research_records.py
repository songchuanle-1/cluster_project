"""Final current-tick evidence, bounded resource disposition and seven-section memory."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;AEF='hierarchy-parent-antisymmetric-edge-flux';CRE='hierarchy-cross-root-directed-edge-broadcast';HPC='hierarchy-tree-resolvent-nonlinear-composition'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def atomic(p,v,text=False):
 guard();tmp=Path(str(p)+'.f395.final.tmp')
 with tmp.open('x',encoding='utf8') as f:f.write(v if text else json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 guard();os.replace(tmp,p)
def protected(b):
 git=lambda *a:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
 assert git('rev-parse','HEAD').decode().strip()==b['head'] and git('status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not git('diff','--cached','--name-only','-z')
 for n,h in b['files'].items():assert sha(ROOT/'Cluster'/n)==h,n
 for n,h in b['protected_ledgers'].items():assert sha(ROOT/'pipeline'/n)==h,n
def main():
 guard();baseline=read(HERE/'protected_assets_before.json');protected(baseline)
 final=HERE/'aef_training_progress_observation_final.json';assert sha(final)=='5a49792b02fc979decf3e720a4f0af93e77a7112727d38452b6ebade5e6a35cf'
 live=read(final);assert live['returncode']==0;ob=live['observation'];samples=ob['samples'];assert samples[-1]['max_native_step']>samples[0]['max_native_step']
 guards={CRE:HERE/'cre_actual_current_guard.json',HPC:HERE/'hpc_actual_current_guard.json'}
 assert sha(guards[CRE])=='47a0a5e16c452ebf9191e65682fc7524524bbce5a169d88132d176abd6f1aefb' and sha(guards[HPC])=='92f1d0d5757fa495c13547f5f95855e0aa54f76e28cb3286ddb9c337c0d9a520'
 for p in guards.values():
  g=read(p);assert g['transport_calls']==0 and g['active_binding_manifest_lease_created'] is False and g['native_or_resources_executed'] is False
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();protected(baseline);work=read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==144
  assert all(digest(c)==baseline['candidate_digests'][c['id']] for c in work['candidates'] if c['id']!=HPC)
  ae=next(c for c in work['candidates'] if c['id']==AEF);cre=next(c for c in work['candidates'] if c['id']==CRE);hpc=next(c for c in work['candidates'] if c['id']==HPC)
  assert ae['stage']=='training' and cre['stage']==hpc['stage']=='validation' and hpc['code_commit']=='2f7eff19ca59cc4586e13ca81a547a18ea7e313d'
  now=datetime.now(timezone.utc).isoformat();save(HERE/'records_final_intent.json',{'recorded_at':now,'owner':EXPECTED,'before_research_work_sha256':sha(ROOT/'pipeline/research_work.json'),'operation':'Actual HPC source/native-op static preparation and blocked current guard; original AEF readback only, no native/admission/queue.'})
  ae.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(ae.get('latest_native_training_progress'))})
  ae['latest_native_training_progress']={'recorded_at':ob['observed_at'],'epoch':samples[-1]['max_native_step'][0],'step':samples[-1]['max_native_step'][1],'steps_per_epoch':4686,'observed_steps':samples,'precise_native_validation':live['precise_native_validation'],'evidence':ref(final),'scope':'Partial original ongoing training only. Original source/runtime56/PID759301/GPU0 verified; no checkpoint body or signal.'}
  for p in [HERE/'aef_training_progress_observation.json',final]:
   e=ref(p)
   if e not in ae['evidence']:ae['evidence'].append(e)
  for c in [cre,hpc]:
   g=read(guards[c['id']]);c.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(c.get('resource_check')),'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
   c['resource_check']=ref(guards[c['id']]);c['current_resource_check']={'kind':'resource_check','result':'blocked','server':'server-4','physical_gpu':0,'recorded_at':g['recorded_at'],'evidence':ref(guards[c['id']]),'hardware_evidence':ref(final),'scope':'Actual current local pretransport refusal for original AEF registered0. No new hardware query or native PASS implied by local guard; physical proof has separate timestamp.'}
   for p in [guards[c['id']],final]:
    e=ref(p)
    if e not in c['evidence']:c['evidence'].append(e)
  for p in [HERE/'hpc_tools_catalogue_result.json',HERE/'hpc_source_catalogue_result.json']:
   e=ref(p)
   if e not in hpc['evidence']:hpc['evidence'].append(e)
  if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
  work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':HPC,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_f395f943/check_hpc_current_guard.py','observation':'Actual new version-bound HPC adapter passed current identity/source/external anchors/current grant to the local idle guard, then refused GPU0 because original AEF is registered running; GPU1 refused locally. Zero transport/active material/native/resource execution. Actual2f7 source plus reviewed native/op tools prepared this tick, efficacy unknown.','evidence':[ref(guards[HPC]),ref(HERE/'hpc_tools_catalogue_result.json')]}
  work['last_event_tick']=EXPECTED['generated_at'];work['updated_at']=now;work['next_action']='Monitor exact original AEF PID/log on server4 GPU0; once genuinely idle use existing reviewed compatible CRE d585 tools first, then HPC2f7 only if its parent/runtime remains compatible. Both are validation reserve with native/resources NOT_RUN. Any primary advance requires compatible source/tool metadata and actual testing, never sibling ff/relabelled raw. GPU1 prohibited; M206 and oldholds remain.'
  atomic(ROOT/'pipeline/research_work.json',work)
  for c in [ae,cre,hpc]:
   for e in c['evidence']:closure.artifact(ROOT,e)
  protected(baseline)
  old=(ROOT/'pipeline/codex_memory.md').read_text('utf8').splitlines();sections={};name=None
  for line in old:
   if line.startswith('## '):name=line[3:];sections[name]=[]
   elif name is not None:sections[name].append(line)
  sections['Goal And Phase'][0]='- 当前f395f943dd534ede890abe929de52269；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T08:08:18.932684Z/deadline09:08:18.932684Z原值保持不延长。'
  sections['Champion And Baseline']=[s.replace('M215-BEC上轮','M215-BEC既有') for s in sections['Champion And Baseline']]
  active=[]
  for s in sections['Active Hypotheses']:
   if s.startswith('- HPC prep c94f'):continue
   active.append(s.replace('上轮真实四臂','既有真实四臂').replace('上轮aef_execution','既有aef_execution').replace('三标准和新收据路径均在本轮458bf62f','三标准和收据路径均在历史458bf62f'))
  active.extend(['- HPC原c94f9c28/17map/8源+1原YAML的code/source/actualparent null声明原字节保留；本轮实际隔离source2f7eff19ca59cc4586e13ca81a547a18ea7e313d/唯一父56，恰9A/9blob与c94相同，isolated clean，proof9cc3661e/实际Git独审e3e2b16c。主线/runtime仍56，未promote/sync/native。CRE d585与HPC2f7是56的两个独立子版本，不跨兄弟ff。',
   '- HPC新native f9a2ab3e/worker bff46bdc/runtime e79b89aa/template e26e520f/sourcebinding2e945ef1，独审b703cfdc；原348e协议/raw9保持。27观察器软件核+30packet/guardAST核只软件，原208/34等未重跑。实际2solver/3原LN/FFN/原skip/HCG/inst观察准备好；全named参数实配对但未跑，不排除旧FFN或硬套843。',
   '- HPC op136255da/release模板bytecopy6bfe89a9、独审f95fa070；原0-only/6owner/1020s余量/三锁/双idle/noreplay安全函数保留。当前guard92f1d0d5 prepare0因原AEF登记占用拒绝/prepare1本地拒绝，0transport/active。10执行字段null，native/resources/FP32/autograd/配对/效果均NOT_RUN或UNKNOWN。',
   '- HPC原prototype36小forest+1双batch+8非法case/208软件断言及0311源审仍仅生产函数AST/list载体vsFraction oracle；不是208实验或Torch证据。当前源码参数delta0只是源推断。初始工具assembly/readback/carrier harness失败与修正原样保留，均非模型/原生失败，不增加模型修订。'])
  sections['Active Hypotheses']=active
  sections['Closed Or Failed Directions']=[s.replace('上轮archive','既有archive') for s in sections['Closed Or Failed Directions'] if not s.startswith('- 旧10 holds')]
  sections['Closed Or Failed Directions'].append('- 旧10 holds本轮NOTdue，保持授权/数值负证据，不新读旧655目标、旧grant或checkpoint body、不重开。144条旧候选仅AEF/CRE/HPC更新，其余141保持；本轮0新候选/0模型修订。')
  sections['Running And Queue'][0]='- 唯一确认训练M216-AEF server4 GPU0原PID759301/source-runtime56；上海16:11 TRAIN8/50 837→846，16:40:58再读TRAIN9/50 1012→1021/4686。8次精确native validation best.47460028529167175/no_improve0，仅训练中部分最佳；M95.5020/目标.5100保持。0ready；M206仍暂停。CRE/HPC各有受审静态工具，均未native准入。'
  sections['Open Questions And Risks']=[s for s in sections['Open Questions And Risks'] if not s.startswith('- CRE d585当前兼容')]
  sections['Open Questions And Risks'].append('- CRE d585/HPC2f7现均有真实隔离源及受审静态native/op工具，仍无实际Tensor/native/common配对/梯度/资源结果。未来主线改变必须兼容包装并真测，静态release/软件用例/registeredbusy拒绝均不是未来空卡许可或训练效果。全部旧恢复/额外修订限制保持。')
  sections['Last Tick']=['- begin一次canonical监控/goal/已有派发，无新训练终态。原AEF8→9/50继续增长，最新部分best.4746002853且noimprove0；不据此判最终收益或停分支。',
   '- 本轮HPC精确9源首次实际隔离保存2f7（父56）+Git独审，原c94/null/旧源审保持；27观察器软件核和30packet核/52op元数据核+独审通过，都非Torch/native/资源。主线/index/28用户文件/16账/CRE旧9+工具包保持。',
   '- 新HPC版本绑定原生worker记录2原solver/3原FFN及原HCG/inst路径、全named初始化、原resource函数完整保留；op仅版本/ID/namespace元信息移植原安全函数，productionrelease仅模板精确bytecopy，无active绑定/manifest/lease。',
   '- 当前CRE47a0a5e1/HPC92f1d0d5实际localguard均因原AEF登记0占用拒绝，GPU1在本地拒绝；0transport或新GPU计算，候选继续等待合法空槽。原模型图/seed/data/YAML/schedule/门不改。',
   '- tick_attempt=HPC真实resource_check/blocked，source/tooling有本轮新证据。0新候选/0模型修订/1隔离sourcecommit/0主线ff-sync-准入-入队-启动。只读自己的PID/log/source/NVML0，无checkpoint body/信号/驱逐/调度变更。root随后实际report/finish并核释放，不预签收尾。']
  names=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick'];lines=['# Codex Research Memory','']
  for name in names:lines.extend(['## '+name]+[s for s in sections[name] if s]+[''])
  assert len(lines)<120;atomic(ROOT/'pipeline/codex_memory.md','\n'.join(lines),text=True)
  notes={'actions':['2026-10-27上海16:11原AEF TRAIN8/50 837→846；16:40:58同原PID/source8/YAML/runtime56/NVML physical0复核，TRAIN9/50 1012→1021/4686，8次精确native validation best0.47460028529167175/no_improve0。部分训练结果，无checkpoint body/信号，继续原训练。','HPC原c94冻结9文件首次实际隔离source2f7（唯一父56）保存并独立核Gitobjects/9blob/clean/主线28/index/16账及CRE原包保护。原c94 NULL和0311软件源审保留，不relabel为原生PASS。','完成HPC版本绑定native f9a2和op1362静态工具；27观察器软件核+30packet核及52op元数据核、外置独审b703/f95无阻断。原资源整函数/handlers、348e协议与原9source保持，无Torch/native/FP32/资源执行。','新HPC production static release仅6bfe模板bytecopy。实际当前CRE/HPC local prepare0因原AEF登记占用拒绝、prepare1在本地拒绝；0transport/active binding/manifest/lease/新GPU计算。'],
   'decisions':['M95仍0.5020，目标0.5100/gap0.0080；AEF当前0.4746是训练中部分最佳，不能当最终效果/失败，不调参或提前停止。','保持CRE优先，未来GPU0真正空闲且fresh owner/原deadline/资产/UUID/三锁通过后，执行原matched TRAIN2/resources，过门再同轮入队派发。HPC2f7与CREd585是兄弟源，主线变化必须兼容包装并实际测试，不跨兄弟ff/重标签raw。','HPC全named初始参数实际配对/3原FFN aggregate有限非零及更新、新2solver与HCG-mask路径检查仍待测；无新mean/FP32 residual/逐row-call非零/Jacobian门。CPU工作按whole-call latency，原fvcore unsupported保留，pureTRAIN峰值未知。','本轮0新模型/0修订/0新准入排队启动，只完成既有HPC准备与资源拒绝核验。server4仅GPU0/max1，GPU1禁用、M206暂停、旧10边界/其他项目/调度不动；无需新增人工确认。']}
  save(HERE/'report_notes.json',notes)
  after={c['id']:digest(c) for c in work['candidates']};changed=[k for k,h in baseline['candidate_digests'].items() if after[k]!=h];assert set(changed)=={AEF,CRE,HPC} and set(after)==set(baseline['candidate_digests'])
  save(HERE/'protected_assets_after.json',{'recorded_at':now,'primary_HEAD':baseline['head'],'primary_source28_status_index_unchanged':True,'lifecycle16_unchanged':True,'candidate_count':144,'new_candidates':[],'changed_candidates':changed,'other141_candidates_unchanged':True,'new_source_commit':'2f7eff19ca59cc4586e13ca81a547a18ea7e313d','native_GPU_admission_queue_launch':'NOT_RUN','primary_ff_or_remote_sync':False})
  print(json.dumps({'HPC_stage':hpc['stage'],'HPC_native':'NOT_RUN','AEF_progress':samples[-1]['max_native_step'],'AEF_partial_best':live['precise_native_validation']['best'],'memory_lines':len(lines),'report_notes':ref(HERE/'report_notes.json'),'protected_assets_after':ref(HERE/'protected_assets_after.json')},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
