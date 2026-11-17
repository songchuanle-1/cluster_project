"""Persist actual current-tick outcomes and honest unfinished attribution work."""
from datetime import datetime,timezone
import json
from ops import guard,save,run,add,evidence,ROOT,OUT,TOKEN
import foreground_tick as tick
guard(180)
a=tick.load(OUT/'final_analysis.json');assert a['passed']
assert tick.load(OUT/'source_and_helper_postcheck.json')['production_source_unchanged']
terminal=tick.load(OUT/'terminal_content/native_diagnostic_result.json');assert terminal['passed']
obs=tick.load(OUT/'attention_audit/native_attention_result.json');assert obs['passed']
work=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']=='fle-native-nonself-target-mixing-audit')
c.update(stage='validation',failure_scope='inconclusive',gate_result='32TRAINscene target-alignment observed(delta-.0105940,CI[-.0160851,-.0065348]);terminal matched content controls all0,Piou delta+.0075331,CI[-.0001237,.0218365]crosses0. Not established trained benefit or novelty.',
    next_action='Next freeze native Q/F four-factor attribution on SAMEterminalbest13/32TRAINcohort/helperrevision2:hook actual out_norm(query) and mask_feats,first reconstruct native L00/L11<=1e-6,then cross-factor masks at fixed original query index;report scene-level task readouts. CPUsource fixture passed5cases but native attribution NOT_RUN. Require fresh owning lease/liveidleGPU0/3locks and enough time;no training,restart,VALselection or arithmeticrevision3.')
c['gates']={'observational_source_and_null_controls':'PASS32SCENES_SOURCEERROR0_COMPLEMENTERROR0',
    'target_alignment':'OBSERVED_VS_MATCHED_UNIFORM_SUPPORT_NOT_CAUSAL_BENEFIT',
    'terminal_native_sameprefix_controls':'PASS32SCENES_96SUFFIX_REPLAYS_ALLERROR0',
    'terminal_content_task_benefit':'INCONCLUSIVE_CI_CROSSES0',
    'QF_source_fixture':'PASS5_FLOAT64_CASES_NOT_NATIVE_TRAINED_ATTRIBUTION',
    'native_QF_attribution':'NOT_RUN','trained_efficacy':'M203_NEGATIVE_REALIZATION_SEPARATE','material_novelty':'UNESTABLISHED'}
c['followup_preregistration']=evidence(OUT/'qf_attribution_prereg.md')
add(c,[OUT/'terminal_content/native_diagnostic_result.json',OUT/'terminal_native_execution.json',OUT/'final_analysis.json',OUT/'qf_attribution_prereg.md',OUT/'source_and_helper_postcheck.json'])
work.pop('design_cycle',None);guard();tick.save(ROOT/'pipeline/research_work.json',work)
paths=['cached_result_reconciliation.json','revision2_disposition.json','norm_revision2/cpu_contracts_result.json','norm_revision2/interval_cpu_result.json',
       'norm_revision2/native_diagnostic_result.json','attention_audit/cpu_prepare_result.json','attention_audit/native_attention_result.json',
       'terminal_content/native_diagnostic_result.json','final_analysis.json','source_and_helper_postcheck.json','server4_final_resources.json','server3_final_resources.json','qf_attribution_prereg.md']
save('progress_summary.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'reconciled_prior_ids':4,'new_diagnostic_candidates':1,'diagnostic_arithmetic_revisions':1,
    'new_native_forwards':72,'suffix_replays':120,'original_CPU_contract_groups':8,'saved_failure_conditions':8,'readout_CPU_cases':4,'QF_CPU_fixture_cases':5,'CPU_feature_gradient_executions':4,
    'native_backwards':0,'optimizer_steps':0,'new_production_models':0,'new_admissions':0,'new_train_launches':0,'new_VAL_evaluations':0,
    'attempted_ids':['fine-leaf-local-point-exchange','fle-self-neighbor-content-separation','fle-fixed-membership-metric-geometry-audit','fle-native-run-exit-disposition-audit','fle-native-nonself-target-mixing-audit'],
    'evidence':[evidence(OUT/name) for name in paths],'execution_status':'PENDING_FINISH','scientific_status':'M203negative;new alignment observed;causal task benefit inconclusive;native QF pending'})
