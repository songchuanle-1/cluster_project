"""Archive the predeclared coarse-specific claim and register its distinct rival."""
from collections import defaultdict
import json
import statistics
from pathlib import Path
import register

c=register.c
ROOT,OUT=register.ROOT,register.OUT
SECOND='hierarchy-scale-output-constant-shift-explanation'


def main():
    c.guard(1200)
    raw=c.tick.load(OUT/'native_scale_result.json')
    assert raw['execution_completed'] and raw['summary']['distinct_scenes']==8
    assert all(max(batch['controls'].values())==0 for batch in raw['batches'])
    assert all(record[key]==0 for batch in raw['batches'] for record in batch['correspondence_controls']
        for key in ('middle_multiset_inverse_error','coarse_multiset_inverse_error'))
    rows=[row for batch in raw['batches'] for row in batch['readouts']]
    by_scene=defaultdict(list)
    for row in rows:by_scene[row['scene_id']].append(row)
    def mean(values):
        finite=[value for value in values if value is not None]
        return statistics.mean(finite) if finite else None
    scenes=[]
    for scene,values in sorted(by_scene.items()):
        scenes.append({'scene_id':scene,'expressions':len(values),
            'support_expression_pairs':sum(row['supports'] for row in values),
            'foreground_support_expression_pairs':sum(row['target_supports'] for row in values),
            'missing_foreground_expression_count':sum(row['target_supports']==0 for row in values),
            'foreground_contamination_by_scale':[mean(row['foreground_contamination_by_scale'][i] for row in values) for i in range(3)],
            'arms':{arm:{metric:mean(row['arms'][arm][metric] for row in values) for metric in
                ('all_mae_delta','foreground_mae_delta','other_mae_delta','impurity_weighted_foreground_mae_delta')}
                for arm in values[0]['arms']}})
    primary=[scene['arms']['omit_coarse']['impurity_weighted_foreground_mae_delta'] for scene in scenes[:2]]
    assert primary[0]<0 and primary[1]>0
    summary={arm:{metric:mean(scene['arms'][arm][metric] for scene in scenes) for metric in
        ('all_mae_delta','foreground_mae_delta','other_mae_delta','impurity_weighted_foreground_mae_delta')}
        for arm in rows[0]['arms']}
    analysis=c.save('scale_analysis.json',{'observed_at':c.now(),'candidate_id':c.CID,
        'test':c.evidence(OUT/'native_scale_result.json'),'protocol':c.evidence(OUT/'preregistration.json'),
        'distinct_scenes':8,'expressions':len(rows),'scene_means':scenes,'scene_balanced_means':summary,
        'primary_original_two_scene_impurity_foreground_delta':primary,
        'primary_necessary_condition_met':False,
        'diagnostic_claim_disposition':'Rejected the preregistered coarse-specific consistent-contamination explanation on this fixed cohort; do not generalize this to a family ban or trained harm.',
        'coarse_omission_foreground_improved_scenes':sum(scene['arms']['omit_coarse']['foreground_mae_delta']<0 for scene in scenes),
        'middle_omission_foreground_improved_scenes':sum(scene['arms']['omit_middle']['foreground_mae_delta']<0 for scene in scenes),
        'all_identity_errors':0,'point_message_inverse_multiset_errors':0,
        'interpretation':'Scale interventions alter real inst_feats/masks, but effects have foreground/background tradeoffs and lack coarse specificity. Token rotation is not point-marginal matched when clusters differ in size; distribution-preserving point cycles are separately reported. No delete-layer variant or trained gain follows.',
        'scientific_admission':False,'new_training':0,
        'next_discriminating_test':'Separate actual omission/rotation logit differences into label-free constant projection and zero-mean spatial residual, keeping native query fixed.'})
    work=c.tick.load(ROOT/'pipeline/research_work.json')
    candidate=next(item for item in work['candidates'] if item['id']==c.CID)
    candidate['evidence'].extend([c.evidence(analysis),c.evidence(__file__)])
    candidate.update(stage='rejected',failure_scope='hypothesis',
        next_action='Archive this specific fixed-cohort coarse-specific contamination claim as unsupported by its predeclared necessary control. No architecture was proposed/trained; preserve all mixed scene results and do not promote a fine-only ablation.',
        diagnostic_outcome='Predeclared two-scene necessary condition failed; no coarse-specific source of target-feature deficit established.',scientific_admission=False)
    assert not any(item['id']==SECOND for item in work['candidates'])
    protocol=c.save('constant_shift_preregistration.json',{
        'preregistered_at':c.now(),'candidate_id':SECOND,'token':c.TOKEN,
        'hypothesis_id':'scale-intervention-mask-change-is-only-a-spatially-constant-logit-offset',
        'hypothesis':'The observed foreground/non-target tradeoff from existing M95 scale interventions can be fully explained by a spatially constant selected-query logit shift, rather than a change in spatial discrimination.',
        'motivation_evidence':c.evidence(analysis),'diagnostic_only':True,
        'frozen_cohort':c.evidence(OUT/'cohort.json'),'assets':c.evidence(OUT/'native_manifest.json'),
        'arms':['omit_middle','omit_coarse','cycle_middle_messages','cycle_coarse_messages'],
        'decomposition':'For each expression and original native selected query, delta=z_arm-z_native over valid supports; constant=mean(delta), residual=delta-constant. No labels, fit parameters or alternate threshold. Read z_native+constant, z_native+residual, z_native+constant+residual.',
        'controls':['Original native readback/head/frozen-bank identities<=1e-6',
            'delta reconstruction and full-arm logits reconstruction<=1e-6',
            'Valid-support residual mean, unchanged query/native indi and input hash',
            'Labels read only after interventions/decomposition; no production source or training changes'],
        'falsifier':'Bias-only explanation fails on this fixed cohort if any correctly reconstructed intervention has max_abs_residual>original1e-6. Report residual RMS/energy and all scene directions rather than claiming that a small nonzero spatial residual is a task benefit.',
        'readouts':['Per-expression constant,delta/residual maximum and RMS, constant/residual energy fractions',
            'All/foreground/non-target probability-MAE changes for full/constant-only/residual-only/reconstructed arms',
            'Probability-MAE interaction because sigmoid is nonlinear; never call this scale complementarity or add the effects as if linear'],
        'limits':'This is an explanatory output diagnostic only. A constant cannot change point ranking. This does not authorize bias correction, centering/scaling, parameter tuning or any new model. Same8TRAINscenes/32expressions are not a new population or trained evaluation.',
        'tolerance':1e-6,'new_training':0,'optimizer_steps':0})
    work['candidates'].append({'id':SECOND,'stage':'diagnosis',
        'hypothesis_id':'scale-intervention-mask-change-is-only-a-spatially-constant-logit-offset',
        'hypothesis':c.tick.load(protocol)['hypothesis'],
        'matched_control':'Label-free constant/residual decomposition of four existing fixed-query scale interventions, preserving exact reconstruction and native identity controls.',
        'next_action':'Execute the preregistered constant-vs-spatial-residual explanation on the same frozen8TRAINscene cohort; no calibration model or training.',
        'evidence':[c.evidence(protocol),c.evidence(analysis)],'diagnostic_only':True,'scientific_admission':False})
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'primary_condition_met':False,'original_two_scene_deltas':primary,
        'foreground_scene_counts':{'coarse':sum(s['arms']['omit_coarse']['foreground_mae_delta']<0 for s in scenes),'middle':sum(s['arms']['omit_middle']['foreground_mae_delta']<0 for s in scenes)},
        'new_diagnosis':SECOND},ensure_ascii=False))


if __name__=='__main__':main()
