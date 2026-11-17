"""Truthful terminal-log supplement, research state and current-run handoff only."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess,sys
from run_next_bec_arm import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='94f8ddb8a6e049c48c8e6237f4c737e8';CODE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
CTS='hierarchy-parent-cyclic-triadic-state-composition';BEC='hierarchy-cross-level-bipartite-edge-composition';AEF='hierarchy-parent-antisymmetric-edge-flux'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def data(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def save(p,x):
 with Path(p).open('xb') as f:f.write(data(x));f.flush();os.fsync(f.fileno())
def replace(p,x):
 t=p.with_name(p.name+'.'+TOKEN+'.finish.tmp')
 with t.open('xb') as f:f.write(x);f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def main():
 guard();assert not (HERE/'completion_intent.json').exists(),'Existing intent requires reconciliation, never replay'
 obs=read(HERE/'bec_training_progress_observation.json');peer=read(HERE/'bec_training_progress_independent_review.json')
 dispatch=read(HERE/'bec_dispatch_result.json');assert obs['owner_token']==TOKEN and obs['native_TRAIN_growth'] and dispatch['verified_native_progress'] and peer['material_concerns']==[]
 first,last=obs['observations'][0],obs['observations'][-1]
 assert (last['pid'],last['start_ticks'],last['runtime_HEAD'])==(1558071,'64444390',CODE)
 assert first['train_progress']==[1,50,471,4686] and last['train_progress']==[1,50,480,4686]
 receipt=ROOT/'pipeline/admissions/M215-BEC.json';assert sha(receipt)=='113a72afb83c57401d00072b1a723a5cc3094a76a1e2d9acfe75b465f10238dc'
 archive=read(HERE/'cts_exact_archive/archive_evidence.json');log=Path(archive['local_path'])
 assert archive['sha256_size_match'] and log.is_relative_to(ROOT) and log.stat().st_size==17693952 and sha(log)=='05dce0486051bf0cf8d4af30de61a6a756200efb47b32033b6355f5e7df12da4'
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor;import closure
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();baseline=read(HERE/'protected_assets_before.json')
  def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
  assert git('rev-parse','HEAD').decode().strip()==CODE and not git('diff','--cached','--name-only')
  assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==baseline['status_hex']
  assert all(sha(ROOT/'Cluster'/p)==h for p,h in baseline['files'].items())
  registry={n:sha(ROOT/'pipeline'/n) for n in baseline['protected_ledgers']}
  q=read(ROOT/'pipeline/queue.json');task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M215-BEC')
  assert task['status']=='running' and task['pid']==1558071 and task['launch_verified'] and task['launch_verification']=='training_progress'
  assert read(ROOT/'pipeline/running.json')['server-4']['0']=='M215-BEC';closure.admission(ROOT,task)
  cpath=ROOT/'pipeline/experiments/M214-CTS.json';oldcts=read(cpath);newcts=copy.deepcopy(oldcts)
  assert oldcts['status']=='stopped_unknown' and oldcts['archive_id']=='a966d7e40d26454598863ac4a87fc4a9' and oldcts['final_best']=='0.4890'
  assert oldcts['log_local']=='';newcts['log_local']=str(log);newcts['training_status']='stopped_unknown'
  expdiff={k:{'before':oldcts.get(k),'after':newcts.get(k)} for k in set(oldcts)|set(newcts) if oldcts.get(k)!=newcts.get(k)}
  assert set(expdiff)=={'log_local','training_status'}
  wp=ROOT/'pipeline/research_work.json';w=read(wp);out=copy.deepcopy(w)
  c=next(z for z in out['candidates'] if z['id']==CTS);b=next(z for z in out['candidates'] if z['id']==BEC);a=next(z for z in out['candidates'] if z['id']==AEF)
  assert len(w['candidates'])==142 and b['revision_history'][0]['result']=='passed' and b['code_commit']==CODE and b['stage']=='training'
  assert b['implementation_revision_sha256']==closure.revision_digest(b['revision_history'][0])
  now=datetime.now(timezone.utc).isoformat()
  c['stage']='complete';c['training_status']='stopped_unknown';c['training_terminal']={'archive_id':oldcts['archive_id'],'status':'stopped_unknown','epochs_final':'14/50','best_recorded':'0.4890','cause':'UNKNOWN','partial_run_not_scientific_falsification':True,'exact_own_log':ref(log),'archive_evidence':ref(HERE/'cts_exact_archive/archive_evidence.json')}
  c['next_action']='Preserve exact original partial CTS stopped_unknown archive/log/checkpoint/source. No automatic restart/resume, no claim of normal completion or mechanism falsification. A concrete native resume plan and any required experiment-specific authorization are separate future work.'
  for x in [ref(log),ref(HERE/'cts_exact_archive/archive_evidence.json')]:
   if x not in c['evidence']:c['evidence'].append(x)
  b.setdefault('resource_check_history',[]).append(copy.deepcopy(b.get('current_resource_check')))
  b['current_resource_check']={'result':'original_training_running','evidence':ref(HERE/'bec_training_progress_observation.json'),'observed_at':last['observed_at'],'server':'server-4','physical_gpu':0,'scope':'Bounded current original BEC source/process/step/UUID observation; not continuous exclusivity or pure TRAIN peak measurement.'}
  b['training_progress_observation']={'first':first['train_progress'],'last':last['train_progress'],'pid':1558071,'start_ticks':'64444390','observed_at':last['observed_at'],'evidence':ref(HERE/'bec_training_progress_observation.json'),'independent_review':ref(HERE/'bec_training_progress_independent_review.json')}
  b['efficacy']='UNKNOWN';b['next_action']='Monitor original verified BEC PID1558071/source026c/log on server4 physicalGPU0; preserve original YAML/seed1999/schedule/data/optimizer. No rerun, other-GPU fallback or validation-based tuning; efficacy remains to be measured.'
  for x in [ref(HERE/'bec_training_progress_observation.json'),ref(HERE/'bec_training_progress_independent_review.json'),ref(HERE/'bec_dispatch_result.json')]:
   if x not in b['evidence']:b['evidence'].append(x)
  a['operational_compatibility']={'current_primary_reference':CODE,'frozen_source_preparation_unchanged':True,'original_prospective_parent':'4e80006047d5cb3dcdfb9c1102e02c33f354a07d','actual_source_version':'NOT_CREATED','scope':'Original private9 AEF files unchanged; future source packaging must be a genuinely compatible child of then-current main, never assume sibling ff.'}
  a['next_action']='While original BEC uses soleGPU0, prepare actual compatible isolated source/native tooling from unchanged frozen AEF9 files against current main026c. Do not change old source metadata or assume sibling ff. Native TRAIN2/resources still NOT_RUN and must wait for genuine authorized idleGPU0; no GPU1 or old held reopening.'
  out['updated_at']=now;out['next_action']=b['next_action']
  others=lambda z:{x['id']:x for x in z['candidates'] if x['id'] not in (CTS,BEC,AEF)}
  assert others(out)==others(w)
  oldmem=(ROOT/'pipeline/codex_memory.md').read_text('utf8');parts={};key=None
  for line in oldmem.splitlines():
   if line.startswith('## '):key=line;parts[key]=[]
   elif key:parts[key].append(line)
  headers=['## Goal And Phase','## Champion And Baseline','## Active Hypotheses','## Closed Or Failed Directions','## Running And Queue','## Open Questions And Risks','## Last Tick'];assert set(parts)==set(headers)
  parts[headers[0]][0]='- 当前94f8ddb8a6e049c48c8e6237f4c737e8，用户主动询问没有实验后新begin；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致，generated2026-10-26T14:57:12.614254+00:00/deadline15:57:12.614254+00:00原值保持。'
  parts[headers[2]]=[
   '- M215-BEC R1现已真实训练，primary/runtime/source026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563（父4e8），精确9A ff，不新造commit。admission113a72afb83c57401d00072b1a723a5cc3094a76a1e2d9acfe75b465f10238dc，唯一canonical dispatch/native Popen1次，原GPU0 PID1558071/start64444390，原YAML/seed1999/epochs50/maxiters70/data/optimizer不变。',
   '- BEC双跨层joint child+parent→2C/GELU split u/v，v按true child等权上行，经原coarse LN/FFN再两2C→C/GELU回传middle/fine；六原model/rawmean/FPS/IDs/CSORT/HCG/单inst保持。原9b两smoke成功/JIT bool index_fill资源失败f8fac959仍保留历史，非假设否定，不重标为026c结果。',
   '- 唯一implementation R1原注册3fa782b8… immutable字段保持；仅True→1 CPU兼容修复，CPU390ac50a先前bool/int1 eager相同、bool JIT失败/int1 trace+fvcore通过，原2ef/617源与原声明不改。现真实四臂独审后R1.result=passed、追加本轮actual result_evidence并用canonical revision_digest绑定收据，无新修订。',
   '- 本轮94f新R1四臂全terminal/rc0；原checker报告89099675a78da788f8186968102de364901859110f68ad8cd7bb45065ee798e0，独审46c47d4983a31205d710be5889e7e9e812bd4d3649865edef60c5f046b4c0a36。TRAIN2 loss9.3905391693/13.9133872986、真实两batch/common839张量/156432954参数/hash768c65…配对；5module/12原W块每步原loss有限grad+实际更新，fine边2048/middle512、上下行/私mean/原coarse/HCG/inst-mask路径观察通过。',
   '- BEC R1原资源9.720589388G vsM959.762532428G，params157220922 vs157484090（−263168）；同GPU0 median36.89109697 vs35.94086046ms（慢2.6439%），P9038.59042175 vs38.09330325ms（慢1.3050%）；预测allocated−.11237%，observer-smoke allocated−.03420%，+15%条件未触。保原handlers/fullunsupported，pureTRAIN峰值/效果/新颖性未知，不称全面更快。',
   '- 原R1 op9a81/nativeedd/worker7e/releaseee75、四结果checker57752/071202/98def均原字节；本轮只fresh绑定94f/原deadline/GPU0 staging执行，未原地改旧2d/null或322c原23文件/null/DRAFTTrue、旧9b op420/8e/b551。',
   '- M214-CTS已canonical stopped_unknown，archivea966d7e40d26454598863ac4a87fc4a9/14of50/best记录.4890；原PID3505065不见，ownlog停14:1843无尾部异常/正常结束标记。原因UNKNOWN，不说正常完成/模型失败，不自动恢复。原source4e8/receipt5416/launch/检查点未动。',
   '- CTS唯一完整log已root精确读取并本远SHA/size一致：17693952B，05dce0486051bf0cf8d4af30de61a6a756200efb47b32033b6355f5e7df12da4；tick_94f8ddb8/cts_exact_archive/archive_evidence.json，root补log_local与辅助training_status两field，原archive/status/best/epochs/receipt不改。',
   '- M216-AEF现stageimplementation/code+source=null；原150c冻结9源码配置prep9d6a03/candidate3898be/独审27d626（21集成+46独立stdlib）及01d交接011e37/复用cd1a6保持。只middle同原父组detached几何MST上的q=GELU(W[xi,xj])-GELU(W[xj,xi])及+/- incidence，原LN/skip/fine/coarse/rawmean/CSORT/HCG/单inst不变；只实数unweighted sum，不保RSTR πpointmean/非Markov，不授旧RSTR恢复/R3。',
   '- AEF原未来父4e8只是历史参考；现primary026c，后续须真实兼容source子版本与native工具，原冻结9文件不改/不假定sibling ff。理论参数−394240，实际Torch/FP32/grad/资源/效果均未测，不入队、不占GPU0。',
   *[line for line in parts[headers[2]] if line.startswith('- M213-BFC') or line.startswith('- BFC last.pth')]]
  closed=parts[headers[3]];closed[0]='- 旧10本轮未due，不读655正文/旧grant/checkpoint体、不重开/重测。最近bounded metadata tick_3d001030/held_boundary_check.json SHAed313bb0…是原时间证据，无新增恢复/修订许可。';parts[headers[3]]=closed
  parts[headers[4]]=[
   f"- 当前1个确认训练：M215-BEC source026c，server4 GPU0 PID1558071/start64444390；采集{first['observed_at']}→{last['observed_at']}，TRAIN1/50 471→480/4686；045ee028…观测/d265e8c0…独审。queue/experiment/running/receipt/current revision_digest一致，唯一selected0 mapping；不声称持续独占。",
   '- CTS已unknown终态归档并释放登记槽位，无自动resume；M206waiting但paused/dispatch_hold/resume_authorized=false不计ready，GPU1禁用。当前0ready，AEF只准备未入队；BFC不恢复。',
   *[line for line in parts[headers[4]] if line.startswith('- pinned') or line.startswith('- 未知claim')]]
  parts[headers[5]]=['- CTS停止原因UNKNOWN；仅日志无尾标，未读新checkpoint或构造恢复计划/授权，不推断外部kill/OOM/模型崩溃，不借HAP等grant。','- 当前BEC仅确认原生+资源与训练步数增长，准确率仍待测；目标.5100/M95.5020/gap.0080。原buffer/RNG/offdiagonal/未行使零边界/pureTRAIN峰值未知；单row/call零合法，不新加数值门。','- 初次额外observer因root guard返回None只在构造JSON时TypeError，先前两remote样本通过但未保存；新副本只适配guard真实owner返回+BEC输出key，remote观测程序不变，真实045ee结果已存。不是模型R2/训练失败，原失败源码留存。']
  parts[headers[6]]=['- 用户问为何无实验，本轮新begin先canonical第三次确认CTS缺失→stopped_unknown归档/登记槽位释放，非新造旧lease或绕阈值。随后GPU0真probe41MiB/0util/contexts空/3锁available，fresh R1 prepare/stage/四臂原请求执行。','- 真实4臂+原checker/独审通过后，只精确9A ff4e8→026c；canonical标准/decision/收据/R1passed digest/1队列，再一次canonical FIFO/selected0独占检查/Popen，源/配置实际同步到026c并verified原生步数增长。0新candidate/0新修订/0新commit，1实际准入/1实际训练启动。','- 原28用户文件status+bytes/index空保持；CTS canonical归档原字段与receipt、BFC crash/BCR earlystop/M206暂停保持。收尾只补CTS精确log_local/辅助training_status两field、CTS/BEC/AEF工作交接，不动其他139候选；原生raw/原owner/原先负结果均保持。','- 完整六段report与本七段memory后canonical finish，以实际FINALIZED/released receipt为准；释放后不回写。']
  mem='# Codex Research Memory\n\n'+'\n'.join(h+'\n'+'\n'.join(parts[h]).strip()+'\n' for h in headers)+'\n';assert len(mem.splitlines())<120 and mem.count('\n## ')==7
  notes={'actions':['确认CTS原进程连续缺失达canonical阈值，归档stopped_unknown/14of50/记录best.4890；原因UNKNOWN，原source/receipt/launch/checkpoint保持，未自动恢复。精确唯一完整17693952B ownlog本远SHA05dce048…一致，补log_local与辅助终态两field。','本轮GPU0真idle/UUID/3锁复核后，在新94f原deadline下执行BEC R1全部4原生臂，均terminal/rc0；两TRAIN loss9.3905391693/13.9133872986、common839/156432954、5module12块每步原loss有限grad及更新、真实双up/private mean/coarse/down/HCG/inst-mask路径核过。','原资源9.720589388G<10G、参数−263168；median比同卡M95慢2.6439%、P90慢1.3050%，observed内存+15%条件未触。保原handlers/fullunsupported，pureTRAIN峰值和训练效果未知，不称全面更快。','真实原checker89099675/独审46c47d49后，精确tested9A ff4e8→026c，28用户文件status+bytes/index空保持；soleR1原immutable prereg不改，result=passed/result_evidence为本轮真实四臂，canonical revision_digest/标准/收据113a72af有效。','1项真实准入/入队后，一次canonical FIFO+selected0三锁/idle→Popen，实际source/YAML同步后PID1558071 verified_native_progress；额外独立source8/ownlog/UUID/PIDstart核实TRAIN1/50步数471→480。新observer只修返回owner的记录schema，非模型修订。','0新候选/修订/Gitcommit/额外GPU；AEF保持原source-only准备，并记录须针对当前main026c做未来兼容版本，M206暂停/BFC不恢复/GPU1禁用，原139其他候选保持。'], 'decisions':['当前空档由CTS未知停止与后续原生门未完成造成；本轮已实际启动M215-BEC训练，后续监测其原PID/日志与验证指标，不把准入或步数增长当准确率收益。','CTS原partial未知停止不科学否定机制，保存精确证据，任何专属resume方案/必要授权另行准备，不借其他grant。','AEF后续在BEC占唯一GPU0时可做兼容source/native工具准备，实际TRAIN与资源仍待真空卡；不修改原私包/用旧源结果代签或假定sibling ff。','本轮有1有效新准入和验证启动，按实际budget完成；最终收尾以canonical postflight/FINALIZED released为准，无新增人类确认请求。']}
  wb,eb,mb=data(out),data(newcts),mem.encode();data(notes)
  before={'work_sha256':sha(wp),'CTS_experiment_sha256':sha(cpath),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
  save(HERE/'completion_before.json',{'owner_token':TOKEN,'before':before,'protected_ledgers':registry,'CTS_experiment_before':oldcts,'candidate_digests':{x['id']:hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest() for x in w['candidates']}})
  save(HERE/'completion_intent.json',{'owner_token':TOKEN,'recorded_at':now,'scope':'Research CTS/BEC/AEF handoff; CTS log_local+aux training_status only; compact memory/notes','before':before})
  guard();assert sha(wp)==before['work_sha256'] and sha(cpath)==before['CTS_experiment_sha256']
  replace(wp,wb);replace(cpath,eb);replace(ROOT/'pipeline/codex_memory.md',mb);save(HERE/'report_notes.json',notes)
  assert read(wp)==out and others(read(wp))==others(w) and read(cpath)==newcts
  changed=[n for n,h in registry.items() if sha(ROOT/'pipeline'/n)!=h];assert changed==['experiments/M214-CTS.json']
  assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==baseline['status_hex'] and not git('diff','--cached','--name-only')
  assert all(sha(ROOT/'Cluster'/p)==h for p,h in baseline['files'].items())
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'other139_candidates_unchanged':True,'new_candidates':0,'candidate_total':142,'source_HEAD':CODE,'protected28_status_bytes_index_preserved':True,'CTS_experiment_semantic_diff':expdiff,'other11_existing_lifecycle_ledgers_unchanged_during_completion':True,'BEC_original_training_verified':True,'BEC_receipt_sha256':sha(receipt),'CTS_log_sha256':sha(log),'memory_lines':len(mem.splitlines()),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md'),'work_sha256':sha(wp),'notes':ref(HERE/'report_notes.json')}
  save(HERE/'completion_result.json',result);print(json.dumps({'status':'REAL_RUNNING_BEC_AND_TERMINAL_CTS_HANDOFF_SAVED','result':ref(HERE/'completion_result.json'),'memory_lines':len(mem.splitlines())},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
