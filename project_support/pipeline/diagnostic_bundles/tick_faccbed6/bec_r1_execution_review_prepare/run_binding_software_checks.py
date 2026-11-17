"""Minimal R1 binding regression checks; all populated inputs SYNTHETIC SOFTWARE ONLY."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
ORIGINAL=ROOT/'pipeline/diagnostic_bundles/tick_521a6f59/bec_execution_review_prepare/review_bec.py'
CHECKER=HERE/'review_bec_r1.py'
SCIENTIFIC=['need','finite','digest','read','hash_string','tensor','gradients','common','named_hashes','resources','plan_metadata','bec_record','required_weight_blocks','smoke','review_payloads']
REF_SHA='1aace484d376493d4a1eb53bbfb04771117e3476eef3b6e8fdeff2f66588418a'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def obj(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def main():
    events=[]
    def audit(name,args):
        if name.startswith(('subprocess.','socket.')) or name in ('os.system','os.posix_spawn','os.exec','os.fork'):
            events.append(name)
            raise RuntimeError('Software check forbids subprocess/network: '+name)
    sys.addaudithook(audit)
    checks=[]
    def yes(label,value):
        if not value:raise AssertionError(label)
        checks.append({'name':label,'outcome':'PASS_SOFTWARE_ONLY'})
    def refused(label,call,contains=None):
        try:call()
        except (ValueError,KeyError,OSError,TypeError) as e:
            if contains is not None and contains not in str(e):raise AssertionError((label,type(e).__name__,str(e)))
            checks.append({'name':label,'outcome':'REFUSED_AS_EXPECTED','error_type':type(e).__name__,'error':str(e)[:240]})
        else:raise AssertionError(label+' unexpectedly accepted')
    yes('frozen_original_checker_sha',sha(ORIGINAL)==REF_SHA)
    old=ast.parse(ORIGINAL.read_text(encoding='utf-8'));new=ast.parse(CHECKER.read_text(encoding='utf-8'))
    functions=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    a,b=functions(old),functions(new)
    for name in SCIENTIFIC:yes('original_AST_exact_'+name,a[name]==b[name])
    compile(new,str(CHECKER),'exec')
    spec=importlib.util.spec_from_file_location('private_bec_r1_result_checker_software',CHECKER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    yes('R1_scientific_source_runtime_identity_distinct',module.COMMIT=='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563' and module.RUNTIME_EXPECTED=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d')
    yes('only_physical_GPU0_catalog',module.UUIDS=={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'})
    yes('frozen_contract_actual_hash',module.hash_string(module.CONTRACT_SHA) and sha(HERE/'external_packet_contract.json')==module.CONTRACT_SHA)
    contract=obj(HERE/'external_packet_contract.json')
    registration=obj(ROOT/contract['revision_preregistration']['path'])['preregistration']
    candidate={'revision_history':[copy.deepcopy(registration)]}
    expected=module.revision_lineage(ROOT,candidate,contract)
    yes('immutable_prereg_pending_accepted',len(expected)==4)
    candidate['revision_history'][0]['result']='passed'
    candidate['revision_history'][0]['evidence']=[{'path':'SYNTHETIC_MUTABLE_NEW_RESULT_NOT_A_REAL_RESULT','sha256':'0'*64}]
    yes('mutable_passed_result_and_evidence_do_not_reject_raw_review',module.revision_lineage(ROOT,candidate,contract)==expected)
    changed=copy.deepcopy(candidate);changed['revision_history'][0]['change']='SYNTHETIC_UNPREREGISTERED_CHANGE'
    refused('immutable_prereg_change_rejected',lambda:module.revision_lineage(ROOT,changed,contract),'R1 immutable registration field changed')
    refused('missing_R1_prereg_rejected',lambda:module.revision_lineage(ROOT,{'revision_history':[]},contract),'Exactly one immutable')
    malformed=copy.deepcopy(candidate);malformed['revision_history'][0]['revision']=True
    refused('bool_revision_cannot_alias_integer_R1',lambda:module.revision_lineage(ROOT,malformed,contract),'Exactly one immutable')
    doubled=copy.deepcopy(candidate);doubled['revision_history']*=2
    refused('duplicate_R1_prereg_rejected',lambda:module.revision_lineage(ROOT,doubled,contract),'Exactly one immutable')
    wrong=copy.deepcopy(contract);wrong['source_version']['sha256']='0'*64
    refused('wrong_version617_anchor_rejected',lambda:module.revision_lineage(ROOT,candidate,wrong),'Immutable R1 provenance changed')
    wrong=copy.deepcopy(contract);wrong['revision_source_preparation']['sha256']='0'*64
    refused('wrong_R1_source2ef_anchor_rejected',lambda:module.revision_lineage(ROOT,candidate,wrong),'Immutable R1 provenance changed')
    refused('missing_four_actual_results_rejected',lambda:module.review_payloads({},{}),'Exactly four actual raw JSON objects')
    oldraw={'execution_completed':True,'mode':'smoke','target':'candidate','candidate_id':module.CID,'code_commit':'9b6782f44ca7f2c8ac35baea01dfd070314b5701','goal_sha256':module.GOAL}
    refused('old_R0_9b_raw_cannot_be_relabelled_R1',lambda:module.common(oldraw,{},'smoke','candidate'),'Raw identity/mode/target mismatch')
    manifest={'candidate_id':module.CID,'code_commit':module.COMMIT,'goal_sha256':module.GOAL,'config':module.CONFIG,'experiment_id':module.EID,'tolerance':1e-6,'runtime_code_commit':module.RUNTIME_EXPECTED,'runtime_expected_commit':module.RUNTIME_EXPECTED,'source_parent_commit':module.RUNTIME_EXPECTED,'source_version_commit':module.COMMIT,'source_preparation_sha256':module.SOURCE_PREP_SHA,'candidate_config_sha256':module.YAML_SHA,'diagnostic_files':{'worker.py':module.WORKER_SHA},'physical_gpu':1,'gpu_uuid':'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
    refused('GPU1_result_rejected_before_scientific_results',lambda:module.review_payloads({m+'_'+t:{} for m,t in module.PAIRS},manifest),'Selected authorized physical GPU/UUID mismatch')
    with tempfile.TemporaryDirectory(prefix='software_empty_fixture_',dir=HERE) as td:
        yes('temporary_empty_fixture_contained_in_private_packet',Path(td).resolve().is_relative_to(HERE.resolve()))
        refused('empty_directory_no_binding_no_four_results_rejected',lambda:module._review_directory_bound(ROOT,td))
    lineage=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='revision_lineage')
    yes('no_mutable_result_evidence_gate_in_lineage_AST',not any(isinstance(n,ast.Constant) and n.value in ('result','evidence') for n in ast.walk(lineage)))
    yes('no_Torch_import',not any(n=='torch' or n.startswith('torch.') for n in sys.modules))
    yes('no_process_or_network_audit_events',events==[])
    result={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'MINIMAL_R1_BINDING_SOFTWARE_CHECKS_PASSED_NOT_NATIVE','candidate_id':module.CID,'code_commit':module.COMMIT,'fixture_scope':'All populated raw/manifest/candidate modifications are SYNTHETIC SOFTWARE ONLY in memory. No synthetic actual execution/request/lease/result files were written. Actual immutable provenance files are hash-checked as provenance only.','checker_sha256':sha(CHECKER),'checker_reference_sha256':REF_SHA,'contract_sha256':sha(HERE/'external_packet_contract.json'),'test_source_sha256':sha(__file__),'scientific_functions_AST_exact':SCIENTIFIC,'checks':checks,'check_count':len(checks),'failures':0,'subprocess_network_audit_events':events,'torch_imported':False,'actual_R1_native_TRAIN2':'NOT_RUN','actual_R1_resources':'NOT_RUN','standard_PASS_receipt_queue_or_active_execution_created':False}
    output=HERE/'minimal_binding_software_validation.json'
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'checks':len(checks),'sha256':sha(output),'output':str(output)}))

if __name__=='__main__':main()
