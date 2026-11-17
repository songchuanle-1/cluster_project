"""Register the actually reviewed BCR source, with no admission or launch."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
P=HERE/'new_candidate_prepare'; TOKEN='41eb62fa1d32436f859264a19b0d4049'
CID='hierarchy-parent-bidirectional-complement-recurrence'
COMMIT='11a811618179ab1ddc0cee299194667413b7fdb9'
BASE='00e2b18c6b8d568a64edb496e6979d766440883c'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
    q=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with q.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(q,p)
owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
prep=read(P/'preparation.json');assert sha(P/'preparation.json')=='faf3494d13c5026b21e1d235dab311cc4f9a9d88b9653c4726a5ccbdc8958615'
assert prep['candidate_id']==CID and prep['code_commit'] is None and prep['source_file_count']==9 and prep['base_reference_commit']==BASE
for name,h in prep['prepared_file_hashes'].items():assert sha(P/name)==h,name
version=read(HERE/'isolated_source_version.json');assert version['code_commit']==COMMIT and version['parent_commit']==BASE and version['primary_HEAD_index_status_28_protected_bytes_unchanged']
for n in ['bcr_topology_review.json','bcr_integration_review.json','bcr_isolated_version_review.json','bcr_independent_review/research_boundary.json','waiting_boundary_check.json']:
    assert read(HERE/n)['material_concerns']==[],n
check=read(P/'static_validation.json');assert check['error'] is None and check['torch_imported'] is False and check['native_execution']=='NOT_RUN' and check['assertion_count']==1334 and check['production_plan_case_count']==22
obs=read(HERE/'btc_progress_observation.json');a,b=[o['data'] for o in obs['observations']]
assert obs['same_exact_registered_process_and_native_TRAIN_growth'] and a['pid']==b['pid']==2784474 and a['start_ticks']==b['start_ticks']=='47557208' and not b['errors']
assert a['train_progress']==[3,50,3469,4686] and b['train_progress']==[3,50,3476,4686]
goal=sha(ROOT/'pipeline/goal.json');assert goal=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
policy=read(ROOT/'pipeline/closure_policy.json');auth=policy['experiment_first']['authorization'];assert policy['experiment_first']['enabled'] and sha(ROOT/auth['path'])==auth['sha256']
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
lock=monitor.acquire_lock(str(ROOT));assert lock is not None
try:
    protected=['queue.json','running.json','experiments/M211-BTC.json','experiments/M210-PSNC.json','experiments/M206-CGCA.json','admissions/M211-BTC.json','admissions/M210-PSNC.json']
    before={n:sha(ROOT/'pipeline'/n) for n in protected}
    queue=monitor.load_queue(str(ROOT));task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M211-BTC')
    assert task['status']=='running' and task['pid']==2784474 and task['launch_verified'] and str(task['gpu'])=='0' and task['code_commit']==BASE
    paused=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA');assert paused['dispatch_hold'] and paused['resume_authorized'] is False
    assert monitor.load_running(str(ROOT))['server-4']=={'0':'M211-BTC'}
    work=read(ROOT/'pipeline/research_work.json');assert not any(c['id']==CID or c.get('experiment_id')=='M212-BCR' for c in work['candidates'])
    now=datetime.now(timezone.utc)
    evidence=[ref(P/n) for n in ['preparation.json','static_validation.json','mechanism.md','native_protocol.md','scope_comparison.json']]+[ref(HERE/n) for n in ['isolated_source_version.json','bcr_topology_review.json','bcr_integration_review.json','bcr_isolated_version_review.json','bcr_independent_review/research_boundary.json','btc_progress_observation.json','waiting_boundary_check.json']]
    config='configs/Quard/ctf_hcg_csort_bcr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr.yaml'
    c={'id':CID,'experiment_id':'M212-BCR','stage':'blocked','resume_stage':'validation','created_at':now.isoformat(),
       'hypothesis':'Replace only the original middle FFN with strict-exclusive sibling-prefix/suffix recurrent factorization: each normalized token enters its own linear readout block, while the shared forward/reverse scan states exclude that token and cover its original true-supported same-parent siblings. This removes the own-to-context mixing edge present in inclusive PSBR. Preserve original LN/raw-cf skip/fine-coarse/raw-CSORT/HCG/single inst_feats delivery.',
       'matched_control':'M95 original native YAML/seed1999/epochs50/max_iters70/data/optimizer. The complete candidate is compared with M95; activation/skip/readout differences from PSBR prevent single-factor causal attribution. No paired native batches/parameters or trained efficacy measured yet.',
       'mechanism_scope':'A narrowly specified strict-exclusive graph fork near PSBR/BTC, not independent literature novelty, an old PSBR resume/retry, a pure activation/skip tuning variant, or reopening a held/rejected ID. Preserve branch-stop constraints and all old negative evidence.',
       'config':config,'code_commit':COMMIT,'base_reference_commit':BASE,'source_parent_commit':BASE,'native_execution_code_commit':None,'goal_sha256':goal,'authorization':auth,
       'source_preparation':ref(P/'preparation.json'),'source_version':ref(HERE/'isolated_source_version.json'),
       'source_version_history':[{'recorded_at':prep['prepared_at'],'code_commit':None,'preparation':ref(P/'preparation.json')},{'recorded_at':version['recorded_at'],'code_commit':COMMIT,'evidence':ref(HERE/'isolated_source_version.json')}],
       'offline_checks':{'status':'PASSED_SOURCE_AND_STDLIB_PRODUCTION_PLAN_ONLY','assertions':check['assertion_count'],'distinct_labels':check['distinct_check_labels'],'production_plan_cases':check['production_plan_case_count'],'independent_plan_invocations':24,'not_training_experiments':True,'evidence':ref(P/'static_validation.json')},
       'source_status':'FROZEN_NINE_EXACT_BLOBS_IN_ISOLATED_VERSION_PRIMARY_UNCHANGED','native_status':'NOT_RUN','native_smoke_status':'NOT_RUN','resource_profile_status':'NOT_RUN','admission_status':'NOT_EVALUATED','efficacy':'UNKNOWN','operational_preparation_status':'IN_PREPARATION_THIS_TICK_NO_ACTIVE_BINDING',
       'source_inference_parameter_change':{'new_scan_and_readout':328192,'removed_middle_FFN':525568,'delta':-197376,'actual_registered_inventory':'NOT_RUN'},
       'future_native_protocol':ref(P/'native_protocol.md'),
       'known_limits':['No torch/native/autograd/FP32/real resource/paired initialization or loader evidence yet. Static support is not numerical dependency or efficacy.','Real fixed TRAIN2 must exercise n>=3/depth>=2/nonzero state and separately prove original-loss nonzero finite Ws recurrent-state weight-half and Wf own/left/right block gradients plus optimizer updates; weight decay alone is insufficient.','Geometry CPU transfer, sorting and sequential scans may add latency; inferred fewer parameters do not establish actual resource compliance.','This changes more than one factor relative to PSBR and cannot establish an exclusive-only causal explanation or a new literature contribution.'],
       'blocker_kind':'exclusive_gpu_slot','required_server':'server-4','required_gpu':'0','blocked_at':now.isoformat(),'last_resource_check_at':obs['recorded_at'],'retry_after':(now+timedelta(hours=1)).isoformat(),
       'blocker':'Only authorized GPU0 is occupied by original BTC2784474/start47557208; actual native3/50 steps3469->3476 observed '+obs['recorded_at']+'. BCR source has only local static/plan checks. Its native diagnostic packet is being prepared this tick; no BCR native checks, receipt or queue entry exist. GPU1 released/M206 paused.',
       'unblock_condition':'Complete reviewed BCR original-YAML observer/guarded packet without GPU, then require a genuinely free authorized physicalGPU0, fresh actual owner/context/deadline/assets/runtime/UUID/occupation/three-lock checks after the original BTC run naturally ends. Preserve foreign jobs and all existing runs.',
       'next_action':'Finish and freeze the already-started local BCR diagnostic packet, preserving exact source11a/native YAML. After fresh authorized GPU0 availability, run actual matched M95/BCR original TRAIN2, the preregistered scan/readout block observations, original resource pair and constraints. Only real passing results may produce an admission receipt and waiting/dispatch; no GPU1/M206 resume, sample/seed/order/dtype/threshold/schedule change or source relabel.',
       'evidence':evidence}
    work['candidates'].append(c)
    live=next(c for c in work['candidates'] if c.get('experiment_id')=='M211-BTC')
    for item in [ref(HERE/'btc_progress_observation.json'),ref(HERE/'waiting_boundary_check.json')]:
        if item not in live['evidence']:live['evidence'].append(item)
    work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CID,'kind':'implementation_test','result':'passed','command':prep['static_check_command'],'observation':'Actually executed production-plan/source checks1334 assertions/62labels/22plan cases plus independent24 stdlib invocations, not independent training experiments. Strict-exclusive source9 frozen and saved as isolated11a, primary/liveBTC00e unchanged. All native/autograd/actual resources and efficacy NOT_RUN/UNKNOWN; packet preparation is ongoing and soleGPU0 occupied. Exactly1 new candidate; no admission or launch.','evidence':evidence}
    work['updated_at']=now.isoformat();save(ROOT/'pipeline/research_work.json',work)
    assert {n:sha(ROOT/'pipeline'/n) for n in protected}==before
    save(HERE/'bcr_source_registration.json',{'recorded_at':now.isoformat(),'token':TOKEN,'candidate_id':CID,'code_commit':COMMIT,'new_candidates':1,'admissions':0,'native':'NOT_RUN','resources':'NOT_RUN','source_only_static_preparation':True,'protected_registries_unchanged':True,'evidence':evidence})
    print(json.dumps({'registered':CID,'code_commit':COMMIT,'new_candidates':1,'native':'NOT_RUN','new_admissions':0},ensure_ascii=False))
finally:lock.close()
