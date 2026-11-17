"""Execute only the exact nine-file local commit explicitly approved by the user."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT


def git(*args):
    r=subprocess.run(['git','-C',str(ROOT/'Cluster'),*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    assert r.returncode==0,r.stderr
    return r.stdout.strip()


def main():
    c.guard(1200)
    bundle=c.tick.load(OUT/'tested_commit_bundle.json')
    assert bundle['requested_operation']=='local_git_commit_only' and len(bundle['files'])==9
    paths=[x['repository_path'] for x in bundle['files']]
    for x in bundle['files']:assert c.tick.digest(Path(x['absolute_path']))==x['sha256']
    assert not git('diff','--cached','--name-only'),'Existing staged files need preservation; never include them'
    original_head=git('rev-parse','HEAD')
    authorization=ROOT/'pipeline/authorizations/rstr_local_commit_20261021_99819673.json'
    assert not authorization.exists()
    c.tick.save(authorization,{'recorded_at':c.now(),'candidate_id':c.CID,'thread_id':c.THREAD,'goal_sha256':c.GOAL,
        'source':'Direct human answer in this owning chat to request_user_input_async questionItemId [request_user_input_async,call_e63710e02dc04f9890ece9faafc1b210,0]',
        'human_reply':'授权这 9 个文件的本地提交',
        'allowed_operations':['local Git commit of exactly the tested eight RSTR model source files and one config'],
        'tested_bundle':c.evidence(OUT/'tested_commit_bundle.json'),'files':bundle['files'],
        'does_not_grant':['additional file scope','new revision','scientific gate exception','push or training permission beyond existing project authorization']})
    c.guard(900)
    git('add','--',*paths)
    staged=git('diff','--cached','--name-only').splitlines()
    assert set(staged)==set(paths) and len(staged)==9
    git('diff','--cached','--check')
    committed=git('commit','-m','Add reversible sibling token transport for point features')
    current=git('rev-parse','HEAD')
    changed=git('diff-tree','--no-commit-id','--name-only','-r',current).splitlines()
    assert current!=original_head and set(changed)==set(paths) and len(changed)==9
    for x in bundle['files']:
        assert c.tick.digest(Path(x['absolute_path']))==x['sha256']
        data=subprocess.run(['git','-C',str(ROOT/'Cluster'),'show',current+':'+x['repository_path']],capture_output=True,timeout=30)
        import hashlib
        assert data.returncode==0 and hashlib.sha256(data.stdout).hexdigest()==x['sha256']
    result=c.save('local_commit_result.json',{'observed_at':c.now(),'candidate_id':c.CID,'previous_head':original_head,'code_commit':current,
        'authorization':c.evidence(authorization),'files':changed,'staged_before':[],'staged_after':git('diff','--cached','--name-only'),
        'committed_blob_hashes_equal_tested_bytes':True,'unrelated_work_status_after':git('status','--short'),'stdout':committed,
        'remote_push_executed':False,'production_sync_executed':False,'training_executed':False})
    c.advance([authorization,result,Path(__file__)],'Exact tested local commit completed under direct authorization. Determine remaining admission/deployment scope from existing project grants; never infer additional permissions from this local-commit reply.')
    print(json.dumps({'code_commit':current,'files':9,'tested_bytes_identical':True,'other_work_preserved':True},ensure_ascii=False))


if __name__=='__main__':main()
