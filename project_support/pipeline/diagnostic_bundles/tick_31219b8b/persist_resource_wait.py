"""Record one genuine resource-precondition check; preserve all preparation and original runs."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import sys,json,re
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
CID='hierarchy-coupled-node-edge-state-composition'
def main():
 if len(sys.argv)!=3 or sys.argv[1]!='--execute-root':print('DEFAULT_NOP');return
 peer_hash=sys.argv[2];assert re.fullmatch('[0-9a-f]{64}',peer_hash)
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  b=u.read(HERE/'protected_assets_before.json');u.protect(b)
  rawpath=HERE/'existing_runs_and_resource_observation.json';assert sha(rawpath)=='987f49829e1154e534a4047e8e1903d0b4648e802d13c452ad7389b467ad4a58'
  peerpath=HERE/'readonly_observation_independent_review.json';assert sha(peerpath)==peer_hash
  peer=u.read(peerpath);assert peer['material_concerns']==[]
  raw=u.read(rawpath);assert raw['owner']==EXPECTED and raw['returncode']==0 and raw['resource_precondition']['idle_gpu_ids']==[] and raw['resource_precondition']['result']=='blocked'
  runs=raw['observation']['observations'];assert all(x['strict_native_train_growth'] or x['strict_native_validation_growth'] for x in runs)
  assert [x['identity_before']['pid'] for x in runs]==[2085005,2685912]
  observed=datetime.fromisoformat(raw['observation']['observed_at']);now=datetime.now(timezone.utc).isoformat()
  oldmemory=(ROOT/'pipeline/codex_memory.md').read_text('utf8');assert sha(ROOT/'pipeline/codex_memory.md')==b['memory_sha256']
  lines=oldmemory.splitlines();updated=[];section='';lasttick=False
  for line in lines:
   if line=='## Last Tick':
    updated.extend(['## Last Tick','- begin18:09已查进展/尝试既有ready派发，无终态/故障/合格待跑；本轮0creation/0reserve，两既有储备已备源码和诊断，不重新复制草案、编译旧suite或造新候选。','- 只引用已审冻结reader一次实测：18:11双原TRAIN/log增长、精确native部分指标、源与UUID/原PID/start及NVML占用均核实；busy[0,1]/idle[]。当前resource_check blocked证据归NEC，未执行候选模型/资源profile，不把等待当机制失败。','- 0新候选/0模型修订/0源码提交/0nativearm/0新准入/0新训练/0终态；MIC及旧10holds/M206全记录不动，旧hold仅时间到期，goal/授权/资源输入无变化不重开。报告0–3为begin18:09冻结事实。','- 本轮仅健康轮询、资源等待和必要审计留档，无需用户动作，应DONT_NOTIFY。七段memory/六段report先保存，finish/release以真实receipt为准；释放后不补写。下一轮资源释放或新事件才做已授权原生检查/派发。']);lasttick=True;break
   if line.startswith('## '):section=line[3:]
   if line.startswith('- 当前owner '):line='- 当前owner31219b8b221e4a1caf715f19e34864b3，generated2026-10-31T18:09:23.320258Z/deadline19:09:23.320258Z；真实root thread01a159c5-29ab-7a22-ba7f-e79174757253与foreground target一致，不延租约；收尾以真实receipt为准。'
   elif line.startswith('- 上轮94c2ad26实际'):line='- 上轮e2659f91实际FINALIZED/PASS/context_committed/released于2026-10-31T16:27:42.695465Z；不代表方法有效或研究目标完成。'
   elif line.startswith('- M226-WFC：'):line='- M226-WFC：无序楔共享非线性后一次incidence mean回节点，保原LN/skip/HCG/单inst。原PID2085005/start105948793/source94/GPU0不变；18:11:08→11Z TRAIN[12,3991]→3996，11次已完native val best .4875631034374237/noimp1；最近.4790439009666443，仍是部分验证，不额外早停。'
   elif line.startswith('- M227-LFT：'):line='- M227-LFT：真fine祖先路径P/U三角分析→原3packedFFN→逆合成→三层原写回。原PID2685912/start106767833/source4457/GPU1不变；18:11:11→14Z TRAIN[8,3544]→3550，7次已完native val best .4697253704071045/noimp0，部分结果未超冠军。'
   elif line.startswith('- M228-NEC：'):line=line.replace('上轮source6bc','94c2轮source6bc')
   elif line.startswith('- MIC本轮实际另存'):line=line.replace('MIC本轮实际另存','MIC e265轮已另存')
   elif line.startswith('- 正式运行仍WFC'):line='- 正式运行仍WFC GPU0与LFT GPU1，原PID/source/参数/耐心不变；本轮987f一次现场双TRAIN增长，NVML两UUID/compute原PID占用，busy[0,1]/idle[]。没有空闲卡，NEC/MIC原生检查继续等待，无CUDA模型或新训练。'
   elif line.startswith('- WFC .4774/LFT .4255'):line=line.replace('WFC .4774/LFT .4255','WFC .4876/LFT .4697')
   updated.append(line)
  assert lasttick;memory='\n'.join(updated)+'\n';assert memory.count('\n## ')==7 and len(memory.splitlines())<120
  work=u.read(ROOT/'pipeline/research_work.json');assert sha(ROOT/'pipeline/research_work.json')==b['research_work_sha256']
  assert {c['id']:u.digest(c) for c in work['candidates']}==b['candidate_digests']
  c=next(c for c in work['candidates'] if c['id']==CID);assert c['stage']=='validation' and c['native_status']==c['resource_status']=='NOT_RUN'
  refs=[u.ref(rawpath),u.ref(peerpath)]
  for ref in refs:
   if ref not in c['evidence']:c['evidence'].append(ref)
  c['last_resource_check_at']=observed.isoformat();c['retry_after']=(observed+timedelta(hours=1)).isoformat()
  c['native_execution_blocker']={'kind':'occupied_authorized_gpus','server':'server-4','observed_at':observed.isoformat(),'busy_gpu_ids':[0,1],'original_tasks':['M226-WFC','M227-LFT'],'evidence':u.ref(rawpath),'scope':'Current physical precondition only; not candidate backward/profile failure or new human permission.'}
  prior=work.get('tick_attempt')
  if prior and prior.get('tick_started_at')!=EXPECTED['generated_at']:work.setdefault('tick_attempt_history',[]).append(prior)
  work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+str(HERE/'observe_existing_runs.py')+' --execute-root','observation':'One actual pinned source/PID/start/UUID/original native progress and NVML observation; both authorized cards occupied by original runs. No candidate model/profile/lease/queue/launch entered.','evidence':[u.ref(rawpath)]}
  work['updated_at']=now
  assert all(u.digest(x)==b['candidate_digests'][x['id']] for x in work['candidates'] if x['id']!=CID)
  notes={'actions':['本轮18:11:08→14Z（上海11月1日02:11）只做一次原运行及资源观测：WFC原PID/source94/GPU0 TRAIN12/3991→3996，native11valbest.4875631034374237/noimp1；LFT原PID/source4457/GPU1 TRAIN8/3544→3550，native7valbest.4697253704071045/noimp0。两原TRAIN/log真实增长，均部分验证，非终态或收益证明。','实际hostname/UUID/原PID/start/源18文件与NVML原进程成员保持，两授权卡busy[0,1]/idle[]；NEC当前物理资源前置检查blocked，证据与tick_attempt归该候选，未执行模型/backward/profile，不将资源等待当科学失败。','0新候选/源码保存/模型修订/nativearm/准入/新训练/终态。两储备已准备且无空槽，因此不重编译旧suite或复制同一草案；MIC、旧10holds、M206暂停及其他154候选/队列/running/CSV/原receipt保持。旧holds时钟到期不是新授权，冻结goal/授权/资源输入无变化。'],'decisions':['冠军仍M95 .5020，目标.5100/gap.0080；WFC.4876/LFT.4697仅健康训练的部分验证，保持原seed/data/schedule/patience，不调参/重启/提前切换。','仅常规状态检查和相同资源等待，无新实质结论或用户动作，DONT_NOTIFY；六段报告/七段memory完整留档，真实finish与release后只读核验。下一轮新事件或空闲资源出现时才继续NEC/MIC已授权真实检查并在实际通过后当轮派发。']}
  u.protect(b);u.atomic(ROOT/'pipeline/research_work.json',work)
  target=ROOT/'pipeline/codex_memory.md';temp=target.with_name(target.name+'.31219b8b.tmp');assert not temp.exists();guard();temp.write_text(memory,encoding='utf8');guard();temp.replace(target)
  u.save(HERE/'final_report_notes.json',notes)
  state={'owner':EXPECTED,'recorded_at':now,'work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(target),'notes':u.ref(HERE/'final_report_notes.json'),'evidence':refs,'candidate_stage_counts':dict(Counter(x['stage'] for x in work['candidates'])),'all154_other_candidates_and_all38_lifecycle_user28_running18_index_preserved':True,'resource_result':'blocked','new_scientific_or_implementation_result':False,'notify':'DONT_NOTIFY','finish':'NOT_YET_RUN'}
  u.save(HERE/'preclosure_actual_state.json',state);u.protect(b)
  print(json.dumps({'status':'ROUTINE_RESOURCE_WAIT_PERSISTED_FINISH_PENDING','state':u.ref(HERE/'preclosure_actual_state.json'),'memory_lines':len(memory.splitlines()),'notify':'DONT_NOTIFY'}))
 finally:lock.close()
if __name__=='__main__':main()
