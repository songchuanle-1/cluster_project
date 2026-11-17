"""Retain all failures and reconcile actual native/CPU/resource scopes."""
from datetime import datetime,timezone
import ast
import json
import shlex
from ops import guard,save,run,add,evidence,ROOT,OUT,CID,STAGE
import foreground_tick as tick

guard(200)
config_local=OUT/'configuration_probe_result.json'
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/'probe_configuration.py'),
    'songcl@192.168.1.115:'+STAGE+'/'])
save('config_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr})
assert upload.returncode==0
command=('test "$(hostname)" = dl04-MS-7E06 && source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
    'conda activate project_cluster && CUDA_VISIBLE_DEVICES= python -B '+shlex.quote(STAGE+'/probe_configuration.py'))
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],90)
save('config_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
    'songcl@192.168.1.115:'+STAGE+'/configuration_probe_result.json',str(config_local)])
save('config_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
assert fetch.returncode==0,response.stderr
config=tick.load(config_local)
cpu=tick.load(OUT/'cpu_contract_result.json')
summary={'observed_at':datetime.now(timezone.utc).isoformat(),'cpu_contract_pass':cpu['passed'],
    'synthetic_cpu_backwards':cpu['synthetic_cpu_backwards'],'counterparts':{},'native_forwards':0,
    'native_backwards':0,'native_interface_backwards':0,'full_model_training_backwards':0,'suffix_replays':0,
    'optimizer_steps':0,'new_training_loops':0,'new_VAL':0,'new_admissions':0,'new_models':0,
    'reference_arithmetic_revisions':1,'initial_failures_preserved':True}
evidence_paths=[OUT/'cpu_contract_result.json',config_local]
for tag in ('m95','fle'):
    first_path=OUT/('native_'+tag)/'native_contract_result.json'
    first=tick.load(first_path)
    assert first['passed'] is False
    first_controls=ast.literal_eval(first['error'])
    assert max(first_controls.values())>1e-6
    fixed_path=OUT/('flag_'+tag)/'native_contract_result.json'
    fixed=tick.load(fixed_path)
    assert fixed['passed'] and max(fixed['controls'].values())<=1e-6
    probes=fixed['execution_probes']
    assert all(v==0 for p in probes if p['context']!='all_flags_false_before_autograd' for v in p['errors'].values())
    assert max(probes[1]['errors'].values())>1e-6
    steps={}
    for condition in ('original','reference'):
        path=OUT/('backward_'+tag+'_'+condition)/'native_full_backward_result.json'
        step=tick.load(path)
        assert step['passed'] and step['native_backwards']==1 and step['optimizer_steps']==0
        assert step['parameter_flags_preserved']
        steps[condition]=step
        evidence_paths.append(path)
    assert steps['original']['input_sha256']==steps['reference']['input_sha256']
    prefix_equal=steps['original']['prefix_sha256']==steps['reference']['prefix_sha256']
    resources=fixed['resources']
    resource_delta={
        'interface_median_added_ms':resources['reference']['median_ms']-resources['original']['median_ms'],
        'interface_median_relative_change':resources['reference']['median_ms']/resources['original']['median_ms']-1,
        'interface_peak_added_bytes':resources['reference']['allocated_peak_bytes']-resources['original']['allocated_peak_bytes'],
        'single_backward_peak_added_bytes':steps['reference']['allocated_peak_bytes']-steps['original']['allocated_peak_bytes'],
        'single_backward_original_peak_GiB':steps['original']['allocated_peak_bytes']/1024**3,
        'single_backward_reference_peak_GiB':steps['reference']['allocated_peak_bytes']/1024**3,
        'scope':'warm/repeatgatherbench and singlecoldnativebackward separately;optimizerstatenotloaded;notfulltrainingpeak'}
    item={'initial_attempt_passed':False,'initial_failure_controls':first_controls,
        'execution_flag_probe':probes,'original_flag_contract_passed':True,
        'native_reference_masked_gradient':fixed['controls']['masked_reference_gradient'],
        'native_original_masked_gradient':fixed['original_masked_gradient_max'],
        'native_reference_valid_gradient':fixed['reference_valid_gradient_max'],
        'full_backward_passed':True,'native_training_batch_inputs_equal':True,
        'native_training_prefix_fingerprints_equal':prefix_equal,
        'prefix_difference_magnitude':'UNKNOWN_NOT_CAPTURED;no matchedlossgainclaim',
        'original_whole_point_gradient':steps['original']['whole_point_feature_gradient'],
        'reference_whole_point_gradient':steps['reference']['whole_point_feature_gradient'],
        'resource_delta':resource_delta,
        'fixed_checkpoint_task_gain':'UNKNOWN;noinstantloss or differentweights efficacyclaim',
        'config':config['models'][tag]}
    summary['counterparts'][tag]=item
    for result in (first,fixed,*steps.values()):
        for name in ('native_forwards','native_backwards','native_interface_backwards','full_model_training_backwards','suffix_replays'):
            summary[name]+=result.get(name,0)
    evidence_paths.extend([first_path,fixed_path])
summary['scientific_status']='Uniformfinitepaddingcontract passes source/nativegradient smoke;non-novelbugfix;no trainedefficacy/generalization established'
summary['execution_status']='evidence analyzed;finish not yet validated'
summary['evidence']=[evidence(p) for p in evidence_paths]
save('analysis_summary.json',summary)
work=tick.load(ROOT/'pipeline/research_work.json')
c=next(c for c in work['candidates'] if c['id']==CID)
c.update(stage='validation',failure_scope='inconclusive',
    gate_result='Uniformreference1 CPU/nativeinterface plus4native.train backward smokePASS;initialfailures explained by allfalsegradflags/preserved. Nooptimizer/training/VAL/efficacy. Prefixhashmismatch blocksinstantlossgain.',
    next_action='Review uniformbugfix scope and frozen data/efficiency boundaries;do not admit singleopPhase1variant or restartstoppedFLE. Need separate properstructural mechanism beforetraining;native/fulltrainingefficacy remains unknown.')
add(c,evidence_paths+[OUT/'analysis_summary.json',OUT/'contract_prereg.md',OUT/'flag_probe_prereg.md',OUT/'full_backward_prereg.md'])
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({k:v for k,v in summary.items() if k not in ('evidence','counterparts')},ensure_ascii=False))
print(json.dumps(summary['counterparts'],ensure_ascii=False))
