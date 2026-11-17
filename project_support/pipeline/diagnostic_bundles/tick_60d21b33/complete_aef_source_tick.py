"""Record actual isolated source version and current resource blocker only."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='60d21b3324c94445b26d2ecb24a3ba65';BASE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563';NEW='56b2a96dc48cc8a88f0f7105527ef448113b1060'
AEF='hierarchy-parent-antisymmetric-edge-flux';BEC='hierarchy-cross-level-bipartite-edge-composition'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def save(p,v):
 with Path(p).open('xb') as f:f.write(encoded(v));f.flush();os.fsync(f.fileno())
def replace(p,v):
 tmp=p.with_name(p.name+'.'+TOKEN+'.source_handoff.tmp')
 with tmp.open('xb') as f:f.write(v);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def main():
 owner=guard();assert not(HERE/'completion_intent.json').exists(),'Reconcile any partial operation; no replay'
 version_path=HERE/'aef_version_execute/isolated_source_version.json'
 assert sha(version_path)=='427ee808a74e0501e0e76cc9828fa8da2a61f8e49d0c39e3b04c7a39c78e9a68'
 version=read(version_path);assert version['code_commit']==NEW and version['parent_commit']==BASE and version['diff_exact9A'] and version['isolated_worktree_and_index_clean']
 source_peer_path=HERE/'aef_actual_source_version_independent_review.json'
 assert sha(source_peer_path)=='4d1e98e09d6e0b7109f10340b0a38d0041da7debc814f338106f02d99b1b6e4a'
 assert read(source_peer_path)['material_concerns']==[]
 obs_path=HERE/'bec_training_progress_observation.json';obs=read(obs_path)
 assert sha(obs_path)=='4974189d8a32ce4a0588aedb8599314090f2adc150914a53d52cad31b2282d4b' and obs['owner_token']==TOKEN and obs['native_TRAIN_growth'] is True
 progress_peer=HERE/'bec_training_progress_independent_review.json';assert read(progress_peer)['material_concerns']==[]
 resource_path=HERE/'aef_resource_slot_check.json';resource=read(resource_path)
 assert sha(resource_path)=='059165685a57521ec9ed1e480198b8081d3affe203edc47f82be3ab35a86561f'
 assert resource['kind']=='resource_check' and resource['result']=='blocked' and resource['candidate_id']==AEF and resource['transport_calls']==0 and resource['AEF_native_execution']=='NOT_RUN'
 first,last=obs['observations'][0],obs['observations'][-1]
 assert (last['pid'],last['start_ticks'],last['runtime_HEAD'])==(1558071,'64444390',BASE)
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();pre=snapshot();baseline=read(HERE/'protected_assets_before.json')
  assert all(pre[k]==baseline[k] for k in ['head','index_empty','status_hex','files','protected_ledgers','candidate_digests'])
  wp=ROOT/'pipeline/research_work.json';work=read(wp);out=copy.deepcopy(work)
  a=next(c for c in out['candidates'] if c['id']==AEF);b=next(c for c in out['candidates'] if c['id']==BEC)
  assert len(work['candidates'])==142 and a['code_commit'] is None and a['source_commit'] is None
  assert a['source_preparation']==version['source_preparation'] and a['native_status']==a['resource_status']=='NOT_RUN'
  now=datetime.now(timezone.utc).isoformat()
  prior_keys=['code_commit','source_commit','future_version_parent','operational_compatibility','source_status','next_action']
  a.setdefault('source_version_history',[]).append({'recorded_at':now,'reason':'Actual exact9 local source commit on compatible current026c; original9d6/3898 null/reference4e8 declarations remain immutable.','prior_fields':{k:copy.deepcopy(a.get(k)) for k in prior_keys},'actual_version':ref(version_path),'actual_version_peer':ref(source_peer_path)})
  a.update(code_commit=NEW,source_commit=NEW,source_parent_commit=BASE,future_version_parent=BASE,source_version=ref(version_path),isolated_worktree=version['worktree'],source_status='ACTUAL_ISOLATED_COMPATIBLE_SOURCE_VERSION_SAVED_NATIVE_TOOLING_PENDING',version_packaging_status='EXACT9A_SINGLE_CHILD026C_PRIMARY_RUNTIME_NOT_PROMOTED',native_execution_code_commit=None,resource_check=ref(resource_path),
   next_action='Keep original BEC1558071/source026c on soleGPU0. Prepare AEF native worker/metadata against actual isolated56b2 source and unchanged original YAML/protocol, derive actual common names rather than reusing BEC/CTS counts. Execute original matched M95/AEF TRAIN2/resources only after genuine permitted idleGPU0/current-owner/assets/UUID/three-lock/deadline checks. Do not promote main/runtime, tune, resample, useGPU1 or reopen oldholds.')
  a['operational_compatibility']={'actual_source_commit':NEW,'actual_parent_commit':BASE,'actual_primary_runtime_unchanged':BASE,'historical_source_reference_only':'4e80006047d5cb3dcdfb9c1102e02c33f354a07d','frozen9_source_unchanged':True,'actual_native_or_resource_results':'NOT_RUN','source_version':ref(version_path),'independent_review':ref(source_peer_path)}
  for entry in [ref(version_path),ref(source_peer_path),ref(resource_path),ref(HERE/'aef_version_helper_independent_review.json')]:
   if entry not in a['evidence']:a['evidence'].append(entry)
  b.setdefault('training_progress_history',[]).append(copy.deepcopy(b.get('training_progress_observation')))
  b['training_progress_observation']={'first':first['train_progress'],'last':last['train_progress'],'pid':1558071,'start_ticks':'64444390','observed_at':last['observed_at'],'evidence':ref(obs_path),'independent_review':ref(progress_peer)}
  b['current_resource_check']={'result':'original_training_running','server':'server-4','physical_gpu':0,'observed_at':last['observed_at'],'evidence':ref(obs_path),'scope':'Bounded actual original BEC source/process/steps/context; no continuous exclusivity or pure TRAIN peak claim.'}
  for entry in [ref(obs_path),ref(progress_peer)]:
   if entry not in b['evidence']:b['evidence'].append(entry)
  if work.get('tick_attempt'):out.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
  out['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':AEF,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+(HERE/'check_aef_resource_slot.py').as_posix()+' --execute-root','observation':'Actual current owner/policy/BEC queue+running and exact this-tick actual GPU0 source/process/context/progress evidence confirm no permitted idle slot for AEF native. Local-only checker made zero transport/process/network/Torch/hardware queries; it references separately collected current root hardware samples. Separately saved actual compatible56b2 source on026c is not native/FP32/resources/admission PASS.','evidence':[ref(resource_path)]}
  out['updated_at']=now;out['next_action']='Continue original verified BEC on soleserver4GPU0. AEF exact isolated56b2 source is saved on parent026c; complete native tooling without altering frozen source or running main, then wait real GPU0 availability for original matched native/resource tests. No GPU1, source promotion, repeated old tests or protected-run recovery.'
  others=lambda w:{c['id']:c for c in w['candidates'] if c['id'] not in (AEF,BEC)}
  assert others(out)==others(work) and len(out['candidates'])==142
  memold=(ROOT/'pipeline/codex_memory.md').read_text('utf8');parts={};key=None
  for line in memold.splitlines():
   if line.startswith('## '):key=line;parts[key]=[]
   elif key:parts[key].append(line)
  headers=['## Goal And Phase','## Champion And Baseline','## Active Hypotheses','## Closed Or Failed Directions','## Running And Queue','## Open Questions And Risks','## Last Tick'];assert set(parts)==set(headers)
  parts[headers[0]][0]='- 当前60d21b3324c94445b26d2ecb24a3ba65，actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T16:09:41.027895+00:00/deadline17:09:41.027895+00:00原值保持。'
  active=[]
  for line in parts[headers[2]]:
   if line.startswith('- M216-AEF现'):
    active.append('- M216-AEF现已保存真实隔离source56b2a96dc48cc8a88f0f7105527ef448113b1060，唯一父026c，恰9A/9blob全等原9d6冻结源码，隔离HEAD/index/worktree clean；版本证明427ee808…/实际Git独审4d1e98e0…。主线/运行源仍026c，未promotion/sync/native/FP32/资源/准入。')
    active.append('- 原150c AEF prep9d6a03/candidate3898be内code/source=null、reference4e8维持原字节，21集成+46独立stdlib结果仍只覆盖旧原源码软件性质；新实际parent026c由本轮新source_version单独记录，不回填或重标旧证据，不增加模型修订。')
    active.append('- AEF只middle原父组detached几何MST上的双向共享GELU/W反对称q和signedincidence，原LN/skip/fine/coarse/rawmean/CSORT/HCG/单inst不变；只实数unweighted sum，不保RSTR πpointmean/非Markov，不授旧RSTR恢复/R3。理论参数−394240，实际资源/梯度/准确率未知。')
   elif line.startswith('- AEF原未来父'):
    active.append('- AEF当前native工具尚未完成：下一步按真实56b2源版本/原YAML协议准备native worker；实际M95/AEF TRAIN2与原资源只在BEC自然释放唯一GPU0且fresh UUID/三锁/currentowner/原deadline通过后执行。不得复用B E C common839或CTS843计数代实际派生，不原地改源码/抽样/阈值，不现在promote运行主线。')
   else:active.append(line.replace('- 本轮94f新R1四臂','- 历史94f真实R1四臂').replace('本轮只fresh绑定94f','94f仅fresh绑定'))
  parts[headers[2]]=active
  parts[headers[4]][0]=f"- 当前1个确认训练：M215-BEC source026c，server4GPU0 原PID1558071/start64444390；采集{first['observed_at']}→{last['observed_at']}，TRAIN2/50 3963→3972/4686；本轮4974189d…观测/0eb7c9eb…独审。原source8/YAML/queue/experiment/receipt/revision_digest及唯一selected0 mapping核实，不声称持续独占。"
  parts[headers[4]].insert(2,'- AEF本轮实际resource_check05916568…引用本轮root硬件实观和当前登记，唯一GPU0被原BEC占用；检查本身0transport/Popen/network/Torch/新硬件查询，无AEF adapter/PASS或工具可用性声明。源码版本保存不等于准入或可运行待跑。')
  parts[headers[5]]=[line for line in parts[headers[5]] if not line.startswith('- 初次额外observer')]
  parts[headers[5]].append('- AEF只有兼容源版本与原软件性质，Torch/原生forward/backward/实际grad、浮点Σδ、同口径资源与效果均未测；不能拿Git/CPU/符号性质代签。最新BEC验证指标本轮未提取，完整训练效果待评估。')
  parts[headers[6]]=['- 新begin完成一次canonical进展/派发；当前BEC原训练继续，无新终态/运维故障，M206暂停不计ready。AEF是唯一due可推进项，creation/reserve预算1但未新增候选，只接续已有source版本。', '- 实际本地隔离worktree+单父026c普通commit56b2，仅新增原9d6九文件；保存helper478075/93e243与源审fb9b0598，root执行新副本仅启用单flag，actual Git独审4d1e98e0确认9blob/单父/clean与primary28/index/14账+19保护文件在该操作前后全同。无主线ff/remote/模型执行。', '- 本轮真实tick_attempt为AEF resource_check/blocked，原BEC source/progress双样本证明原GPU0占用；实际0新candidate/0模型revision/1隔离local source commit/0新准入/入队/训练启动。不重跑原136/46软件套件，不读旧655/grant/ckpt。', '- 收尾仅work中AEF实际source/current resource与BEC当前进度、七段memory/notes改变；其他140候选、全部14生命周期账、主线026c/28status+bytes/index不变。六段report后canonical finish，以实际receipt/释放为准，释放后不回写。']
  memory='# Codex Research Memory\n\n'+'\n'.join(h+'\n'+'\n'.join(parts[h]).strip()+'\n' for h in headers)+'\n';assert len(memory.splitlines())<120 and memory.count('\n## ')==7
  notes={'actions':['canonical begin确认原BEC继续运行、无新终态/运维故障；root两次只读观测原PID1558071/start64444390、source026c/8源/YAML/UUID0/ownlog，TRAIN2/50步数3963→3972，独立18项复核无实质疑点；未触GPU1或改原运行。','本轮仅接续同一M216-AEF，将原9d6冻结9源码配置保存为真实隔离版本56b2a96dc48cc8a88f0f7105527ef448113b1060，唯一父当前026c；actual Git独审确认恰9A、9blob原SHA、worktree/index clean，原null/reference4e8声明不动。','原source算法/21集成/46独立stdlib结论仅按原时间复用，未重跑旧136/46套件；版本保存不是Torch、FP32、原生、资源或训练效果PASS，AEF仍需native worker与真实M95配对检查。','真实当前AEF resource_check blocked：引用本轮root实际GPU0 context/原BEC进度和canonical登记，无可用授权空槽；slot检查0transport/Popen/network/Torch/新GPU查询，不冒称AEF adapter或工具PASS。','0新candidate/模型revision/准入/入队/训练启动，仅1隔离local source commit；primary/runtime026c、28用户status+bytes/index、14生命周期账和其他140候选保持；M206暂停、CTS unknown/BFC crash证据不动。'], 'decisions':['原BEC继续占用唯一授权GPU0训练；该时间窗的源/进度已核，最新验证指标本轮未提取，M95.5020/目标.5100/gap.0080保持。','AEF下一步按真实56b2源和原YAML准备native tooling，实际TRAIN2/resources等待GPU0自然释放后fresh currentowner/UUID/assets/三锁/原deadline；不为填队列抢卡、换seed或用旧计数代新实测。','旧AEF母本null/reference4e8原字节保持；新实际parent026c另记，不假定sibling ff、不主线推广未测版本、不恢复旧held或增加额度。','本轮有真实隔离保存与资源检查，按实际blocked和原版本证据收尾，不凑准入额度，最终以canonical postflight/FINALIZED released为准，无新增人工确认。']}
  wb,mb=encoded(out),memory.encode('utf8');encoded(notes)
  before={'work_sha256':sha(wp),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
  save(HERE/'completion_before.json',{'owner_token':TOKEN,'hashes':before,'protected_snapshot':pre,'AEF_before':next(c for c in work['candidates'] if c['id']==AEF),'BEC_before':next(c for c in work['candidates'] if c['id']==BEC),'tick_attempt_before':work.get('tick_attempt')})
  save(HERE/'completion_intent.json',{'owner_token':TOKEN,'recorded_at':now,'scope':'Only AEF actual isolated source/resource evidence and BEC current observation; compact memory','before':before})
  guard();assert sha(wp)==before['work_sha256']
  replace(wp,wb);replace(ROOT/'pipeline/codex_memory.md',mb);save(HERE/'report_notes.json',notes)
  post=snapshot();assert all(post[k]==pre[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
  assert read(wp)==out and others(read(wp))==others(work) and (ROOT/'pipeline/codex_memory.md').read_bytes()==mb
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'candidate_count':142,'new_candidates':0,'other140_candidates_unchanged':True,'all14_lifecycle_ledgers_unchanged':True,'primary026c_protected28_status_bytes_and_index_unchanged':True,'AEF_actual_source_commit':NEW,'AEF_actual_parent':BASE,'AEF_native_resources':'NOT_RUN','new_training_launches':0,'memory_lines':len(memory.splitlines()),'work_sha256':sha(wp),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md'),'notes':ref(HERE/'report_notes.json')}
  save(HERE/'completion_result.json',result);print(json.dumps({'status':'ACTUAL_AEF_SOURCE_AND_CURRENT_RESOURCE_BLOCK_RECORDED','result':ref(HERE/'completion_result.json'),'memory_lines':len(memory.splitlines())},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
