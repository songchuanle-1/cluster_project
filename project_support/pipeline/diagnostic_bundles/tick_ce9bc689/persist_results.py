"""Freeze actual test deltas, verify assets/locks, and prepare honest closure."""
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
from ops import guard,save,ssh,run,advance,evidence,tick,ROOT,OUT,OLD,TOKEN,CID,STAGE

owner=guard(60)
labels=['trace_m95_1','trace_m95_2','trace_fle_1','trace_fle_2',
    'sparse_m95_1','sparse_m95_2','sparse_fle_1','sparse_fle_2',
    'aligned_fle_1','aligned_fle_2','bn_fle','backend_m95_1','backend_m95_2']
files=[]
results=[]
for label in labels:
    filename='native_sparse_result.json' if label.startswith('sparse') else 'native_backend_result.json' if label.startswith('backend') else 'native_trace_result.json'
    path=OUT/label/filename
    value=tick.load(path)
    assert value['passed'],label
    results.append(value)
    files.append(path)
counts={k:sum(r.get(k,0) for r in results) for k in ('native_forwards','native_backwards','operator_forwards','operator_vjps','zero_vjps','optimizer_steps','scheduler_steps')}
assert counts=={'native_forwards':11,'native_backwards':11,'operator_forwards':15,'operator_vjps':15,'zero_vjps':7,'optimizer_steps':0,'scheduler_steps':0}
counts.update(new_training=0,new_VAL=0,new_models=0,new_admissions=0,total_backward_invocations=33)
save('final_progress.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'counts':counts,
    'results':[evidence(p) for p in files],'cached_counts_included':False,
    'scope':'this tick only;multi-tensor VJP is one invocation,not number of gradient tensors'})
models=tick.load(OLD/'models.json')
assets={name:{'root':m['root'],'name':m['name'],'assets':m['assets']} for name,m in models.items()}
program='''from pathlib import Path
import hashlib,json,subprocess,fcntl,datetime
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
assets='''+repr(assets)+'''
verified={}
for model,m in assets.items():
    root=Path(m['root'])
    a=m['assets']
    for name,expected in a['source_hashes'].items():assert digest(root/'framework/model/Quard_model'/m['name']/name)==expected
    for name,path in [('config',a['config_path']),('checkpoint',a['checkpoint']),('annotation',a['annotation_path'])]:assert digest(path)==a[name+'_sha256']
    assert digest(root/'framework/dataset/scannetv2.py')==a['dataset_source_sha256']
    verified[model]={'sources':len(a['source_hashes']),'configuration_checkpoint_annotation_dataset_unchanged':True}
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert row.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert not contexts
locks={}
for kind in ('training','diagnostic','exclusive'):
    with open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locks[kind]='released'
raw=[]
root=Path('''+repr(STAGE)+''')
for label in '''+repr(labels)+''':
    names=('control_bundle.npz','operator_arrays.npz') if label.startswith('sparse') else ('backend_arrays.npz',) if label.startswith('backend') else ('trace_arrays.npz',)
    for name in names:
        path=root/label/name
        raw.append({'path':str(path),'sha256':digest(path),'bytes':path.stat().st_size})
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'gpu':row,'contexts':contexts,'locks':locks,'verified_assets':verified,'remote_raw':raw}))
'''
environment=ssh(program,timeout=100)
save('final_environment.json',environment)
backend=[tick.load(OUT/('backend_m95_'+str(i))/'native_backend_result.json') for i in (1,2)]
summary={'observed_at':datetime.now(timezone.utc).isoformat(),'counts':counts,
    'trace':{name:tick.load(OUT/(name+'_trace_comparison.json'))['first_difference'] for name in ('m95','fle')},
    'sparse':tick.load(OUT/'sparse_control_comparison.json'),
    'aligned':tick.load(OUT/'aligned_control_comparison.json'),
    'bn':tick.load(OUT/'bn_fle/bn_probe_result.json'),
    'backend_same_descriptor':backend[0]['calls'][0]['cache_after']['descriptor']==backend[1]['calls'][0]['cache_after']['descriptor'],
    'backend_same_output_hash':backend[0]['calls'][0]['output_sha256']==backend[1]['calls'][0]['output_sha256'],
    'M95_original_crossprocess_kernel_cause':'UNKNOWN','trained_efficacy':'UNKNOWN','core_novelty':'UNESTABLISHED',
    'execution_status':'PENDING canonical finish/abort;not complete by artifact generation'}
