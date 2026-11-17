"""Promote exactly the measured PSNC commit without touching protected work."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
CODE = ROOT / 'Cluster'
TOKEN = 'a4f7314098ed4dbd8351aa005661583d'
BASE = '74fcd21df0af9a971792038ffe251af1ffea2604'
TESTED = '43dce016c1a1713c2a5dab7061810dc2efde8954'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git', '-C', str(CODE), *args], text=True, encoding='utf-8').strip()
def save(p, x):
    with p.open('x', encoding='utf-8') as f:
        json.dump(x, f, ensure_ascii=False, indent=2); f.write('\n')

def protected():
    rows = read(ROOT / 'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json')['protected_existing_worktree']
    raw = subprocess.check_output(['git','-C',str(CODE),'status','--porcelain','--untracked-files=all'],text=True,encoding='utf-8')
    assert {(x[:2], x[3:]) for x in raw.splitlines() if x} == {(r['status'], r['path']) for r in rows}
    for r in rows: assert sha(CODE / r['path']) == r['sha256']
    assert not git('diff','--cached','--name-only')
    return rows

def main():
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']
    review = HERE/'psnc_primary_ff_review/review.json'
    assert sha(review) == '063a3641c9194b27930598f73386789bc79fb11178ff3d91187d8e7450afe3c1'
    assert not read(review)['material_concerns']
    semantic = HERE/'psnc_execution_independent_review/actual_four_result_review.json'
    independent = HERE/'psnc_native_resource_independent_review.json'
    assert sha(semantic) == '69ca0aee312744106885d2f617b5ca8369436e20a952363b66d4317c811d7563'
    assert sha(independent) == '41888b342544c8912679cefa39e6c548336a6286c32ab8d1af2b83b5e6b9ed16'
    assert read(semantic)['review_status'] == 'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION'
    assert read(independent)['status'] == 'FOUR_ACTUAL_PSNC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
    assert not read(semantic)['material_concerns'] and not read(independent)['material_concerns']
    # The measured executions, not their CLI copies, bind this promotion.
    executions = {}
    for name in ('smoke_champion','smoke_candidate','resources_champion','resources_candidate'):
        p = HERE/'psnc_execution'/(name+'_execution.json'); x = read(p)
        assert x['certainty'] == 'terminal' and x['returncode'] == 0
        assert x['result']['execution_completed'] is True and x['result']['code_commit'] == TESTED
        executions[name] = sha(p)
    assert git('rev-parse','HEAD') == BASE
    assert git('show','-s','--format=%P',TESTED) == BASE
    rows = protected()
    manifest = read(HERE/'psnc_execution/native_manifest.json')
    source = 'framework/model/Quard_model/'+manifest['candidate_name']+'/'
    paths = {source+n:h for n,h in manifest['candidate_source_hashes'].items()}
    paths[manifest['config']] = manifest['candidate_config_sha256']
    diff = git('diff-tree','--no-commit-id','--name-status','-r',TESTED).splitlines()
    assert set(diff) == {'A\t'+p for p in paths} and len(paths) == 9
    for p,h in paths.items():
        assert not (CODE/p).exists()
        assert hashlib.sha256(subprocess.check_output(['git','-C',str(CODE),'show',TESTED+':'+p])).hexdigest() == h
        assert p not in {r['path'] for r in rows}
    before = {'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'before_commit':BASE,
              'tested_commit':TESTED,'changed_paths':paths,'protected_rows':rows,'actual_execution_hashes':executions,
              'independent_ff_boundary_review_sha256':sha(review),'index_empty':True,'new_commit_created':False}
    save(HERE/'psnc_primary_ff_before.json',before)
    hooks = HERE/'empty_hooks'; hooks.mkdir(exist_ok=False)
    env = os.environ.copy(); env['GIT_LFS_SKIP_SMUDGE'] = '1'
    command = ['git','-C',str(CODE),'-c','merge.autoStash=false','-c','core.autocrlf=false','-c','core.eol=lf','-c','core.hooksPath='+str(hooks),'merge','--ff-only',TESTED]
    assert read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json') == owner
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']
    run = subprocess.run(command,capture_output=True,text=True,encoding='utf-8',env=env,timeout=120)
    save(HERE/'psnc_primary_ff_command.json',{'command':command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
    assert run.returncode == 0, run.stderr
    assert git('rev-parse','HEAD') == TESTED
    assert protected() == rows
    for p,h in paths.items(): assert sha(CODE/p) == h
    result = {'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'HEAD':TESTED,
              'only_nine_tested_additions':True,'protected_28_status_and_bytes_unchanged':True,'index_empty':True,
              'source_hashes':paths,'remote_sync_performed':False,'admission_or_launch_performed':False,
              'new_commit_created':False,'reset_clean_stash_force_used':False}
    save(HERE/'psnc_primary_ff_result.json',result)
    print(json.dumps(result,ensure_ascii=False))

if __name__ == '__main__': main()
