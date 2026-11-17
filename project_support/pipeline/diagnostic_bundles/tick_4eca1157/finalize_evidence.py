"""Final research evidence and reporting inputs,not a finish substitute."""
from datetime import datetime,timezone
import json
import shlex
import shutil
from ops import guard,save,run,ssh,add,evidence,ROOT,OUT,CID,STAGE,TOKEN
import foreground_tick as tick

owner=guard(90)
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/'analyze_repeat_remote.py'),
    'songcl@192.168.1.115:'+STAGE+'/'])
save('repeat_analysis_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr})
assert upload.returncode==0
command=('test "$(hostname)" = dl04-MS-7E06 && source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
    'conda activate project_cluster && CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -B '+shlex.quote(STAGE+'/analyze_repeat_remote.py'))
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],90)
save('repeat_analysis_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
    'songcl@192.168.1.115:'+STAGE+'/repeat_analysis_result.json',str(OUT/'repeat_analysis_result.json')])
save('repeat_analysis_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
assert fetch.returncode==0,response.stderr
repeat=tick.load(OUT/'repeat_analysis_result.json')
assert repeat['passed']
base=tick.load(OUT/'analysis_summary.json')
totals={k:base[k] for k in ('native_forwards','native_backwards','native_interface_backwards','full_model_training_backwards','suffix_replays')}
repeat_paths=[]
for tag in ('m95','fle'):
    for n in (1,2):
        path=OUT/('repeat_'+tag+'_'+str(n))/'native_full_backward_result.json'
        result=tick.load(path)
        assert result['passed'] and result['optimizer_steps']==0
        for key in totals:totals[key]+=result.get(key,0)
        repeat_paths.append(path)
models=tick.load(OUT/'models.json')
for m in models.values():
    for name,digest in m['assets']['source_hashes'].items():
        assert tick.digest(ROOT/'Cluster/framework/model/Quard_model'/m['name']/name)==digest
probe='''
import json,subprocess,fcntl,hashlib
from pathlib import Path
from datetime import datetime,timezone
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True).strip()
assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
 with open('/tmp/cluster_project_gpu0_'+kind+'.lock','rb') as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='released_at_probe'
  except BlockingIOError:locks[kind]='busy_preserved'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
models=json.loads(Path(MODELS_PATH).read_text())
checked={}
for tag,m in models.items():
 a=m['assets']
 for name,digest in a['source_hashes'].items():assert sha(Path(m['root'])/'framework/model/Quard_model'/m['name']/name)==digest
 assert sha(a['checkpoint'])==a['checkpoint_sha256']
 assert sha(a['config_path'])==a['config_sha256']
 checked[tag]={'production_source_files':len(a['source_hashes']),'checkpoint_unchanged':True,'config_unchanged':True}
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':gpu,'contexts':contexts,'locks':locks,'frozen_assets':checked}))
'''.replace('MODELS_PATH',repr(STAGE+'/models.json'))
resources=ssh(probe,timeout=90)
save('final_resources_and_sources.json',resources)
assert not resources['contexts'] and all(v=='released_at_probe' for v in resources['locks'].values())
summary={'observed_at':datetime.now(timezone.utc).isoformat(),'snapshot_at':'2026-10-18T10:12:30.890299+00:00',
    **totals,'synthetic_cpu_backwards':base['synthetic_cpu_backwards'],'module_timing_samples':400,
    'new_training_loops':0,'optimizer_steps':0,'new_VAL':0,'new_models':0,'new_admissions':0,
    'new_diagnostic_ids':1,'production_modified':False,'initial_failures_retained':True,
    'reference_function_revision':1,'diagnostic_adapter_flag_probe':1,
    'repeat_models':{tag:{'prefix_bitwise_equal':row['prefix_bitwise_equal'],'all_rng_equal':all(row['rng_equal'].values()),
        'point_prefix_max_abs_difference':row['arrays']['arg_0']['max_absolute'],
        'loss_abs_difference':row['loss_abs_difference']} for tag,row in repeat['models'].items()},
    'scientific_status':'Finitepaddingcorrectness confirmed;no trainedgain/novelty. Originalnativeprefix notbitwiserepeatable despite sameRNG;causeunlocalized,not seedvariance.',
    'execution_status':'Evidence/report prepared,canonicalfinish pending'}
save('final_progress.json',summary)
work=tick.load(ROOT/'pipeline/research_work.json')
c=next(c for c in work['candidates'] if c['id']==CID)
c.update(stage='complete',failure_scope='inconclusive',
    gate_result='Finiteuniformpadding source/nativecontract+4fullnativebackwards PASS;initialsuffixfailures preserved,flagcontrast identified. Nooptimizer/trainingefficacy/productionpatch/admission.',
    next_action='Keep correctnessrepair separate from newcoreattention. No automatic singleopPhase1admission,stoppedFLErestart or uniformrollout;futurestructuralwork retains allgates.')
add(c,[OUT/'analysis_summary.json',OUT/'final_resources_and_sources.json',OUT/'final_progress.json'])
r=next(c for c in work['candidates'] if c['id']=='native-train-prefix-repeatability-audit')
r.update(stage='validation',failure_scope='inconclusive',
    gate_result='Twooriginalfreshrepeats/model withidenticalbatch+4RNGstates stillnonbitwiseprefix;rawarrays measured. Onepair/model not seedvariance/CI;do not loosen1e-6gates.',
    next_action='Localize first divergent native tensor across backbone/encoder with frozenoriginalmodel,input,RNG and exactsavedprefix controls. No seedscan,retryuntilmatching,tolerancechange or falseefficacy;freshlease/liveGPU3locks first.')
add(r,repeat_paths+[OUT/'repeat_analysis_result.json',OUT/'repeat_analysis_execution.json',OUT/'final_progress.json'])
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
if remaining<=180:
    work['design_cycle']={'stop_reason':'tick_deadline_near','attempted_ids':[CID,r['id']],
        'evidence':[evidence(OUT/'final_progress.json')],'resume_condition':r['next_action'],'observed_remaining_seconds':remaining}
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
shutil.copyfile(ROOT/'pipeline/codex_memory.md',OUT/'previous_memory.md')
decision=run(['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
    'cluster_project','other','统一padding参考是否技术可行，训练前缀能否严格重复？',
    '双模型正确性、接口反向及真实train模式反向通过但未生产修复或训练入队；保留初始失败，单独量化原模型前缀漂移，不放宽门槛。',
    '冻结参数标志触发重建偏差，恢复原标志后误差0；重复原模型输入与RNG一致仍有数值差异，瞬时loss不能当机制收益。',
    'pipeline/diagnostic_bundles/tick_4eca1157/final_progress.json'])
save('decision_log_execution.json',{'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr})
assert decision.returncode==0
notes={'actions':[
    '快照2026-10-18 18:12:30上海/design，0训练0排队；后续观测时间单列，不重复预检。',
    '同一padding稳定ID：双现成checkpoint源AST/权重CPU契约通过，无padding输出和梯度精确复现，全masked/零消息/有限差分通过；CPU反向10次，不冒充原生准入。',
    '保留M95/FLE初始末层重建失败；一次冻结标志/顺序对照证明全冻结requires_grad会触发偏差，恢复原标志后所有原重建及不变性/梯度控制误差0，算法和1e-6容差未变。',
    '两模型原始/参考四项真实train模式前向、loss.backward及原0.1梯度裁剪通过，优化器/调度器更新0；参考使已测batch的masked点特征梯度归0。并非训练完成或mIoU提升。',
    '模块bs1/20warmup/100repeat：M95/FLE参考分别增加约0.0530/0.0580ms，模块峰值各增加1536字节；固定batch完整反向峰值约3.5924/3.8183GiB，不含优化器状态，不是整段训练峰值。',
    '新稳定原生训练前缀重复性诊断：两模型各2个原始条件独立进程，输入与四类RNG一致但前缀不逐位一致；保存原数组并量化差异，具体最早分歧与跨seed训练方差仍未知，不能据瞬时loss推收益。',
    '本轮实际原生前向'+str(totals['native_forwards'])+'，原生反向'+str(totals['native_backwards'])+'（完整train模式'+str(totals['full_model_training_backwards'])+'，接口'+str(totals['native_interface_backwards'])+'），后缀回放'+str(totals['suffix_replays'])+'；400个模块计时样本。新模型/训练/VAL/入队0，历史缓存不重复计数。',
    '用量收据仅覆盖本轮begin到收据可见日志的部分窗口；当前数值未知。缓存是输入子集、推理是输出子集，不重复相加、不当账单。',
    '最新GPU0无计算上下文、三类生命周期锁释放；两模型生产源码、checkpoint/config哈希保持不变；server4GPU1及其他项目/调度/外部进程未动。执行状态待canonical finish验证。'],
    'decisions':['padding有限正确性审计完成，不把单均值修复包装成分层注意力核心创新，不自动重启停止的FLE或训练。',
        '原层级特征路径审计已有相同尺度互补性问题，未改名重复创建；新的前缀诊断由本轮实际指纹差异触发，续做同一新ID，不为容量造变体。',
        '保持科学收益未知与执行校验分离；只有finish成功并核实收据及锁释放才称本轮完成，否则保留证据abort。']}
save('report_notes.json',notes)
print(json.dumps({'summary':summary,'resources':resources,'decision':decision.stdout,'remaining_seconds':remaining},ensure_ascii=False))
