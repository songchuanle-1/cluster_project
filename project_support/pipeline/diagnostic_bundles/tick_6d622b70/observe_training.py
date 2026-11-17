"""Read only the active CPA process, its native log, and frozen runtime assets."""
from ops import *
import closure
import pipeline_monitor as monitor
import time
from datetime import timedelta

guard()
ID='M204-CPA'
experiment=monitor.load_experiment(str(ROOT),ID)
assert experiment['status']=='running' and experiment['pid']==141278
assert experiment['scientific_admission'] is False
authorization=ROOT/experiment['manual_exploratory_authorization']['path']
assert tick.digest(authorization)==experiment['manual_exploratory_authorization']['sha256']
program=r'''import os,json,re,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
pid=PID
cfg=CONFIG
stage=Path('/data/songcl/Project/Cluster_project/pipeline/cpa_explore_72695a5d')
manifest=json.loads((stage/'runtime_manifest.json').read_text())
root=Path(manifest['root'])
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==manifest['code_commit']
unchanged={path:sha(root/path)==digest for path,digest in manifest['runtime_files'].items()}
assert all(unchanged.values()),unchanged
process=Path('/proc')/str(pid)
alive=process.exists()
command=process.joinpath('cmdline').read_bytes().split(b'\0') if alive else []
owned=alive and b'tools/train.py' in command and cfg.encode() in command
stdout_path=Path(STDOUT)
with stdout_path.open('rb') as stream:
 stream.seek(0,2)
 size=stream.tell()
 stream.seek(max(0,size-40000))
 stdout=stream.read().decode('utf-8','replace')
steps=[(int(a),int(b)) for a,b in re.findall(r'Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+',stdout)]
native_base=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')/Path(cfg).stem
native_paths=[]
lock_paths=[]
if alive:
 for item in process.joinpath('fd').iterdir():
  try:target=Path(os.readlink(item))
  except OSError:continue
  if target.name in ['cluster_project_gpu0_'+kind+'.lock' for kind in ('training','diagnostic','exclusive')]:lock_paths.append(str(target))
  if target.suffix=='.log' and target.is_relative_to(native_base):native_paths.append(target)
native_paths=sorted(set(native_paths))
assert len(native_paths)<=1,native_paths
native=None
if native_paths:
 path=native_paths[0]
 metrics=[]
 current_epoch=None
 last_row=None
 with path.open(encoding='utf-8',errors='replace') as stream:
  for line in stream:
   epoch=re.search(r'Epoch\s*\[(\d+)/50\]\s*\[\s*(\d+)/(\d+)\]',line)
   if epoch:
    current_epoch=int(epoch.group(1))
    last_row=line.strip()
   metric=re.search(r'\bmIoU\s*:\s*([0-9.eE+-]+)',line)
   if metric:metrics.append({'epoch':current_epoch,'mIoU':float(metric.group(1)),'source_line':line.strip()})
  read_bytes=stream.tell()
 best=max(metrics,key=lambda item:item['mIoU']) if metrics else None
 native={'path':str(path),'read_bytes':read_bytes,'validation_history':metrics,'best':best,'last_training_row':last_row}
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
assert [value.strip() for value in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
exit_path=stage/'native_exit.json'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'pid_alive':alive,'exact_process_owned':bool(owned),'last_native_steps':steps[-6:],'gpu':gpu,'contexts':contexts,'open_lifetime_lockfiles':sorted(lock_paths),'runtime_files_unchanged':unchanged,'native_log':native,'stdout_log_bytes':size,'stdout_traceback':'Traceback (most recent call last)' in stdout,'stdout_unstable_loss_skip':'Skipping backward due to unstable loss' in stdout,'exit_record':json.loads(exit_path.read_text()) if exit_path.exists() else None}))
'''
program=program.replace('PID',str(experiment['pid'])).replace('CONFIG',repr(experiment['config'])).replace('STDOUT',repr(experiment['log']))
before=ssh(program)
save('native_before.json',before)
time.sleep(3)
after=ssh(program)
save('native_after.json',after)
first=before['last_native_steps'][-1] if before['last_native_steps'] else None
last=after['last_native_steps'][-1] if after['last_native_steps'] else None
progress=bool(first is not None and last is not None and tuple(last)>tuple(first))
native=after['native_log']
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment_id':ID,
 'pid_alive':after['pid_alive'],'exact_process_owned':after['exact_process_owned'],
 'progress_increased_this_tick':progress,'first_native_step':first,'last_native_step':last,
 'current_native_validation_history':native['validation_history'] if native else None,
 'current_native_best':native['best'] if native else None,
 'source_and_config_unchanged':all(after['runtime_files_unchanged'].values()),
 'scientific_admission':False,'scientific_status':'inconclusive;early ongoing training is not a benefit/harm or novelty conclusion',
 'new_launches':0,'restarts':0,'new_candidates':0,'diagnostic_replays':0,
 'research_deferred':'Four existing human scope holds are not due until13:36Shanghai;reserve_budget0,do not create or revive candidates.',
 'material_failure':not after['pid_alive'] or not after['exact_process_owned'] or after['stdout_traceback'] or bool(after['exit_record']),
 'evidence':[evidence(OUT/'native_before.json'),evidence(OUT/'native_after.json')]}
