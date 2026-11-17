"""One bounded fresh native readiness recheck after current complete CPU prefix control."""
from pathlib import Path
from datetime import datetime,timezone
import json
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
guard();p=HERE/'import_order_prepare/import_order_actual_result.json'
assert sha(p)=='b4969bf06fe29f6bd751cb4f815efd09ced323ea488831ce8a4e2028ff66080d'
r=json.loads(p.read_text('utf8'));assert r['owner']==EXPECTED and r['returncode']==0
assert len(r['observation']['conditions'])==2
for c in r['observation']['conditions']:
    assert c['returncode']==0 and c['observation']['status']=='COMPLETE_PCCM_REAL_TRANSFORMER_AND_GORILLA_TORCH_CPU_IMPORT_PASSED'
    assert c['observation']['actual_original_parser']['real_AttrArgTransformer_instance'] is True and c['observation']['policy_denials']==[]
out={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'candidate_id':'hierarchy-cross-root-directed-edge-broadcast','code_commit':'d58576b396cfb54577652be972f3ffaffda508c9','original_failed_request':'f11717294d4f4e82b66daa065b58c2ee','original_failed_evidence':{'path':'pipeline/diagnostic_bundles/tick_0f02aaa2/cre_execution/smoke_champion_execution.json','sha256':'998c15df671d2e12c0b8a2ce741f9fb35011e425c77683d192c817201d97081c'},'fresh_current_CPU_control':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)},'new_initial_control_attempt_limit':1,'candidate_model_or_worker_or_runtime_or_dependency_change':False,'native_seed_data_YAML_schedule_unchanged':True,'root_cause':'UNKNOWN','scope':'Current complete original dependency prefix is now observed in both fixed CPU orders; this supports a bounded fresh native readiness check, not a proven repair. CPU private caches/startup hashseed are not silently copied into the original native worker. New token/new stage/new request/fresh actual slot+UUID+three locks required. Preserve all old failed raws. Nonzero or uncertain original request is reconciled, never replayed; no remaining arm before actual control success. Four real native/resources results still required for admission.'}
guard()
with (HERE/'cre_readiness_retest_plan.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print('Bounded current native readiness recheck preregistered; no GPU worker started.')
