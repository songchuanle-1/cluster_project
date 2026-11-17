"""Current-owner routine resource check persistence; no model/source/preparation changes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import sys,json,re,math
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
CID='hierarchy-coupled-node-edge-state-composition'
def main():
 if len(sys.argv)!=3 or sys.argv[1]!='--execute-root':print('DEFAULT_NOP');return
 assert re.fullmatch('[0-9a-f]{64}',sys.argv[2]);guard()
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  b=u.read(HERE/'protected_assets_before.json');u.protect(b)
  path=HERE/'existing_runs_and_resource_observation.json';assert sha(path)==sys.argv[2];raw=u.read(path)
  assert raw['owner']==EXPECTED and raw['returncode']==0 and raw['resource_precondition']['idle_gpu_ids']==[] and raw['resource_precondition']['result']=='blocked'
  runs=raw['observation']['observations'];assert [r['identity_before']['pid'] for r in runs]==[2085005,2685912]
  assert all(r['strict_native_train_growth'] or r['strict_native_validation_growth'] for r in runs)
  assert all(isinstance(r['precise_native_validation']['values'],list) and r['precise_native_validation']['values'] and all(math.isfinite(x) for x in r['precise_native_validation']['values']) and r['precise_native_validation']['best']<.502 for r in runs),'Material metric event is outside quiet routine persistence'
  observed=datetime.fromisoformat(raw['observation']['observed_at']);now=datetime.now(timezone.utc).isoformat()
  summaries=[]
  for r in runs:
   x,y=r['samples'];m=r['precise_native_validation'];summaries.append(f"{r['experiment_id']} 原PID{r['identity_before']['pid']}/start{r['identity_before']['start_ticks']}/source{r['original_source_commit']}/GPU{r['physical_gpu']}；{x['observed_at']}→{y['observed_at']} TRAIN{x['max_native_step']}→{y['max_native_step']}，log+{y['log_size']-x['log_size']}B；{len(m['values'])}次已完native val best {m['best']!r}/noimp{m['no_improve']}，最近{m['values'][-1]!r}，均为部分验证。")
  mp=ROOT/'pipeline/codex_memory.md';assert sha(mp)==b['memory_sha256'];memory=mp.read_text('utf8')
  oldtoken=re.search(r'^- 当前owner\s*([0-9a-f]{32})',memory,re.M).group(1);previous=u.read(ROOT/'pipeline/tick_receipts'/(oldtoken+'.json'));assert previous['status']=='FINALIZED' and previous['lease_release']=='released'
  def change(pattern,text):
   nonlocal memory
   memory,n=re.subn(pattern,lambda m:text,memory,count=1,flags=re.M);assert n==1,pattern
  change(r'^- 当前owner.*$',f"- 当前owner{EXPECTED['token']}，generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}；真实root thread{EXPECTED['thread_id']}与foreground target一致，不延租约；收尾以真实receipt为准。")
  change(r'^- 上轮.*实际FINALIZED.*$',f"- 上轮{oldtoken[:8]}实际FINALIZED/PASS/context_committed/released于{previous['lease_released_at']}；只说明轮询审计完成，不代表科学收益。")
  change(r'^- M226-WFC：.*$','- M226-WFC：原无序楔机制、原数据/seed/schedule/patience不变。'+summaries[0])
  change(r'^- M227-LFT：.*$','- M227-LFT：原P/U三角分析→3packedFFN→逆合成、原协议不变。'+summaries[1])
  change(r'^- 正式运行仍WFC.*$',f"- 正式运行仍WFC GPU0与LFT GPU1；本轮{sha(path)[:8]}一次原源/PID/start/UUID/native进度与NVML检查，busy[0,1]/idle[]，原TRAIN/log增长。NEC/MIC等待空槽，没有新CUDA模型/训练。")
  change(r'^- WFC \..*LFT \..*$',f"- WFC {runs[0]['precise_native_validation']['best']:.4f}/LFT {runs[1]['precise_native_validation']['best']:.4f}仍是部分验证，低于冠军.5020；不调参/改seed/重启/额外早停。NEC/MIC效力/novelty/预算未知，原whole新core聚合有限非零梯度与真实更新门保持，个别map/row/column/bias零合法。")
  memory=memory.split('## Last Tick',1)[0]+f'''## Last Tick
- begin{EXPECTED['generated_at']}已查进展并尝试现有ready派发，无终态/故障/合格待跑；creation/reserve_budget0、两个储备已准备，不新建候选/复制草案/重跑旧suite。
- 唯一新实测{sha(path)[:8]}于{observed.isoformat()}：两原TRAIN/log增长、精确partial native指标与物理双卡忙核真；resource_check blocked证据归NEC，不是模型/backward/profile失败。PCE一次无文件写入的只读文字交叉核对，未查询remote/复测或制造新peer包。
- 0源码提交/修订/nativearm/准入/新训练/终态；MIC和其他154候选、旧10holds/M206暂停、38账/用户28/index/原运行18源保持。旧holds时钟到期不带来新授权或解除限制。
- 仅健康轮询与相同资源等待，无新科学结论/用户动作，DONT_NOTIFY。六段report/七段memory先落盘，finish/release据实际receipt验收，释放后只读；空槽或其他实质事件出现再继续已授权检查派发。
'''
  assert memory.count('\n## ')==7 and len(memory.splitlines())<120
  w=u.read(ROOT/'pipeline/research_work.json');assert sha(ROOT/'pipeline/research_work.json')==b['research_work_sha256'];c=next(c for c in w['candidates'] if c['id']==CID);assert c['stage']=='validation' and c['native_status']==c['resource_status']=='NOT_RUN';ref=u.ref(path)
  if ref not in c['evidence']:c['evidence'].append(ref)
  c['last_resource_check_at']=observed.isoformat();c['retry_after']=(observed+timedelta(hours=1)).isoformat();c['native_execution_blocker']={'kind':'occupied_authorized_gpus','server':'server-4','observed_at':observed.isoformat(),'busy_gpu_ids':[0,1],'original_tasks':['M226-WFC','M227-LFT'],'evidence':ref,'scope':'Physical precondition only, not candidate model/backward/resource-profile failure.'}
  prior=w.get('tick_attempt')
  if prior and prior.get('tick_started_at')!=EXPECTED['generated_at']:w.setdefault('tick_attempt_history',[]).append(prior)
  w['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+str(HERE/'observe_existing_runs.py')+' --execute-root','observation':'Actual original source/PID/start/UUID/native progression and NVML: both authorized physical cards occupied; no candidate model, profile, active binding, admission, queue or launch entered.','evidence':[ref]};w['updated_at']=now
  assert all(u.digest(x)==b['candidate_digests'][x['id']] for x in w['candidates'] if x['id']!=CID)
  notes={'actions':['本轮唯一原运行/物理资源实测采集于'+observed.isoformat()+'（UTC）；0–3表仍是begin冻结事实。',*summaries,'原hostname/source18/UUID/PID/start与NVML成员保持，busy[0,1]/idle[]；NEC物理资源前置检查blocked当前证据归候选，不是候选模型/backward/profile执行。NEC/MIC已备草案等待空槽，没有重复旧suite/源码/草案/lease/receipt/queue/训练。','0新候选/修订/源码提交/nativearm/准入/新训练/终态；MIC和其他154候选、旧10holds/M206暂停、用户28/index/运行18源和38账保持。PCE只读文字核对无写入或第二次remote查询。'],'decisions':['冠军M95仍.5020，目标.5100/gap.0080；两原部分指标低于冠军，继续原数据/seed/schedule/patience，不改参数或提前重启。','仅常规健康进度和相同资源等待，无新科学结论或用户待办，DONT_NOTIFY；六段报告/七段memory后依据真实finish/release验收。空槽或实质事件到来才继续已授权原生检查，并真实通过后同轮派发。']}
  u.protect(b);u.atomic(ROOT/'pipeline/research_work.json',w);temp=mp.with_name(mp.name+'.'+EXPECTED['token'][:8]+'.tmp');assert not temp.exists();guard();temp.write_text(memory,encoding='utf8');guard();temp.replace(mp)
  u.save(HERE/'final_report_notes.json',notes);u.save(HERE/'preclosure_actual_state.json',{'owner':EXPECTED,'recorded_at':now,'work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(mp),'notes':u.ref(HERE/'final_report_notes.json'),'evidence':[ref],'candidate_stage_counts':dict(Counter(x['stage'] for x in w['candidates'])),'all154_other_candidates_and_all38_lifecycle_user28_running18_index_preserved':True,'resource_result':'blocked','new_scientific_or_implementation_result':False,'notify':'DONT_NOTIFY','finish':'NOT_YET_RUN'});u.protect(b)
  print(json.dumps({'status':'ROUTINE_WAIT_PERSISTED_FINISH_PENDING','state':u.ref(HERE/'preclosure_actual_state.json'),'notify':'DONT_NOTIFY','memory_lines':len(memory.splitlines())}))
 finally:lock.close()
if __name__=='__main__':main()
