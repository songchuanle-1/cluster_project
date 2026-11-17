"""Register reviewed static preparations; no native, deployment or queue action."""
from pathlib import Path
from datetime import datetime, timezone
import copy,json,sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
EXPECTED_COMMITS={u.HPC:'6282263d805c1741234f97afc981a05aca2ad6e3',u.APF:'bf6c3fafe0f690e16e838e7c0192f09e789389f9'}
def verify_map(preparation):
    p=ROOT/preparation['path'];v=u.read(p);assert sha(p)==preparation['sha256']
    for name,want in v['prepared_file_hashes'].items():
        f=(p.parent/name).resolve();assert f.is_relative_to(p.parent.resolve()) and sha(f)==want,name
    return v
def main():
    guard();b=u.read(HERE/'protected_assets_before.json')
    u.primary_protection(b);u.lifecycle_protection(b)
    catalogue=u.read(HERE/'packet_catalogue.json');assert catalogue['owner']==EXPECTED
    assert {c['id'] for c in catalogue['candidates']}==set(EXPECTED_COMMITS)
    validated=[]
    for entry in catalogue['candidates']:
        required=('source_version','source_review','native_preparation','native_review','operational_preparation','operational_review')
        u.check_refs(entry['evidence']+[entry[key] for key in required]);cid=entry['id'];commit=EXPECTED_COMMITS[cid]
        assert entry['code_commit']==commit and entry['source_parent_commit']==u.SOURCE
        version=u.read(ROOT/entry['source_version']['path'])
        assert version['code_commit']==commit and version['parent_commit']==u.SOURCE and version['diff_exact9A'] is True
        wt=Path(version['worktree'])
        assert u.git(wt,'rev-list','--parents','-n','1',commit).decode().split()==[commit,u.SOURCE]
        assert not u.git(wt,'status','--porcelain=v1','--untracked-files=all','-z')
        assert all(sha(wt/n)==h for n,h in version['frozen_source_files'].items())
        native=verify_map(entry['native_preparation']);op=verify_map(entry['operational_preparation'])
        assert native['candidate_id']==cid and native['source_commit']==commit
        assert op['candidate_id']==cid and op['code_commit']==commit
        native_dir=(ROOT/entry['native_preparation']['path']).parent
        manifest=u.read(native_dir/'manifest_template.json')
        active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
        assert all(manifest[k] is None for k in active)
        for key in ('source_review','native_review','operational_review'):
            review=u.read(ROOT/entry[key]['path'])
            assert review.get('material_concerns')==[] and review['candidate_id']==cid and review['code_commit']==commit,key
            anchors=review['anchors']
            if key=='source_review':assert anchors['source_version']==entry['source_version']
            if key=='native_review':assert entry['native_preparation'] in (anchors.get('preparation'),anchors.get('native_preparation'))
            if key=='operational_review':assert entry['operational_preparation'] in (anchors.get('preparation'),anchors.get('operational_preparation'))
        op_dir=(ROOT/entry['operational_preparation']['path']).parent
        release=u.read(op_dir/'release_template.json')
        assert release['candidate_id']==cid and release['code_commit']==commit
        assert release['native_preparation_sha256']==entry['native_preparation']['sha256']
        assert set(release['source_hashes'])=={'adapter.py','remote_ops.py'}
        assert all(sha(op_dir/n)==h for n,h in release['source_hashes'].items())
        assert 'adapter_release.json' not in op['prepared_file_hashes']
        assert not (op_dir/'adapter_release.json').exists()
        assert not (HERE/entry['execution_directory']).exists()
        validated.append((entry,native,op,native_dir,op_dir,release))
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);u.lifecycle_protection(b)
        work=u.read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==145
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'])
        now=datetime.now(timezone.utc).isoformat();before_work_sha256=sha(ROOT/'pipeline/research_work.json')
        release_plan=[]
        for entry,native,op,native_dir,op_dir,release in validated:
            release_ref={'path':(op_dir/'adapter_release.json').relative_to(ROOT).as_posix(),'sha256':sha(op_dir/'release_template.json')}
            release_plan.append((op_dir,release_ref))
            c=next(c for c in work['candidates'] if c['id']==entry['id'])
            if c['id']==u.HPC:
                assert c['code_commit']=='2f7eff19ca59cc4586e13ca81a547a18ea7e313d'
                c.setdefault('source_version_history',[]).append({
                    'recorded_at':now,'code_commit':c['code_commit'],'source_commit':c.get('source_commit'),
                    'source_parent_commit':c.get('source_parent_commit'),'source_version':copy.deepcopy(c.get('source_version')),
                    'actual_source_version_independent_review':copy.deepcopy(c.get('actual_source_version_independent_review')),
                    'scope':'Original old2f7/parent56 source and all raw failures retained; new version is exactsame9 source compatible with actuald585, no model revision or native retest.'})
            for field in ('worker_preparation','execution_adapter','current_version_compatibility'):
                if c.get(field):c.setdefault(field+'_history',[]).append(copy.deepcopy(c[field]))
            c.update(code_commit=entry['code_commit'],source_commit=entry['code_commit'],source_parent_commit=u.SOURCE,
                     source_version=entry['source_version'],actual_source_version_independent_review=entry['source_review'],
                     stage='validation',source_status='ISOLATED_SOURCE_AND_CURRENT_PARENT_COMPATIBLE_STATIC_TOOLS_NOT_PROMOTED',
                     native_status='NOT_RUN_FOR_CURRENT_SOURCE_PACKET',resource_status='NOT_RUN_FOR_CURRENT_SOURCE_PACKET',
                     native_execution_code_commit=None,queued=False)
            c['worker_preparation']={
                'status':'STATIC_REVIEWED_NATIVE_NOT_RUN','preparation':entry['native_preparation'],
                'worker':u.ref(native_dir/'worker.py'),'runtime':u.ref(native_dir/'native_runtime.py'),
                'manifest_template':u.ref(native_dir/'manifest_template.json'),
                'source_commit':entry['code_commit'],'source_parent_commit':u.SOURCE,'runtime_expected_commit':u.SOURCE,
                'independent_review':entry['native_review'],'native_backward_executed':False,
                'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False}
            c['execution_adapter']={
                'status':'STATIC_REVIEWED_CATALOGUE_ONLY_NATIVE_NOT_RUN','preparation':entry['operational_preparation'],
                'release':release_ref,'independent_review':entry['operational_review'],
                'active_binding_manifest_lease_created':False,'transport_executed':False}
            c['current_version_compatibility']={
                'current_source_commit':entry['code_commit'],'current_parent_commit':u.SOURCE,
                'current_primary_and_runtime':u.SOURCE,'source_version':entry['source_version'],
                'status':'CURRENT_PARENT_COMPATIBLE_ISOLATED_SOURCE_AND_REVIEWED_STATIC_TOOLS',
                'scope':'Source-only and static tool readiness. Current primary/runtime unchanged, native/resources for this source packet NOT_RUN. Old NULL/reference and previous source/native failures retained.'}
            c['implementation_status']='SOURCE_AND_NATIVE_OPERATIONAL_OBSERVERS_STATIC_REVIEWED_WAITING_ACTUAL_NATIVE'
            c['next_action']='Use a future fresh actual owner/original deadline and genuinely idle authorized server4GPU0 for original paired two natural TRAIN steps and original resource arms. Current original CRE118189 must continue; GPU1 prohibited. Preserve all historical failures; no borrowed PASS, replay, model tuning, receipt or queue before actual gates.'
            for item in entry['evidence']+[release_ref]:
                if item not in c['evidence']:c['evidence'].append(item)
        work['updated_at']=now;work['last_event_tick']=EXPECTED['generated_at']
        work['next_action']='Monitor original M217-CRE PID118189/source d585 on sole server4GPU0. HPC6282 and APFbf6 now have reviewed current-parent static native/op packets; when an authorized slot really opens, execute HPC original pairedTRAIN2/resources first, then APF. No model efficacy or native PASS from software preparation.'
        assert len(work['candidates'])==145 and {c['id'] for c in work['candidates']}==set(b['candidate_digests'])
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in {u.HPC,u.APF})
        json.dumps(work,ensure_ascii=False,indent=2,allow_nan=False)
        u.primary_protection(b);u.lifecycle_protection(b);assert sha(ROOT/'pipeline/research_work.json')==before_work_sha256
        u.save(HERE/'preparation_registration_intent.json',{
            'recorded_at':now,'owner':EXPECTED,'catalogue':u.ref(HERE/'packet_catalogue.json'),
            'program':u.ref(__file__),'before_work_sha256':before_work_sha256,
            'before_primary_index_sha256':b['index_sha256'],'prepared_after_work_digest':u.digest(work),
            'scope':'Only existing HPC compatible source metadata and APF/HPC reviewed static tool registration. All full record composition/serialization and 143 unchanged candidate digests verified first. Two bytecopy static releases, not execution leases. Zero new candidates, revisions, native commands, receipts, queue or launch.'})
        for op_dir,release_ref in release_plan:
            guard()
            with (op_dir/'adapter_release.json').open('xb') as f:f.write((op_dir/'release_template.json').read_bytes())
            assert sha(op_dir/'adapter_release.json')==release_ref['sha256']
        guard();assert sha(ROOT/'pipeline/research_work.json')==before_work_sha256
        u.atomic(ROOT/'pipeline/research_work.json',work)
        u.primary_protection(b);u.lifecycle_protection(b)
        after=u.read(ROOT/'pipeline/research_work.json')
        changed=[c['id'] for c in after['candidates'] if u.digest(c)!=b['candidate_digests'][c['id']]]
        assert set(changed)=={u.HPC,u.APF} and len(after['candidates'])==145
        u.save(HERE/'preparation_registration_result.json',{
            'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,
            'changed_existing_candidates':changed,'candidate_count':145,'new_candidates':0,
            'model_revisions':0,'new_native_commands':0,'new_admissions_or_queue_or_launches':0,
            'primary_index_source28_and_18_lifecycle_ledgers_unchanged':True,
            'catalogue':u.ref(HERE/'packet_catalogue.json'),'new_work_sha256':sha(ROOT/'pipeline/research_work.json')})
        print(json.dumps({'updated':changed,'candidate_count':145,'native_commands':0}))
    finally:lock.close()
if __name__=='__main__':main()
