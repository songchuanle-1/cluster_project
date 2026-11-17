"""Finish the finite exact arithmetic audit and preserve existing native blockers."""
from datetime import datetime,timedelta,timezone
import json
import sys
from ops import guard,save,evidence,run,ROOT,OUT,CID
import foreground_tick as tick

guard();now=datetime.now(timezone.utc)
result=tick.load(OUT/'exact_distance_result.json')
four=tick.load(OUT/'server4_live.json');three=tick.load(OUT/'server3_live.json')
assert result['execution_passed'] and not result['torch_imported']
assert four['occupied'] and three['occupied'] and four['pid_alive']
assert all(pids==[1995443] for pids in four['lock_owner_pids'].values())
rotated=next(r for r in result['fixtures'] if r['sample']=='lattice40_rotated')
assert rotated['float_vs_full_exact_rank_predicate_disagreements']==10
real_denominator=sum(r['recipients'] for r in result['real_coordinate_pairs'])
assert real_denominator==6422 and not any(r['disagreements'] for r in result['real_coordinate_pairs'])
paths=[OUT/name for name in ('exact_distance_prereg.md','exact_distance_cpu.py','manifest.json','exact_distance_result.json',
    'source_verification.json','execution.json','server4_live.json','server3_live.json')]
paths+=[ROOT/'pipeline/reviews/motivation_review_20261018_79a22121.md',ROOT/'pipeline/designs/exp_design_20261018_79a22121.md']
entries=[evidence(path) for path in paths]
work=tick.load(ROOT/'pipeline/research_work.json')
scope_ids=['m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence','m95-native-secondary-positive-mass','m95-native-between-pair-support']
rechecked=[]
for cid in scope_ids:
    candidate=next(c for c in work['candidates'] if c['id']==cid)
    if datetime.fromisoformat(candidate['retry_after'])>now:continue
    fetched=run([sys.executable,'-B','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/foreground_tick.py','cluster_project','candidate','--id',cid])
    assert fetched.returncode==0
    detail=json.loads(fetched.stdout)
    assert detail['stage']=='blocked' and detail['blocker_kind']=='human_authorization' and 'auxiliary' in detail['blocker']
    rechecked.append({k:detail[k] for k in ('id','stage','blocker_kind','retry_after','unblock_condition','next_action')})
save('scope_recheck.json',{'observed_at':now.isoformat(),'goal_sha256':'42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec',
    'scope':'Initial snapshot due0;four known human holds may reach their actual retry during this tick. Recheck existing authorization only;no new user priority restoration or mainline-required auxiliary evidence supplied.','new_authorization':False,'items':rechecked})
for row in rechecked:
    candidate=next(c for c in work['candidates'] if c['id']==row['id'])
    candidate['evidence'].append(evidence(OUT/'scope_recheck.json'))
    candidate['retry_after']=(now+timedelta(hours=4)).isoformat();candidate['last_rechecked_at']=now.isoformat()
summary={'observed_at':now.isoformat(),'finite_audit_status':'EXECUTED_COMPLETE_NOT_MODEL_PASS','new_diagnostic_ids':1,
    'fixture_recipients_full_exact_rank':120,'real_reported_neighbor_pairs_exact':6422,'real_full_exact_rank':False,
    'rotated_lattice_float_ties':20,'rotated_lattice_exact_ties':10,'false_float_cutoff_ties':10,'exact_reported_pair_order_inversions':7,
    'real_pair_disagreements':0,'independent_decimal256_traps':'Inexact enabled;all disagreement signs agreed',
    'source_changed':False,'model_revisions':0,'neural_forwards':0,'native_FPS_calls':0,'optimizer_steps':0,'new_training_models':0,'admissions':0,'launches':0,
    'human_authorization_holds_rechecked':len(rechecked),'scope_holds_unblocked':0,
    'M203_best_early_miou':max(four['validation_miou']),'M203_epoch_steps':four['epoch_steps'],
    'science_limitations':'Source predicate arithmetic only;artificial-leaf realdata andrepresentedcoordinates;native fine membership,trained features,mask harm,repair,efficacy and novelty unknown','evidence':entries}
save('progress_summary.json',summary);entries.append(evidence(OUT/'progress_summary.json'))
candidate=next(c for c in work['candidates'] if c['id']==CID)
assert candidate['stage']=='diagnosis'
candidate.update(stage='complete',failure_scope='implementation',updated_at=now.isoformat(),evidence=entries,
    next_action='Finite exact-arithmetic question answered;do not rerun unchanged arrays or interpret completion as a model PASS. Preserve10float/exact cutoff disagreements and7pair inversions. Continue original native FPS/fine-kernel andself/nonself mask diagnostics under their stable IDs when genuinely authorized idle resources appear;do not add epsilon/source repair or changeM203.',
    scientific_result='Coordinate representation alone is insufficient to explain all reported float cutoff ties:the rotated40point fixture reports20ties but exact squared-distance rank has10. All10disagreements independently confirmed;6422artificial-leaf realdata reported pairs show0disagreement,not fullrank or nativeFPS evidence.',
    gates={'finite_arithmetic_execution':'COMPLETE','exact_comparison':'FRACTION_AND_DECIMAL256_AGREE','native_membership':'NOT_MEASURED','trained_mask_harm':'UNKNOWN','production_repair':'NOT_IMPLEMENTED'})
resource_ids=['fle-self-neighbor-content-separation','fle-fixed-membership-metric-geometry-audit']
for cid in resource_ids:
    pending=next(c for c in work['candidates'] if c['id']==cid)
    assert pending['stage']=='blocked' and pending['blocker_kind']=='exclusive_gpu_slot'
    pending['evidence']+=[evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json')]
    pending['blocker']='Non-GPU preparations remain complete and frozen,not rerun. Resource-only check at06:18:21-22Shanghai:server4GPU0 originalM203PID1995443 owns training/diagnostic/exclusive locks;server3GPU1 occupied by foreignjob. No exclusive idle authorized slot;no CUDA/native diagnostic run. Actual compute must recheck live identity/idleness,assets and freshlease.'
    pending['retry_after']=(now+timedelta(hours=1)).isoformat();pending['last_rechecked_at']=now.isoformat()
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID,*resource_ids,*[r['id'] for r in rechecked]],
    'evidence':[evidence(OUT/'progress_summary.json'),evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json'),evidence(OUT/'scope_recheck.json')],
    'resume_condition':'Finite CPU arithmetic audit completed. Resume existing frozen native geometry/mask tests only when an authorized pinned physical card is actually idle and a fresh owning execution lease,lifetime GPUlocks and target asset checks pass;human holds retain original authorization/mainline-needed auxiliary conditions.',
    'retry_after':(now+timedelta(hours=1)).isoformat(),'scope':'Not route exhaustion,new model,source repair or proof of trained harm.'}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'candidate':CID,'stage':'complete','finite_question_only':True,'human_holds_rechecked':len(rechecked),'native_tests_still_resource_blocked':2,'M203_best_early':summary['M203_best_early_miou']}))
