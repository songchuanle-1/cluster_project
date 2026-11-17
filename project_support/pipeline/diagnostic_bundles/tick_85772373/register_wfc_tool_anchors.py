"""Root-only static tool registration and local guard integration; no transport."""
from pathlib import Path
from datetime import datetime, timezone
import copy, importlib.util, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
CID='hierarchy-wedge-factor-incidence-composition'

def main():
    guard();assert sys.dont_write_bytecode
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        baseline=u.read(HERE/'protected_assets_before.json')
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        nativepath=HERE/'wfc_native_activation_prepare/preparation.json'
        oppath=HERE/'wfc_operational_prepare/preparation.json'
        peerpath=HERE/'wfc_operational_independent_review.json'
        releasepath=HERE/'wfc_operational_prepare/adapter_release.json'
        native,op,peer=u.read(nativepath),u.read(oppath),u.read(peerpath)
        assert sha(nativepath)=='07a019fbbf60ebc3ac16d982b058af282290dd5a10b0b0ae0fa65f4ac582bbd8'
        assert sha(oppath)=='30d304e59fd6e5caa0858cb5bd10329560e2233e5d9731b2221a2b3e2902643d'
        assert peer['candidate_id']==CID and peer['material_concerns']==[]
        assert peer['anchors']['native_preparation']==u.ref(nativepath)
        assert peer['anchors']['operational_preparation']==u.ref(oppath)
        u.check_refs(list(peer['anchors'].values()))
        for folder,prep in [(nativepath.parent,native),(oppath.parent,op)]:
            assert prep['candidate_id']==CID and prep['code_commit']=='94c4fe61b38f46f321a7ee84236fea70ade04d9b'
            assert prep['operational_ready'] is False
            for n,h in prep['prepared_file_hashes'].items():assert sha(folder/n)==h,n
        assert sha(releasepath)==sha(oppath.parent/'release_template.json')
        registration=u.read(HERE/'wfc_static_release_registration_prepare/registration_result.json')
        assert registration['release']==u.ref(releasepath) and registration['active_binding_created'] is False
        workpath=ROOT/'pipeline/research_work.json';before=sha(workpath);work=u.read(workpath)
        candidate=next(c for c in work['candidates'] if c['id']==CID)
        assert candidate['stage']=='validation' and candidate['queued'] is False
        others={c['id']:u.digest(c) for c in work['candidates'] if c['id']!=CID}
        assert len(others)==152
        u.check_refs([native['isolated_source_version'],native['source_preparation'],native['native_protocol']])
        version=u.read(ROOT/native['isolated_source_version']['path'])
        prototype=u.read(ROOT/native['source_preparation']['path'])
        assert version['candidate_id']==CID and version['code_commit']==native['code_commit']
        assert version['parent_commit']==u.SOURCE and version['diff_exact9A']
        assert version['frozen_source_files']==version['committed_blob_sha256']==native['source_files']==prototype['source_files']
        assert all(prototype[k] is None for k in ('code_commit','source_commit','source_parent_commit'))
        assert candidate.get('code_commit') in (None,native['code_commit'])
        candidate.update(code_commit=version['code_commit'],source_commit=version['code_commit'],source_parent_commit=version['parent_commit'],source_version=native['isolated_source_version'],source_version_status='ISOLATED_LOCAL_EXACT9A_ONLY_NATIVE_UNTESTED_PRIMARY_RUNTIME_UNCHANGED')
        candidate.setdefault('native_tool_preparation_history',[]).append({k:copy.deepcopy(candidate.get(k)) for k in ('native_tool_preparation','native_tool_preparation_review','native_tool_status')})
        candidate['native_tool_preparation']=u.ref(nativepath)
        candidate['native_tool_preparation_review']=u.ref(peerpath)
        candidate['native_tool_status']='STATIC_CAPABILITY_REGISTERED_NO_ACTIVE_MANIFEST_LEASE_OR_NATIVE_RESULT'
        candidate['worker_preparation']={'preparation':u.ref(nativepath),'independent_review':u.ref(peerpath),'status':'STATIC_ONLY_NATIVE_NOT_RUN'}
        candidate['execution_adapter']={'preparation':u.ref(oppath),'release':u.ref(releasepath),'independent_review':u.ref(peerpath),'selected_physical_GPU_capability':[0],'status':'STATIC_REGISTERED_NO_ACTIVE_BINDING_OR_EXECUTION'}
        refs=[u.ref(nativepath),u.ref(oppath),u.ref(peerpath),u.ref(releasepath),native['static_validation'],op['metadata_validation'],u.ref(HERE/'wfc_static_release_registration_prepare/registration_result.json'),native['isolated_source_version'],native['source_preparation'],native['native_protocol']]
        for entry in refs:
            if entry not in candidate['evidence']:candidate['evidence'].append(entry)
        candidate['next_action']='Static physicalGPU0 native capability and adapter/release are registered; no active binding or native result. First check current real GPU occupation and actual main18e/source94 compatibility. When selectedGPU0 is genuinely idle, use the registered defaultNOP root launcher with a fresh current owner/manifest/lease and three locks, execute original paired TRAIN2/resources, then independently review before admission/promotion/queue. If GPU1 opens first, preserve this GPU0 package and prepare an actually reviewed physicalGPU1 operational adaptation without model/protocol changes.'
        intent=HERE/'wfc_tool_registration_intent.json';resultpath=HERE/'wfc_tool_registration_result.json'
        assert not intent.exists() and not resultpath.exists()
        u.save(intent,dict(owner=EXPECTED,recorded_at=datetime.now(timezone.utc).isoformat(),work_before_sha256=before,other152_digests=others,static_refs=refs,scope='WFC exact static anchors plus real local guard integration only. No prepare/stage/run/probe/status/SSH/GPU/native/activebinding/source/lifecycle changes.'))
        guard();assert sha(workpath)==before
        u.atomic(workpath,work)
        registered_sha=sha(workpath)
        integration={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'native': 'NOT_RUN','resources':'NOT_RUN','remote_transport':False,'active_binding_created':False,'scope':'Actual registered adapter guard/candidate/parent-receipt local read-only integration; local occupation refusal is not a new physical GPU observation.'}
        try:
            spec=importlib.util.spec_from_file_location('wfc_registered_guard',oppath.parent/'adapter.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            class NoTransport:
                def call(self,*args,**kwargs):raise AssertionError('Transport is prohibited in this local guard integration.')
            adapter=module.Adapter(transport=NoTransport())
            observed=adapter.guard(0,0,mutation=True)
            assert {k:observed['owner'][k] for k in EXPECTED}==EXPECTED
            integration['registered_current_guard_passed']=True
            try:
                adapter._local_idle(0)
                integration['local_registered_slot']='NO_RUNNING_OR_PENDING_RESERVATION; RECHECK_PHYSICAL_BEFORE_ANY_COMPUTE'
            except module.Refused as e:
                integration['local_registered_slot']='REFUSED_BUSY'
                integration['local_busy_refusal']=str(e)
            integration['status']='LOCAL_REGISTERED_GUARD_INTEGRATION_PASSED_NATIVE_NOT_RUN'
        except Exception as e:
            integration.update(status='LOCAL_GUARD_INTEGRATION_FAILED_NATIVE_NOT_RUN',exception_type=type(e).__name__,exception=str(e))
            candidate['native_tool_status']='STATIC_REGISTERED_LOCAL_GUARD_FAILURE_REQUIRES_SCOPED_REPAIR'
        assert sha(workpath)==registered_sha
        integrationpath=HERE/'wfc_registered_guard_integration.json';u.save(integrationpath,integration)
        candidate['evidence'].append(u.ref(integrationpath));candidate['registered_guard_integration']=u.ref(integrationpath)
        assert {c['id']:u.digest(c) for c in work['candidates'] if c['id']!=CID}==others
        u.atomic(workpath,work)
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        u.save(resultpath,dict(owner=EXPECTED,recorded_at=datetime.now(timezone.utc).isoformat(),work_after_sha256=sha(workpath),candidate_after_sha256=u.digest(candidate),other152_unchanged=True,primary_index_user28_all34_lifecycle_unchanged=True,static_refs=refs,integration=u.ref(integrationpath),integration_status=integration['status'],active_binding_created=False,native_resources_remote_queue_launch='NOT_RUN'))
        print(json.dumps(dict(result=u.ref(resultpath),integration_status=integration['status'],local_registered_slot=integration.get('local_registered_slot'))))
    finally:lock.close()

if __name__=='__main__':main()
