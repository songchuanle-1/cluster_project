"""Archive independent source-path results and the bounded research disposition."""
from collections import defaultdict
from datetime import datetime,timedelta,timezone
import json
import statistics
import subprocess
import register

c=register.c
ROOT,OUT=register.ROOT,register.OUT
LANG='m95-final-ila-expression-source-dependence'


def main():
    c.guard(300)
    result=c.tick.load(OUT/'ila_runtime/native_ila_result.json')
    assert result['execution_completed']
    rows=[row for batch in result['batches'] for row in batch['readouts']]
    assert len(rows)==32
    assert all(max(batch['controls'].values())==0 and batch['captured_inputs_unchanged'] for batch in result['batches'])
    assert all(row['inst_feats_max_abs']>1e-6 and row['selected_mask_logit_max_abs']>1e-6 for row in rows)
    by_scene=defaultdict(list)
    for row in rows:by_scene[row['scene_id']].append(row)
    def mean(values):
        values=[value for value in values if value is not None]
        return statistics.mean(values) if values else None
    scenes=[{'scene_id':scene,'expressions':len(values),
        'supports':sum(row['supports'] for row in values),
        'changed_receivers':sum(row['changed_receivers_above_tolerance'] for row in values),
        'all_mae_delta':mean(row['all_mae_delta'] for row in values),
        'foreground_mae_delta':mean(row['foreground_mae_delta'] for row in values),
        'other_mae_delta':mean(row['other_mae_delta'] for row in values)} for scene,values in sorted(by_scene.items())]
    analysis=c.save('ila_analysis.json',{
        'observed_at':c.now(),'candidate_id':LANG,
        'hypothesis_id':'final-native-language-to-point-update-is-expression-invariant',
        'protocol':c.evidence(OUT/'ila_source_preregistration.json'),
        'native_result':c.evidence(OUT/'ila_runtime/native_ila_result.json'),
        'diagnostic_claim_disposition':'Reject the final-ILA expression-invariance/missing-direct-path explanation on the fixed cohort: controlled language-side activation exchange changes actual inst_feats and fixed-query masks for all32expressions. This is computational dependence, not useful semantic information or training gain.',
        'identity_and_inverse_controls_max_abs':0,'distinct_scenes':8,'expressions':32,
        'same_target_donor_pairs':sum(row['same_target_annotation'] for row in rows),
        'different_target_donor_pairs':sum(not row['same_target_annotation'] for row in rows),
        'valid_support_expression_pairs':sum(row['supports'] for row in rows),
        'changed_valid_receiver_expression_pairs':sum(row['changed_receivers_above_tolerance'] for row in rows),
        'inst_feats_max_abs_range':[min(row['inst_feats_max_abs'] for row in rows),max(row['inst_feats_max_abs'] for row in rows)],
        'selected_mask_logit_max_abs_range':[min(row['selected_mask_logit_max_abs'] for row in rows),max(row['selected_mask_logit_max_abs'] for row in rows)],
        'scene_means':scenes,
        'same_different_target_strata':{stratum:{'expressions':sum(row['same_target_annotation']==value for row in rows),
            'all_mae_delta':mean(row['all_mae_delta'] for row in rows if row['same_target_annotation']==value),
            'foreground_mae_delta':mean(row['foreground_mae_delta'] for row in rows if row['same_target_annotation']==value),
            'other_mae_delta':mean(row['other_mae_delta'] for row in rows if row['same_target_annotation']==value)}
            for stratum,value in (('same_target',True),('different_target',False))},
        'limits':['ILA source already contains precedingLLA/LIA multimodal processing; not pure language',
            'Same8TRAINscenes/32expressions as scale diagnostics, not statistical independent repeats',
            'Task directions mixed; no useful-pairing, population harm or efficacy PASS',
            'No encoder input swap, hierarchy message swap, source formula change, model revision or new routing',
            'Direct ILA/head control is not full-source numerical admission'],
        'scientific_admission':False,'new_training':0,'optimizer_steps':0})
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
    released=c.save('final_diagnostic_release.json',c.remote(release_code))
    observed=c.tick.load(released)
    assert observed['returncode']==0 and not observed['data']['contexts'] and set(observed['data']['locks'].values())=={'available'}
    decision=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',
        'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
        'cluster_project','other','实际ILA输入路径与层级尺度来源的两条独立解释筛查已完成',
        '保留三项局部诊断及混合方向；尺度特异污染与ILA缺失路径均未获支持，暂不形成新结构或训练。',
        '不同因果边：hierarchy消息组成对照和实际ILA语言侧source交换。所有身份控制0；同一8场景，不冒充统计独立数据或全局路线穷尽。',str(analysis)],
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    decision_path=c.save('final_decision_helper.json',{'returncode':decision.returncode,'stdout':decision.stdout,'stderr':decision.stderr})
    assert decision.returncode==0
    work=c.tick.load(ROOT/'pipeline/research_work.json')
    candidate=next(item for item in work['candidates'] if item['id']==LANG)
    candidate['evidence'].extend([c.evidence(analysis),c.evidence(released),c.evidence(decision_path),c.evidence(__file__)])
    candidate.update(stage='rejected',failure_scope='hypothesis',scientific_admission=False,
        diagnostic_outcome='Controlled source dependence falsifies this specific missing-path/invariance diagnosis, not the hierarchy family or useful language conditioning.',
        next_action='Preserve the native ILA dependence evidence and all mixed task directions. Do not retry the same source-cycle or claim a new language-routing mechanism; future structural work requires a distinct feature deficit and matched causal evidence.')
    retry=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    work['design_cycle']={
        'updated_at':c.now(),'stop_reason':'no_information_gain','attempted_ids':[c.CID,LANG],
        'no_gain_reason':'The bounded explanatory screen tested two different causal input paths, not merely two IDs: coarse hierarchy-message composition (coarse-specific contamination) and actual final-ILA language-side activation paired with a fixed receiving point query (expression-invariance/missing path). Each specific explanation is contradicted by its preregistered native control. The constant-output decomposition is a follow-up of the first line and is NOT counted as an independent route. All assays share the frozen8scene cohort/checkpoint; causal-path distinction is not statistical independence or global route exhaustion. Further unchanged replay of these tested explanations adds no supported structural candidate; do not manufacture a model from deletion, calibration, prohibited language routing or renamed historical work.',
        'resume_condition':'A genuinely new prediction-blind point-feature deficit with a distinct native matched intervention, new admissible evidence or explicit changed scope. Original PCE/other failures and existing mainline authorization remain; no global research pause or new training permission.',
        'retry_after':retry,
        'evidence':[c.evidence(OUT/'scale_analysis.json'),c.evidence(analysis),c.evidence(OUT/'stop_independence_review.json')],
        'attempt_results':[
            {'candidate_id':c.CID,'hypothesis_id':'mixed-coarse-context-degrades-fixed-query-target-separability',
                'test':'Original hierarchy source capture and matched fixed-weight scale omissions/point-correspondence changes; task readout at a fixed native query on8TRAINscenes.',
                'result':'Identity/inverse controls0; original two-scene coarse impurity-FG deltas have opposite signs and middle omission has broader FG changes. The registered coarse-specific consistent contamination explanation is rejected on the fixed cohort, not the entire hierarchy mechanism.',
                'evidence':[c.evidence(OUT/'native_scale_result.json'),c.evidence(OUT/'scale_analysis.json')]},
            {'candidate_id':LANG,'hypothesis_id':'final-native-language-to-point-update-is-expression-invariant',
                'test':'At the actual final ILA boundary, cycle only language-side source plus padding mask within scene; freeze receiving point query and native decoder readout; original/inverse/source/head controls.',
                'result':'All identity/inverse errors0; source exchange changes actual inst_feats and fixed-query masks in32/32expressions, contradicting missing-path/invariance. Task directions mixed; no useful-semantic or trained-effect claim.',
                'evidence':[c.evidence(OUT/'ila_runtime/native_ila_result.json'),c.evidence(analysis)]}]}
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'ila_missing_path_claim':'rejected','identity_max':0,'changed_receivers':sum(r['changed_receivers_above_tolerance'] for r in rows),
        'causal_paths_counted_for_stop':2,'shared_cohort_not_independent_repeats':True,'retry_after':retry}))


if __name__=='__main__':main()
