"""Root-only merge of tested source reserves; never creates admission or queue entries."""
from pathlib import Path
from datetime import datetime, timezone
import copy, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u

HERE=Path(__file__).resolve().parent
WFC='hierarchy-wedge-factor-incidence-composition'
LFT='hierarchy-nonlinear-lifting-analysis-synthesis'
PREPS={WFC:('new_candidate_prepare','wfc_source_independent_review.json','659528feeee9f8a08f2b5e5aad22af9f21f8cc5994940e8fd04854b1976316c6'),LFT:('lft_candidate_prepare','lft_source_independent_review.json','1210502d2454513983554dacf80293f7cd85fbdb55949b39f34e50b8fd01be92')}

def main():
    guard()
    assert sys.dont_write_bytecode
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    import gpu_occupation
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();baseline=u.read(HERE/'protected_assets_before.json')
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        intentpath=HERE/'source_reserve_final_record_intent.json'
        resultpath=HERE/'source_reserve_final_record_result.json'
        assert not intentpath.exists() and not resultpath.exists(), 'Reconcile existing attempt; no replay.'
        workpath=ROOT/'pipeline/research_work.json'
        work=u.read(workpath);assert len(work['candidates'])==153
        before=sha(workpath)
        others={c['id']:u.digest(c) for c in work['candidates'] if c['id'] not in (WFC,LFT)}
        assert len(others)==151
        now=datetime.now(timezone.utc).isoformat()
        context=u.read(ROOT/'pipeline/headless/.tick_context.json')
        server=next(s for s in context['queue']['servers'] if s['name']=='server-4')
        queue=mon.load_queue(str(ROOT))
        occupation=u.ref(HERE/'source_reserve_gpu_occupation.json')
        raw=u.ref(HERE/'source_reserve_gpu_occupation_raw.json')
        resource_refs=[occupation,raw,u.ref(HERE/'source_reserve_gpu_occupation_validation.json'),u.ref(HERE/'source_reserve_resource_helper_independent_review.json')]
        per_candidate={}
        for cid,(dirname,reviewname,expected_sha) in PREPS.items():
            folder=HERE/dirname;prep_path=folder/'preparation.json';peerpath=HERE/reviewname
            assert sha(prep_path)==expected_sha
            prep=u.read(prep_path);peer=u.read(peerpath)
            assert prep['candidate_id']==peer['candidate_id']==cid
            assert peer['material_concerns']==[] and peer['anchors']['preparation']==u.ref(prep_path)
            assert peer['source_files_exact9']==prep['source_files'] and len(prep['source_files'])==9
            assert prep['native']==prep['resources']=='NOT_RUN'
            assert all(prep[k] is None for k in ('code_commit','source_commit','source_parent_commit'))
            for n,h in prep['prepared_file_hashes'].items():assert sha(folder/n)==h,n
            for n,h in prep['source_files'].items():assert sha(folder/'staged_repository'/n)==h,n
            u.check_refs(list(peer['anchors'].values()))
            candidate=next(c for c in work['candidates'] if c['id']==cid)
            assert candidate['stage']=='implementation' and candidate['created_tick']==EXPECTED['generated_at'] and candidate['queued'] is False
            refs=[u.ref(prep_path),prep['source_manifest'],prep['native_protocol'],prep['static_validation'],u.ref(peerpath),u.ref(HERE/'source_reserve_classification_review.json')]+list(peer['anchors'].values())+resource_refs
            for entry in refs:
                if entry not in candidate['evidence']:candidate['evidence'].append(entry)
            candidate.update(stage='validation',source_status='FROZEN_SOURCE_SOFTWARE_CHECKS_AND_INDEPENDENT_REVIEW_PASSED_NATIVE_PENDING',native_status='NOT_RUN_BOTH_ALLOWED_GPUS_OCCUPIED',resource_status='NOT_RUN_BOTH_ALLOWED_GPUS_OCCUPIED',occupation_evidence=occupation,last_resource_check_at=u.read(HERE/'source_reserve_gpu_occupation.json')['observed_at'],source_preparation=u.ref(prep_path),independent_source_review=u.ref(peerpath),implementation_test=dict(result='passed',command=prep['static_check_command'],evidence=[prep['static_validation'],u.ref(peerpath)],scope='Local stdlib production AST/list-carrier and compile/integration only. Not Torch, autograd, native TRAIN, resources, accuracy or novelty.'),updated_at=now)
            if cid==WFC:
                versionpath=HERE/'wfc_version_prepare/isolated_source_version.json'
                version=u.read(versionpath)
                assert version['candidate_id']==cid and version['parent_commit']==u.SOURCE
                assert version['frozen_source_files']==prep['source_files']==version['committed_blob_sha256']
                assert version['primary_HEAD_before']==version['primary_HEAD_after']==u.SOURCE
                assert version['diff_exact9A'] and version['native_resources_remote_queue_launch']=='NOT_RUN'
                candidate.update(code_commit=version['code_commit'],source_commit=version['code_commit'],source_parent_commit=version['parent_commit'],source_version=u.ref(versionpath),source_version_status='ISOLATED_LOCAL_EXACT9A_ONLY_PRIMARY_RUNTIME_UNCHANGED_NATIVE_UNTESTED')
                candidate['evidence'].append(u.ref(versionpath))
                candidate['next_action']='Both allowed physical cards are occupied by protected original SFC/ELC. Complete/review the separately prepared WFC native worker; on a genuinely idle authorized card, recheck actual intended main and source compatibility, then original paired natural TRAIN2 plus wholemodel resources under frozen YAML/protocol. Only after real technical PASS save/promote the tested compatible version, receipt, queue and canonical dispatch. No current native/resource/efficacy PASS.'
            else:
                assert all(candidate[k] is None for k in ('code_commit','source_commit','source_parent_commit','future_version_parent'))
                candidate['next_action']='Both allowed physical cards are occupied by protected original SFC/ELC. Preserve frozen source prototype and implement/review native worker; save an actual compatible source version from then-current intended main, and execute original paired natural TRAIN2/resources when an authorized card is genuinely idle. Original3FFNs remain common; only whole newP/Ucore aggregate gradient and actual update gate, no additional invertibility/FP32/coverage gate. No receipt/queue/native or efficacy PASS.'
            state=gpu_occupation.validated_state(ROOT,context,candidate,server,queue)
            assert state['busy_gpu_ids']==[0,1] and not state['idle_gpu_ids']
            per_candidate[cid]=dict(experiment_id=candidate['experiment_id'],stage=candidate['stage'],preparation=u.ref(prep_path),source_review=u.ref(peerpath),native=candidate['native_status'],resources=candidate['resource_status'],source_version=candidate.get('source_version'),evidence_count=len(candidate['evidence']))
        old=copy.deepcopy(work.get('tick_attempt'))
        if old:work.setdefault('tick_attempt_history',[]).append(old)
        candidate=next(c for c in work['candidates'] if c['id']==LFT)
        work['tick_attempt']=dict(tick_started_at=EXPECTED['generated_at'],candidate_id=LFT,kind='implementation_test',result='passed',command=candidate['implementation_test']['command'],observation='Frozen LFT original-value YAML/source8: 72 actual local software checks and independent source97 plus narrowintegration46 passed. This is stdlib production AST/list-carrier evidence only; original native TRAIN2/Torch gradient/resource checks NOT_RUN because both allowed cards retain protected training. WFC separately completed35/independent111 and exact isolated source save; neither admitted or queued.',evidence=candidate['implementation_test']['evidence'])
        work['updated_at']=now
        work['next_action']='Monitor protected original SFC/ELC progress first; preserve two software-tested validation source reserves WFC/LFT, ready-waiting0. Fresh physical GPU0/1 both busy; execute missing native preparation/checks at an authorized genuine opening without reopening M206 or old holds.'
        assert {c['id']:u.digest(c) for c in work['candidates'] if c['id'] not in (WFC,LFT)}==others
        for c in work['candidates']:
            if c['id'] in (WFC,LFT):u.check_refs(c['evidence'])
        u.save(intentpath,dict(owner=EXPECTED,recorded_at=now,work_before_sha256=before,other151_candidate_digests=others,protected_baseline=u.ref(HERE/'protected_assets_before.json'),scope='Only2 newly registered source prototypes to honest validation reserve; no queue/admission/native/remote/primary source changes.',candidate_dispositions=per_candidate))
        guard();assert sha(workpath)==before
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        u.atomic(workpath,work)
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        after=u.read(workpath)
        assert {c['id']:u.digest(c) for c in after['candidates'] if c['id'] not in (WFC,LFT)}==others
        u.save(resultpath,dict(owner=EXPECTED,recorded_at=datetime.now(timezone.utc).isoformat(),work_after_sha256=sha(workpath),candidate_count=153,new_source_prototypes=2,new_model_revisions=0,native_diagnostic_arms=0,new_admissions=0,new_queue_entries=0,new_formal_launches=0,other151_candidates_unchanged=True,primary_HEAD_index_user28_all34_lifecycle_bytes_unchanged=True,candidate_dispositions=per_candidate,tick_attempt=after['tick_attempt']))
        print(json.dumps(dict(result=u.ref(resultpath),new_source_reserves=2,ready_waiting=0,native_tests=0,admissions=0,launches=0)))
    finally:lock.close()

if __name__=='__main__':main()
