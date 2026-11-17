"""Preregister one independent, prediction-blind hierarchy diagnostic."""
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('hierarchy_diagnostic_ops', ROOT / 'pipeline/diagnostic_bundles/tick_fefdcc2a/control.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
c.TOKEN = 'e7cf135a487f4ec4b53c386489ba38f1'
c.THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
c.CID = 'hierarchy-coarse-context-target-contamination'
c.OUT = OUT
c.STAGE = '/data/songcl/Project/Cluster_project/pipeline/hierarchy_e7cf135a'


def main():
    c.guard(1200)
    work = c.tick.load(ROOT / 'pipeline/research_work.json')
    assert not any(item['id'] == c.CID for item in work['candidates'])
    assert sum(item['stage'] not in ('complete','rejected','closed') for item in work['candidates']) == 7
    protocol = c.save('preregistration.json', {
        'preregistered_at': c.now(), 'candidate_id': c.CID, 'token': c.TOKEN,
        'hypothesis_id': 'mixed-coarse-context-degrades-fixed-query-target-separability',
        'hypothesis': 'M95 coarse context is shared by target and non-target supports inside mixed coarse clusters. Its existing broadcast may specifically degrade target discrimination at contaminated foreground supports, independently of cross-leaf physical contact exchange.',
        'source_motivation': c.evidence(ROOT / 'docs/research_mainline_correction_20261015.md'),
        'diagnostic_only': True, 'new_structural_model': False,
        'mechanism_to_test': 'Existing M95 fine/middle/coarse context contributions to actual inst_feats and fixed-query masks; no PCE code, contact graph or same-leaf donor-exchange implementation.',
        'cohort_selection': 'First8 distinct scene_ids in existing TRAIN dataset.scene_inputs order; use each first language group (up to4expressions as configured). Select/freeze metadata before model outputs. Same M95epoch16, source/config/annotation hashes and seed1999; paired scene batches, no new dataset.',
        'first_test': 'Native source capture plus exact frozen-bank/readback/head identity controls, then omit each one of3scale messages before the unchanged fusion/projection while holding original level weights, query and supervision fixed. Coarse-token cyclic value rotation is the topology/count-matched negative control.',
        'matched_controls': ['Original native forward readback vs exact replica, tolerance1e-6',
            'Fixed-query native head identity and frozen-bank encoder identity, tolerance1e-6',
            'All3unmodified scale readbacks reconstructed; omission changes only the selected message contribution, no softmax renormalization',
            'One-position cyclic coarse token values, unchanged memberships/point order/weights/precision',
            'Fine/middle omission controls test whether any effect is coarse-specific rather than generic context removal'],
        'sampling_unit': 'scene; expressions and superpoints are nested readouts, not independent samples',
        'readouts': ['Expression and scene denominators; valid/target/non-target support counts',
            'Target purity of each hierarchy token, foreground target-weighted contamination by scale',
            'Native selected query frozen from unmodified indi prediction; no target-oracle query selection',
            'Probability MAE change on all valid supports, foreground and non-target separately',
            'Foreground impurity-weighted MAE change; exact valid support count and missing strata',
            'Actual inst_feats/mask logits maximum intervention change'],
        'decision': 'This is a feature-deficit diagnostic, not a deployable variant or trained efficacy test. Coarse-contamination premise is not supported if coarse omission does not reduce impurity-weighted foreground error in both originally fixed scenes or is no more specific than the matched fine/middle/rotated controls. Report all8scenes and mixed directions, do not select a favorable mechanism/threshold on validation.',
        'limits': 'Frozen-bank controls are NOT full-source numerical admission. No production edit, optimizer step, training, new gate, routing, parameter sweep, threshold/precision/FPS change or reopening historical variants. Labels never enter the intervention. A positive tiny-cohort result only motivates a separately reviewed causal mechanism.',
        'tolerance': 1e-6, 'seed': 1999, 'epochs': 50, 'max_iters': 70,
        'new_training': 0, 'optimizer_steps': 0})
    work['candidates'].append({
        'id': c.CID, 'stage': 'diagnosis',
        'hypothesis_id': 'mixed-coarse-context-degrades-fixed-query-target-separability',
        'hypothesis': c.tick.load(protocol)['hypothesis'],
        'matched_control': 'Matched native fixed-query scale omissions and coarse token rotation, with unchanged fusion weights and labels used only for readout.',
        'next_action': 'Freeze first8TRAINscene groups prediction-blind, execute exact native capture/readback identity controls and the preregistered scale interventions in this tick.',
        'evidence': [c.evidence(protocol), c.evidence(__file__)],
        'scientific_admission': False, 'diagnostic_only': True})
    c.tick.save(ROOT / 'pipeline/research_work.json', work)
    print(json.dumps({'created': c.CID, 'stage': 'diagnosis', 'pending': 8, 'training': 0}))


if __name__ == '__main__':
    main()
