"""Persist a confirmed CPU numerical issue without claiming native mask harm."""
from datetime import datetime,timedelta,timezone
import json
from ops import guard,save,evidence,ROOT,OUT,CID
import foreground_tick as tick

guard()
cpu=tick.load(OUT/'metric_cpu_result.json');confirmation=tick.load(OUT/'counterexample_confirmation.json')
train=tick.load(OUT/'train_geometry_cpu_result.json');prepared=tick.load(OUT/'native_metric_prepare_result.json')
four=tick.load(OUT/'server4_live.json');three=tick.load(OUT/'server3_live.json')
assert cpu['execution_passed'] and confirmation['passed_confirmation'] and train['execution_passed'] and prepared['passed']
assert not cpu['cuda_initialized'] and not train['cuda_initialized'] and not prepared['torch_imported']
assert four['occupied'] and three['occupied'] and four['pid_alive']
assert all(pids==[1995443] for pids in four['lock_owner_pids'].values())
assert len(cpu['metric_failures'])==1 and confirmation['fallback_flips']==8
assert len(train['scenes'])==8 and train['expressions']==32 and not train['failures']
now=datetime.now(timezone.utc)
for observation in (four,three):assert (now-datetime.fromisoformat(observation['observed_at'])).total_seconds()<3600
paths=[OUT/name for name in ('metric_prereg.md','fixture_addendum.md','confirmation_prereg.md','source_clarification.md',
    'source_verification.json','manifest.json','metric_cpu.py','metric_cpu_result.json','cpu_execution.json',
    'counterexample_lattice40_rotation_z_pi4.npz','confirm_counterexample.py','counterexample_confirmation.json',
    'train_geometry_cpu.py','train_geometry_cpu_result.json','confirmation_execution.json',
    'native_metric.py','native_metric_manifest.json','native_metric_prepare_result.json','native_metric_prepare_execution.json',
    'server4_live.json','server3_live.json')]
paths += [OUT/scene['geometry_file'] for scene in train['scenes']]
paths += [ROOT/'pipeline/reviews/motivation_review_20261018_b4174e26.md',ROOT/'pipeline/designs/exp_design_20261018_b4174e26.md']
entries=[evidence(path) for path in paths]
summary={'observed_at':now.isoformat(),'scientific_status':'implementation_numerical_sensitivity_confirmed_in_fixed_lattice_probes;native_fine_membership_and_trained_mask_effect_unknown',
    'fixture_transform_conditions':len(cpu['cases']),'fixture_null_controls':len(cpu['controls']),
    'isometry_or_uniform_scale_conditions':sum(r['isometry_or_uniform_scale'] for r in cpu['cases']),
    'numerical_counterexamples':cpu['metric_failures'],'independent_numpy_error':confirmation['independent_numpy_max_error'],
    'integer_tie_oracle_error':confirmation['diagnostic_oracle_output_error'],'fallback_flips':8,
    'real_coordinate_cpu_scenes':8,'expressions':32,'artificial_single_leaf_conditions':sum(len(s['transforms']) for s in train['scenes']),
    'artificial_single_leaf_failures':0,'artificial_membership_not_native':True,
    'native_FPS_calls':0,'neural_model_forwards':0,'native_backwards':0,'optimizer_steps':0,'source_changes':0,'model_revisions':0,
    'new_diagnostic_ids':1,'new_training_models':0,'admissions':0,'launches':0,
    'M203_epoch_steps':four['epoch_steps'],'M203_early_validation_miou':four['validation_miou'],
    'historical_champion':.5020,'target':.51,'native_resource_observation_at':four['observed_at'],
    'limitations':['Synthetic probe features are not trained inst_feats','Real-coordinate stress uses artificial single leaf,not native FPS membership',
        'Small input-rounding sensitivity does not prove mask or mIoU harm','No source repair,tolerance adjustment or architecture failure claim','Material novelty unestablished'],
    'evidence':entries}
