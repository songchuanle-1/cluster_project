"""Persist the reconciled failed original native request, without replay or model changes."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    guard();rawp=HERE/'cre_execution/smoke_champion_execution.json';raw=read(rawp)
    assert sha(rawp)=='998c15df671d2e12c0b8a2ce741f9fb35011e425c77683d192c817201d97081c'
    assert raw['certainty']=='terminal' and raw['returncode']==1 and raw['identity']['request_id']=='f11717294d4f4e82b66daa065b58c2ee'
    assert raw['result']['optimizer_steps']==raw['result']['native_loss_forwards']==raw['result']['native_criterion_backwards']==0
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();work=read(ROOT/'pipeline/research_work.json');cre=next(c for c in work['candidates'] if c['id']=='hierarchy-cross-root-directed-edge-broadcast')
        assert cre['stage']=='validation' and cre['code_commit']=='d58576b396cfb54577652be972f3ffaffda508c9'
        intent=HERE/'cre_failure_record_intent.json';assert not intent.exists()
        now=datetime.now(timezone.utc).isoformat()
        with intent.open('x',encoding='utf8') as f:json.dump({'recorded_at':now,'owner':EXPECTED,'research_before_sha256':sha(ROOT/'pipeline/research_work.json'),'candidate_before':copy.deepcopy(cre),'scope':'Record actual first native failure and ongoing diagnosis; no scientific/model revision or gate PASS.'},f,ensure_ascii=False,indent=2);f.write('\n')
        cre.setdefault('native_check_history',[]).append({'recorded_at':now,'prior_current_native_check':copy.deepcopy(cre.get('current_native_check'))})
        cre['current_native_check']={'recorded_at':now,'kind':'native_smoke','result':'failed','target':'champion','optimizer_steps':0,'native_loss_forwards':0,'native_criterion_backwards':0,'request_id':raw['identity']['request_id'],'evidence':ref(rawp),'failure_scope':'dependency_import_before_model_construction','error_type':'TypeError','error':"'list' object is not callable",'root_cause':'UNKNOWN; CPU import/code provenance diagnosis in progress','model_revision_created':False,'remaining_three_arms':'NOT_RUN','scope':'Original M95 dependency import failed before CRE model execution; not a CRE mechanism or resource-budget refutation.'}
        cre.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(cre.get('resource_check')),'prior_current_resource_check':copy.deepcopy(cre.get('current_resource_check'))})
        cre['current_resource_check']={'recorded_at':now,'result':'not_the_current_blocker','physical_gpu':0,'hardware_evidence':ref(HERE/'aef_end_and_slot_observation.json'),'scope':'Physical0 idle at separately recorded16:12 observation; failed request subsequently terminal/reconciled. Import failure blocks native readiness, no future idle/launch permission.'}
        cre['next_action']='Diagnose exact original M95 import failure using bounded CPU traceback/loaded-code provenance. Preserve original terminal failed request, all raw and source d585; do not replay or run remaining native arms before a concrete reviewed diagnosis/repair and fresh idle owner/deadline/UUID/locks. No model revision or scientific gate PASS was created; original paired native TRAIN2/resources remain required.'
        files=['cre_execution/execution_binding.json','cre_execution/native_manifest.json','cre_execution/smoke_champion_execution.json','cre_initial_smoke_trace.json','regex_environment_readback.json','cre_import_diagnostic_prepare/cpu_import_probe_result.json','cre_import_diagnostic_r1/cpu_import_probe_result.json']
        for name in files:
            e=ref(HERE/name)
            if e not in cre['evidence']:cre['evidence'].append(e)
        if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':cre['id'],'kind':'native_smoke','result':'failed','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_d08825b5/cre_compatible_tooling/adapter.py run --mode smoke --target champion','observation':'Actual first original request terminal rc1 TypeError in original M95 spconv/pccm/lark/sre_compile import before model construction; 0 native loss forwards/backwards/optimizer steps. Exact request reconciled and no worker remains. Candidate mechanism and resources still NOT_RUN. Diagnosis ongoing; no replay or gate PASS.','evidence':[ref(rawp),ref(HERE/'cre_initial_smoke_trace.json')]}
        work['last_terminal_event']={'experiment_id':'M216-AEF','status':'done_earlystop','native_printed_best':0.4956,'native_validation_logger_best':0.495597243309021,'epochs':'23/50','evidence':ref(HERE/'aef_finalize_result.json')}
        work['last_event_tick']=EXPECTED['generated_at'];work['updated_at']=now;work['next_action']='Complete bounded CRE original-baseline dependency import diagnosis. AEF canonical and research complete23/50, best .4955972433 below M95 .5020. Existing HPC prepared but native NOT_RUN. No GPU1 or protected resume; preserve all source/config/negative evidence.'
        tmp=ROOT/'pipeline/research_work.json.0f02aaa2.cre_failure.tmp';assert not tmp.exists();guard()
        with tmp.open('x',encoding='utf8') as f:json.dump(work,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        guard();os.replace(tmp,ROOT/'pipeline/research_work.json')
        print('Original reconciled CRE baseline-import failure recorded; source/revision/gates unchanged.')
    finally:lock.close()
if __name__=='__main__':main()
