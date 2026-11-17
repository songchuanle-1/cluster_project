"""Persist completed numerical controls separately from causal/efficacy claims."""
from datetime import datetime,timezone
import json
from ops import guard,save,add,evidence,ROOT,OUT,CID
import foreground_tick as tick
guard()
p=OUT/'norm_revision2';r=tick.load(p/'native_diagnostic_result.json')
assert r['passed'] and r['native_forwards']==8 and len(r['scenes'])==8 and r['suffix_replays']==24
assert r['checkpoint_meta']['epoch']==2
assert all(max(scene['controls'].values())<=1e-6 for scene in r['scenes'])
work=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
c['diagnostic_revision_history'][-1].update(result='passed',evidence=[evidence(p/name) for name in ['cpu_contracts_result.json','interval_cpu_result.json','native_diagnostic_result.json']],
    interpretation='Original CPU8groups,saved8conditions,and complete native8scene controls passed;not a productionmodel revision or efficacyPASS.')
c.update(stage='complete',failure_scope='inconclusive',gate_result='Finite matched-control diagnostic complete;allnativecontrols0. Original-minus-permutedPiou=-.0079657659,exploratory8TRAINsceneCI[-.0196140222,.0005174335];no established neighbor-content benefit.',
    next_action='Finite early-checkpoint diagnostic complete;do not rerun or launch training from a controlPASS. Retain uncertainty/OODpermutation limitation. Diagnose terminal trained feature/neighbor mixing separately before choosing a new core structure.')
c['gates'].update(native_same_prefix_diagnostic='PASS_FINITE8_SCENES_ALLREPLAYERROR0',diagnostic_revision2='PASS_BOTH_ORIGINAL_NORMS',causal_neighbor_usefulness='INCONCLUSIVE_8_EARLY_TRAIN_SCENES',trained_efficacy='M203_TERMINAL_NEGATIVE_SEPARATE')
add(c,[p/'native_diagnostic_result.json',OUT/'native_execution.json'])
guard();tick.save(ROOT/'pipeline/research_work.json',work)
save('revision2_disposition.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'controls_passed':True,'scientific_status':'inconclusive_local_neighbor_benefit',
    'native_forwards':8,'suffix_replays':24,'optimizer_steps':0,'new_training_models':0,'original_minus_permuted_piou':r['scene_mean_normal_minus_intervention_piou'],'exploratory_scene_ci95':r['scene_bootstrap_95ci'],
    'evidence':[evidence(p/'native_diagnostic_result.json')]})
print(json.dumps({'candidate':'finite_diagnostic_complete','controls':'PASS','neighbor_benefit':'INCONCLUSIVE','new_training':0}))
