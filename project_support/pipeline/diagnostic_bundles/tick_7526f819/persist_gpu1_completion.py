"""Persist only actual GPU1 activation/train proof under the existing owner."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='7526f819f16e4f688566119d347cd198';CID='hierarchy-parent-bidirectional-complement-recurrence';BTCID='hierarchy-parent-binary-tree-complement-composition'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def read(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
 t=p.with_name(p.name+'.'+TOKEN+'.tmp')
 with t.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def main():
 owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
 assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
 assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
 assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
 assert sha(ROOT/'pipeline/authorizations/server4_gpu1_20261025.json')=='90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8'
 dispatch=read(HERE/'bcr_dispatch_result.json');assert dispatch['verified_native_progress'] is True and dispatch['canonical_dispatch_invoked_once'] is True
 bcr=read(HERE/'bcr_progress_observation.json');btc=read(HERE/'btc_progress_observation_after.json')
 assert btc['same_exact_registered_process_and_native_TRAIN_growth'] is True
 final_review=HERE/'bcr_final_dispatch_independent_review.json';review=read(final_review)
 assert review['material_concerns']==[]
 assert not (HERE/'gpu1_completion_persisted.json').exists()
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  protected=['queue.json','running.json','experiments/M211-BTC.json','experiments/M212-BCR.json','experiments/M206-CGCA.json','admissions/M211-BTC.json','admissions/M212-BCR.json'];before={n:sha(ROOT/'pipeline'/n) for n in protected}
  queue=monitor.load_queue(str(ROOT));tasks=queue['gpu_queues']['server-4'];tb=next(t for t in tasks if t['id']=='M212-BCR');tt=next(t for t in tasks if t['id']=='M211-BTC');tm=next(t for t in tasks if t['id']=='M206-CGCA')
  assert tb['status']=='running' and tb['pid']==1215422 and str(tb['gpu'])=='1' and tb['launch_verified']
  assert tt['status']=='running' and tt['pid']==2784474 and str(tt['gpu'])=='0' and tt['launch_verified']
  assert tm['status']=='waiting' and tm['dispatch_hold'] and tm['resume_authorized'] is False and not tm.get('pid')
  work=read(ROOT/'pipeline/research_work.json');c=next(x for x in work['candidates'] if x['id']==CID);bc=next(x for x in work['candidates'] if x['id']==BTCID)
  assert c['code_commit']==c['native_execution_code_commit']=='11a811618179ab1ddc0cee299194667413b7fdb9' and bc['code_commit']=='00e2b18c6b8d568a64edb496e6979d766440883c'
  c.update(stage='training',training_status='running',admission_status='ADMITTED_RUNNING_NATIVE_PROGRESS_VERIFIED',operational_preparation_status='ACTUAL_GPU1_NATIVE_RESOURCES_ADMISSION_AND_TRAIN_LAUNCH_VERIFIED',training_runtime_code_commit=c['code_commit'],training_process={'pid':1215422,'start_ticks':'51717921','physical_gpu':1,'log':tb['log'],'start_identity_scope':'First real postlaunch observation, stable across two exact samples; not claimed as dispatch-time capture'},efficacy='UNKNOWN',next_action='Monitor only exact BCR GPU1 PID1215422/start51717921 and original BTC GPU0 PID2784474/start47557208; await natural training outcomes. Keep original YAML/seed/schedule/data/source and one task per card. M206 remains user-paused; no automatic resume/restart/migration.')
  refs=[ROOT/'pipeline/authorizations/server4_gpu1_20261025.json',HERE/'bcr_gpu1_static_anchor_result.json',HERE/'bcr_native_operation_history.json',HERE/'bcr_native_resource_independent_review.json',HERE/'bcr_primary_ff_result.json',HERE/'bcr_admission_queue_result.json',HERE/'bcr_pre_dispatch_review.json',HERE/'bcr_dispatch_result.json',HERE/'bcr_progress_observation.json',final_review]
  for p in refs:
   x=ref(p)
   if x not in c['evidence']:c['evidence'].append(x)
  bc['current_public_runtime_code_commit']=c['code_commit'];bc['runtime_advance_scope']='Public runtime ff-only00e to11a added exactly9 BCR files. BTC model8/native deployed YAML/common source, admitted source00e/receipt and exact process are unchanged.'
  bc['next_action']='Monitor exact original BTC GPU0 PID2784474/start47557208 and unique original native log. Tested/admitted BTC source00e remains distinct from public runtime11a; only BCR9 additions advanced. Preserve BCR GPU1 and M206 pause.'
  for p in [HERE/'protected_btc_source_before.json',HERE/'btc_progress_observation.json',HERE/'btc_progress_observation_after.json',HERE/'bcr_primary_ff_result.json',final_review]:
   x=ref(p)
   if x not in bc['evidence']:bc['evidence'].append(x)
  work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=c['next_action']
  work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CID,'kind':'native_smoke','result':'passed','command':'python -B -X utf8 '+str(HERE/'invoke_bcr_gpu1.py')+' run --mode smoke --target candidate','observation':'实际原TRAIN2、五分块原loss梯度和权重更新、同数据/共同初始化及原资源配对通过；实测4请求均terminal，正式准入并唯一GPU1派发后原生Train1/50 62→67，BTC0原进程18/50 1→6，M206暂停保持；不是训练效果结论。','evidence':[ref(HERE/'bcr_gpu1_execution/smoke_candidate_execution.json'),ref(HERE/'bcr_native_resource_independent_review.json'),ref(HERE/'bcr_progress_observation.json'),ref(final_review)]}
  save(ROOT/'pipeline/research_work.json',work)
  assert {n:sha(ROOT/'pipeline'/n) for n in protected}==before
  notes={'actions':['依用户“server4 GPU1也可以用了”新增resource授权90f882与SERVERS白名单[0,1]，每卡max1；不改goal/数据/调度，M206人工pause保持。','冻结GPU1专属BCR工具并独审；实际52项离线PASS，先前1fail/1error两fixture改正另run2，旧run1保留；不算模型修订或原生实验。','原owner7526/a524/782/原deadline下实际GPU1 UUID7f82/idle/三锁/assets绑定；原M95/BCR两步TRAIN与资源配对4请求均terminal/rc0，逐原请求只读reconcile完整对象一致。','BCR两loss9.521808624/13.909966469；common843/156958522和两batch配对；每forward64真n>=3组/768 depth>=2 scan，五权重块两步原loss梯度有限非零并更新。','BCR实测9.756240972G/10G，参数157286714较M95少197376；预测median87.026832 vs84.860083ms(+2.5533%)、P90108.935047 vs99.932505(+9.0086%)，allocated−0.0841%，原15%条件未触发；完整unsupported保留。','2026-10-25 11:54上海主源码仅00e→11a已测9新增ff-only，原28status/bytes和index空保持；M212 receipt b8532405入队后仅一次canonical dispatch/safe-sync/原生launch。','2026-10-25约11:58上海后验：GPU1 M212 PID1215422/start51717921原argv/cwd/fd1/UUID1/source8/YAML/HEAD11a，Train1/50 62→67；GPU0 BTC原PID2784474/start47557208/source8及mappedYAML不变，Train18/50 1→6。完整双卡证明与独审留档。'],'decisions':['复用experiment-first常规操作授权2e892及本轮GPU1人类grant90f882，不重复询问；资源开放不恢复M206，不改变旧8hold/revision/rejected边界。','准入仅为原生技术门通过，BCR/BTC正式训练效能仍UNKNOWN；当前GPU1同口径资源pair不与旧GPU0时延作归因。空/pad/singleton本次0未行使、pureTRAIN峰值/fullbuffer-RNG/offdiag未知保留。','本轮1个真实新准入并验证双卡在跑，原前台deadline不延长；保存七段记忆与六段报告后真实finish核FINALIZED/released，释放后停止写入。']}
  with (HERE/'report_notes.json').open('x',encoding='utf-8') as f:json.dump(notes,f,ensure_ascii=False,indent=2);f.write('\n')
  memory=f"""# Codex Research Memory

