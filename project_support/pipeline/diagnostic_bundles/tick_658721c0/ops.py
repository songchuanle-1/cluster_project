"""One current foreground lease; bounded contact-path research only."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0, str(SKILL))
import foreground_tick as tick
import yaml

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
TOKEN = '658721c071ae487ea47224e55d51abde'
THREAD = '01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
ID = 'hierarchy-cross-leaf-physical-contact-exchange'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
SSH = ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10']


def now():
    return datetime.now(timezone.utc).isoformat()


def guard(seconds=0):
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN
    assert owner['thread_id'] == THREAD == os.environ['CODEX_THREAD_ID']
    assert (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds() > seconds
    assert tick.digest(ROOT / 'pipeline/goal.json') == GOAL
    assert tick.digest(ROOT / 'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert tick.digest(ROOT / 'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']
    servers = yaml.safe_load((ROOT / 'SERVERS.yaml').read_text(encoding='utf-8'))['servers']
    cfg = servers['server-4']
    assert cfg['host'] == '192.168.1.115' and cfg['expected_hostname'] == 'dl04-MS-7E06'
    assert cfg['allowed_gpus'] == [0, 1] and cfg['max_tasks_per_gpu'] == 1
    return owner, servers


def evidence(path):
    path = Path(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': tick.digest(path)}


def save(name, value):
    guard()
    path = OUT / name
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return path


def remote(code, timeout=120, conda=False):
    _, servers = guard(120)
    cfg = servers['server-4']
    prefix = "import socket\nassert socket.gethostname() == 'dl04-MS-7E06'\n"
    command = shlex.join(['python' if conda else '/usr/bin/python3', '-B', '-'])
    if conda:
        command = shlex.join(['bash', '-lc', 'source ' + shlex.quote(cfg['conda_source'])
            + ' && conda activate ' + shlex.quote(cfg['conda_env']) + ' && ' + command])
    process = subprocess.run(['ssh', *SSH, cfg['user'] + '@' + cfg['host'], command],
        input=prefix + code, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    result = {'observed_at': now(), 'returncode': process.returncode,
              'stdout': process.stdout[-16000:], 'stderr': process.stderr[-6000:]}
    if process.returncode == 0:
        result['data'] = json.loads(process.stdout)
    return result


def register():
    guard(600)
    view = tick.load(ROOT / 'pipeline/headless/.tick_model_view.json')
    assert view['mode'] == 'design' and not view['research']['reserve_only']
    assert view['research']['pending_count'] < view['research']['pending_limit']
    ledger = ROOT / 'pipeline/research_work.json'
    work = tick.load(ledger)
    assert not any(c['id'] == ID for c in work['candidates'])
    old = ROOT / 'pipeline/diagnostic_bundles/tick_c121c67d/native_relabel/native_manifest.json'
    manifest = tick.load(old)
    protocol = save('contact_protocol.json', {
        'preregistered_at': now(), 'candidate_id': ID, 'token': TOKEN,
        'goal_sha256': GOAL, 'cohort': manifest['cohort'], 'frozen_assets': manifest['assets'],
        'hypothesis': 'Fine FPS leaves exclude physical contact donors belonging to other leaves. A sparse physical-contact feature exchange across leaves can create a distinct point-feature information path absent from same-leaf FLE, without query/language routing.',
        'mechanism': 'Replace only the fine-scale readback on receivers with cross-leaf contacts by headwise content attention to physical contact donors; preserve middle/coarse M95 banks, existing fusion/projection and outer writeback. No extra gate/residual/projection, top-k, radius, seed or schedule search.',
        'graph': 'Use all actual occupied-voxel/superpoint memberships and six-face voxel adjacency, retaining co-occupancy contacts. Do not choose an owner by numeric superpoint ID. Undirected distinct-superpoint edges; inference geometry only, no target or selected mask.',
        'first_test': 'Check actual information-path distinction from FLE and historical boundary-contrast/anchor-support supervision before any model claim. Native TRAIN capture measures cross-leaf contact incidence and recipient-specific feature/gradient dependence.',
        'matched_controls': ['Exact identity and point-row relabeling of graph/features with inverse permutation; original 1e-6 numerical tolerance.',
            'Original same-leaf FLE gives zero donor dependency across leaves; direct physical-contact path must differ on such donors.',
            'Delete cross-leaf contacts, retain original fine fallback; fixed one-position donor-value rotation with identical topology and no outcome selection.',
            'GT labels are readout/stratification only; scene is sampling unit. A contact or gradient alone is not task benefit or admission.'],
        'falsifiers': ['No extra physical cross-leaf donor path, or exact same causal graph as a rejected historical proposal, rejects the distinct-mechanism claim.',
            'Failed numerical/identity controls block this realization; preserve all failures, do not relax the threshold.',
            'Task-harm/benefit remains inconclusive without matched native readout; missing capture is executable work, not a fake external block.'],
        'scope_limits': 'Diagnostic candidate, not scientifically admitted or trained. No automatic FLE/HDS/M201/M204 recovery. All prior banned routes and failed numeric results remain.'})
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
    goal = tick.load(ROOT / 'pipeline/goal.json')
    review = ROOT / 'pipeline/reviews' / ('motivation_review_' + stamp + '_contact.md')
    review.write_text('# Motivation Review - cluster_project\n\n## 1. Goal\n```json\n'
        + json.dumps(goal, ensure_ascii=False, indent=2) + '\n```\n'
        + '\n## 2. Story Status\nM95 context works historically; distinct level roles and a new trained benefit remain unproved. Target .5100; historical best .5020; gap .0080.\n'
        + '\n## 3. Experiment Assessment\nM203 within-leaf FLE and M204 point-to-coarse CPA are terminal, not reopened. Old numerical diagnostics cannot freeze independent work.\n'
        + '\n## 4. Gap Analysis\nCross-leaf physical donor connectivity is a falsifiable missing fine-scale path, not yet an observed task deficit.\n'
        + '\n## 5. Design Rationale\nFirst distinguish physical contact exchange from same-leaf FLE, selected-mask boundary contrast and named-anchor contact supervision. No efficacy or novelty claim yet.\n'
        + '\n## 6. Next Batch\nStable diagnosis ID: ' + ID + '; execute the frozen source/native controls before any independent model/config or admission.\n', encoding='utf-8')
    candidate = {'id': ID, 'stage': 'diagnosis', 'created_at': now(),
        'hypothesis': tick.load(protocol)['hypothesis'],
        'matched_control': '; '.join(tick.load(protocol)['matched_controls']),
        'next_action': 'Execute frozen source-distinction and native physical-contact capture; persist all identity, row-permutation, off-leaf donor and scene-level readouts. No training until all gates pass.',
        'scientific_admission': False, 'evidence': [evidence(protocol), evidence(review)]}
    work['candidates'].append(candidate)
    save('due_scope_disposition.json', {'observed_at': now(), 'candidate_ids': [c['id'] for c in work['candidates'] if c.get('stage') == 'blocked'],
        'result': 'Four supervision priority holds are unchanged. Two strict numerical measurement failures have no preregistered repair; no unchanged replay is informative. This is not scientific rejection or a global structural-design freeze.',
        'next_action': 'Preserve old evidence/gates and proceed with the new independent information-path diagnosis.', 'native_replays': 0})
    tick.save(ledger, work)
    print(json.dumps({'registered': ID, 'protocol': evidence(protocol), 'review': evidence(review), 'pending_count': 7, 'admitted': False}))


if __name__ == '__main__':
    if sys.argv[1:] == ['register']:
        register()