save('analysis_summary.json',summary)
goal=tick.load(ROOT/'pipeline/goal.json')
review=ROOT/'pipeline/reviews/motivation_review_20261018_ce9bc689.md'
design=ROOT/'pipeline/designs/exp_design_20261018_ce9bc689.md'
review_text='# Motivation Review - cluster_project\n\n## 1. Goal\n```json\n'+json.dumps(goal,ensure_ascii=False,indent=2)+'\n```\nTarget0.5100,historicalbest0.5020,gap0.0080.\n\n'
review_text+='## 2. Story Status\n| 假设 | 状态 | 证据 | 缺口 |\n|---|---|---|---|\n| 原生前缀逐位重复 | 不成立于有限已测配对 | 本轮原生跟踪与固定输入对照 | M95具体执行机制未知 |\n| 分层点特征更新改善mask | 本轮未验证收益 | 维持原主线和历史结果 | 结构新机制及训练证据 |\n\n'
review_text+='## 3. Experiment Assessment\n| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |\n|---|---|---|---|\n| 缓存M95 | 0.5020 | 既有分层点更新对照 | 非本轮成果 |\n| 缓存M203-FLE | 0.4885315597 | 负面训练实现 | 不重启不外推整条主线 |\n| 本轮原生重复性诊断 | 未训练/未知 | 防止把数值漂移归给新机制 | FLE局部行序原因确立,M95留未知 |\n\n'
review_text+='## 4. Gap Analysis\n核实了早期分叉与FLE局部行序效应；并未量化种子方差、效能或新颖性。\n\n## 5. Design Rationale\n续做唯一到期稳定ID，使用原生参数标志与固定输入/梯度信号，不增占位变体、不放宽阈值。\n\n## 6. Next Batch\n见exp_design_20261018_ce9bc689.md；下一项为绑定实际原生M95首层所选描述/indice表与数值差异。\n'
guard()
with review.open('x',encoding='utf-8') as f:f.write(review_text)
design_text='# Experiment Design - cluster_project diagnostic continuation\n\n## 1. Motivation\n'+goal['description']+'\n本轮补齐因果对照的数值可重复性，不是训练变体设计。\n\n'
design_text+='## 2. Current Best Results\n缓存M95=.5020,M203-FLE=.4885315597；本轮无训练/VAL/收益。\n\n## 3. Analysis & Direction\n见本轮analysis.md和analysis_summary.json；FLE行排列足以引起局部BN数值漂移，M95实际首层内核差异原因未知。\n\n'
design_text+='## 4. Experiment Plan\n| ID | Purpose | Actual result | Next |\n|---|---|---|---|\n| native-train-prefix-repeatability-audit | 原始跟踪/坐标对齐/固定输入VJP/BN行排列/算法观测 | 11次原生反向、22次算子VJP含7次零控制 | M95实际原生描述与indice表绑定 |\n\n'
design_text+='## 5. GPU Allocation Plan\n仅server4物理GPU0，本轮逐进程三锁；server3GPU1保留授权未使用；server4GPU1未授权。最终证据见final_environment.json。\n\n'
design_text+='## 6. Implementation Checklist\n- [x] 冻结原checkpoint/input/seed/nativeflags；保存预注册与实际结果。\n- [x] 原生前后向及有界固定输入控制；保持全部历史失败。\n- [x] 复核生产源码/配置/权重哈希及GPU三锁释放。\n- [ ] 未完成M95实际原生首层描述/indice绑定；同稳定ID续做。\n训练模型、配置新建、commit/push、准入、队列、训练启动均未授权为本轮诊断的自动后续，实际未执行。\n\n'
design_text+='## 7. Risk Assessment\n固定批次不证明总体效益、创新或全训练资源；观测可能影响时序；M95原因保持未知。不得把一次确定性配对当成普遍确定性，也不重试至匹配。\n\nStatus: diagnostic controls IMPLEMENTED;training NOT ADMITTED;scientific validation PARTIAL.\n'
guard()
with design.open('x',encoding='utf-8') as f:f.write(design_text)
guard()
shutil.copyfile(ROOT/'pipeline/codex_memory.md',OUT/'previous_memory.md')
shutil.copyfile(OUT/'memory_template.md',ROOT/'pipeline/codex_memory.md')
assert len((ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8').splitlines())<120
bash=Path('C:/Program Files/Git/bin/bash.exe')
assert bash.is_file()
decision=run([str(bash),'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh','cluster_project','other',
    '原生前缀漂移是否来自新点特征机制，能否据此宣称提升？',
    '保留主线和门槛：FLE局部行序原因已实测，M95原因未知；不新训不重启，同稳定ID续做实际原生描述与indice绑定。',
    '11次原生反向与固定输入坐标对齐/VJP/BN只改排列对照；两个后端观测未解释旧配对差异，不能制造结论。',
    'pipeline/diagnostic_bundles/tick_ce9bc689/analysis_summary.json; final_environment.json; analysis.md'],timeout=30)
save('decision_execution.json',{'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr})
assert decision.returncode==0,decision.stderr
decision_path=Path(decision.stdout.strip().rsplit('-> ',1)[1])
advance([*files,OUT/'bn_fle/bn_probe_result.json',OUT/'final_environment.json',OUT/'final_progress.json',
    OUT/'analysis_summary.json',OUT/'analysis.md',review,design,decision_path],
    stage='validation',failure_scope='inconclusive',
    gate_result='Firstnativeboundary localized;FLErowpermutation sufficientlocalBNcause with exactnativeA/B andnulls;M95perkernelcause unknown,not trainingbenefit/admission.',
    next_action='Bind actual ORIGINAL nativeM95 firststride selecteddescriptor AND indice tables to crossprocess coordinatealigneddifference usingfrozeninput/checkpoint/RNG/nativeflags. No backendforcing,seedscan,tolerancechange or stoppedbranchrestart.')
work=tick.load(ROOT/'pipeline/research_work.json')
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
if remaining<=180:
    work['design_cycle']={'stop_reason':'tick_deadline_near','attempted_ids':[CID],
        'evidence':[evidence(OUT/'analysis_summary.json'),evidence(OUT/'final_progress.json')],
        'resume_condition':'Fresh owning tick + authorized liveidle GPU/triple locks;nativeM95 selecteddescriptor/indice-table binding with frozen exactprefix controls,not gate relaxation.'}
    guard()
    tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'counts':counts,'environment_time':environment['observed_at'],'remaining_seconds':remaining,
    'near_deadline':remaining<=180,'decision':str(decision_path),'science':'partial diagnostic validation,not efficacy','finish':'NOT YET'},ensure_ascii=False))
