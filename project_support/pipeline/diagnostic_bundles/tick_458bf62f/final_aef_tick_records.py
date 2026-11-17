"""Final owned-tick records after original canonical AEF launch verification."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,io,json,os,subprocess,sys
from anchor_bfc_packet import ROOT,guard,sha,EXPECTED
HERE=Path(__file__).resolve().parent;CID='hierarchy-parent-antisymmetric-edge-flux';EXP='M216-AEF'
COMMIT='56b2a96dc48cc8a88f0f7105527ef448113b1060'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def atomic(p,v,text=False):
 guard();tmp=Path(str(p)+'.458bf62f.final.tmp')
 with tmp.open('x',encoding='utf8') as f:
  f.write(v if text else json.dumps(v,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 guard();os.replace(tmp,p)
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def main():
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  queue=mon.load_queue(str(ROOT));tasks=[t for ts in queue['gpu_queues'].values() for t in ts if t.get('id')==EXP];assert len(tasks)==1
  task=tasks[0];assert task['status']=='running' and task['launch_verified'] is True and str(task['gpu'])=='0' and task['code_commit']==COMMIT
  receipt=closure.admission(ROOT,task);baseline=read(HERE/'protected_assets_before.json');before=read(HERE/'aef_before_admission_lifecycle.json')
  def strip_queue(q):
   q=__import__('copy').deepcopy(q)
   for k in q['gpu_queues']:q['gpu_queues'][k]=[t for t in q['gpu_queues'][k] if t.get('id')!=EXP]
   return q
  assert strip_queue(queue)==before['queue']
  running=mon.load_running(str(ROOT));old=before['running'];trim=__import__('copy').deepcopy(running)
  for k in list(trim):
   trim[k]={gpu:e for gpu,e in trim[k].items() if e!=EXP}
   if k not in old and not trim[k]:trim.pop(k)
  assert trim==old
  rows=list(csv.DictReader(io.StringIO((ROOT/'pipeline/experiments.csv').read_text(encoding='utf-8-sig'))))
  def targetrow(r):return EXP in (r.get('id'),r.get('exp_id'),r.get('experiment_id'))
  # CSV schema may use model as identifier; explicit target config/name also identifies its sole row.
  def is_aef(r):return targetrow(r) or any(str(v)==EXP or str(v).endswith('_aef') or str(v).endswith('_aef.yaml') for v in r.values())
  assert [r for r in rows if not is_aef(r)]==before['csv_rows']
  for p,h in before['protected_ledgers'].items():
   if p not in ['queue.json','running.json','experiments.csv']:assert sha(ROOT/'pipeline'/p)==h,p
  git=lambda *a:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
  assert git('rev-parse','HEAD').decode().strip()==COMMIT
  assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==baseline['status_hex'] and not git('diff','--cached','--name-only','-z')
  for p,h in baseline['files'].items():assert sha(ROOT/'Cluster'/p)==h
  for p,h in read(HERE/'aef_root_ff_result.json')['source_paths'].items():assert sha(ROOT/'Cluster'/p)==h
  work=read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==143
  changed=[c['id'] for c in work['candidates'] if digest(c)!=before['candidate_digests'][c['id']]];assert set(changed)<={CID},changed
  candidate=next(c for c in work['candidates'] if c['id']==CID);assert candidate['stage']=='training'
  now=datetime.now(timezone.utc).isoformat();review=ref(HERE/'aef_actual_four_result_review.json')
  work.setdefault('tick_attempt_history',[]).append(work['tick_attempt'])
  work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'passed','command':'Original reviewed adapter: prepare GPU0; stage; smoke champion; smoke candidate; resources champion; resources candidate (each exactly once).','observation':'Actual two original TRAIN steps and matched original resource arms independently reviewed; exact tested56 source admitted and original canonical GPU0 launch has increasing native progress. Accuracy unknown.','evidence':[review]}
  if review not in candidate['evidence']:candidate['evidence'].append(review)
  work['last_event_tick']=EXPECTED['generated_at'];work['last_terminal_event']={'experiment_id':'M215-BEC','status':'done_earlystop','native_printed_best':0.5001,'epochs':'24/50','evidence':ref(HERE/'bec_finalize_result.json')}
  work['updated_at']=now;work['next_action']='Monitor only original M216-AEF PID/config/log on server4 GPU0 and preserve all pauses. Continue existing CRE with compatible source packaging/native tests before any later admission; old7ed and tools are historical026c bindings, never sibling ff or relabeled raw. No GPU1.'
  atomic(ROOT/'pipeline/research_work.json',work)
  m=read(HERE/'aef_actual_four_result_review.json');obs=m['observations'];ready=sum(t.get('status')=='waiting' and not t.get('dispatch_hold') for ts in queue['gpu_queues'].values() for t in ts)
  lines=[
   '# Codex Research Memory','', '## Goal And Phase',
   '- 当前458bf62f20024209b63da2009998d280；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致。原generated04:13:06.857021Z/deadline05:13:06.857021Z，2026-10-27，不延长。',
   '- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020，baseline.4894/gap.0080。Phase1层级分工→inst_feats→query/masks，监督辅助，Phase2人工。',
   '- standing experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖项目普通实现/保存/测试/同步/准入/训练，不覆盖旧拒绝重开/额外修订/受保护恢复/扩大资源/调度。',
   '- 最新人类“不用gpu1”：仅server4 physicalGPU0/max1；SERVERS2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1；server4_gpu0_only_20261026.json SHA94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09。未来禁止GPU1，其他allowed[]，Windows Pipeline-cluster_project Disabled。',
   '- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变。原fvcore handlers/fullunsupported、≤10G、bs1/lang1/warm20/repeat100 median/P90；峰值显存+15%需≥+.003mIoU。',
   '- 禁调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst注入/改3-4-6层/无图改变微调、旧rejected改名。',
   '', '## Champion And Baseline',
   '- M95仍.5020，目标未达。M205-MDC.4872、M207-HAP.5002、M208-HRC.4901、M209-PSBR.4969、M210-PSNC.5001、M211-BTC.4914、M212-BCR.4995均原自然早停，无调参重跑。',
   '- M215-BEC本轮正常earlystop24/50，native打印best.5001（checkpoint精确值未新读），低M95 .0019；只判断该次实现未超过champion，不否定整个层级机制。',
   '', '## Active Hypotheses',
   '- M216-AEF原source56b2a96dc48cc8a88f0f7105527ef448113b1060/唯一父026c；本轮真实四臂检查后精确9A ff到主线并由canonical派发，未新造sourcecommit。28原用户文件/status/index完整保持。',
   '- AEF只替换middle FFN：真实原parent内detached几何MST，两方向共享Linear2C→C/GELU差q，再原index_add对端±q；原middle LN/skip、fine/coarseFFN、FPS/IDs/rawmean/CSORT/HCG/单inst保持。仅实数unweighted sum，不保RSTR πpointmean/非Markov。',
   '- 本轮aef_execution四臂均terminal/rc0，原worker75fa/native78f7/op965e/release8913不改；manifest59cb9328cb8e7b1a73286c896f4462ee7ae61b97a78b689728c12b5b4013ffae，fresh原token/deadline/GPU0。旧150c9d6 null/reference4e8母本不回填。',
   '- AEF真实TRAIN2 loss9.5404720306/13.9079742432；M95 loss9.5291242599/13.9095869064，实际两TRAIN指纹/common集合相同；实测843项/156958522参数/hash04231c…是本次观测非固定门。',
   '- AEF每forward448真实MST边/896orientation行，1原共享map/1GELU/2原signedscatter；左右W列每步原loss有限非零aggregate grad且slice更新，fine/coarseFFN、原LN/skip/HCG/inst/ILA-mask路径实核。单row/call/bias零合法，无新FP32sum/πmean门。',
   '- AEF 9.74365806G vsM95 9.762532428G；params157089850 vs157484090（−394240）。GPU0 median35.66337499 vs34.44139898ms（慢3.55%），P9037.46051111 vs36.04126107ms（慢3.94%）；预测allocated−.16818%，reserved−.17606%，+15%未触发。smoke峰值含observer，pureTRAIN峰值/准确率/新颖性未知。',
   '- 当前真实四结果review906b40de60f3ed0ce009feab9e157decb9266e4ef112b9e73a00c489f31343c7，smoke独审e2a4e587…/资源独审73540281…，三标准和新收据路径均在本轮458bf62f。技术准入不等训练收益。',
   '- CRE M217既有储备：原root receiver+不同sender联合U/GELU定向vector message→私equalmean，再D0/D1联合原fine/middle与ancestor root message；原三LN/skip/raw/CSORT/HCG/单inst保持，替代三FFN。source7ed9373db335d44c884133da3eced3fca03ad29a是026c的兄弟版本，不能ff到当前56。',
   '- CRE原c760冻结prep/null、694507协议、native1b669/op54c199/release1765及独审只为旧026c兼容源码/静态工具；原native/resources NOT_RUN。下次须当前兼容源包装+新实际原生检查，不借AEF/BEC raw或重标签。',
   '', '## Closed Or Failed Directions',
   '- BEC source026c/receipt113a72afb83c57401d00072b1a723a5cc3094a76a1e2d9acfe75b465f10238dc/R1历史不变；本轮archive4bd2119b138d4676972019b7462720fa，完整log SHA f7bb1b6bed37685e1acc1d310ecd98f06b04a1ea22168966d5792c9a19b787fd，本远size/hash一致且原PID消失。canonical终态和辅助training_status/researchcomplete已校准。',
   '- BEC R1唯一True→1原bool JIT兼容修复、原9b失败和94f实测通过全保留；原native/资源通过事实不改。本次不重启/调参/加R2。',
   '- M214-CTS canonical stopped_unknown archivea966d7e40d26454598863ac4a87fc4a9/14of50/best.4890；ownlog无正常/异常尾标，根因UNKNOWN，不自动恢复。完整log17693952B/SHA05dce0486051bf0cf8d4af30de61a6a756200efb47b32033b6355f5e7df12da4保持。',
   '- M213-BFC crashed archiveb91b3ba11671451bb28f39dc3cc3f2c7，TRAIN20/50 step3832/4686 DataLoader scatter overlap；根因UNKNOWN，不否定机制/自动恢复。last.pth旧SHA24b3424f…/epoch19/best.4992169439792633，RNG/sampler/失败输入未复现；需BFC专属新计划和人工恢复授权。',
   '- HAP epoch18恢复授权已消费；M206用户暂停+dispatch_hold+resumeFalse保持。PCE默认2+额外1已尽，RSTR默认2已尽；禁PCE_R4/RSTR_R3/M201自动恢复。旧RSTR9文件localcommit授权不授额外修订。',
   '- 旧10 holds本轮保留原scope/授权/数值负证据，无新目标/旧grant/checkpoint正文读取，不借GPU0空闲或due timer重开；141个非BEC/AEF候选保持。',
   '', '## Running And Queue',
   f'- 唯一确认训练M216-AEF server4 GPU0，原PID{task.get("pid")}；source/runtime56b2，canonical launch_verified=true，原生步数递增证据保存在当前dispatch结果。最佳mIoU尚未知。ready waiting={ready}；M206继续暂停，不计ready。',
   '- server4 pinned songcl@192.168.1.115，先验dl04-MS-7E06；GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c。runtime /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1；conda project_cluster/server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。',
   '- SSH keys/strict hostkey；不用旧IP.137/密码/sudo。未知claim/request/PID只reconcile，不盲重启/kill/删锁；当前allowed0也不是未来空卡许可，执行需fresh占用/UUID/三锁/owner原deadline。',
   '', '## Open Questions And Risks',
   '- AEF正式训练效果未知；延迟本次较慢，不称全面更高效。两步finite/backward和准入不证明准确率/新颖性/因果收益。',
   '- AEF actualsingleton/empty/padding/zero-distance/tie未行使处NOT_EXERCISED；offdiagonal dependency probe未实现；unweighted FP32 delta sum只描述，无额外阈值。pureTRAIN峰值未知。',
   '- CRE旧7ed与旧runtime26工具不能直接在新primary56复用执行；需要兼容包装和真实测试。旧PCE/RSTR/M201/M206/BFC/CTS权限保持。',
   '', '## Last Tick',
   '- begin仅一次canonical监控/goal/已有派发。随后原BEC own完整日志证明自然earlystop24/.5001，实际PID已消失，fresh仅GPU0占用/三锁free；用已审canonical finalize_task正常归档，未伪造deathwatch或停止训练。',
   '- 原AEF工具fresh prepare/stage，各smoke/resources四臂只执行一次并完整核验；actual原生/MST/W列与同口径资源通过，原28文件/14受保护账和非目标任务完整。',
   '- 本轮0新候选/0模型修订/0新sourcecommit；1既有AEF真实四臂检查、1exact9主线ff、1实际准入/队列/原canonical派发，原生进度已核。BEC1正常终态；GPU1禁用、M206暂停/其他项目/调度不动。',
   '- 保留所有负结果，当前tick_attempt为AEF真实resource_check/passed。root随后实际report/finish并核释放，不在memory预签postflight成功。',
  ]
  assert len(lines)<120
  atomic(ROOT/'pipeline/codex_memory.md','\n'.join(lines)+'\n',text=True)
  save(HERE/'protected_assets_after.json',{'recorded_at':now,'head':COMMIT,'only_tested_nine_additions':True,'protected_28_status_and_bytes_unchanged':True,'index_empty':True,'other_142_candidates_after_BEC_unchanged':True,'changed_since_after_BEC_before_admission':changed,'non_AEF_queue_and_running_unchanged':True,'non_AEF_csv_rows_unchanged':True,'protected_terminal_experiment_receipts_unchanged':True,'verified_launch':True,'receipt':ref(ROOT/task['admission_receipt'])})
  notes={'actions':['原BEC自然earlystop24/50，native打印best0.5001，未超M95.5020；精确完整日志本远hash/size匹配，canonical正常归档并校准辅助status，未停止/重启任何训练。','AEF原工具fresh GPU0/owner/原deadline绑定，四臂各执行一次，真实TRAIN2/MST/两W列原loss梯度及更新/HCG-inst和原资源通过。','AEF source56b2精确9A主线ff，28用户文件/index/其他任务保留；生成真实标准/准入收据入队，经既有canonical GPU0派发并确认原生日志步数递增。'], 'decisions':['M95仍0.5020，目标0.5100/gap0.0080；BEC本次无champion增益，不整体否定机制或调参重跑。','AEF9.74365806G≤10G，params−394240；同GPU0 median慢3.55%/P90慢3.94%，预测显存略降，15%条件未触发；pureTRAIN峰值/训练效果/新颖性未知。','只使用server4 GPU0/max1，GPU1禁用、M206暂停与旧10边界不变；CRE旧7ed是026c兄弟源，后续须兼容新primary56包装并真测，不跨兄弟ff/借raw。']}
  save(HERE/'report_notes.json',notes)
  print(json.dumps({'memory_lines':len(lines),'verified_running':EXP,'ready_waiting':ready,'protected_assets_after':ref(HERE/'protected_assets_after.json'),'report_notes':ref(HERE/'report_notes.json')}))
 finally:lock.close()
if __name__=='__main__':main()
