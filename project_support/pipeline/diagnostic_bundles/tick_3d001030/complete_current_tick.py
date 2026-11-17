"""Reconcile current research catalogue after actual reviewed R1 guard.
No remote, queue, source, resource-policy, or training operation.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='3d001030cda04cddade0810e9d380a22'
CTS='hierarchy-parent-cyclic-triadic-state-composition';BEC='hierarchy-cross-level-bipartite-edge-composition'
CODE='4e80006047d5cb3dcdfb9c1102e02c33f354a07d';NEW='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encoded(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def save(p,x):
 with Path(p).open('xb') as f:f.write(encoded(x));f.flush();os.fsync(f.fileno())
def replace(p,data):
 tmp=p.with_name(p.name+'.'+TOKEN+'.reconcile.tmp')
 with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def main():
 owner=guard();sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();assert not (HERE/'final_reconciliation_intent.json').exists(),'Reconcile any interrupted intent; no replay'
  baseline=read(HERE/'protected_assets_before.json');pre=snapshot()
  assert all(pre[k]==baseline[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
  assert (HERE/'protected_assets_after.json').exists()
  anchor=read(HERE/'bec_r1_static_anchor_result.json');local=read(HERE/'bec_r1_actual_local_guard.json')
  assert anchor['owner']['token']==local['owner']['token']==TOKEN and anchor['R1_revision_result']=='pending'
  assert local['native']==local['resources']=='NOT_RUN' and local['transport_calls']==0 and local['outcomes']['0']['refused'] and local['outcomes']['1']['refused']
  obs=read(HERE/'cts_native_progress_observation.json');peer=read(HERE/'cts_native_progress_independent_review.json')
  assert obs['owner_token']==TOKEN and obs['native_TRAIN_growth'] is True and peer['material_concerns']==[]
  first,last=obs['observations'][0],obs['observations'][-1]
  assert (last['pid'],last['start_ticks'],last['runtime_HEAD'])==(3505065,'61122472',CODE)
  assert (last['train_progress'][0],last['train_progress'][2])>(first['train_progress'][0],first['train_progress'][2])
  wp=ROOT/'pipeline/research_work.json';w=read(wp);out=copy.deepcopy(w)
  c=next(x for x in out['candidates'] if x['id']==CTS);b=next(x for x in out['candidates'] if x['id']==BEC)
  assert c['code_commit']==CODE and b['code_commit']==NEW and b['native_execution_code_commit'] is None
  assert len(b['revision_history'])==1 and b['revision_history'][0]['result']=='pending'
  now=datetime.now(timezone.utc).isoformat()
  keys=['stage','training_status','admission_status','resource_authorization','resource_wait','next_action','known_limits','matched_control','preparation_complete_source_only','operational_preparation_status']
  c.setdefault('training_catalog_history',[]).append({'recorded_at':now,'reason':'Preserve earlier waiting/source-only catalogue before reconciliation with original verified launch and current real progress.','previous_fields':{k:copy.deepcopy(c.get(k)) for k in keys}})
  resource={'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}
  progress={'observed_at':last['observed_at'],'pid':3505065,'start_ticks':'61122472','server':'server-4','physical_gpu':0,'first':first['train_progress'],'last':last['train_progress'],'evidence':ref(HERE/'cts_native_progress_observation.json'),'independent_review':ref(HERE/'cts_native_progress_independent_review.json'),'scope':'Original training verified by current increasing native steps; no new launch by this observer.'}
  c.update(stage='training',training_status='running',admission_status='ADMITTED_TRAINING_PROGRESS_VERIFIED',resource_authorization=resource,preparation_complete_source_only=False,operational_preparation_status='ORIGINAL_TRAINING_PROGRESS_VERIFIED',training_progress_observation=progress,
   matched_control='Original M95 native YAML/pretrain/seed1999/epochs50/max_iters70/data/optimizer. Matched fixed TRAIN2/common initialization and original resource arms were actually reviewed in tick45eb/a33c; trained efficacy remains unknown.',
   resource_wait={'state':'OWN_ORIGINAL_CTS_RUNNING','server':'server-4','physical_gpu':0,'observed_at':last['observed_at'],'evidence':ref(HERE/'cts_native_progress_observation.json'),'scope':'Bounded own-process observation, not continuous exclusivity; earlier foreign-PID wait remains in history.'},
   next_action='Preserve original CTS PID3505065 on sole server4 physicalGPU0. Observe original training/validation and canonical terminal handling. No restart, GPU1, eviction, old no-launch helper replay or source promotion while CTS remains active.')
  c['known_limits']=['Actual fixed TRAIN2 backward and original paired resources passed on source4e8; this does not establish trained efficacy, novelty or single-factor causality.','Current original native training growth is independently observed in this tick. Latest validation metric was not extracted by this observer.','Full-buffer/RNG equality, offdiagonal effects, unexercised singleton/empty/pad boundaries and pure TRAIN peak memory remain unknown.','All earlier source-only/software checks and old resource authorizations are historical. Current GPU0-only authorization governs future computation.']
  for item in [ref(HERE/'cts_native_progress_observation.json'),ref(HERE/'cts_native_progress_independent_review.json')]:
   if item not in c['evidence']:c['evidence'].append(item)
  actual_refs=[ref(HERE/'bec_r1_static_anchor_result.json'),ref(HERE/'bec_r1_actual_local_guard.json')]
  for item in actual_refs:
   if item not in b['evidence']:b['evidence'].append(item)
  b['execution_adapter']['actual_current_local_guard']=actual_refs[1]
  b['current_resource_check']={'result':'blocked','evidence':actual_refs[1],'reason':'Actual software guard reached registered CTS busy on sole permitted GPU0 and authorization refusal for GPU1. Separate current native observation confirms original CTS running. This is not a hardware-idle query or native R1 resource PASS.'}
  if w.get('tick_attempt'):out.setdefault('tick_attempt_history',[]).append(copy.deepcopy(w['tick_attempt']))
  out['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':BEC,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+(HERE/'bec_r1_anchor_execute/check_bec_r1_current_guard.py').as_posix()+' --execute-root','observation':'Reviewed actual R1 adapter passed current-owner/source026c/external-anchor checks, then GPU0 refused registered original CTS occupancy and GPU1 refused explicit GPU0-only scope. No transport/process/network/Torch/active material. R1 native TRAIN/resources remain NOT_RUN.','evidence':[actual_refs[1]]}
  out['updated_at']=now;out['next_action']='Preserve original CTS on sole server4 GPU0. BEC R1 exact026c and reviewed tools are statically bound; after CTS releases GPU0, fresh actual idle/UUID/assets/three-lock/current-owner checks must precede original fixed M95/R1 TRAIN2 and resource arms. M206 paused; no GPU1, BFC restart or held-route reopening.'
  others=lambda z:{x['id']:x for x in z['candidates'] if x['id'] not in (CTS,BEC)}
  assert len(out['candidates'])==141 and others(out)==others(w)
  assert b['revision_history']==next(x for x in w['candidates'] if x['id']==BEC)['revision_history']
  ep=ROOT/'pipeline/experiments/M214-CTS.json';old_exp=read(ep);new_exp=copy.deepcopy(old_exp)
  assert (old_exp['status'],old_exp['training_status'],old_exp['pid'],old_exp['launch_verified'],old_exp['code_commit'])==('running','waiting',3505065,True,CODE)
  new_exp['training_status']='running'
  mem='''# Codex Research Memory

## Goal And Phase
- 当前3d001030cda04cddade0810e9d380a22，实际会话/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T10:05:37.308291+00:00/deadline11:05:37.308291+00:00原值保持。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020/baseline.4894/gap.0080。Phase1层级分工→inst_feats→query/masks，监督辅助，Phase2需人工确认。
- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变；原10G/原fvcore handlers/fullunsupported、bs1/lang1/warm20/repeat100 median/P90。峰值显存+15%需≥+.003mIoU；禁调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst注入、旧rejected改名/无图改变微调。
- standing authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖项目普通实验操作，不授旧hold重开/额外修订/受保护恢复/扩大资源/改调度。
- 最新人类不用gpu1：SERVERS SHA2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1仅server4 physical[0]/max1；授权server4_gpu0_only_20261026.json SHA94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09。旧GPU1实测仅历史依据；未来禁用GPU1，其他allowed[]/调度Disabled保持。

## Champion And Baseline
- M95仍.5020；M205-MDC26/.4872、M207-HAP31/.5002、M208-HRC31/.4901、M209-PSBR23/.4969、M210-PSNC31/.5001、M211-BTC31/.4914、M212-BCR27/.4995均自然早停未超M95。不调参重跑或整体否定层级方向。
- HAP原DataLoader异常根因UNKNOWN、epoch18恢复授权已消费；BTC/BCR原版本/归档/完整日志保持，不再启动。BCR archive5d060afca23d43deb4ae63525c00ff3d/完整log f14c962f…。

## Active Hypotheses
- M214-CTS真实训练；source/primary/runtime4e80006047d5cb3dcdfb9c1102e02c33f354a07d（父48fc），原8源/YAML/receipt5416d5e…保持。准入在e245、启动在前facc canonical begin，本轮新启动0。当前进度见下方Running及本轮观测文件，不拿旧waiting或queue残余phase重启。
- CTS为同父几何cycle上共享dense3tap dilated circular Conv1D家族：old own/±3^r→3C→C/GELU，最小3^k≥n；保留原LN/cfskip/finecoarse/rawmean/FPS/IDs/CSORT/HCG/单inst。不是新覆盖、新颖或单因素收益证明。
- 原45eb实际M95/CTS TRAIN2+原资源四臂a33c0fe7…/独审5d2f0716…通过，loss9.547047615/13.908418655、共同843张量/156958522参数、真实3distinct、多轮64/60、三W列原loss有限非零grad/每step更新；原owner/GPU0不重标重测。资源9.761811532G vs9.762532428G、params157155386 vs157484090、同GPU0 median35.8969 vs38.2312ms/P9037.4890 vs42.4553ms；+15%条件未触发，准确率/pureTRAIN峰值未知。
- M215-BEC现有candidate已静态绑定隔离R1 source026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563（单父4e8）；主线/运行源仍4e8。双跨层joint child+parent→2C/GELU split u/v，v等权上行，经coarse原LN/FFN再两2C→C/GELU回传middle/fine；原六model文件/rawmean/FPS/IDs/CSORT/单inst保持。
- 原9b678…两smoke真实finite成功，但candidate资源rc1/JIT aten::index_fill bool alias断言f8fac959…；原四raw/native9b/旧双卡snapshot完整留history，属于实现失败，非资源超标或假设反证，不继承为R1原生结果。
- 唯一implementation R1仍pending，prereg3fa782b8…；CPU390ac50a…原3case：bool/int1 eager mask相同，bool JIT原错重现，int1 trace/eager相同且原fvcore通过。仅CPU兼容，非新全模型GPU通过。单True→1私包2ef488c4…/Git实证617203db…（创建时primary48fc）保持；无新修订。
- R1 op tick_faccbed6/bec_r1_operational_prepare/preparation.json SHA9a81c28ac80f2f9f00184f67f7bd47841124cb8a18e0a22c554eaceb10957d35/nativeedd2049e…/releaseee75b293…、原worker7e5d与9runtime函数AST保持；静态独审tick_e2e3d058/bec_r1_operational_independent_review.json SHA0e3572192e3a0d68e8d4f656cdf3d74d15a8e3f9b1b2b79f2fcf4671f5dcc627仅工具准备。
- 新只读四结果checker57752ca3…/071202cf…与peer98def957…保留原15科学函数AST，拒旧9b/GPU1/缺四结果；source026c真实native TRAIN/resources均NOT_RUN，native_execution_code_commit=null、10active字段null，不造标准PASS/receipt/queue。
- 本轮仅currentowner新copy重绑、审后静态release bytecopy与sameBEC外锚；actual NoTransport实际到达0 registeredCTSbusy和1仅GPU0授权拒绝，0transport/process/network/Torch/active材料。当前resource_check/blocked不是硬件空闲查询或native资源PASS。
- BEC后续仅原CTS自然终态/释放GPU0后，fresh实际idle/UUID/assets/三锁/currentowner复核，再跑原M95/R1固定TRAIN2+资源四臂；不得改样本/seed/阈值，不对运行CTS同步026c。
- M213-BFC原TRAIN20/50 step3832/4686共享DataLoader scatter overlap RuntimeError，crashed archiveb91b3ba11671451bb28f39dc3cc3f2c7；source48fc/receipt812454/launch/完整log daf14d06…保持，根因UNKNOWN，不否定机制、不自动恢复。
- BFC last.pth SHA24b3424f0cdc3a6f004bf20ff49b1799e75b92382214b2590d90486192883777，epoch19/best.4992169439792633/noimprove4/1151CPUtensor finite/640optstates/5groups/maxstep89034/scheduler19；证据9b957f10…/计划8379534d…已存。RNG/sampler/失败输入未复现，不能称续3833；需具体兼容源计划与BFC专属人类授权，不借HAP/M206grant。

## Closed Or Failed Directions
- 旧10本轮due已bounded metadata复核，tick_3d001030/held_boundary_check.json SHAed313bb0799275f8fe6e1bccae03196e1cd1b80d95b589983ec71f040cc08441；旧8记录/655声明ref与M206暂停全同509e，原14授权metadata同，现15仅新增已知GPU0-only撤回，非重开许可。未读655正文/旧grant/checkpoint体，不重开或重测，无新action。
- PCE默认2+额外1已尽/2.861e-6/13.86x，RSTR默认2已尽/R2mean1.027033878e-6>1e-6；禁PCE_R4/RSTR_R3/M201自动恢复。旧RSTR9文件localcommit授权不授额外修订，负证据全保留。
- 原2d06 prep/null、native322c原23文件/null/DRAFTTrue、旧9b op420/8e/b551均原字节；新R1工具是新包，不填旧null或原地启用。BFC P90+3.2118%/BCR原GPU1较慢，不夸全面效率；预测/observer不等pureTRAIN峰值。

## Running And Queue
- CURRENT_PROGRESS_PLACEHOLDER
- CTS catalogue现training，experiment仅辅助training_status waiting→running单字段校正；queue/running/receipt/code保持，旧catalog/字段前值完整留档。最新验证指标本轮未知，不把步数当收益。
- M206-CGCA仍waiting但paused/dispatch_hold/resume_authorized=false，不计ready；0可运行待跑，BEC R1未准入待GPU0；BFC不恢复，GPU1禁用。
- pinned songcl@192.168.1.115，先验证dl04-MS-7E06；GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1；conda project_cluster/server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。keys/strict hostkey，不用旧IP/密码/sudo。
- 未知claim/request/PID只读reconcile，不盲重启/kill/删锁；白名单/旧lease不是未来空卡许可。真实GPU计算前核当前资源/UUID/三锁/原deadline；python -B与PYTHONDONTWRITEBYTECODE=1。

## Open Questions And Risks
- 目标gap.0080不变，CTS效果仍待测，R1尚未GPU复测；静态工具/CPU兼容/NoTransport不代签原生backward/resources/准确率。
- 原CTS/BFC相应native臂已观测finitegrad/update；fullbuffer/RNG/offdiagonal、未行使零边界/pureTRAIN峰值未知。BFC根因/输入未复现，clone未验证，未经专属授权不续训。

## Last Tick
- 前facc及e2e3因上游模型容量中断已各按原token canonical abort/INCOMPLETE/released；旧快照/原deadline不延长、旧freeze证据保留。本轮新owner/context独立，不执行过期旧helper。
- snapshot candidate/admission预算2、creation/reserve预算0、reserve2/target2、pending12；只完成CTS/BEC已有工作与bounded hold复核，0新候选/修订/Git/receipt/准入/入队/派发/训练启动。
- 本轮真实进展为R1受审工具静态外锚+actual NoTransport current resource_check/blocked，以及CTS当前只读进度复核；R1仍pending/NOT_RUN，所有历史原生结果保留原owner/版本。
- primary4e8/28用户文件status+bytes/index空、其他139候选与11账保持；CTS experiment仅辅助training_status一个field改变并保存前对象/精确diff。七段memory/六段report后canonical finish，以实际receipt/释放为准，释放后不回写。
'''
  mem=mem.replace('CURRENT_PROGRESS_PLACEHOLDER',f"当前1running CTS，server4 GPU0，原PID3505065/start61122472；采集{first['observed_at']}→{last['observed_at']}，TRAIN{first['train_progress']}→{last['train_progress']}；证据tick_3d001030/cts_native_progress_observation.json SHA{sha(HERE/'cts_native_progress_observation.json')}，独审同目录。此为原训练当前有界观测，不声称持续独占。")
  assert len(mem.splitlines())<120 and mem.count('\n## ')==7 and 'PLACEHOLDER' not in mem
  notes={'actions':[
   f"本轮只读核原CTS3505065/start61122472，nativeTRAIN{first['train_progress']}→{last['train_progress']}；source4e8/8源/YAML/UUID0/argv/cwd/fd1保持，当前独立复核无实质疑点；本轮新启动0。",
   '复用原deadline内冻结且受审的R1 op/native/checker，只重绑新owner和fresh保护基线；审后static release bytecopy与existingBEC source026c外锚，完整旧9b两smoke成功/JIT资源失败及原null/禁用包保持，不继承为R1原生通过。',
   '真实执行currentowner/new026c/external-anchor NoTransport guard：GPU0到达registered CTSbusy拒绝、GPU1按明确GPU0-only拒绝；0transport/process/network/Torch/active材料。该软件保护核验并非硬件idle或native资源PASS；R1仍pending/四原生臂NOT_RUN。',
   'CTS catalogue对齐真实训练；experiment只修辅助training_status waiting→running，queue/running/receipt/source保持。主线4e8/28用户文件/index及其他139候选/其他11受保护账不变，前对象/精确diff与保护audit留档。',
   '旧10到期仅有界metadata复核：旧8记录及655声明ref/M206暂停与509e一致，原14授权metadata同、现15仅新增已知GPU0-only撤回；未读655目标/旧grant/checkpoint体，无新许可或可行动事项。证据held_boundary_check.json SHAed313bb0799275f8fe6e1bccae03196e1cd1b80d95b589983ec71f040cc08441。',
   '0新候选/修订/Git/准入/入队/派发/训练启动，未超creation预算0；仅GPU0，M206暂停/BFC未恢复/调度Disabled保持。'],
   'decisions':['CTS继续原GPU0训练，验证指标/效果本轮未知；目标.5100/M95.5020/gap.0080保持。','BEC R1等待原CTS释放GPU0；fresh真实idle/UUID/assets/三锁/currentowner通过后，按原YAML跑固定M95/R1 TRAIN2与资源臂，不换样本/seed/阈值，不对原运行同步026c。','以当前真实resource_check/blocked留档收尾，不凑准入额度，不将NoTransport或静态工具当科学PASS。既有授权足够常规后续工作，无新增确认请求。','前e2e3中断收据为INCOMPLETE；本轮不预签postflight，最终以canonical finish和实际FINALIZED/released为准。']}
  work_bytes,exp_bytes,memory_bytes=encoded(out),encoded(new_exp),mem.encode('utf8');encoded(notes)
  before={'work_sha256':sha(wp),'exp_sha256':sha(ep),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
  save(HERE/'final_reconciliation_before.json',{'owner_token':TOKEN,'CTS_experiment_before':old_exp,'CTS_catalog_before':next(x for x in w['candidates'] if x['id']==CTS),'BEC_before_final_notes':next(x for x in w['candidates'] if x['id']==BEC),'tick_attempt_before':w.get('tick_attempt'),'protected_snapshot':pre,'hashes':before})
  save(HERE/'final_reconciliation_intent.json',{'recorded_at':now,'owner_token':TOKEN,'before':before,'scope':'Two existing catalogues/current blocked attempt/compact memory; CTS exp auxiliary training_status only','no_remote_source_or_queue_operation':True})
  guard();assert sha(wp)==before['work_sha256'] and sha(ep)==before['exp_sha256']
  replace(wp,work_bytes);replace(ep,exp_bytes);replace(ROOT/'pipeline/codex_memory.md',memory_bytes);save(HERE/'report_notes.json',notes)
  after=snapshot();assert all(after[k]==pre[k] for k in ['head','index_empty','status_hex','files'])
  changed=[k for k in pre['protected_ledgers'] if pre['protected_ledgers'][k]!=after['protected_ledgers'][k]];assert changed==['experiments/M214-CTS.json']
  assert read(ep)==new_exp and {k for k in set(old_exp)|set(new_exp) if old_exp.get(k)!=new_exp.get(k)}=={'training_status'}
  assert read(wp)==out and others(read(wp))==others(w)
  assert (ROOT/'pipeline/codex_memory.md').read_bytes()==memory_bytes
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'source_head_28_user_files_status_and_index_unchanged':True,'other139_candidates_unchanged':True,'candidate_count':141,'new_candidates':0,'changed_protected_ledgers':changed,'CTS_experiment_semantic_diff':{'training_status':{'before':'waiting','after':'running'}},'other11_protected_ledgers_unchanged':True,'queue_running_receipts_unchanged':True,'CTS_native_progress':progress,'BEC_R1_native_resources':'NOT_RUN','BEC_R1_revision_result':'pending','new_training_launches_by_this_tick':0,'memory_lines':len(mem.splitlines()),'after_snapshot':after,'work_sha256':sha(wp),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md'),'notes':ref(HERE/'report_notes.json'),'material_concerns':[]}
  save(HERE/'final_reconciliation_result.json',result);print(json.dumps({'status':'CURRENT_CATALOGUE_AND_SINGLE_AUX_FIELD_RECONCILED','result':ref(HERE/'final_reconciliation_result.json'),'memory_lines':len(mem.splitlines())},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