save('progress_summary.json',summary);entries.append(evidence(OUT/'progress_summary.json'))
work=tick.load(ROOT/'pipeline/research_work.json')
candidate=next(c for c in work['candidates'] if c['id']==CID)
assert candidate['stage']=='diagnosis'
candidate.update(stage='blocked',failure_scope='implementation',blocker_kind='exclusive_gpu_slot',required_server='server-4',
    blocker='All non-GPU work complete:fixed CPU probe counterexample independently confirmed,8native CPU TRAIN geometry groups prepared,56explicit artificial-leaf real-coordinate conditions measured,and pinned native FPS/fine runner source/asset prepare-check passed without Torch. Exact native FPS memberships require CUDA;both authorized slots occupied at04:16:40Shanghai,server4M203 owns all3locks and server3 has a foreign job. No native FPS/neural mask call run.',
    retry_after=(now+timedelta(hours=1)).isoformat(),
    unblock_condition='A currently authorized pinned physical GPU is live-idle and lifetime exclusive locks plus a fresh current foreground lease are acquired;server4GPU0 runtime/assets are frozen ready,server3GPU1 fallback additionally needs target runtime/data/source validation. Preserve existing/foreign jobs.',
    next_action='After genuine resource release,execute frozen native_metric.py --lease <fresh_lease_bound_to_native_metric_manifest.json> on the8raw TRAIN geometries;use original GPUscatter and CUDA FPS,hold originalfine IDs fixed and compare all7transforms at unchanged1e-6. Record actual memberships,CPU/GPU position residuals and all results. Synthetic feature probe findings are not trained mask effects;continue existing self/nonself mask diagnostic and M203 original posttraining plan separately. Do not edit M203 or implement an arbitrary epsilon fix.',
    gates={'CPU_fixture_execution':'PASS','rigid_geometry_numerical_stability':'COUNTEREXAMPLE_LATTICE40_ROTATION',
        'independent_confirmation':'PASS_INTEGER_DISTANCE_AND_NUMPY','real_coordinate_artificial_leaf':'56CONDITIONS_NO_REPRODUCTION_NOT_NATIVE',
        'native_FPS_membership':'NOT_RUN_RESOURCE_BLOCKED','trained_mask_effect':'UNKNOWN','material_novelty':'UNESTABLISHED'},
    evidence=entries,updated_at=now.isoformat(),
    attempted_alternatives=['Actual16fixture-transform CPUconditions+2nullcontrols executed before any source change',
        'Independent integer-distance and NumPy reconstruction confirmed8fallbackflips;diagnostic oracle only,not deployable repair',
        'Original8TRAINgroups32expressions CPUpreprocessed;56artificial single-leaf real-coordinate controls measured with0counterexamples',
        'Original CUDA FPS is required for native memberships;no CPU substitute claimed;frozen native runner preparecheck passed with0Torch/CUDA',
        'Both authorized cards checked once live;existing training/foreign jobs preserved'])
primary=next(c for c in work['candidates'] if c['id']=='fle-self-neighbor-content-separation')
assert primary['stage']=='blocked' and primary['blocker_kind']=='exclusive_gpu_slot'
primary['evidence'] += [evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json')]
primary['blocker']='Prior self/nonself CPU/source/data/epoch2checkpoint preparation remains unchanged,not rerun. At04:16:40Shanghai both authorized GPUslots occupied;server4M203PID1995443 owns all3locks,server3 foreignjob preserved. No CUDA/native mask test possible without sharing. Reuse these current resource facts after more than one hour;no scientific conclusion from the timer.'
primary['retry_after']=(now+timedelta(hours=1)).isoformat();primary['last_rechecked_at']=now.isoformat()
work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID,primary['id']],
    'evidence':[evidence(OUT/'progress_summary.json'),evidence(OUT/'native_metric_manifest.json'),evidence(OUT/'native_metric_prepare_result.json'),evidence(OUT/'server4_live.json'),evidence(OUT/'server3_live.json')],
    'resume_condition':candidate['unblock_condition'],'retry_after':candidate['retry_after'],
    'scope':'New fixed-membership numerical robustness diagnosis actually tested and independently explained;not a new model,not route exhaustion and not trained harm. All remaining native geometry/mask tests need a real exclusive idle card.'}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'candidate':CID,'stage':'blocked','failure_scope':'implementation','CPU_counterexample_confirmed':True,
    'real_native_membership':'not_run','native_mask_harm':'unknown','admissions':0,'retry_after':candidate['retry_after']}))