## Goal And Phase
- 最新接管{TOKEN}；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner['generated_at']}/原deadline{owner['deadline_at']}不延长。真实finish状态见receipt，未提前签。
- goal0441fecda…；ScanRefer目标.5100、M95最佳.5020/gap.0080、baseline.4894。Phase1 hierarchy→inst_feats→query/masks，supervision辅助；Phase2仍需人工确认。
- 原seed1999/epochs50/maxiters70/native YAML/data/optimizer和10G原口径、资源bs1/lang1/warm20/repeat100、显存+15%条件保持。禁调参/gate/语言路由/大QKV/pointN²/重复注入/新残差/纯缩放/旧rejected改名。
- standing experiment_first_20261021.json SHA2e892959…覆盖常规实现/实测/相关版本/安全同步/准入训练；不授旧hold重开/额外修订/受保护恢复/扩资源/改调度。
- 最新人类“server4 GPU1也可以用了”：pipeline/authorizations/server4_gpu1_20261025.json SHA90f8820a…，SERVERS d5277972…允许physical[0,1]/每卡max1，替代旧GPU1释放限制；M206暂停仍保留。其他服务器无allowed，Windows Pipeline-cluster_project Disabled。

## Champion And Baseline
- M95仍.5020；M205-MDC自然earlystop26/.4872，M207-HAP授权epoch18恢复后earlystop31/.5002，M208-HRC自然earlystop31/.4901，M209-PSBR自然earlystop23/.4969，M210-PSNC自然earlystop31/.5001；均未超M95，不调参重跑，不整体否定hierarchy机制。
- HAP原19轮DataLoader AttributeError根因UNKNOWN，epoch18授权已消费非再次restart许可；原crash/snapshot/prior_runs和完整日志/archive保持。
- PSBR完整原log30,985,906B/0204be90…在tick_a4f73140；PSNC完整原log在tick_ddb531fb/psnc_native_earlystop_log_evidence.json，本远SHA一致，canonical归档与source43/receipt406e…保留。

