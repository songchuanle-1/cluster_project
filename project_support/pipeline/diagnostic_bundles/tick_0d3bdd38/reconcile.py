"""Reconcile saved prior-tick evidence, without repeating native tests."""
from datetime import datetime, timezone
import json
from ops import guard,save,evidence,add,ROOT,OUT,OLD,CID,GOAL
import foreground_tick as tick

guard(300)
save('scope_goal.json',tick.load(ROOT/'pipeline/goal.json'))
save('memory_before.json',{'text':(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8')})
work=tick.load(ROOT/'pipeline/research_work.json')
save('research_work_before.json',work)
prior=tick.load(ROOT/'pipeline/tick_receipts/ceb5e6c142dc446d87145d00bdce392e.json')
assert prior['status']=='INCOMPLETE' and not prior['context_committed']
capture=tick.load(OLD/'fullval/paired_candidate_capture_index.json')
analysis=tick.load(OLD/'fullval/paired_analysis_result.json')
assert capture['passed'] and capture['optimizer_steps']==0
assert tick.digest(OLD/'fullval/candidate_fle_epoch13.json')==capture['conditions']['candidate_fle_epoch13']['sha256']==analysis['candidate_sha256']
assert tick.digest(ROOT/'pipeline/diagnostic_bundles/tick_21500d1a/reference_m95_epoch16.json')==analysis['reference_sha256']
assert tick.digest(OLD/'fullval/paired_analysis.py')==analysis['analysis_sha256']
assert tick.load(OLD/'independent_analysis_audit.json')['passed']
exit_result=tick.load(OLD/'exit_result.json')
assert exit_result['disposition']=='done_earlystop' and exit_result['native_validation_count']==23
assert exit_result['best_native_miou']==analysis['candidate_native_miou']==.48853155970573425
geometry=tick.load(OLD/'native_metric_result.json')
assert geometry['execution_passed'] and len(geometry['scenes'])==8 and not geometry['failures']
assert all(t['output_max_error']==0 and t['fallback_flips']==0 for s in geometry['scenes'] for t in s['transforms'])
assert not tick.load(OLD/'native_diagnostic_result.json')['passed']
assert not tick.load(OLD/'norm_repair/native_diagnostic_result.json')['passed']
precision=tick.load(OLD/'precision_cpu_result.json')
assert sum(r.get('legacy_CPU_norm_pass') is False for r in precision['controls'])==3
now=datetime.now(timezone.utc).isoformat()
cached=['exit_result.json','terminal_reconciliation.json','native_metric_result.json','native_diagnostic_result.json',
        'norm_capture/native_diagnostic_result.json','norm_capture/failed_norm_input.npz','norm_forensics_result.json',
        'precision_cpu_result.json','norm_repair/native_diagnostic_result.json','norm_repair/failed_norm_input.npz',
        'fullval/candidate_fle_epoch13.json','fullval/paired_candidate_capture_index.json','fullval/paired_analysis_result.json','independent_analysis_audit.json']
save('cached_result_reconciliation.json',{'observed_at':now,'cache_times':{'native_exit':exit_result['observed_at'],'geometry':geometry['observed_at'],'fullval':capture['observed_at'],'analysis':analysis['observed_at']},
    'new_native_forwards':0,'new_cuda_calls':0,'prior_receipt':'INCOMPLETE_CONTEXT_NOT_COMMITTED','hash_checks_passed':True,
    'candidate_miou':analysis['candidate_native_miou'],'paired_delta':analysis['groups']['all']['delta'],
    'paired_ci95':analysis['groups']['all']['expression_delta_ci95'],'evidence':[evidence(OLD/name) for name in cached]})
by={c['id']:c for c in work['candidates']}
def resolve(c):
    keys=('blocker','blocker_kind','required_server','retry_after','unblock_condition','last_rechecked_at')
    old={k:c.pop(k) for k in keys if k in c}
    if old:c.setdefault('resolved_resource_holds',[]).append({'resolved_at':now,'reason':'Original frozen diagnostic actually executed in prior tick;not a new idleness claim','previous':old,'evidence':[evidence(OUT/'cached_result_reconciliation.json')]})
c=by['fle-native-run-exit-disposition-audit']
c.update(stage='complete',failure_scope='inconclusive',next_action='Finite exact-run audit complete;preserve native earlystop/best/last evidence,no restart. Interpret frozen terminal evaluation separately.',
         gate_result='Normal native earlystop23;bestepoch13;23VALs,no error markers. Last checkpoint22 is expected break-before-save;not efficacy PASS.')
add(c,[OLD/'exit_result.json',OLD/'terminal_reconciliation.json',OUT/'cached_result_reconciliation.json'])
c=by['fle-fixed-membership-metric-geometry-audit'];resolve(c)
c.update(stage='complete',failure_scope='inconclusive',next_action='Finite native fixed-membership audit complete. Retain artificial lattice failure;no arbitrary epsilon repair or whole-hierarchy/trained-mask robustness claim.',
         gate_result='8TRAINgeometries,24FPS/64kernels/56transform comparisons,zero output differences/fallback flips;synthetic feature probes only.')
c['gates'].update(native_FPS_membership='EXECUTED_8_TRAIN_GEOMETRIES',native_fixed_membership_transform='PASS_FINITE_56_COMPARISONS',trained_mask_effect='UNKNOWN')
add(c,[OLD/'native_metric_result.json',OLD/'native_execution_metric.json',OUT/'cached_result_reconciliation.json'])
c=by['fine-leaf-local-point-exchange']
c.update(stage='complete',failure_scope='implementation',result='trained_realization_no_gain',trained_model_branch_stopped=True,
         gate_result='Terminal best .4885315597 belowbaseline.4894/M95.5020/target.5100;paired availableM95delta-.0139291520,sceneCI excludes0. Not universal mechanism falsification.',
         next_action='Original posttraining plan complete;stop this converged trained realization,no restart or VAL-selected variants. Preserve mainline and independent diagnostic ID;new distinct structural work still needs diagnosis/all gates.',
         unmeasured_gates=['material novelty','full-training allocator peak','original no-cluster resource delta','independent-repeat noise floor'])
add(c,[OLD/'exit_result.json',OLD/'terminal_reconciliation.json',OLD/'fullval/candidate_fle_epoch13.json',OLD/'fullval/paired_analysis_result.json',OUT/'cached_result_reconciliation.json'])
c=by[CID];resolve(c)
c.update(stage='implementation',failure_scope='implementation',next_action='Derive and preregister final bounded diagnostic revision2 on saved vectors;unchanged native/true1e-6 controls and original8scene early checkpoint. No production model or threshold change.',gate_result='Prior original and diagnosticrevision1 failed norm control;native cohort incomplete,causal usefulness unknown.')
c['gates'].update(native_same_prefix_diagnostic='FAILED_STRICT_NORM_CONTROL_INCOMPLETE',diagnostic_revision1='FAILED_NATIVE_AND_3OF4_LEGACY_CPU',trained_efficacy='TERMINAL_M203_NEGATIVE_SEPARATE_FROM_MECHANISM_READOUT')
c['diagnostic_instrumentation_history'][-1].update(result='failed_control_captured',evidence=[evidence(OLD/'norm_capture/native_diagnostic_result.json'),evidence(OLD/'norm_capture/failed_norm_input.npz'),evidence(OLD/'norm_forensics_result.json')])
c['diagnostic_revision_history'][-1].update(result='failed',evidence=[evidence(OLD/'precision_cpu_result.json'),evidence(OLD/'norm_repair/native_diagnostic_result.json')],interpretation='True norm errors improved;legacyCPU3of4 and native scene2 failed. CPUaggregateflag is not allcontrols PASS. Diagnostic arithmetic,not productionrevision.')
add(c,[OLD/name for name in cached if name.startswith(('native_diagnostic','norm_','precision_'))]+[OUT/'cached_result_reconciliation.json'])
work.pop('design_cycle',None)
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'reconciled_ids':4,'cached_tests_not_rerun':True,'M203':'complete_negative_realization','diagnostic_revision1':'failed','new_native_forwards':0}))
