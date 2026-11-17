"""Summarize the fixed diagnostic cohort, without population efficacy claims."""
from ops import *

guard()
labels=['error_readout_0_attempt2','error_readout_1','error_readout_2','error_readout_3']
result={'observed_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
 'scientific_status':'inconclusive','training_started':False,'optimizer_steps':0,
 'scope':'8 fixed TRAIN scenes,32 correlated expressions;first-order surrogate is not trained effect',
 'scenes':[],'batches':[],'evidence':[],'successful_native_forwards':0,'successful_native_backwards':0,
 'source_interface_forwards':0,'suffix_replays':0,'criterion_replays':0,'suffix_gradient_probes':0,
 'failed_partial_native_attempts':1,'diagnostic_interface_failure':'Initial readout ANDed unpadded masks with padded validity;attempt2 maps exact valid positions,model/thresholds unchanged.'}
for label in labels:
    manifest=tick.load(OUT/label/'native_manifest.json')
    value=tick.load(OUT/label/'native_error_readout_result.json')
    assert value['execution_completed'] and value['controls_passed']
    assert value['optimizer_steps']==value['scheduler_steps']==0
    conditions={c['condition']:c for c in value['coarse_conditions']}
    assert max(value['controls'].values())<=1e-6
    assert all(c['matching_identical'] for c in conditions.values())
    for key,target in [('native_forwards','successful_native_forwards'),('native_backwards','successful_native_backwards'),('source_interface_forwards','source_interface_forwards'),('suffix_replays','suffix_replays'),('criterion_replays','criterion_replays'),('suffix_gradient_probes','suffix_gradient_probes')]:
        result[target]+=value.get(key,0)
    result['evidence'].append(evidence(OUT/label/'native_error_readout_result.json'))
    result['batches'].append({'scene_ids':value['scene_ids'],'native_loss':value['native_loss'],
      'native_loss_deltas':{k:c['native_loss_delta'] for k,c in conditions.items()}})
    for si,scene in enumerate(manifest['cohort']):
        record={'scene_id':scene['scene_id'],'expressions':len(scene['expression_ids']),'groups':{}}
        expression_slice=slice(si*4,(si+1)*4)
        for group in ['original_error','original_correct']:
            rows=conditions['coarse_attention']['error_group_readouts'][expression_slice]
            count=sum(x[group]['points'] for x in rows if x is not None)
            gdot={mode:sum(x[group]['native_gradient_dot_message_delta'] for x in c['error_group_readouts'][expression_slice] if x is not None) for mode,c in conditions.items()}
            maximum=max((x[group]['mask_logit_max_change'] for x in rows if x is not None and x[group]['points']),default=None)
            record['groups'][group]={'expression_point_occurrences':count,'native_gradient_dot_message_delta':gdot,
             'candidate_minus_uniform':gdot['coarse_attention']-gdot['uniform_coarse_mean'],
             'candidate_minus_mismatch':gdot['coarse_attention']-gdot['cyclic_key_value_mismatch'],
             'candidate_mask_logit_max_change':maximum}
        result['scenes'].append(record)
for group in ['original_error','original_correct']:
    rows=[s['groups'][group] for s in result['scenes']]
    result[group]={'expression_point_occurrences':sum(x['expression_point_occurrences'] for x in rows),
     'candidate_better_surrogate_than_uniform_scenes':sum(x['candidate_minus_uniform']<0 for x in rows),
     'candidate_better_surrogate_than_mismatch_scenes':sum(x['candidate_minus_mismatch']<0 for x in rows),
     'candidate_negative_native_surrogate_scenes':sum(x['native_gradient_dot_message_delta']['coarse_attention']<0 for x in rows),
     'candidate_minus_uniform_per_scene':[x['candidate_minus_uniform'] for x in rows],
     'candidate_minus_mismatch_per_scene':[x['candidate_minus_mismatch'] for x in rows]}
save('error_readout_summary.json',result)
advance([OUT/'error_readout_summary.json',OUT/'error_readout.py',OUT/'summarize_readout.py'],
 next_action='Review completed8scene error-localized controls against frozen diagnosis;do not infer trained benefit or mark unresolved gates passed',
 gate_result='Error-localized8scene protocol executed with exact matching;scientific interpretation pending,no training')
print(json.dumps({key:value for key,value in result.items() if key not in ['evidence','scenes']},ensure_ascii=False,indent=2))
