"""Approve static module hashes only; never create an execution lease or launch."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'psnc_operational_prepare'
TOKEN='42ce600bac914e84bceee707167a669b'
CID='hierarchy-parent-spectral-nonlinear-token-coupling'
COMMIT='43dce016c1a1713c2a5dab7061810dc2efde8954'
BASE='74fcd21df0af9a971792038ffe251af1ffea2604'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,value):
    p=Path(p);tmp=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def verify_map(directory):
    p=read(directory/'preparation.json')
    for name,expected in p['prepared_file_hashes'].items():
        file=(directory/name).resolve()
        assert file.is_relative_to(directory.resolve()) and sha(file)==expected,name
    return p

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--review',required=True);parser.add_argument('--review-sha',required=True)
    args=parser.parse_args();review=Path(args.review)
    assert sha(review)==args.review_sha and read(review)['material_concerns']==[]
    independent=HERE/'psnc_operational_independent_review.json'
    assert sha(independent)=='eaf8a8731c257d1e8faa22379f688e722d3cc9fe703e96cee8f74fcbc9034d15'
    assert read(independent)['material_concerns']==[]
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    prep=verify_map(PACKAGE);native=verify_map(PACKAGE/'native')
    assert prep.get('candidate_id')==native.get('candidate_id')==CID
    assert native.get('source_commit',native.get('code_commit'))==COMMIT
    assert subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'rev-parse','HEAD'],text=True).strip()==BASE
    assert not subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'diff','--cached','--name-only'],text=True).strip()
    assert not (HERE/'psnc_execution').exists()
    release_template=PACKAGE/'release_template.json';release=PACKAGE/'adapter_release.json'
    assert not release.exists()
    data=read(release_template)
    assert set(data['source_hashes'])=={'adapter.py','remote_ops.py'}
    assert all(sha(PACKAGE/name)==expected for name,expected in data['source_hashes'].items())
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        protected={name:sha(ROOT/'pipeline'/name) for name in ['queue.json','running.json','experiments/M208-HRC.json',
            'experiments/M209-PSBR.json','experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']}
        work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
        assert c['stage']=='blocked' and c['blocker_kind']=='exclusive_gpu_slot' and c['code_commit']==COMMIT
        assert c.get('native_execution_code_commit') is None
        assert not c.get('execution_adapter') and not (ROOT/'pipeline/admissions/M210-PSNC.json').exists()
        with release.open('xb') as f:f.write(release_template.read_bytes());f.flush();os.fsync(f.fileno())
        assert sha(release)==sha(release_template)
        c.setdefault('native_tool_preparation_history',[]).append({'preparation':c['native_tool_preparation'],
            'review':c['native_tool_independent_review'],'status':c['native_worker_adapter'],
            'preserved_reason':'Frozen disabled draft remains unchanged; new operational preparation is separately reviewed.'})
        c['native_tool_preparation']=ref(PACKAGE/'native/preparation.json')
        c['native_tool_independent_review']=ref(review)
        c['native_worker_adapter']='OPERATIONAL_PREPARED_EXTERNALLY_ANCHORED_NATIVE_UNEXECUTED'
        c['worker_preparation']={'status':'PREPARED_UNEXECUTED','preparation':ref(PACKAGE/'native/preparation.json'),
            'worker':ref(PACKAGE/'native/worker.py'),'runtime':ref(PACKAGE/'native/native_runtime.py'),
            'source_commit':COMMIT,'native_backward_passed':False,'resources_passed':False}
        c['execution_adapter']={'status':'PREPARED_UNEXECUTED','preparation':ref(PACKAGE/'preparation.json'),
            'release':ref(release),'adapter':ref(PACKAGE/'adapter.py'),'remote_ops':ref(PACKAGE/'remote_ops.py'),
            'README':ref(PACKAGE/'README.md'),'independent_review':ref(review),'external_anchor_required':True,
            'independent_fixture_review':ref(independent),
            'independent_tests':ref(PACKAGE/'independent_offline_run_v1.json'),
            'preparer_static_tests':ref(PACKAGE/'packet_static_validation.json'),
            'native_execution_tested':False,'remote_adapter_execution_tested':False,
            'active_binding_manifest_lease_created':False,'static_release_scope':'Exact reviewed module/version hashes only; not an execution lease or resource grant.',
            'source_commit':COMMIT,'native_execution_code_commit':None,
            'provenance':'Root materialized reviewed static release and external anchors. Actual native/runtime/remote/GPU work NOT_RUN; future fresh owner/assets/idleGPU0 and locks are mandatory.'}
        c['resume_stage']='validation'
        c['implementation_status']='PREPARED_STATIC_VERIFIED_NATIVE_UNEXECUTED'
        now=datetime.now(timezone.utc);c['updated_at']=now.isoformat()
        for item in [ref(PACKAGE/'preparation.json'),ref(PACKAGE/'native/preparation.json'),ref(release),ref(review),ref(independent),
                ref(PACKAGE/'independent_offline_run_v1.json'),ref(PACKAGE/'packet_static_validation.json')]:
            if item not in c['evidence']:c['evidence'].append(item)
        work['updated_at']=now.isoformat();save(ROOT/'pipeline/research_work.json',work)
        assert {name:sha(ROOT/'pipeline'/name) for name in protected}==protected
        save(HERE/'static_adapter_anchor_result.json',{'recorded_at':now.isoformat(),'token':TOKEN,'candidate_id':CID,
            'code_commit':COMMIT,'native_preparation':ref(PACKAGE/'native/preparation.json'),
            'adapter_preparation':ref(PACKAGE/'preparation.json'),'static_release':ref(release),'review':ref(review),
            'independent_review':ref(independent),'independent_tests':ref(PACKAGE/'independent_offline_run_v1.json'),
            'preparer_static_tests':ref(PACKAGE/'packet_static_validation.json'),
            'static_module_release_only':True,'native_manifest_lease_binding_created':False,
            'remote_GPU_native_resources_receipt_queue_or_launch':'NOT_RUN','protected_registry_hashes':protected,
            'new_Git_commit_or_sync':False})
        print(json.dumps({'static_anchor_saved':True,'source_commit':COMMIT,'release':ref(release),
            'native':'NOT_RUN','active_binding_created':False},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