save('training_observation.json',result)
advance([OUT/'training_observation.json',OUT/'native_before.json',OUT/'native_after.json',OUT/'observe_training.py'],
 next_action='Continue monitoring the SAME M204-CPA native run and frozen evaluation plan;no automatic restart,scientific PASS,old-route promotion or duplicate design during recognized deferred waits')
mutex=monitor.acquire_lock(str(ROOT));assert mutex is not None
try:
 current=monitor.load_experiment(str(ROOT),ID)
 assert current['pid']==experiment['pid'] and current['scientific_admission'] is False
 current['latest_training_observation']=evidence(OUT/'training_observation.json')
 current['observed_native_step']=last
 if native and native['best']:
  current['observed_native_best_miou']=native['best']['mIoU']
  current['observed_native_best_epoch']=native['best']['epoch']
  current['observed_validation_count']=len(native['validation_history'])
 monitor.save_experiment(str(ROOT),current)
finally:mutex.close()
best=native['best']['mIoU'] if native and native['best'] else None
notes={'actions':[
 '本轮快照为北京时间2026-10-19 10:11:57，event，唯一结构事件为active_queue_changed；begin监控/目标检查仅执行一次。运行1、排队0、未到期人工冻结4、储备预算0。',
 '对M204-CPA原进程及原日志做两次只读取样：原生步数'+str(first)+'至'+str(last)+'；是否增长='+str(progress)+'。核对固定server4GPU0 UUID、进程命令和运行源码/配置哈希；不新建CUDA测试、不改配置或权重、不重启训练。',
 '从当前训练进程持有的原生日志读取验证记录；本轮观测最佳mIoU='+str(best)+'。仅为早期训练监测，不与历史完整训练混作因果效果或终态，不声称目标达成或机制通过。',
 '保留CPA单次人工探索授权、diagnosis/semantic controls未通过及revision1 inconclusive。四个辅助监督候选仍未到复查时间，不重复索要授权、不复查旧证据、不因空槽创建占位变体。',
 '本轮实际产出为原进程/日志的时间戳证据与早期验证记录；新增训练、重启、候选、结构修订及重复资源诊断均为0。server3当前占用未知，未推断空闲或阻塞。',
 '收据用量仅覆盖begin至收据写入的本地可见窗口，前置读取及最终回复不包含；当前统计未知，以收据为准。缓存输入/推理输出为子集，不重复相加、不作为账单。',
 '六段报告生成时尚未声称收尾完成，以随后finish和租约释放核实为准；远端训练跨tick继续持有GPU锁。'],
 'decisions':[
 '继续同一个M204-CPA固定配置训练，等待后续原生ScanReferVAL与既定场景级评价；早期数值和在训状态没有触发调参、重启或新机制结论。',
 '遵循紧凑快照research.deferred，当前仅监控和处理active_queue_changed，不扩展储备、不消耗deadline重复设计、不改调度或其他项目。',
 '常规健康训练进展不主动通知；仅完成、故障、实质结论变化或确需用户行动时通知。']}
save('report_notes.json',notes)
timestamp=datetime.fromisoformat(after['observed_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
brief='cluster_project｜数据采集于 '+timestamp+'（上海时间）\n\n结论：M204-CPA继续训练，尚无训练收益结论。目标0.5100，历史最佳0.5020，差0.0080。\n\n实验进展\n| 实验 | 当前情况 | 训练进度 | 已观测最佳mIoU |\n|---|---|---|---|\n| M204-CPA 粗层点云注意力 | '+('确认训练中' if progress and after['exact_process_owned'] else '进度待确认')+' | '+str(last)+' | '+str(best)+' |\n排队：0。\n\n本轮成果\n- 两次只读核对原生进度与当前日志；源码/配置未变，没有新候选、诊断或重启。\n- 早期验证仅作监测，科学准入未通过标记保留。\n\n下一步\n- 继续原运行和既定验证；旧辅助范围冻结未到期，无需新的用户动作。\n'
guard();(OUT/'reader_brief.md').write_text(brief,encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key!='evidence'},ensure_ascii=False,indent=2))
