"""Preserve the completed diagnostic and the unresolved launch decision."""
from ops import *
import pipeline_monitor

owner=guard()
remote=ssh('''import json,subprocess,fcntl
from datetime import datetime,timezone
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert [x.strip() for x in row.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
    handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
    try:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locks[kind]='available'
    except BlockingIOError:
        locks[kind]='busy'
    finally:
        handle.close()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':row,'contexts':contexts,'locks':locks}))
''')
save('final_environment.json',remote)
summary=tick.load(OUT/'error_readout_summary.json')
review={
 'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'user_request':'启动实验',
 'scientific_status':'inconclusive','execution_status':'diagnostic_completed_training_not_launched',
 'evidence':[evidence(OUT/'error_readout_summary.json'),evidence(OUT/'final_environment.json')],
 'diagnosis':{'passed':False,'reason':'Error-point activity is verified,but no stable task-relevant coarse semantic deficit has been established.'},
 'controls':{'passed':False,'reason':'Native reconstruction/matching pass;candidate-vs-mismatch error-point first-order direction is split4/8scenes and candidate-vs-uniform5/8.No pretraining efficacy cutoff is imposed.'},
 'native_backward_resources_independence':'Previously measured passes retained;not repeated this tick.',
 'immutable_revision_status':'Revision1 was recorded inconclusive before begin;not rewritten into passed.No new structural revision.',
 'requested_clarification':'是否明确授权 CPA-R1 在保留科学准入未通过标记的条件下，进行一次固定 seed1999/batch2/epochs50/max_iters70 的探索性训练？这不是机制有效性认定。',
 'not_a_resource_block':True,'new_queue_entries':0,'new_training_launches':0,
 'next_action':'Obtain explicit one-candidate exploratory-training exception before launch;otherwise preregister a genuinely discriminating causal diagnosis under the same stable ID,not another resource/backward/old8scene replay.',
 'termination':'No claimed deadline/exhaustion/resource block.No scientific PASS fabricated;attempt normal close once,then preserve/abort if honest disposition is not accepted.'}
save('launch_request_review.json',review)
advance([OUT/'launch_request_review.json',OUT/'final_environment.json'],
 stage='validation',failure_scope='inconclusive',
 gate_result='8scene error-localized diagnostic complete;diagnosis/semantic controls remain unpassed;user launch request pending explicit exploratory exception,no training',
 next_action=review['next_action'])
decision=run([pipeline_monitor.bash_executable(),'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh','cluster_project','question',
 '用户要求启动CPA-R1，但科学准入仍有未通过项，是否可以直接训练？',
 '不伪造准入或启动；请求仅对此候选的明确探索性训练授权，保留全部未通过证据，固定配置和GPU白名单不变。',
 '8个固定TRAIN场景32表达诊断完成；恒等重建/匹配通过，错误点相对打乱语义方向4/8、均匀对照5/8，仍为证据不足；GPU0空闲不是科学PASS。',
 'pipeline/diagnostic_bundles/tick_4419252f/error_readout_summary.json;pipeline/diagnostic_bundles/tick_4419252f/launch_request_review.json'],timeout=30)
save('decision_execution.json',{'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr})
assert decision.returncode==0,decision.stderr
notes={
 'actions':[
 '本轮快照为北京时间2026-10-19 08:13:08，design；用户中途明确要求启动实验。按当前候选核对后未将普通启动请求擅自改成科学准入豁免。',
 '完成原定8个TRAIN场景/32个相关表达的错误点诊断：375个表达-错误点出现、26165个表达-正确点出现；这些不是独立点样本。4次完整原生forward/backward、24次源接口、28次suffix及criterion重放、16次suffix梯度读数，优化器/调度器步骤均为0。',
 '首个诊断因原生loss去padding与诊断补齐掩码长度不同而中断，失败记录保留；仅将有效点散回原补齐坐标后attempt2及其余3对均完成。模型、1e-6阈值、场景、匹配与参数标志未改变。',
 '原生重建/恒等/监督匹配检查通过。错误点的一阶代理相对均匀对照在5/8场景更低、相对打乱语义在4/8更低；不能据此声称训练收益、稳定语义优势或机制被证伪。',
 'server4 physicalGPU0的实时身份、占用及三个互斥锁在执行前由原生运行时核验，结束时再次核验，详情见final_environment.json；server3当前占用未知。没有复测已通过的资源/独立完整backward，没有正式训练/部署/入队。',
 '收据用量窗口为begin至收据写入，排除前置阅读、延迟记录及最终回复；当前可见统计未知，以实际收据为准。缓存输入/推理输出是子集，不重复相加，不作为账单。实际产出仅为上述诊断及启动决策证据。',
 '本报告生成时尚未完成收尾校验；执行状态以随后finish/abort及租约释放核验为准。'],
 'decisions':[
 'CPA-R1保持validation/inconclusive；diagnosis和semantic controls不改成PASS，不改已终结的revision1状态，不创建修订2或替代候选凑数。',
 '用户如明确授权一次探索性训练豁免，下一步仅对CPA-R1落实固定配置、独立提交/安全同步/实时GPU锁及原生步数增长验证；未得到该豁免前不绕过当前项目科学准入。',
 '本轮不伪造资源阻塞、路线穷尽或截止已到。若正常收尾拒绝这个真实未完成状态，则保存证据并abort核实释放，不重复空跑finish或等待截止。']}
save('report_notes.json',notes)
print(json.dumps({'remote':remote,'decision':decision.stdout.strip(),'notes':str(OUT/'report_notes.json'),'review':review['execution_status']},ensure_ascii=False))
