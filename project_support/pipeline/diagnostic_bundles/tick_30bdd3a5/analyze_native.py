"""Aggregate the predeclared frozen cohort without efficacy/admission claims."""
from gpu1_ops import *
import importlib.util
guard(180)
families={};artifacts=[]
for label,cid,metricfile,metricfunc in (
 ('expression_fix','m95-expression-specific-point-message','expression_metrics.py','summarize'),
 ('scale_fix','m95-scale-specific-boundary-responsibility','scale_metrics.py','summarize')):
 rows=[];controls=[];unfixed=[];counts=[]
 manifest=tick.load(OUT/label/'native_manifest.json');expected={s['scene_id'] for s in manifest['cohort']}
 for pair in range(4):
  path=OUT/(label+'_pair_'+str(pair)+'_result.json');result=tick.load(path)
  assert result['execution_completed'] and result['controls_passed']
  assert max(result['controls'].values())<=1e-6
  rows.extend(result['records']);controls.append(result['controls']);counts.append(result['native_task_mask_replays'])
  if 'full_source_permutation_max_error' in result:unfixed.append({'pair':pair,'error':result['full_source_permutation_max_error'],'original_1e_minus6_passed':result['full_source_permutation_original_1e_minus6_passed']})
  artifacts.extend([path,OUT/(label+'_pair_'+str(pair)+'_execution.json')])
 spec=importlib.util.spec_from_file_location('_metrics_'+label,OUT/label/metricfile);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 summary=getattr(module,metricfunc)(rows)
 scene_values=summary.get('scene_effects',summary.get('scene_interactions'));assert set(scene_values)==expected
 mean=summary.get('scene_balanced_effect',summary.get('scene_balanced_mean'))
 result={'candidate_id':cid,'fixed_TRAIN_scenes':8,'fixed_expressions':32,'summary':summary,'preregistered_positive_direction_mean':mean,'positive_scenes':sum(value>0 for value in scene_values.values() if value is not None),'negative_scenes':sum(value<0 for value in scene_values.values() if value is not None),'same_query_native_controls_passed_all_4_pairs':True,'controls_max_error':max(value for c in controls for value in c.values()),'native_task_mask_replays':sum(counts),'original_unfixed_full_source_permutation':unfixed,'local_prediction_status':'direction_supported_on_fixed_cohort_only' if mean>0 else 'positive_direction_not_supported_on_fixed_cohort','population_interval':None,'new_training':0,'scientific_admission':False,'limitations':'8fixedTRAINscenes/32expressions,querieswithinexpressionscorrelated;availableM95epoch16notverifiedhistoricalchampion;notpopulationefficacy or a newtrainablemechanism.'}
 if label=='scale_fix':result['control_scope']='Fixed-original-fusion conditional intervention operator. Original full-source re-evaluation permutation remains separately FAILED,not silentlypassed.'
 families[label]=result
