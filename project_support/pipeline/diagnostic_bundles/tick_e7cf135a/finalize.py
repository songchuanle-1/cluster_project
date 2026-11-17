"""Archive two tested diagnostic claims and an evidence-bounded stop."""
from collections import defaultdict
from datetime import datetime,timedelta,timezone
import copy
import json
from pathlib import Path
import statistics
import subprocess
import register

c=register.c
ROOT,OUT=register.ROOT,register.OUT
SECOND='hierarchy-scale-output-constant-shift-explanation'


def main():
    c.guard(300)
    raw=c.tick.load(OUT/'constant_runtime/native_constant_result.json')
    first=c.tick.load(OUT/'native_scale_result.json')
    rows=[row for batch in raw['batches'] for row in batch['readouts']]
    earlier=[row for batch in first['batches'] for row in batch['readouts']]
    assert raw['execution_completed'] and len(rows)==32
    assert all(max(batch['controls'].values())==0 for batch in raw['batches'])
    assert [(r['scene_id'],r['object_id'],r['ann_id']) for r in rows]==[(r['scene_id'],r['object_id'],r['ann_id']) for r in earlier]
    native_repeat=max(abs(a['native_mae']-b['native_mae']) for a,b in zip(rows,earlier))
    assert native_repeat<=1e-6
    by_scene=defaultdict(list)
    for row in rows:by_scene[row['scene_id']].append(row)
    def mean(values):
        available=[value for value in values if value is not None]
        return statistics.mean(available) if available else None
    arms={}
    for arm in rows[0]['bias_arms']:
        stats=[row['bias_arms'][arm]['decomposition'] for row in rows]
        arms[arm]={'expressions':len(stats),
            'residual_above_tolerance_count':sum(s['residual_max_abs']>1e-6 for s in stats),
            'residual_max_abs_range':[min(s['residual_max_abs'] for s in stats),max(s['residual_max_abs'] for s in stats)],
            'mean_expression_constant_energy_fraction':mean(s['constant_energy_fraction'] for s in stats),
            'mean_expression_residual_energy_fraction':mean(s['residual_energy_fraction'] for s in stats),
            'scene_means':[]}
        for scene,values in sorted(by_scene.items()):
            arms[arm]['scene_means'].append({'scene_id':scene,
                'constant_logit_shift':mean(row['bias_arms'][arm]['decomposition']['constant_logit_shift'] for row in values),
                'full_foreground_mae_delta':mean(row['arms'][arm]['foreground_mae_delta'] for row in values),
                'constant_foreground_mae_delta':mean(row['bias_arms'][arm]['readouts']['constant']['foreground_mae_delta'] for row in values),
                'residual_foreground_mae_delta':mean(row['bias_arms'][arm]['readouts']['residual']['foreground_mae_delta'] for row in values),
                'constant_other_mae_delta':mean(row['bias_arms'][arm]['readouts']['constant']['other_mae_delta'] for row in values),
                'residual_other_mae_delta':mean(row['bias_arms'][arm]['readouts']['residual']['other_mae_delta'] for row in values)})
    reconstruction=max(row['bias_arms'][arm]['decomposition'][key] for row in rows for arm in arms
        for key in ('delta_reconstruction_max_abs','logits_reconstruction_max_abs'))
    assert reconstruction<=1e-6
    assert all(arm['residual_above_tolerance_count']==32 for arm in arms.values())
    analysis=c.save('constant_analysis.json',{
        'observed_at':c.now(),'candidate_id':SECOND,'hypothesis_id':'scale-intervention-mask-change-is-only-a-spatially-constant-logit-offset',
        'protocol':c.evidence(OUT/'constant_shift_preregistration.json'),
        'native_result':c.evidence(OUT/'constant_runtime/native_constant_result.json'),
        'diagnostic_claim_disposition':'Reject exact bias-only explanation on this fixed cohort; substantial spatial residuals remain in all128expression-arm comparisons. This does not reject the presence of a partial calibration component.',
        'distinct_scenes':8,'expressions':32,'independent_new_population':False,
        'support_expression_pairs':sum(row['supports'] for row in rows),
        'foreground_support_expression_pairs':sum(row['target_supports'] for row in rows),
        'foreground_expression_denominator':sum(row['target_supports']>0 for row in rows),
        'identity_max_abs':0,'reconstruction_max_abs':reconstruction,
        'native_probability_mae_repeat_difference':native_repeat,
        'arms':arms,
        'interpretation':'Scale omission combines a constant score displacement with spatially varying effects of opposing foreground direction. Distribution-preserving correspondence cycles are almost entirely spatial but have scene-dependent task direction. Sensitivity and energy fractions are not trained benefit, complementarity, task-effect explained fractions or justification for centering/scaling.',
        'scientific_admission':False,'new_training':0,'optimizer_steps':0,
        'unknown':['Population effect and representativeness','Validation/test efficacy','New structural mechanism','Full-source numerical admissibility','Training resources and native backward for any future realization'],
        'next_action':'Do not turn these diagnostics into fine-only deletion, bias correction or revived CPA/FLE/PCE. Seek a new independently supported, prediction-blind feature mechanism; unchanged reruns of the two tested explanations add no immediate evidence.'})
    release_code='''
import fcntl,json,subprocess
from datetime import datetime,timezone
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert row.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
 handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
 try:
  fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='available'
 except BlockingIOError:locks[kind]='busy'
 finally:handle.close()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':row,'contexts':contexts,'locks':locks}))
'''
    released=c.save('diagnostic_release.json',c.remote(release_code))
    observed=c.tick.load(released)
    assert observed['returncode']==0 and not observed['data']['contexts']
    assert set(observed['data']['locks'].values())=={'available'}
    decision=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',
        'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
        'cluster_project','other','8场景32表达的独立层级特征诊断完成',
        '粗尺度特异污染和纯常数偏移两个预注册解释均未成立；保留空间与校准并存读数，不派生删层/分数校正训练。',
        'identity误差0，重构4.768e-7；粗层omit仅5/8改善FG且缺特异性；4arm全部32表达保留明显空间残差。',
        str(analysis)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    decision_path=c.save('decision_helper.json',{'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr})
    assert decision.returncode==0
    work=c.tick.load(ROOT/'pipeline/research_work.json')
    candidate=next(item for item in work['candidates'] if item['id']==SECOND)
    candidate['evidence'].extend([c.evidence(analysis),c.evidence(released),c.evidence(decision_path),c.evidence(__file__)])
    candidate.update(stage='rejected',failure_scope='hypothesis',
        diagnostic_outcome='Exact constant-only causal explanation falsified on all128fixed expression-arm comparisons; partial constant component remains.',
        next_action='Preserve exact-negative explanation and all partial constant/spatial results. No bias-correction or centering model is authorized by this diagnostic; seek a separately evidenced structural feature hypothesis.',scientific_admission=False)
    retry=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    work['design_cycle']={
        'updated_at':c.now(),'stop_reason':'no_information_gain',
        'attempted_ids':[c.CID,SECOND],
        'no_gain_reason':'Two distinct preregistered causal explanations were actually tested: coarse-specific target contamination (feature-source composition) failed its original two-scene necessary condition and specificity controls; a purely constant output offset failed reconstructed spatial-residual controls in all128expression-arm cases. They are explanatory diagnostics on the SAME8scene cohort, not independent datasets or two trained architectures. No further unchanged probe yields a supported structural candidate; keep empty capacity instead of numerical tuning, renamed old work or unsupported model construction.',
        'resume_condition':'A new prediction-blind point-feature deficit with a distinct matched causal intervention, or materially new admissible evidence/explicit changed scope. Existing PCE/old numerical failures remain, and no timer/free GPU substitutes for scientific admission.',
        'retry_after':retry,
        'evidence':[c.evidence(OUT/'scale_analysis.json'),c.evidence(analysis)],
        'attempt_results':[
            {'candidate_id':c.CID,'hypothesis_id':'mixed-coarse-context-degrades-fixed-query-target-separability',
                'test':'Original source/readback/head identity plus fine/middle/coarse omission and point-marginal-preserving middle/coarse correspondence interventions on8frozenTRAINscenes/32expressions.',
                'result':'All identities/inverse multiset errors0. Coarse impurity-FG omission deltas on original scenes have opposite signs(-.00295528,+.000114533); middle omission has broader FG improvement, so preregistered coarse-specific consistent-contamination claim rejected for this cohort.',
                'evidence':[c.evidence(OUT/'native_scale_result.json'),c.evidence(OUT/'scale_analysis.json')]},
            {'candidate_id':SECOND,'hypothesis_id':'scale-intervention-mask-change-is-only-a-spatially-constant-logit-offset',
                'test':'For four fixed-query interventions separate delta logits into label-free constant mean and zero-mean residual; test exact reconstruction and foreground/other readouts on same8scenes.',
                'result':'Identity0,reconstruction4.768e-7; all128expression-arm comparisons retain residual>1e-6, so exact constant-only explanation rejected. Mixed output components do not establish training efficacy or an allowed calibration structure.',
                'evidence':[c.evidence(OUT/'constant_runtime/native_constant_result.json'),c.evidence(analysis)]}]}
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'constant_only_claim':'rejected','identity_max':0,'reconstruction_max':reconstruction,
        'same_cohort_native_mae_repeat_difference':native_repeat,'bounded_stop':'no_information_gain','retry_after':retry}))


if __name__=='__main__':main()