## Active Hypotheses
- 当前M212-BCR stable {CID}，tested/admitted/training/source11a811618179ab1ddc0cee299194667413b7fdb9单父00e；原17map prep tick_41eb62fa/new_candidate_prepare/preparation.json faf3494d…原code_commitnull保持，1334断言62labels/22生产plan与24独立stdlib调用均属历史本地检查，不是训练实验。
- BCR仅middleFFN换strict-exclusive双向共享scan和own/L/R线性读出，原LN/cfskip/fine-coarse/raw-CSORT/HCG/单inst保留；真point-support、原parent、detached xyz+ID排序、Ws恰2(n−1)，Wf每父1调用/n行。PSBR/BTC近邻因子化新信息流，不宣称独立新颖或PSBR单因素因果，不resume旧PSBR。
- 本轮GPU1 origincc8b4b16…(disabled)/operational e748a619…outer33/native f5724e27…17/diag12、worker a3b10169…原字节、runtime008e536e…，staticrelease40ee3b47…；静态独审2e4dcbad…44项。52离线run2 abf1ed52…PASS，run1原1fail/1error65d508…及两fixture更正保留，不算候选模型修订。
- 实际owner7526/ctxa524/pending782与原deadline、UUID1/idle/assets/三锁后stage bcr_gpu1_7526f819；native manifest be07748d…/lease7b5a9ab2…/bindingbd01b6b1…，诊断source11a与当时公共runtime00e明确区分。原未执行包/准备历史不回写造PASS。
- 实际原M95/BCR TRAIN2：BCR loss9.521808624267578/13.909966468811035，两原loss/backward/optimizer各2；共同843张量/156958522参数/hash04231c23…及两原batch指纹配对。每forward64真n>=3父组、896scan/64readout、768 depth>=2，最大深度9/12；实际非零priorstate、五Ws token/state/Wf own/L/R原loss梯度和权重更新、cfskip/HCG→inst→mask均核实。
- 实际原资源BCR9.756240972G vsM959.762532428G，157286714 vs157484090参数(−197376)；GPU1 median87.026832014 vs84.860082512ms(+2.5533%)、P90108.935047296 vs99.932504783(+9.0086%)；预测allocated935975424 vs936763392(−0.0841%)、reserved1189085184 vs1191182336，15%条件未触发；完整unsupported保留。
- 四原请求terminal/rc0且逐请求只读reconcile完整对象/LF hash一致，workers[]/GPU1contexts空；history15b18429…/status4640b05a…。V2实际语义c2c36812…、独审ab9644ea…104项；receipt pipeline/admissions/M212-BCR.json b8532405…。是技术准入，非准确率收益。
- 当前M211-BTC stable {BTCID}，tested/admitted/科学source00e2b18c6b8d568a64edb496e6979d766440883c、receipt93756329…保持；公共runtime后推进11a仅BCR9新增，BTC8源/已部署YAML/common/原进程未改。原几何父组平衡tree inside/outside、原cfskip/LN/fine-coarse/raw-CSORT/HCG/单inst保留。
- BTC原真TRAIN2 loss9.507390976/13.910472870，common843/hash04231c…；64真n>=3组、inside384/outside896/leaf512/rootinside0，三map更新；原资源9.758338124G vs9.762532428G，157352506参数，旧GPU0 median+13.3134%/P90+19.3694%明确更慢。原ddb四raw/独审dc03…/receipt9375保持，不拿其结果代签BCR。