save('native_analysis.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'families':families,'new_trainable_variants':0,'new_training':0,'scientific_admission':False,'raw_evidence':[evidence(p) for p in artifacts]})
expression=families['expression_fix'];scale=families['scale_fix']
scene_order=[s['scene_id'] for s in tick.load(OUT/'expression_fix/native_manifest.json')['cohort']]
lines=['# GPU1原生诊断结果','',
 '本轮用户明确授权server4 GPU1后，在同一前台租约内实测新卡空闲/UUID/三独占锁，已串行完成两个预注册诊断。GPU0的M204未重启或迁移，未新增模型训练。','',
 '## 固定训练场景结果','',
 '| 场景 | 表达消息移植：donor−own概率误差 | 尺度责任：细删除−粗删除混合/内部差中差 |',
 '|---|---:|---:|']
for scene in scene_order:lines.append('| '+scene+' | '+format(expression['summary']['scene_effects'][scene],'.9f')+' | '+format(scale['summary']['scene_interactions'][scene],'.9f')+' |')
lines.extend(['',
 '- 表达消息移植场景等权均值：'+format(expression['preregistered_positive_direction_mean'],'.9f')+'；正向场景'+str(expression['positive_scenes'])+'/8，反向'+str(expression['negative_scenes'])+'/8。原生正例query行'+str(expression['summary']['matched_query_rows'])+'，不是同等数量独立样本。',
 '- 尺度责任场景等权均值：'+format(scale['preregistered_positive_direction_mean'],'.9f')+'；正向场景'+str(scale['positive_scenes'])+'/8，反向'+str(scale['negative_scenes'])+'/8。有效表达读数'+str(scale['summary']['expressions_with_readout'])+'/32；空分组不补造、不改阈值。',
 '- 两个诊断均为8个固定TRAIN场景/32表达的条件性任务读数；使用已有M95epoch16，不是训练新模型、验证mIoU提升、新champion或总体显著性证据。各query/表达相关，不编造总体置信区间。','',
 '## 保留失败与测量修正','',
 '- 原尺度pair0的完整源重算置换误差2.86102294921875e-6，未过原1e-6，原始结果完整保留；消息/特征/mask/score/identity重建误差均0。',
 '- 事前登记修正仅把本来需要固定的原融合logits在置换控制中一同置换，并增加固定融合identity；baseline与真正细/粗删除、模型/数据/query/目标/阈值不变。当前通过的是该条件干预算子的匹配控制，不是把完整原生源置换失败改称PASS。四对完整源置换误差另记native_analysis.json。',
 '- 原表达pair0在5项原生重建/撤销控制全0后，因bool标签不能参与减法而未生成读数。事前登记修正仅将原0/1标签等值转到预测dtype用于两处误差算术；原标签、选择、query、权重和原1e-6不变，旧失败不覆盖。',
 '- 修正后两组各4对场景的原生匹配控制均通过，最大误差分别为表达'+str(expression['controls_max_error'])+'、固定融合尺度'+str(scale['controls_max_error'])+'。这属于诊断测量修正，不是模型结构修订/科学准入例外。','',
 '## 解释与决策','',
 '- 表达移植检验原点消息在固定query条件下是否携带有用目标表达信息；局部正向结果不等同当前网络缺陷，也不自动给出可训练的新机制。所有反向结果保留。',
 '- 尺度局部预期正向是否得到支持，必须按上表及完整均值判断；不能为讲“细尺度负责边界”的故事忽略反向场景，或把该诊断当细尺度模型有害的总体证据。',
 '- 两个有界诊断的预注册场景均已实际运行，科学状态仍为固定cohort证据/外推未知；不新增训练变体、不放宽准入，不重复原样场景凑实验量。4个旧辅助方向的scope hold不因GPU1授权解除。',
 '- GPU1新增授权已写入SERVERS、goal追加约束及用户授权记录，原有科学目标/禁令/seed1999/epochs50/max_iters70不变。资源变更在本轮begin后发生，begin快照未重写，未重复preflight；后续真实状态写于本轮动作。',
 '- 原派发脚本扩展测量模式前的字节与哈希已归档，旧源码证据仅迁至同哈希归档路径，原负结果未改；见dispatcher_source_relocation.json。',
 '- 本文保存时finish与GPU1最终释放核对仍待完成；不能据此先称整个tick完成。'])
path=OUT/'native_analysis.md'
with path.open('x',encoding='utf-8') as stream:stream.write('\n'.join(lines)+'\n')
work=tick.load(ROOT/'pipeline/research_work.json')
for label,item in families.items():
 c=next(c for c in work['candidates'] if c['id']==item['candidate_id'])
 assert c['revision_history'][-1]['revision']==1 and c['revision_history'][-1]['result']=='pending'
 revision=c['revision_history'][-1];revision['result']='passed';revision['evidence']=[evidence(OUT/'native_analysis.json')]+[evidence(OUT/(label+'_pair_'+str(i)+'_result.json')) for i in range(4)]
 revision['interpretation']='Diagnosticmeasurementrepairpassedunderitspreregisteredscope;notnewmodeladmission. Scaleoriginalfullsourcepermutationfailurepreserved.'
 prior={k:c.get(k) for k in ('blocker_kind','blocker','retry_after','unblock_condition')}
 c.setdefault('resource_hold_history',[]).append({'resolved_by':evidence(AUTH),'prior_hold':prior})
 for key in ('blocker_kind','blocker','retry_after','unblock_condition'):c.pop(key,None)
 c.update(stage='complete',completed_at=datetime.now(timezone.utc).isoformat(),failure_scope='inconclusive',diagnostic_scope='Bounded8scene32expressionnativeTRAINstudycompleted;populationefficacyandnewcoremechanismnotestablished',diagnostic_controls_passed=True,native_task_readout_complete=True,scientific_admission=False,
  gate_result=item['local_prediction_status']+'; scene_balanced_mean='+str(item['preregistered_positive_direction_mean'])+'; scopeddiagnosticcontrolsPASSED;notnewmodel/scientificadmission. Originalnegative/strictprecisionevidenceretained.',
  next_action='Retaincompletedboundednativecohortdiagnosisincludingcounterexamples. Useonlyasmechanisticinputforfutureevidence-backedpoint-featuredesign,nottuning/routecopy/newtraining. Do notrepeatunchangedcohortorclaimpopulationbenefit;M204continuesoriginaltraining.')
 c['gates']['diagnosis']={'passed':False,'reason':'Fixed-cohort mechanistic readout measured;no proposednewtrainablemechanism/taskdeficit admission is established','diagnostic_result':item['local_prediction_status']}
 c['gates']['controls']={'passed':False,'reason':'Scopeddiagnosticnativecontrols passed;not admissionofnewtrainablemechanism','diagnostic_controls_passed':True,'scope':item.get('control_scope','Originalfixedquery/physicalpoint/targetidentityandundo controls')}
 for artifact in [OUT/'native_analysis.json',path,Path(__file__)]:
  record=evidence(artifact)
  if record not in c['evidence']:c['evidence'].append(record)
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'completed_bounded_diagnostics':2,'families':families,'new_training':0},ensure_ascii=True,indent=2))
