"""Persist routine observed facts and a real physical-resource check, without new research artifacts."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import sys,json,re
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
CID='hierarchy-coupled-node-edge-state-composition'
def main():
 if sys.argv[1:]!=['--execute-root']:print('DEFAULT_NOP');return
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  b=u.read(HERE/'protected_assets_before.json');u.protect(b)
  rawpath=HERE/'existing_runs_and_resource_observation.json';assert sha(rawpath)=='09048cbdfab69600d19d161070e1f12a6299420c7569c0042080b21be853da27'
  raw=u.read(rawpath);assert raw['owner']==EXPECTED and raw['returncode']==0 and raw['resource_precondition']['idle_gpu_ids']==[] and raw['resource_precondition']['result']=='blocked'
  runs=raw['observation']['observations'];assert [r['identity_before']['pid'] for r in runs]==[2085005,2685912] and all(r['strict_native_train_growth'] or r['strict_native_validation_growth'] for r in runs)
  a,z=runs;ma=a['precise_native_validation'];mz=z['precise_native_validation'];assert ma['best']<.502 and mz['best']<.502
  now=datetime.now(timezone.utc).isoformat();observed=datetime.fromisoformat(raw['observation']['observed_at'])
  memorypath=ROOT/'pipeline/codex_memory.md';assert sha(memorypath)==b['memory_sha256'];memory=memorypath.read_text('utf8')
  def replace(pattern,value):
   nonlocal memory
   memory,n=re.subn(pattern,lambda m:value,memory,count=1,flags=re.M);assert n==1,pattern
  replace(r'^- 当前owner.*$', '- 当前owner2c5dccfbdc4840a790faa7a0c4003f0e，generated2026-10-31T20:04:05.705401Z/deadline21:04:05.705401Z；真实root thread01a159c5-29ab-7a22-ba7f-e79174757253与foreground target一致，不延租约；收尾以实际receipt为准。')
  previous=u.read(ROOT/'pipeline/tick_receipts/31219b8b221e4a1caf715f19e34864b3.json');assert previous['status']=='FINALIZED' and previous['lease_release']=='released'
  replace(r'^- 上轮.*实际FINALIZED.*$', '- 上轮31219b8b实际FINALIZED/PASS/context_committed/released于'+previous['lease_released_at']+'；只完成轮询和审计，不代表科学收益。')
  replace(r'^- M226-WFC：.*$', '- M226-WFC：原无序楔信息交互、原PID2085005/start105948793/source94/GPU0不变；20:04:40→43Z TRAIN[15,2692]→2698，14次已完native val best .4918264150619507/noimp1，最近.4807886481285095；部分结果，不额外早停。')
  replace(r'^- M227-LFT：.*$', '- M227-LFT：原P/U三角分析→3packedFFN→逆合成，原PID2685912/start106767833/source4457/GPU1不变；20:04:43→46Z TRAIN[11,2226]→2233，10次已完native val best .4855799376964569/noimp0，部分结果未超冠军。')
  replace(r'^- 正式运行仍WFC.*$', '- 正式运行仍WFC GPU0与LFT GPU1，原PID/source/参数/耐心不变；本轮09048一次现场双TRAIN/log增长，NVML busy[0,1]/idle[]，两卡原PID均在。没有空闲卡，NEC/MIC原生检查等待，无新CUDA模型或训练。')
  replace(r'^- WFC \.4876/LFT \.4697.*$', '- WFC .4918/LFT .4856仍是部分验证且低于冠军；不调参/改seed/重启。NEC/MIC效力/novelty/实际预算未知，源MAC代理不能签10G PASS；whole新core原loss聚合finite非零梯度和实际更新才是训练性条件，个别map/row/column/bias零合法。')
  memory=memory.split('## Last Tick',1)[0]+'''## Last Tick
- begin20:04已检查原运行并尝试既有ready派发，无终态/故障/合格待跑。creation/reserve_budget0、已有2validation储备，不新建候选/复制草案/重跑旧源码suite。
- 唯一新实测09048：20:04双原TRAIN/log增长、精确partial native指标、原源/UUID/PID/start和NVML两卡忙核实；resource_check blocked当前证据归NEC。PCE只读文字复核相同事实、未写文件/查询remote，不为轮询造新独审包或科学准入。
- 0源码提交/模型修订/nativearm/准入/新训练/终态；MIC和其余154候选、旧10holds/M206暂停、38生命周期保持。已备实验等真实空槽，不将物理等待当候选native或资源预算失败。
- 仅常规健康进展/相同资源等待，无新科学结论或用户动作，DONT_NOTIFY。六段report/七段memory先留档；finish/release以真实receipt为准，释放后只读验收。下一轮空卡/终态/失败/其他实质事件才通知并继续已授权检查派发。
'''
  assert memory.count('\n## ')==7 and len(memory.splitlines())<120
  work=u.read(ROOT/'pipeline/research_work.json');assert sha(ROOT/'pipeline/research_work.json')==b['research_work_sha256']
  c=next(c for c in work['candidates'] if c['id']==CID);assert c['stage']=='validation' and c['native_status']==c['resource_status']=='NOT_RUN';ref=u.ref(rawpath)
  if ref not in c['evidence']:c['evidence'].append(ref)
  c['last_resource_check_at']=observed.isoformat();c['retry_after']=(observed+timedelta(hours=1)).isoformat()
  c['native_execution_blocker']={'kind':'occupied_authorized_gpus','server':'server-4','observed_at':observed.isoformat(),'busy_gpu_ids':[0,1],'original_tasks':['M226-WFC','M227-LFT'],'evidence':ref,'scope':'Actual physical precondition only; no candidate model/backward/profile execution or scientific failure.'}
  old=work.get('tick_attempt')
  if old and old.get('tick_started_at')!=EXPECTED['generated_at']:work.setdefault('tick_attempt_history',[]).append(old)
  work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+str(HERE/'observe_existing_runs.py')+' --execute-root','observation':'One actual source/original PID/start/UUID/native-progress/NVML observation; both authorized cards occupied. No candidate model, resource profile, lease, queue or new launch.','evidence':[ref]};work['updated_at']=now
  assert all(u.digest(x)==b['candidate_digests'][x['id']] for x in work['candidates'] if x['id']!=CID)
  notes={'actions':['本轮20:04:40→46Z（上海11月1日04:04）仅一次原运行/资源检查：WFC原source94/PID2085005/GPU0 TRAIN15/2692→2698，native14val best.4918264150619507/noimp1；LFT原source4457/PID2685912/GPU1 TRAIN11/2226→2233，native10val best.4855799376964569/noimp0。两原TRAIN/log增长，无终态/异常；均为部分验证。','原hostname/source18/UUID/PID/start和NVML实际占用核实，busy[0,1]/idle[]；NEC资源前置检查blocked有当前证据并归候选，不是候选模型/backward/profile执行。已备NEC/MIC继续等待空卡，没有重复草案、旧suite、新源码/租约/准入/队列/训练。','0新候选/模型修订/源码提交/nativearm/准入/新训练/终态。仅NEC附当前物理资源证据，MIC及其他154候选/旧10holds/M206暂停/用户28与正常index/原运行18源和38账保持。PCE一次只读文字复核，无额外文件或remote查询。0–3表为begin20:04冻结事实。'],'decisions':['冠军仍M95 .5020，目标.5100/gap.0080；WFC.4918/LFT.4856均部分指标且未超冠军，保持原数据/seed/schedule/patience，不调参/重启或提前切换。','无空卡且两储备已准备，本轮仅正常轮询、相同资源等待与留档，无新科学结论或用户待办，DONT_NOTIFY。六段报告/七段memory后按真实finish/release验收，资源释放或实质事件到来才继续已授权真实检查并通过后同轮派发。']}
  u.protect(b);u.atomic(ROOT/'pipeline/research_work.json',work)
  temp=memorypath.with_name(memorypath.name+'.2c5dccfb.tmp');assert not temp.exists();guard();temp.write_text(memory,encoding='utf8');guard();temp.replace(memorypath)
  u.save(HERE/'final_report_notes.json',notes)
  u.save(HERE/'preclosure_actual_state.json',{'owner':EXPECTED,'recorded_at':now,'work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(memorypath),'notes':u.ref(HERE/'final_report_notes.json'),'evidence':[ref],'candidate_stage_counts':dict(Counter(x['stage'] for x in work['candidates'])),'all154_other_candidates_and_all38_lifecycle_user28_running18_index_preserved':True,'resource_result':'blocked','new_scientific_or_implementation_result':False,'notify':'DONT_NOTIFY','finish':'NOT_YET_RUN'});u.protect(b)
  print(json.dumps({'status':'ROUTINE_WAIT_PERSISTED_FINISH_PENDING','state':u.ref(HERE/'preclosure_actual_state.json'),'notify':'DONT_NOTIFY','memory_lines':len(memory.splitlines())}))
 finally:lock.close()
if __name__=='__main__':main()