## Closed Or Failed Directions
- 旧8hold的canonical/655声明ref字符串/13旧授权元数据最近复核为tick_4a08c096/held_boundary_check.json 6326fe1a…。本轮新增GPU1资源授权仅allocation，不重开旧scope，不重新遍历655证据正文或重测旧门。
- 4supervision scope、2measurement implementation/inconclusive及PCE/RSTR限度保持；PCE默认2+额外1已尽/2.861e-6与13.86x；RSTR默认2已尽/R2mean1.027033878e-6>1e-6。禁PCE_R4/RSTR_R3/M201自动恢复；RSTR旧9文件localcommit授权不是新修订许可。
- 所有原HRC/PSBR/HAP/PSNC负结果、版本/日志/收据/archive保留，不整体否定hierarchy或借完成诊断重选样本/seed。

## Running And Queue
- M212-BCR server4 GPU1唯一新run，PID1215422/start51717921；原argv/cwd/fd1唯一log/source8/映射YAML/UUID1/HEAD11a实核，Train1/50 62→67/4686；proof tick_7526f819/bcr_progress_observation.json 7efe878a…。startticks为首次真实postlaunch样本，非声称dispatch时已采集。
- M211-BTC GPU0原PID2784474/start47557208，原argv/cwd/fd1/source8及mappedYAML77eac419…未变，Train18/50 1→6/4686；proof btc_progress_observation_after.json b4dba5c8…。admittedsource00e与公共runtime11a分别记录，效能UNKNOWN。
- primary仅00e→11a已测9新增ff-only，原28dirty/untracked status+bytes及index空保持，不新commit/force/stash/reset/clean。canonical safe_sync远端同样ff-only且前后实际source验证；候选YAML仅既定路径适配。
- 本轮一次_process_queue/一次真实Popen，wrapper只查GPU1并在3flock覆盖UUID/idle至Popen返回，后释放不冒称全程训练锁；actual launch/progress41a14e95…，最终独审{sha(final_review)[:16]}…，M206与BTC原row/exp/receipt保持。
- pinned songcl@192.168.1.115/dl04-MS-7E06；UUID0 GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，UUID1 GPU-7f82edb9-f620-8045-caea-a75232265cd1；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster/runtime server4_conda_4ca73fba.sh，data /home/songcl/data/data/；keys/strict hostkey，不用旧.137/密码/sudo，python -B。
- M206-CGCA仍waiting但paused_by_user/dispatch_hold/resume_authorizedfalse，无PID，不计ready、不自动恢复/迁卡。完整snapshot meta24/best.4952535927295685/noimprove7，last.pth e9b42b26…，admitted898ff63与公共runtime11a有别，GPU1可用不授M206恢复。

