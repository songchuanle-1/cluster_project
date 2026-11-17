"""Explain the measured resource failure without changing the implementation."""
import ast
from datetime import datetime,timezone
import json
from run import BUNDLE,ROOT,TOKEN,GOAL_SHA,guard,tick

guard()
baseline=tick.load(BUNDLE/'profile_counted_baseline_result.json')
candidate=tick.load(BUNDLE/'profile_counted_independent_result.json')
assert baseline['profile']['status']==candidate['profile']['status']=='counted'
assert baseline['scan_ids']==candidate['scan_ids'] and baseline['ann_ids']==candidate['ann_ids']
assert baseline['parameters']==candidate['parameters']==157484090
assert baseline['warmup']==candidate['warmup']==20 and baseline['repeat']==candidate['repeat']==100
base=baseline['profile']['flops']
new=candidate['profile']['flops']
delta=new-base
assert base<=10e9<new
inferred_points=delta/(2*256*328)
assert inferred_points==1620
module_delta={name:value-baseline['profile']['by_module'].get(name,0)
    for name,value in candidate['profile']['by_module'].items()
    if value!=baseline['profile']['by_module'].get(name,0)}
train_base=tick.load(BUNDLE/'revision2_baseline_result.json')
train_new=tick.load(BUNDLE/'independent_native_result.json')
peak=lambda value:max(row.get('torch_peak_allocated_bytes',0) for row in value['observations'])
support=tick.load(BUNDLE/'mechanism_controls_result.json')['support_statistics']
families={}
models=ROOT/'Cluster/framework/model/Quard_model'
for suffix in ('attnpool','qcond','agg','multi'):
    path=models/('model_base1_quard2_c2f_enc_lite_'+suffix)/'hier_postprocess.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    families[suffix]={'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path),
        'source_summary':(ast.get_docstring(tree) or '')[:1100]}
goal=tick.load(ROOT/'pipeline/goal.json')
work=tick.load(ROOT/'pipeline/research_work.json')
primary=next(c for c in work['candidates'] if c['id']=='m95-hierarchical-mask-feature-path-audit')
limit=goal.get('pipeline_policy',{}).get('max_implementation_revisions',2)
assert len(primary['revision_history'])==limit==2
result={'token':TOKEN,'observed_at':datetime.now(timezone.utc).isoformat(),
    'goal_sha256':GOAL_SHA,'standard_same_input':True,'baseline_counted_flops':base,
    'candidate_counted_flops':new,'delta_counted_flops':delta,'limit_flops':10e9,
    'excess_flops':new-10e9,'resource_gate_passed':False,
    'relative_flops_increase':new/base-1,'relative_median_latency_increase':candidate['median_ms']/baseline['median_ms']-1,
    'relative_inference_peak_memory_increase':candidate['peak_allocated_bytes']/baseline['peak_allocated_bytes']-1,
    'training_baseline_peak_bytes':peak(train_base),'training_candidate_peak_bytes':peak(train_new),
    'relative_matched_training_peak_increase':peak(train_new)/peak(train_base)-1,
    'module_delta':module_delta,'inferred_standard_valid_points':inferred_points,
    'source_arithmetic_explanation':'Delta272056320 equals2*N1620*C256*K328 counted dense query-key/value matrix work. Existing projections/FFNs and parameter count unchanged; full-bank arithmetic restored strict numerical controls but computes masked edges.',
    'counterfactual_not_tested':{'half_attention_counted_work':delta/2,
        'required_attention_work_reduction_fraction':(new-10e9)/delta,
        'potential_direction':'Retain canonical QK and softmax axes; investigate genuinely reduced masked value aggregation. This is ONLY arithmetic feasibility, not an implemented/tested/authorized third revision or a PASS.'},
    'effective_revision_limit':limit,'revisions_used':len(primary['revision_history']),
    'no_unilateral_revision3':True,'no_goal_or_gate_change':True,
    'branch_support':{'expressions':len(support),'scenes':4,
        'mean_ancestor_missed_leaf_fraction':sum(row['ancestor_missed_leaf_fraction'] for row in support)/len(support),
        'mean_ancestor_multiply_covered_leaf_fraction':sum(row['ancestor_multiply_covered_leaf_fraction'] for row in support)/len(support),
        'all_disjoint_exact_cover':all(row['disjoint_exact_cover'] for row in support),
        'scope':'Branch value supports only; does not mean all-model context is missing or duplicate information is harmful.'},
    'banned_family_source_review':families,'new_training':0,'hypothesis_falsified':False}
tick.save(BUNDLE/'resource_analysis.json',result)
print(json.dumps({key:value for key,value in result.items() if key not in ('module_delta','banned_family_source_review')},ensure_ascii=False))
for name,item in families.items():print(name+': '+item['source_summary'].split('\n')[0])
