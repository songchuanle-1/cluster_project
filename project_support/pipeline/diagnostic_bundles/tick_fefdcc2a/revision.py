"""One preregistered implementation revision, under the same PCE ID."""
import argparse
import ast
import shutil
from pathlib import Path
import control as c


def preregister():
    c.guard(1100)
    source = c.ROOT / 'Cluster/framework/model/Quard_model' / (c.NAME + '_pce') / 'contact_exchange.py'
    archived = c.OUT / 'contact_exchange_original.py'
    shutil.copyfile(source, archived)
    protocol = c.save('implementation_revision1.json', {
        'preregistered_at': c.now(), 'candidate_id': c.CID, 'revision': 1,
        'failure_scope': 'implementation',
        'reason': 'Full predict median 901.2897ms vs matched M95 33.7900ms; per-recipient GPU launch loop is explicit in source. Standard FVCore misses added elementwise/sum/softmax work.',
        'change': 'Group receivers by exact physical donor degree and batch the SAME headwise dot/softmax/value sum. Geometry sorting, all donors, fallback, heads, weights, dtype, topology and model/config stay unchanged.',
        'prediction': 'Native-feature outputs, input gradients, deleted-edge and row-permutation operator controls stay within original1e-6; full predict latency improves without >15% peak memory increase.',
        'test': 'Frozen original native contact fixture, all eight expressions and original operator, then same full model bs1/warmup20/repeat100 and corrected full-source controls/native backward.',
        'nonclaims': 'Kernel grouping is engineering, not new architecture. Existing full-source numerical failures are NOT waived by operator equivalence or speedup.',
        'failure_evidence': [c.evidence(c.OUT / 'resources_candidate_result.json'),
            c.evidence(c.OUT / 'resources_champion_result.json'),
            c.evidence(c.OUT / 'harness_r1/controls_candidate_result.json')],
        'original_source': c.evidence(archived), 'tolerance': 1e-6,
        'new_parameters': 0, 'new_hyperparameters': 0, 'maximum_revisions': 2})
    work = c.tick.load(c.ROOT / 'pipeline/research_work.json')
    candidate = next(item for item in work['candidates'] if item['id'] == c.CID)
    assert not candidate.get('revision_history')
    candidate['revision_history'] = [{'revision': 1, 'failure_scope': 'implementation',
        'reason': c.tick.load(protocol)['reason'], 'change': c.tick.load(protocol)['change'],
        'prediction': c.tick.load(protocol)['prediction'], 'preregistered_at': c.tick.load(protocol)['preregistered_at'],
        'failure_evidence': c.tick.load(protocol)['failure_evidence'], 'result': 'pending',
        'evidence': [c.evidence(protocol), c.evidence(archived)]}]
    candidate['stage'] = 'implementation'
    candidate['failure_scope'] = 'implementation'
    candidate['scientific_admission'] = False
    candidate['evidence'].extend([c.evidence(protocol), c.evidence(archived)])
    candidate['next_action'] = 'Execute preregistered degree-batched contact implementation revision1. Preserve the failed full-source1e-6 controls; no scientific/training PASS from speedup.'
    c.tick.save(c.ROOT / 'pipeline/research_work.json', work)
    print({'preregistered_revision': 1, 'candidate_id': c.CID, 'scientific_admission': False})


def configure():
    base = Path(__file__).resolve().parent
    c.OUT = base / 'implementation_r1'
    c.STAGE = '/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a/implementation_r1'
    return base


def prepare():
    base = configure()
    c.guard(1100)
    protocol = c.tick.load(base / 'implementation_revision1.json')
    assert protocol['revision'] == 1
    c.OUT.mkdir(exist_ok=False)
    worker = (base / 'harness_r1/worker.py').read_text(encoding='utf-8')
    operator = (base / 'operator_function.py').read_text(encoding='utf-8')
    original_digest = c.tick.load(base / 'implementation_revision1.json')['original_source']['sha256']
    assert operator.count("MANIFEST['original_operator_sha256']") == 1
    operator = operator.replace("MANIFEST['original_operator_sha256']", repr(original_digest))
    assert worker.count('def main():') == 1
    worker = worker.replace('def main():', operator + '\n\ndef main():')
    worker = worker.replace("choices=('resources', 'controls')", "choices=('resources', 'controls', 'operator')")
    old = "        if args.mode == 'resources':\n            resources(torch, gorilla, cfg, model, result)\n        else:"
    new = "        if args.mode == 'operator':\n            operator_equivalence(torch, result)\n        elif args.mode == 'resources':\n            resources(torch, gorilla, cfg, model, result)\n        else:"
    assert worker.count(old) == 1
    worker = worker.replace(old, new)
    ast.parse(worker)
    with (c.OUT / 'worker.py').open('x', encoding='utf-8') as stream:
        stream.write(worker)
    shutil.copyfile(base / 'control.py', c.OUT / 'control.py')
    c.stage()
    c.advance([base / 'implementation_revision1.json', base / 'evaluation_plan.json'],
        'Execute revision1 operator equivalence, full-model same-standard resources and unfrozen full-source controls; old numerical failures remain.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('preregister', 'prepare', 'operator', 'resources', 'controls'))
    args = parser.parse_args()
    if args.operation == 'preregister':
        preregister()
    elif args.operation == 'prepare':
        prepare()
    else:
        configure()
        c.run(args.operation, 'candidate')
