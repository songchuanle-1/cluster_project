"""Register an exact-source conditional AOC capability, without native execution."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, json, os, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent;NATIVE=HERE/'aoc_native_prepare';OP=HERE/'aoc_operational_prepare'
PREP=ROOT/'pipeline/diagnostic_bundles/tick_e666cac0/new_candidate_prepare'
CID='hierarchy-ancestral-order-commutator-composition';EXP='M222-AOC'
COMMIT='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33';PARENT='9c42fdc4e9168acec18980d782ee9c163e043bb7'

def verify(p):
    v=u.read(p)
    for n,h in v['prepared_file_hashes'].items():
        f=(p.parent/n).resolve();assert f.is_relative_to(p.parent.resolve()) and sha(f)==h,n
    return v

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--operational-sha256');ap.add_argument('--review-sha256');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_REGISTRATION');return
    guard();assert sha(PREP/'preparation.json')=='f7b85c78198a538985661e04714b8eb48de7e2173547f93f1a3ba7fede53f9dd'
    proto=verify(PREP/'preparation.json');assert all(proto[k] is None for k in ('code_commit','source_commit','source_parent_commit'))
    version=HERE/'aoc_version_prepare/isolated_source_version.json';assert sha(version)=='83d8bedd7ae1fae56c835028460f380ae797ed57f1b99f1016f155a88fec414e'
    v=u.read(version);assert v['code_commit']==COMMIT and v['parent_commit']==PARENT and v['diff_exact9A'] is True and v['frozen_source_files']==proto['source_files']
    sourcepeer=HERE/'aoc_actual_source_version_independent_review.json';assert sha(sourcepeer)=='c11cccf7d3f98d77ca275845b2ac6346bfa13e39366f164d2453cc705dd5b1fc'
    assert u.read(sourcepeer)['material_concerns']==[]
    assert sha(NATIVE/'preparation.json')=='9cf931d5f788cf1e545c22a1aea017c181d52e05e40391411cc315b1b7600a40'
    assert sha(OP/'preparation.json')==a.operational_sha256
    n=verify(NATIVE/'preparation.json');op=verify(OP/'preparation.json')
    assert n['source_commit']==op['code_commit']==COMMIT and n['source_parent_commit']==n['runtime_expected_commit']==PARENT
    assert op['source_parent_commit']==op['expected_runtime_code_commit']==PARENT and op['draft_execution_disabled'] is False
    assert n['source_files']==proto['source_files'] and n['draft_execution_disabled'] is False
    peer=HERE/'aoc_native_operational_preparation_independent_review.json';assert sha(peer)==a.review_sha256
    review=u.read(peer);assert review['candidate_id']==CID and review['code_commit']==COMMIT and review['material_concerns']==[]
    assert all(r in review['anchors'].values() for r in [u.ref(NATIVE/'preparation.json'),u.ref(OP/'preparation.json')])
    manifest=u.read(NATIVE/'manifest_template.json')
    assert all(manifest[k] is None for k in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'))
    release=u.read(OP/'release_template.json');assert release['code_commit']==COMMIT and release['candidate_id']==CID and release['native_preparation_sha256']==sha(NATIVE/'preparation.json')
    assert release['source_hashes']=={k:sha(OP/k) for k in ('adapter.py','remote_ops.py')}
    assert not any(p.exists() for p in [OP/'adapter_release.json',HERE/'aoc_execution',HERE/'aoc_registration_intent.json',HERE/'aoc_registration_result.json'])
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
        path=ROOT/'pipeline/research_work.json';before=sha(path);w=u.read(path);old={c['id']:u.digest(c) for c in w['candidates']};assert len(old)==148
        c=next(c for c in w['candidates'] if c['id']==CID)
        assert c['experiment_id']==EXP and c['stage']=='implementation' and c['code_commit'] is None
        assert not any((ROOT/'pipeline'/area/f'{EXP}.json').exists() for area in ('admissions','experiments'))
        now=datetime.now(timezone.utc).isoformat();release_ref={'path':(OP/'adapter_release.json').relative_to(ROOT).as_posix(),'sha256':sha(OP/'release_template.json')}
        c.update(stage='validation',code_commit=COMMIT,source_commit=COMMIT,source_parent_commit=PARENT,future_version_parent=PARENT,source_version=u.ref(version),actual_source_version_independent_review=u.ref(sourcepeer),source_status='ISOLATED_SOURCE_AND_STATIC_TOOLS_CONDITIONAL_ON_TESTED_PARENT_PROMOTION',native_status='NOT_RUN_PARENT_NOT_PROMOTED',resource_status='NOT_RUN_GPU0_OCCUPIED',native_execution_code_commit=None,queued=False,required_server='server-4',required_physical_gpu=0)
        c['worker_preparation']={'status':'STATIC_REVIEWED_CONDITIONAL_CAPABILITY_NATIVE_NOT_RUN','preparation':u.ref(NATIVE/'preparation.json'),'worker':u.ref(NATIVE/'worker.py'),'runtime':u.ref(NATIVE/'native_runtime.py'),'manifest_template':u.ref(NATIVE/'manifest_template.json'),'source_commit':COMMIT,'source_parent_commit':PARENT,'runtime_expected_commit':PARENT,'independent_review':u.ref(peer),'native_backward_executed':False,'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False}
        c['execution_adapter']={'status':'STATIC_REVIEWED_PARENT_PROMOTION_FENCED_NATIVE_NOT_RUN','preparation':u.ref(OP/'preparation.json'),'release':release_ref,'independent_review':u.ref(peer),'active_binding_manifest_lease_created':False,'transport_executed':False}
        c['current_version_compatibility']={'current_source_commit':COMMIT,'current_parent_commit':PARENT,'runtime_expected_commit':PARENT,'current_primary_and_runtime':u.SOURCE,'status':'CONDITIONAL_PARENT_NOT_PROMOTED','parent_source_version':u.ref(ROOT/'pipeline/diagnostic_bundles/tick_9db8f3be/pes_version_prepare/isolated_source_version.json'),'scope':'Current main/runtime5c remain. Mutation requires actual primary9c, valid original PES technical receipt and remote runtime9c, then fresh authorized idle GPU0 and original deadline. No PES training accuracy/completion gate. If parent/main differs, preserve all originals and save an actually compatible unchanged-nine version; never ff18A from5c or a sibling.'}
        c['carryover_scope']='Actual isolated source and conditional native tools are prepared; native TRAIN/resource executions and admission remain outstanding. Prototype NULL metadata and original reference5c stay frozen.'
        c['next_action']='Preserve original DCE GPU0 training and advance existing PES first. Only after tested PES9c is actually promoted may this frozen conditional0314 child run original paired natural TRAIN2/resources under a fresh owning tick, exact actual9c parent/runtime and truly idle authorized GPU0. If PES is not promoted or main changes, retain this evidence and prepare a genuinely compatible unchanged-nine source. No GPU1, automatic old recovery or blind18A/sibling ff.'
        for r in [u.ref(version),u.ref(sourcepeer),u.ref(NATIVE/'preparation.json'),u.ref(OP/'preparation.json'),u.ref(peer),release_ref]:
            if r not in c['evidence']:c['evidence'].append(r)
        w['updated_at']=now;w['last_event_tick']=EXPECTED['generated_at'];w['next_action']=c['next_action']
        w['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CID,'kind':'implementation_test','result':'passed','command':n['static_check_command'],'observation':'Actual software checks for AOC native-observer transparency, negative controls, version guards and missing-manifest early refusal passed. No Torch/native/autograd/resources; current primary5c has not promoted parent9c.','evidence':[n['static_validation']]}
        if n['static_validation'] not in c['evidence']:c['evidence'].append(n['static_validation'])
        assert all(u.digest(x)==old[x['id']] for x in w['candidates'] if x['id']!=CID)
        u.save(HERE/'aoc_registration_intent.json',{'owner':EXPECTED,'research_work_before_sha256':before,'candidate_id':CID,'source_version':u.ref(version),'native_preparation':u.ref(NATIVE/'preparation.json'),'operational_preparation':u.ref(OP/'preparation.json'),'independent_review':u.ref(peer),'release':release_ref,'scope':'Existing candidate only, same exact9 source; no model revision/new candidate/native/primary/runtime/queue/receipt/launch mutation.'})
        guard();assert sha(path)==before
        with (OP/'adapter_release.json').open('xb') as f:f.write((OP/'release_template.json').read_bytes());f.flush();os.fsync(f.fileno())
        assert sha(OP/'adapter_release.json')==release_ref['sha256'];u.atomic(path,w)
        u.primary_protection(b);u.lifecycle_protection(b)
        u.save(HERE/'aoc_registration_result.json',{'owner':EXPECTED,'status':'EXISTING_AOC_CONDITIONAL_CAPABILITY_REGISTERED_NATIVE_NOT_RUN','candidate_id':CID,'experiment_id':EXP,'code_commit':COMMIT,'parent_commit':PARENT,'primary_runtime':u.SOURCE,'candidate_count':148,'new_candidates':0,'model_revisions':0,'other147_candidates_unchanged':True,'all24_lifecycle_and28_user_paths_and_index_preserved':True,'release':release_ref,'native_preparation':u.ref(NATIVE/'preparation.json'),'operational_preparation':u.ref(OP/'preparation.json'),'independent_review':u.ref(peer)})
        print('Existing AOC conditional source/native capability registered; current parent not promoted; no native executed.')
    finally:lock.close()

if __name__=='__main__':main()
