"""Default NOP; root-only exact static release copy after an actual external peer.

This never registers shared candidate anchors or creates execution material.
The adapter still refuses until root separately installs its exact external
candidate preparation/release anchors under the canonical project contract.
"""
from pathlib import Path
import argparse, hashlib, json, re, sys

HERE=Path(__file__).resolve().parent
TICK=HERE.parent
ROOT=TICK.parents[2]
OP=TICK/'wfc_operational_prepare'
NATIVE=TICK/'wfc_native_activation_prepare'
CID='hierarchy-wedge-factor-incidence-composition'
COMMIT='94c4fe61b38f46f321a7ee84236fea70ade04d9b'
PARENT='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
NATIVE_SHA='07a019fbbf60ebc3ac16d982b058af282290dd5a10b0b0ae0fa65f4ac582bbd8'
OP_SHA='30d304e59fd6e5caa0858cb5bd10329560e2233e5d9731b2221a2b3e2902643d'
RELEASE_SHA='bf2a88fd27f7bb0aa713ad697cb242ff702b03b05dccfb5eea34cd92acab89a1'
ACTIVE=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute-root',action='store_true')
    p.add_argument('--peer')
    p.add_argument('--peer-sha256')
    args=p.parse_args()
    if not args.execute_root:
        print(json.dumps(dict(status='DEFAULT_NOP_NO_RELEASE_OR_ENTRY_CREATED',candidate_id=CID,code_commit=COMMIT,active_binding_created=False,native_executed=False)))
        return
    assert sys.dont_write_bytecode
    assert args.peer and re.fullmatch(r'[0-9a-f]{64}',args.peer_sha256 or '')
    sys.path.insert(0,str(TICK))
    from anchor import EXPECTED, guard
    import record_utils as u
    guard()
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();baseline=read(TICK/'protected_assets_before.json')
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        peerpath=Path(args.peer)
        if not peerpath.is_absolute():peerpath=ROOT/peerpath
        peerpath=peerpath.resolve();assert peerpath.is_relative_to(TICK)
        assert sha(peerpath)==args.peer_sha256
        peer=read(peerpath)
        assert peer['candidate_id']==CID and peer['code_commit']==COMMIT and peer['material_concerns']==[]
        assert peer.get('metadata_blockers',[])==[]
        assert peer['anchors']['native_preparation']==ref(NATIVE/'preparation.json')
        assert peer['anchors']['operational_preparation']==ref(OP/'preparation.json')
        u.check_refs(list(peer['anchors'].values()))
        assert sha(NATIVE/'preparation.json')==NATIVE_SHA and sha(OP/'preparation.json')==OP_SHA
        native=read(NATIVE/'preparation.json');op=read(OP/'preparation.json')
        for directory,prep in [(NATIVE,native),(OP,op)]:
            assert prep['candidate_id']==CID and prep['code_commit']==COMMIT and prep['source_parent_commit']==PARENT
            assert prep['draft_execution_disabled'] is False and prep['operational_ready'] is False
            for name,h in prep['prepared_file_hashes'].items():
                target=(directory/name).resolve();assert target.is_relative_to(directory) and sha(target)==h,name
        assert op['native_preparation']==ref(NATIVE/'preparation.json')
        assert op['native_manifest_template']==ref(NATIVE/'manifest_template.json')
        assert op['native_source_version_binding']==ref(NATIVE/'source_version_binding.json')
        manifest=read(NATIVE/'manifest_template.json')
        assert all(manifest[k] is None for k in ACTIVE)
        assert manifest['draft_execution_disabled'] is False
        assert manifest['code_commit']==COMMIT and manifest['runtime_expected_commit']==PARENT
        template=OP/'release_template.json';assert sha(template)==RELEASE_SHA
        release=read(template)
        assert release['candidate_id']==CID and release['experiment_id']=='M226-WFC' and release['code_commit']==COMMIT
        assert release['native_preparation_sha256']==NATIVE_SHA
        assert release['manifest_template_sha256']==sha(NATIVE/'manifest_template.json')
        assert release['source_version_binding_sha256']==sha(NATIVE/'source_version_binding.json')
        assert set(release['source_hashes'])=={'adapter.py','remote_ops.py'}
        assert all(sha(OP/n)==h for n,h in release['source_hashes'].items())
        assert release['explicit_selected_physical_GPU_capability']==[0]
        assert release['resource_policy']['live_allowed_gpus']==[0,1]
        assert release['conditional_parent_promotion']['expected_primary_HEAD']==PARENT
        assert release['conditional_parent_promotion']['required_technical_receipt']=='pipeline/admissions/M225-ELC.json'
        assert release['conditional_parent_promotion']['training_completion_or_effect_requirement'] is False
        assert release['conditional_parent_promotion']['applies_to_mutations_only'] is True
        for directory in (NATIVE,OP):
            assert not any((directory/n).exists() for n in ('native_manifest.json','execution_lease.json','execution_binding.json'))
        target=OP/'adapter_release.json'
        intent=HERE/'registration_intent.json';result=HERE/'registration_result.json'
        assert not any(x.exists() for x in (target,intent,result)),'Existing original static-copy attempt; inspect it, never replay.'
        before={'work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
        u.save(intent,dict(owner=EXPECTED,peer=ref(peerpath),native_preparation=ref(NATIVE/'preparation.json'),operational_preparation=ref(OP/'preparation.json'),release_template=ref(template),protected_baseline=ref(TICK/'protected_assets_before.json'),before=before,scope='Only exact static release file copy; no shared anchor registration or active manifest/lease/remote/native/admission/queue.'))
        guard();assert before=={'work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        data=template.read_bytes();assert hashlib.sha256(data).hexdigest()==RELEASE_SHA
        with target.open('xb') as f:f.write(data)
        assert target.read_bytes()==data and sha(target)==RELEASE_SHA
        guard();u.primary_protection(baseline);u.lifecycle_protection(baseline)
        assert before=={'work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
        u.save(result,dict(owner=EXPECTED,status='EXACT_STATIC_RELEASE_CREATED_NOT_EXECUTION_OR_OPERATIONAL_READINESS',candidate_id=CID,code_commit=COMMIT,independent_review=ref(peerpath),release=ref(target),template=ref(template),native_preparation=ref(NATIVE/'preparation.json'),operational_preparation=ref(OP/'preparation.json'),primary_index_user28_all34_lifecycle_and_whole_work_memory_unchanged=True,shared_candidate_anchors_written=False,active_binding_created=False,remote_transport=False,native_executed=False,new_admissions=0,new_queue_entries=0,new_launches=0))
        print(json.dumps(dict(result=ref(result),release=ref(target),shared_candidate_anchor_registration_still_required=True),indent=2))
    finally:lock.close()

if __name__=='__main__':main()
