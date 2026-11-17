"""Read-only PSBR adapter port checks; --write requires current parent tick.

No owner impersonation, SSH, remote process, torch, GPU or live binding creation.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

import adapter


OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[3]
OLD = PROJECT / 'pipeline/diagnostic_bundles/tick_9b40ab74/hrc_execution_adapter'
NATIVE = OUT.parent / 'psbr_native_prepare'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NeverTransport:
    def call(self, *args, **kwargs):
        raise AssertionError('Static checking must never call transport')


def write_guard():
    owner = json.loads((PROJECT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
    assert owner['token'] == '8fafa3d4ebcb48e7ba3436e084f6ee9f'
    assert owner['thread_id'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
    assert owner['deadline_at'] == '2026-10-22T03:12:05.347438+00:00'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    for relative,key in [('pipeline/headless/.tick_context.json','context_sha256'),
                         ('pipeline/headless/.tick_context_state.next.json','pending_sha256')]:
        assert sha(PROJECT / relative) == owner[key]
    mode=json.loads((PROJECT / 'pipeline/execution_mode.json').read_text(encoding='utf-8'))
    assert mode['mode']=='foreground' and mode['target_thread_id']==owner['thread_id']
    assert sha(PROJECT / 'pipeline/goal.json')==adapter.GOAL


def main(write=False):
    checks={}

    def check(name,condition):
        checks[name]=bool(condition)
        assert condition,name

    provenance=json.loads((OUT/'port_provenance.json').read_text(encoding='utf-8'))
    for name,expected in provenance['source_sha256'].items():
        check('old_frozen_unchanged_'+name,sha(OLD/name)==expected)
    for name,transforms in provenance['source_transformations'].items():
        old=(OLD/name).read_text(encoding='utf-8')
        expected=old
        for transform in transforms:
            check('replacement_count_'+name+'_'+str(transforms.index(transform)),expected.count(transform['from'])==transform['count'])
            expected=expected.replace(transform['from'],transform['to'])
        actual=(OUT/name).read_text(encoding='utf-8')
        check('exact_constant_path_only_text_'+name,actual==expected)
        check('exact_transformed_ast_'+name,ast.dump(ast.parse(actual),include_attributes=False)==ast.dump(ast.parse(expected),include_attributes=False))
    check('no_logic_changes_in_port',provenance['logic_changes']==[])
    program=adapter.Adapter(origin=OUT,transport=NeverTransport())
    release=program._release_details()
    preparation,template=program._frozen_details()
    check('new_native_preparation_exact',sha(NATIVE/'preparation.json')==adapter.PREPARATION_SHA=='1e1de105f34ce4f6f87fe862bf35ee2c7c0bf26bf7404b0550559534a0e7472e')
    check('new_native_template_exact',sha(NATIVE/'manifest_template.json')==adapter.TEMPLATE_SHA=='f90e2662cb188b838ff7e6d6b60179529a983d91a32cb06187262aee70267263')
    check('new_worker_runtime_exact',sha(NATIVE/'worker.py')==release['frozen_worker_sha256']=='05ab6ac1f72f804bf9799e6b6a95127057d330d13302686740cb1acb94343385' and sha(NATIVE/'native_runtime.py')==release['frozen_runtime_sha256']=='b6698c77ef9956c2d7381fb99164cdbf1d1f4905c13f59d04c6b9778e2bf8e67')
    check('candidate_commit_identity_exact',adapter.CANDIDATE==release['candidate_id']==preparation['candidate_id']=='hierarchy-parent-segmented-bidirectional-token-state' and adapter.COMMIT==release['source_commit']==preparation['source_commit']=='74fcd21df0af9a971792038ffe251af1ffea2604' and release['experiment_id']=='M209-PSBR')
    check('config_and_package_psbr_exact',template['candidate_name'].endswith('_ctf_hcg_csort_psbr') and template['config']=='configs/Quard/ctf_hcg_csort_psbr/'+template['candidate_name']+'.yaml')
    for path in OUT.glob('*.py'):
        text=path.read_text(encoding='utf-8')
        ast.parse(text,filename=str(path));compile(text,str(path),'exec')
    check('all_current_python_syntax_compiled_without_execution',True)
    for name in ['execution_binding.json','native_manifest.json','execution_lease.json','stage_request.json']:
        check('no_live_artifact_'+name,not list(OUT.rglob(name)))
    check('template_execution_fields_null',all(template[key] is None for key in ['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']))
    check('release_no_formatter_admission_or_execution',release['formatter_implemented'] is False and release['admission_implemented'] is False and release['native_execution']=='NOT_RUN' and release['remote_execution']=='NOT_RUN')
    protected=json.loads((OUT.parent/'psbr_prepare/source_inventory.json').read_text(encoding='utf-8'))['protected_before']
    check('preexisting_28_dirty_files_unchanged',len(protected)==28 and all(sha(PROJECT/'Cluster'/name)==value for name,value in protected.items()))
    check('torch_not_imported', 'torch' not in sys.modules)
    result={'schema_version':1,'status':'STATIC_CONSTANT_PATH_PORT_PASS_NOT_NATIVE_ADMISSION',
        'candidate_id':adapter.CANDIDATE,'experiment_id':'M209-PSBR','source_commit':adapter.COMMIT,
        'checked_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,
        'source_hashes':release['source_hashes'],'adapter_release_sha256':sha(OUT/'adapter_release.json'),
        'port_provenance_sha256':sha(OUT/'port_provenance.json'),
        'native_preparation_sha256':sha(NATIVE/'preparation.json'),
        'native_template_sha256':sha(NATIVE/'manifest_template.json'),
        'validate_static_sha256':sha(Path(__file__)),
        'external_review_and_candidate_anchor_required':True,
        'current_owner_guard_integration':'NOT_PERFORMED_BY_CHILD; actual owning root must separately verify',
        'production_active_bindings_created':False,'ssh_executed':False,'gpu_executed':False,
        'native_executed':False,'torch_imported':False,'formatter_implemented':False,'admission_ready':False}
    if write:
        write_guard()
        (OUT/'static_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    main(parser.parse_args().write)
