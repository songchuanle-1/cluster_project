"""Finite JSON evidence reconciliation and predeclared scene associations."""
from datetime import datetime, timezone
import json
import math
import random
import statistics
from ops import guard, save, add, evidence, ROOT, OUT, OLD, CID
import foreground_tick as tick

guard(180)
first = tick.load(OUT / 'native_qf/native_diagnostic_result.json')
full = tick.load(OUT / 'capture_repeat/native_diagnostic_result.json')
prior = tick.load(OLD / 'terminal_content/native_diagnostic_result.json')
attention = tick.load(OLD / 'attention_audit/native_attention_result.json')
assert not first['passed'] and full['passed'] and prior['passed'] and attention['passed']
assert len(full['scenes']) == len(prior['scenes']) == len(attention['scenes']) == 32

def mean(x): return statistics.fmean(x)

def correlation(x, y):
    a, b = mean(x), mean(y)
    dx, dy = [v - a for v in x], [v - b for v in y]
    scale = math.sqrt(sum(v*v for v in dx) * sum(v*v for v in dy))
    return sum(a*b for a, b in zip(dx, dy)) / scale if scale else None

def ranks(values):
    output = [0.] * len(values)
    ordered = sorted(range(len(values)), key=values.__getitem__)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[ordered[end]] == values[ordered[start]]: end += 1
        for i in ordered[start:end]: output[i] = (start + end - 1) / 2
        start = end
    return output

def percentile(values, q):
    values = sorted(values)
    p = (len(values)-1)*q
    low = int(p)
    high = min(low+1, len(values)-1)
    return values[low] + (p-low)*(values[high]-values[low])

assert abs(correlation([1, 2, 3], [1, 2, 3])-1) <= 1e-12
assert abs(correlation([1, 2, 3], [3, 2, 1])+1) <= 1e-12
assert correlation([1, 1, 1], [1, 2, 3]) is None
scenes = []
loss_differences, piou_differences, query_flips = [], [], 0
excluded, unknown = 0, 0
for current, old, att in zip(full['scenes'], prior['scenes'], attention['scenes']):
    assert current['scene'] == old['scene'] == att['scene']
    assert current['input_sha256'] == old['input_sha256'] == att['input_sha256']
    assert len(current['expressions']) == len(old['expressions']) == len(att['expressions']) == 4
    loss_differences.append(abs(current['native_loss']-old['native_loss']))
    eligible, background = [], []
    for x, y, a in zip(current['expressions'], old['expressions'], att['expressions']):
        assert str(x['ann_id']) == str(y['ann_id']) == a['identity']['ann_id']
        piou_differences.append(abs(x['metrics']['L00']['piou']-y['normal_piou']))
        query_flips += x['normal_query'] != x['intervention_query']
        unknown += not a['labels_known']
        if a['target_weighted_minus_uniform'] is None:
            excluded += 1
            continue
        row = {'alignment': -a['target_weighted_minus_uniform'],
               'piou_benefit': x['metrics']['L00']['piou']-x['metrics']['L01']['piou'],
               'bce_benefit': x['metrics']['L01']['bce']-x['metrics']['L00']['bce']}
        eligible.append(row)
        if a['background_weighted_minus_uniform'] is not None:
            background.append({**row, 'alignment': -a['background_weighted_minus_uniform']})
    assert eligible
    scenes.append({'scene': current['scene'], 'eligible_expressions': len(eligible),
                   **{key: mean(x[key] for x in eligible) for key in eligible[0]},
                   'background_complete_expressions': len(background),
                   'background_alignment': mean(x['alignment'] for x in background) if background else None})
assert sum(s['eligible_expressions'] for s in scenes) == 119 and excluded == 9 and unknown == 0
rng = random.Random(1999)
draws = [[rng.randrange(32) for _ in range(32)] for _ in range(10000)]
links = {}
for predictor in ('alignment', 'background_alignment'):
    complete = [s for s in scenes if s[predictor] is not None]
    for endpoint in ('piou_benefit', 'bce_benefit'):
        x, y = [s[predictor] for s in complete], [s[endpoint] for s in complete]
        for method in ('pearson', 'spearman'):
            def estimate(a, b):
                return correlation(ranks(a), ranks(b)) if method == 'spearman' else correlation(a, b)
            observed = estimate(x, y)
            samples = []
            if len(complete) == 32:
                for indices in draws:
                    v = estimate([x[i] for i in indices], [y[i] for i in indices])
                    if v is not None: samples.append(v)
            links[predictor + '_' + endpoint + '_' + method] = {
                'scenes': len(complete), 'value': observed,
                'ci95': [percentile(samples, .025), percentile(samples, .975)] if samples else None,
                'valid_bootstrap_draws': len(samples), 'scope': 'exploratory association, not causal/novelty/VALgain'}
summary = {'observed_at': datetime.now(timezone.utc).isoformat(), 'passed': True,
    'initial_attempt': {'passed': False, 'native_forwards': first['native_forwards'], 'completed_scenes': len(first['scenes']),
                        'error': first['error'], 'never_overwritten': True},
    'replication': {'passed': True, 'native_forwards': full['native_forwards'], 'scenes': 32, 'expressions': 128,
        'control_max_error': max(v for s in full['scenes'] for v in s['controls'].values()),
        'logit_additivity_max_error': max(s['additive_logit_error'] for s in full['scenes']),
        'query_feature_changed_scenes': sum(s['query_feature_max_change'] > 0 for s in full['scenes']),
        'point_feature_changed_scenes': sum(s['point_feature_max_change'] > 0 for s in full['scenes']),
        'query_index_flips': query_flips, 'task_readouts': full['task_readouts'],
        'paired_scene_contrasts': full['paired_scene_contrasts']},
    'repeat_consistency': {'all32_input_fingerprints_equal': True,
        'normal_piou_max_difference': max(piou_differences), 'native_loss_max_difference': max(loss_differences),
        'strict_norm_controller_reproducible': False, 'training_seed_noise': 'UNKNOWN'},
    'alignment_denominators': {'scenes': 32, 'expressions': 128, 'eligible': 119, 'support_empty': 9, 'unknown_labels': 0},
    'alignment_links': links, 'per_scene_links': scenes, 'statistical_unit_cases': 3,
    'norm_helper_revised': False, 'training_or_VAL_started': False,
    'interpretation': 'Point-only taskreadout dominates this valid32TRAINreplication;initialstrictcontrolfailure remains. No robust efficacy/generalization or newarchitecture is established.'}
save('qf_analysis.json', summary)
work = tick.load(ROOT / 'pipeline/research_work.json')
c = next(c for c in work['candidates'] if c['id'] == CID)
c.update(gate_result='Initial9nativeforwards/8scenesFAILEDstrictnorm;oneexactsource32scene replication controls0,pointonlyPioudelta+.0075331CIcross0;queryonly+.0002626. No efficacy claim or arithmeticrevision3.',
         failure_scope='inconclusive', next_action='Assess finiteQFdiagnostic disposition with retained firstfailure;do not retry-until-success or train. Continue independent padding/context diagnosis.')
add(c, [OUT / 'native_qf/native_diagnostic_result.json', OUT / 'capture_repeat/native_diagnostic_result.json',
        OUT / 'capture_execution.json', OUT / 'alignment_link_prereg.md', OUT / 'qf_analysis.json'])
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps({'passed': True, 'repeat_consistency': summary['repeat_consistency'], 'links': links}))