decision=run(['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh','cluster_project','other',
    'What did valid terminal point-content controls establish?',
    'Keep failed M203 stopped;valid controls do not prove benefit.',
    'Reconciled prior evidence;revision2 valid8scenes;terminal targetmix32scenes;matched32scene PiouCIcrosses0;native QF attribution pending. No new train/admission/model/GPUpermission/scheduler change.',
    'pipeline/diagnostic_bundles/tick_0d3bdd38/progress_summary.json;pipeline/diagnostic_bundles/tick_0d3bdd38/final_analysis.json'],30)
save('decision_log_execution.json',{'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr,'method':'Canonical append-only helper;preexisting mixed-encoding bytes not rewritten'})
assert decision.returncode==0,decision.stderr
notes={'actions':[
'本轮事实快照2026-10-18 14:11:22上海时间/design；0运行/0排队/容量2/准入预算2。归属、冻结目标24约束11禁令、授权server4GPU0及server3GPU1、旧调度Disabled均已核实；未改目标/授权/调度，未重复preflight。',
'先校验上轮缓存哈希并补记4个到期稳定ID：M203正常早停23/50,best13=.4885315597；原全量VAL9508/141与配对M95参考差-0.0139291520。几何有限诊断已完成；诊断修订1确实失败。以上为12:20至12:58旧结果补记，不算本轮新前向或新提升；当前FLE具体训练分支停止，不否定所有点特征交互。',
'本轮预注册诊断算术修订2：不改生产模型，双重原1e-6范数门槛保留。原CPU8类契约及两组失败采集8条件均通过；原早期epoch2/8TRAIN场景32表达式原生完成8前向/24suffix，身份/重复/后缀误差0。原始减置换Piou=-0.0079658，探索性CI[-0.0196140,0.0005174]，不确定而非机制失败。',
'新增终态点特征诊断先冻32个SHA排序TRAIN场景/128表达式及唯一best13。观察原生32前向，源重构/标签常量null/补标签控制误差0；主统计119表达式/32场景，9表达式无目标非自邻居支持、未知标签0。相对同支持均匀权重，跨目标非自项质量delta=-0.0105940，场景CI[-0.0160851,-0.0065348]。这是目标相关性，不是mIoU提升或因果收益。',
'同一终态/32TRAIN场景继续匹配内容对照：32前向/96suffix，身份/重复/源/后缀误差均0；native范数误差最高9.5367e-7，真实范数误差最高9.3244e-7。128/128最终mask改变、query索引翻转0；原始减置换Piou=+0.0075331，CI[-0.0001237,0.0218365]跨0，尚未确立收益。固定query索引不等于固定最终query特征。',
'独立CPU复算配对身份、场景均值与区间均一致。源绑定真实prediction_head含out_norm(query)，5个float64CPU夹具验证Q/F四因子logit分解；这不是原生训练权重归因。原生Q/F分解尚未执行，已留同ID具体恢复条件，不以合成PASS代替。',
'实际本轮新原生前向72、suffix120，CPU原契约8组/失败输入8条件/读数合成4例/QF夹具5例及特征梯度执行4；原生反向、optimizer、新模型、新准入、新训练、新VAL均0。9个生产源文件及终态复用的诊断修订2哈希未变。15:00核验server4GPU0为41MiB/0%/无context且3flock已释放；server3GPU1外部PID1453仍18188MiB/100%，未干预；未用server4GPU1。',
'收据窗口仅本begin至收据落盘，排除此前读取、晚到记录和最终回复；数值在收据生成前未知。缓存是输入子集、推理是输出子集，不重复相加、不当账单。完整训练allocator峰值、原始baseline资源增量、独立原生重复噪声、泛化及创新性仍未知。当前最终执行状态待finish/release核实，不预称完成。'],
'decisions':['当前M203具体实现训练未提升，保持正常终态不重启、不调参、不以有空GPU凑模型；本轮诊断controlPASS不等于科学收益PASS。','已解决上轮台账未收尾和诊断数值匹配问题，保留全部旧失败。终态权重有目标相关性但mask收益CI跨0；下一步同终态checkpoint/cohort冻结真实Q/F四因子重放，先重构native masks再分辨直接点特征与query响应；不自动准入新训练。','四个辅助人审/范围冻结项保持原条件，不因定时到期或GPU空闲恢复。决策使用原append-only helper留档，未重写旧索引混合编码字节。']}
save('report_notes.json',notes)
print(json.dumps({'ledger_persisted':True,'new_native_forwards':72,'new_trainings':0,'next':'native QF attribution pending','report_notes_ready':True,'finish':'NOT_YET_CALLED'}))
