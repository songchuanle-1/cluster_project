"""Reconcile the completed commit and verify Git's LF normalization explicitly."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT
c.guard(1200)
repo=ROOT/'Cluster'
bundle=c.tick.load(OUT/'tested_commit_bundle.json')
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
assert commit=='36b59daae6cdad2560024379eb5ed6acbcb20db2'
changed=subprocess.check_output(['git','-C',str(repo),'diff-tree','--no-commit-id','--name-only','-r',commit],text=True).splitlines()
assert set(changed)=={x['repository_path'] for x in bundle['files']} and len(changed)==9
archive=OUT/'source_committed';archive.mkdir(exist_ok=False)
records=[]
for item in bundle['files']:
    path=Path(item['absolute_path']);before=path.read_bytes()
    assert hashlib.sha256(before).hexdigest()==item['sha256']
    blob=subprocess.check_output(['git','-C',str(repo),'show',commit+':'+item['repository_path']])
    assert before.replace(b'\r\n',b'\n')==blob
    if path.suffix=='.py':assert ast.dump(ast.parse(before.decode('utf-8')))==ast.dump(ast.parse(blob.decode('utf-8')))
    records.append({'path':item['repository_path'],'worktree_tested_sha256':item['sha256'],'committed_blob_sha256':hashlib.sha256(blob).hexdigest(),
        'newline_only':before!=blob,'normalized_bytes_equal':True})
    destination=archive/('candidate.yaml' if path.suffix=='.yaml' else path.name)
    with destination.open('xb') as stream:stream.write(blob)
    # No source-language edit: align actual working bytes with the committed object.
    with path.open('wb') as stream:stream.write(blob)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==hashlib.sha256(blob).hexdigest()
authorization=ROOT/'pipeline/authorizations/rstr_local_commit_20261021_99819673.json'
result=c.save('local_commit_result.json',{'observed_at':c.now(),'candidate_id':c.CID,'previous_head':'c31f45994f8d68b78dfe8bb4fef3f9aaefabe86e','code_commit':commit,
    'authorization':c.evidence(authorization),'files':changed,'records':records,
    'staged_after':subprocess.check_output(['git','-C',str(repo),'diff','--cached','--name-only'],text=True),
    'note':'Commit succeeded before the first reconciliation assertion noticed Git core.autocrlf=true normalizes added files to LF. No repeat commit, no code/AST change. Preserve CRLF-tested R2 archive and retest exact committed LF bytes in a new immutable diagnostic stage.',
    'remote_push_executed':False,'production_sync_executed':False,'training_executed':False})
protocol=c.save('committed_bytes_retest_preregistration.json',{'preregistered_at':c.now(),'candidate_id':c.CID,'revision':2,'code_commit':commit,
    'scope':'Only CRLF→LF source normalization by Git. Identical normalized bytes/AST; no algorithm or implementation revision, no threshold/dtype/FPS/schedule/seed change. Completed R0/R1/R2 records remain immutable.',
    'test':'Re-execute actual native loss backward/full-source controls, same-standard resources and8scene matched controls using exact committed source hashes; no receipt from byte-unequal old tests.',
    'committed_source':[c.evidence(x) for x in sorted(archive.iterdir())],'commit':c.evidence(result),'training':0})
c.advance([authorization,result,protocol], 'Verify exact committed LF source bytes under unchanged R2 protocols before admission or deployment; preserve old tests and original negative evidence.')
controller=(OUT/'validation_r2.py').read_text(encoding='utf-8').replace('_validation_r2','_validation_committed').replace("OUT/'validation_r2'","OUT/'validation_committed'")
controller=controller.replace('validation_r2_execution_preregistration','validation_committed_execution_preregistration').replace('validation_r2_staging','validation_committed_staging').replace("'validation_r2_'+label","'validation_committed_'+label")
with (OUT/'validation_committed.py').open('x',encoding='utf-8') as stream:stream.write(controller)
controller=(OUT/'r2_matched.py').read_text(encoding='utf-8').replace("STAGE=c.STAGE+'_r2_matched'","STAGE=c.STAGE+'_committed_matched'").replace("VOUT=OUT/'r2_matched'","VOUT=OUT/'committed_matched'")
controller=controller.replace('r2_matched_execution_preregistration','committed_matched_execution_preregistration').replace('r2_matched_staging','committed_matched_staging').replace("'r2_matched_'+label","'committed_matched_'+label")
with (OUT/'committed_matched.py').open('x',encoding='utf-8') as stream:stream.write(controller)
print(json.dumps({'commit':commit,'files':9,'only_git_line_endings':True,'committed_byte_retest':'pending'}))