## Open Questions And Risks
- BTC/BCR正式训练准确率UNKNOWN；目标.5100仍差.0080。真实原生门通过不证明上涨/新颖性，不调seed/schedule/阈值，不用test集选机制。BCR recurrence长链衰减/爆炸、方向/tie-ID敏感性及own/context非线性减弱仍待实测，不宣称旋转不变。
- BCR当前同GPU1资源pair时延比M95更慢；不与BTC旧GPU0 timing做因果比较。原fvcore完整unsupported披露，CPU/Python工作未全计；pureTRAIN峰值UNKNOWN，smoke含observer/topology开销。
- 配对仅共同named参数与两原batch，full buffer/RNG未逐值配对；raw/map跨目标digest差异保留、不立新相等门或作因果归因；empty/pad/singleton覆盖0属未行使，offdiag/fullFP32控制NOT_RUN。
- BCR candidate早期/proc argv=[]是瞬时未观测，仅construct command/directPopen.wait/原request/result链证明本次诊断，不用于后续信号身份；正式train另有真PID/start/argv/cwd/fd1/progress双样本。
- 任何未知launch仅原request/PID/log只读reconcile，不盲重启/kill/删锁；后续GPU检查须fresh owner/assets/实际占用/三锁，旧lease与静态catalog不授未来资源。

## Last Tick
- 本轮begin一次monitor/goal/已有派发，experiment_first design预算2，actual1新准入M212并验证双卡运行；不为凑满预算新造占位变体，不改其他项目/资源边界/禁用项/调度。
- 最新人类GPU1授权90f882落盘、SERVERS allowed[0,1]；从完整BCR11a准备继续，静态GPU1port/52离线/独审后本轮实际4原生请求，结果与标准/收据/队列均真，不只改stage。
- 原9source主线ff-only/既有safe-sync/唯一canonical dispatch后GPU1新BCR Train1/50递增，GPU0原BTC Train18/50递增、M206仍暂停；本轮具体证据均在tick_7526f819，full六段report按report_notes.json生成。
- goal0441/YAML/seed/data/训练参数及28旧工作字节/index、原失败/暂停/授权范围保持；本轮无需用户再确认。原deadline不延长；report后真实finish核FINALIZED/released及lock/pending消失，释放后不回写。
"""
  assert len(memory.splitlines())<120
  mp=ROOT/'pipeline/codex_memory.md';tmp=mp.with_name(mp.name+'.'+TOKEN+'.tmp');tmp.write_text(memory,encoding='utf-8');os.replace(tmp,mp)
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'native_training_on_gpu0_and_gpu1_verified':True,'old_M206_user_pause_unchanged':True,'memory_lines':len(memory.splitlines()),'final_independent_review':ref(final_review),'protected_canonical_queue_experiment_receipts_unchanged_during_persist':True,'research_work':ref(ROOT/'pipeline/research_work.json'),'memory':ref(mp),'notes':ref(HERE/'report_notes.json'),'postflight':'NOT_YET_CALLED'}
  with (HERE/'gpu1_completion_persisted.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
  print(json.dumps({'status':'ACTUAL_GPU1_COMPLETION_PERSISTED_PRE_POSTFLIGHT','memory_lines':len(memory.splitlines()),'report_notes':str(HERE/'report_notes.json')}))
 finally:lock.close()
if __name__=='__main__':main()
