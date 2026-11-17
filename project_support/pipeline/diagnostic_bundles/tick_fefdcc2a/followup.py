"""Immutable harness repair; never overwrite earlier diagnostic evidence."""
import argparse
import shutil
from pathlib import Path
import control as c


def configure(label):
    c.guard(700)
    base = Path(__file__).resolve().parent
    c.OUT = base / label
    c.STAGE = '/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a/' + label
    return base


def prepare():
    base = configure('harness_r1')
    c.OUT.mkdir(exist_ok=False)
    source = (base / 'worker.py').read_text(encoding='utf-8')
    old = "        held['args'], held['kwargs'] = clone(values), clone(keywords)"
    new = old + "\n        held['contact_positions'] = clone(attention.physical_contact_positions)\n        held['contact_edges'] = copy.deepcopy(attention.physical_contact_edges)"
    assert source.count(old) == 1
    source = source.replace(old, new)
    old = "    edges = copy.deepcopy(attention.physical_contact_edges)\n    positions = attention.physical_contact_positions.detach().clone()"
    new = "    edges = copy.deepcopy(held['contact_edges'])\n    positions = held['contact_positions'].detach().clone()"
    assert source.count(old) == 1
    source = source.replace(old, new)
    with (c.OUT / 'worker.py').open('x', encoding='utf-8') as stream:
        stream.write(source)
    shutil.copyfile(base / 'control.py', c.OUT / 'control.py')
    repair = c.save('harness_repair.json', {
        'recorded_at': c.now(), 'candidate_id': c.CID,
        'failure_evidence': c.evidence(base / 'controls_candidate_result.json'),
        'failure': 'Candidate intentionally clears temporary geometry at decoder return; harness read too late.',
        'change': 'Capture original contact geometry at existing native encoder pre-hook; model source/config/arithmetic unchanged.',
        'prediction': 'Native same-source controls now execute using exact original geometry; prior failed run is not a scientific test result.',
        'candidate_implementation_revisions': 0})
    c.stage()
    c.advance([repair], 'Run corrected timing-only geometry capture harness; preserve original failure and all 1e-6 controls.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('prepare', 'controls'))
    args = parser.parse_args()
    if args.operation == 'prepare':
        prepare()
    else:
        configure('harness_r1')
        c.run('controls', 'candidate')
