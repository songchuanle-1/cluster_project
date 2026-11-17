"""Lease-bound registration of a fixed reversible sibling-token experiment."""
import importlib.util
import json
from pathlib import Path

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('diagnostic_ops', ROOT/'pipeline/diagnostic_bundles/tick_fefdcc2a/control.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
c.TOKEN = '9981967370ad420c97dcbdf14443b3c5'
c.THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
c.CID = 'hierarchy-reversible-sibling-token-transport'
c.OUT = OUT
c.STAGE = '/data/songcl/Project/Cluster_project/pipeline/sibling_99819673'


def main():
    c.guard(1200)
    work = c.tick.load(ROOT/'pipeline/research_work.json')
    assert not any(item['id']==c.CID for item in work['candidates'])
    assert sum(item['stage'] not in ('complete','rejected','closed') for item in work['candidates'])==7
    protocol = c.save('preregistration.json', {
        'preregistered_at': c.now(), 'candidate_id': c.CID, 'token': c.TOKEN,
        'hypothesis': 'Existing fine readback contains each leaf value and shared pooled ancestor values, but no direct content-dependent value exchange between fine sibling leaves. A fixed reversible transport may add discriminating sibling detail without changing the point-mass-weighted fine pre-fusion mean. Whether this is a useful deficit is UNKNOWN and must be tested, not inferred from conservation.',
        'mechanism': {'input': 'Existing final CTF refined fine tokens after the trained FFN; fine-to-middle parent map cluster_ids_list[1], leaf mass bincount(cluster_ids_list[0]); no new geometry/FPS.',
            'heads': 8, 'head_dim': 32,
            'formula': 'Within each parent and head, pi_i=n_i/sum(n). Q_ij=softmax_j(T_i dot T_j/sqrt(32)). For i!=j, A_ij=min(pi_i*Q_ij,pi_j*Q_ji); P_ij=A_ij/pi_i; P_ii=1-sum_{j!=i}P_ij. Replace fine token T by PT. Other levels and trained readback/fusion/query/suffix unchanged.',
            'parameters_added': 0, 'precision': 'Original FP32; no normalization/temperature/gate/residual/projection sweep',
            'invariant_scope': 'Only each head/parent weighted fine pre-fusion mean; NOT post-fusion/projection/LN or mask/logit mean.',
            'complexity': 'O(sum_parent k_parent^2*C), not point N^2. Actual sibling distribution and saturation measured before any feasibility claim.'},
        'history': {'closest': 'M39-C2C uses dense per-scale Q/K/V/O self-attention + residual/LN; .4865 historical mIoU. Token interaction alone is not new. Fixed local sibling graph + point-mass reversibility + no learned projections/extra residual are whole-mechanism differences needing controls.',
            'other': 'HDS exclusive point supports, FLE within-leaf point attention, PCE physical-contact cross-leaf exchange, CPA point-to-coarse attention remain closed/held; this is not their revision or reopening.',
            'public_novelty': 'UNKNOWN. Metropolis-Hastings/reversible transitions and stochastic attention are established ideas; no novelty claim.'},
        'cohort': 'Reuse prediction-blind first8TRAINscene/first4expression groups frozen in tick_e7cf135a/cohort.json; same seed1999/source/config/checkpoint/annotation. No VAL/test accuracy selection.',
        'minimal_tests': ['Fixed primitive singleton/constant identity, row sums, stationarity/detailed balance, mass-weighted mean, cross-parent Jacobian zero, relabel+inverse and finite gradients, tolerance1e-6.',
            'Native capture/readback/frozen-bank encoder/fixed native query identity controls <=1e-6.',
            'Compare original, fixed content transport, and within-parent deterministic cyclic affinity association control; masses/values/graph/algorithm unchanged. Define exact control in supplement BEFORE outputs.',
            'Report all8scene/32expression task readouts, foreground/non-target separately, sibling path effect/offdiagonal mass/saturation and source-dependency. GT never defines transport.'],
        'falsifiers': 'Invalid invariants/control -> implementation failure. Native identity/no offdiagonal/nonzero source path or content-vs-wrong-association effect <=1e-6 -> mechanism realization unsupported. Mixed task directions remain uncertain; no arbitrary tiny-cohort gain threshold or favorable scene selection.',
        'stage_plan': 'Register diagnosis, execute cheapest discriminating operator + native fixed-query tests, then only if supported build an independent model/config and test actual native loss backward, full-source controls, matched resources and original goal gates. No admission from this diagnostic.',
        'post_training_plan': 'If later admitted: fixed seed1999/epochs50/max_iters70, matched baseline and wrong-association control, report mIoU plus foreground/non-target harmful subgroups; scene-cluster paired uncertainty, all scenes retained; target .5100, no seed/config tuning.',
        'tolerance': 1e-6, 'new_training': 0, 'optimizer_steps': 0,
        'scientific_admission': False, 'production_changes': False})
    work['candidates'].append({'id':c.CID,'stage':'diagnosis',
        'hypothesis':c.tick.load(protocol)['hypothesis'],
        'matched_control':'Same sibling graph/masses/transport, with fixed wrong content-affinity association; original native identity and no-transport baseline.',
        'next_action':'Implement the frozen operator and preregister exact matched control; execute invariants and native source-path diagnostic this tick, then advance remaining gates if evidence supports it.',
        'evidence':[c.evidence(protocol),c.evidence(__file__)], 'scientific_admission':False})
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'created':c.CID,'stage':'diagnosis','pending':8,'training':0}))


if __name__=='__main__':main()
