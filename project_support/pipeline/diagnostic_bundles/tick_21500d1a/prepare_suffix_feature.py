"""Preserve failed full-forward control; prebind a same-prefix native replay."""
from datetime import datetime,timezone
from audit_terminal import guard,save,ROOT,OUT,tick

guard()
attempt=tick.load(OUT/'trained_feature_execution_attempt.json')
assert attempt['returncode']==1 and 'repeat_errors' in attempt['stderr']
source=(OUT/'trained_feature_native.py').read_text(encoding='utf-8')
old=source[source.index('    def capture(batch,zero=False):'):source.index('    def maximum(left,right):')]
new=r'''    def clone(value):
        if torch.is_tensor(value):return value.detach().clone()
        if isinstance(value,tuple):return tuple(clone(v) for v in value)
        if isinstance(value,list):return [clone(v) for v in value]
        return value
    def capture(batch):
        held={'cluster_calls':0}
        def point_hook(module,args,result):
            held['cluster_calls']+=1
            held['point_input']=clone(args[0]);held['point_message']=clone(result['point'])
            held['message_before_norm']=float(result['point'].norm().detach().cpu())
            held['message_after_norm']=held['message_before_norm']
        def ila_hook(module,args):held['ila_args']=clone(args)
        def decoder_hook(module,args):held['decoder_args']=clone(args)
        def head_hook(module,args,result):
            held.update(q=module.out_norm(result[0]).detach().clone(),f=args[2].detach().clone(),
                        mask=args[3].detach().clone(),logits=result[2].detach().clone(),indis=result[3].detach().clone())
        hooks=[model.dec.cluster_att.register_forward_hook(point_hook),
               active[0].ila.register_forward_pre_hook(ila_hook),
               model.dec.decoder_layers[-1].register_forward_pre_hook(decoder_hook),
               model.dec.decoder_layers[-1].register_forward_hook(head_hook)]
        try:
            gorilla.set_random_seed(1999)
            with torch.no_grad():prediction=model(copy.deepcopy(batch),mode='predict')
        finally:
            for hook in hooks:hook.remove()
        assert held['cluster_calls']==1
        assert set(('ila_args','decoder_args','point_input','point_message'))<=set(held)
        gate_tensor=torch.sigmoid(active[0].cluster_att_gate)
        injection=float((held['ila_args'][1]-(held['point_input']+gate_tensor*held['point_message'])).abs().max().detach().cpu())
        assert injection<=1e-6,injection
        held['injection_max_error']=injection;held['prediction']=prediction
        return held
    def replay(prefix,batch,zero=False):
        ila_args=list(clone(prefix['ila_args']))
        message=torch.zeros_like(prefix['point_message']) if zero else prefix['point_message']
        if zero:ila_args[1]=prefix['point_input']+torch.sigmoid(active[0].cluster_att_gate)*message
        with torch.no_grad():
            features=active[0].ila(*ila_args)[0]
            decoder_args=list(clone(prefix['decoder_args']));decoder_args[2]=features
            result=model.dec.decoder_layers[-1](*decoder_args)
            query=model.dec.decoder_layers[-1].out_norm(result[0])
        predicted=model.predict_by_feat(batch['scan_ids'],batch['object_idss'],batch['ann_ids'],
            {'masks':result[2],'indis':result[3],'sample_inds':prefix['prediction']['sample_ind']},
            batch['superpoints'].cuda(),[v.cuda() for v in batch['gt_pmasks']],
            [v.cuda() for v in batch['gt_spmasks']],prefix['prediction']['seed_ind'])
        return {'q':query.detach(),'f':features.detach(),'mask':prefix['mask'],'logits':result[2].detach(),
                'indis':result[3].detach(),'prediction':predicted,'message_after_norm':float(message.norm().detach().cpu())}
'''
source=source.replace(old,new)
changes=[
    ('STAGE/"trained_feature_manifest.json"','STAGE/"trained_suffix_manifest.json"'),
    ("on=capture(batch);repeat=capture(batch);off=capture(batch,zero=True)","on=capture(batch);repeat=replay(on,batch);off=replay(on,batch,zero=True)"),
    ("'native_forwards':12,'optimizer_steps':0","'native_forwards':4,'native_ila_decoder_suffix_replays':8,'optimizer_steps':0"),
    ("STAGE/'trained_feature_result.json'","STAGE/'trained_suffix_result.json'"),
    ("'unchanged_fps_and_proposal_ids':True","'same_captured_prefix_fps_and_proposal_ids':True,'injection_max_error':on['injection_max_error']"),
    ("'scope':'Fixed4TRAINscene trained-network counterfactual only; no retraining,population efficacy,new mechanism selection,gate tuning or revision3. Counterfactual may be off distribution.'",
     "'scope':'SAME-captured-prefix4TRAINscene intervention;4full network captures+8native ILA/decoder suffix replays. Original full-forward repeat FAILED and retained. No generalization,independent-repeat noise estimate,retraining,model change or revision3.'")]
for before,after in changes:
    assert source.count(before)==1,before
    source=source.replace(before,after)
target=OUT/'trained_feature_suffix_native.py'
target.write_text(source,encoding='utf-8',newline='\n');compile(source,target.name,'exec')
manifest=tick.load(OUT/'trained_feature_manifest.json')
manifest['producer_hashes']={name:tick.digest(OUT/name) for name in (target.name,'aligned_evidence.py')}
save('trained_suffix_manifest.json',manifest)
save('trained_protocol_revision1.json',{'registered_at':datetime.now(timezone.utc).isoformat(),
    'scope':'Instrumentation matching only, no model source/revision change','original_control_failed':True,
    'failed_repeat_errors':{'q':6.198883056640625e-6,'f':2.384185791015625e-6,'logits':6.74128532409668e-5},
    'frozen_tolerance':1e-6,'tolerance_changed':False,'native_forward_calls_in_failed_attempt':3,
    'original_prereg_sha256':tick.digest(OUT/'trained_feature_prereg.md'),
    'revision_prereg_sha256':tick.digest(OUT/'trained_suffix_prereg.md'),
    'original_program_sha256':tick.digest(OUT/'trained_feature_native.py'),'revision_program_sha256':tick.digest(target),
    'planned_full_network_captures':4,'planned_native_ila_decoder_suffix_replays':8})
work=tick.load(ROOT/'pipeline/research_work.json')
candidate=next(c for c in work['candidates'] if c['id']=='m202-trained-mask-feature-contribution')
assert candidate['stage']=='validation'
candidate['failure_scope']='inconclusive'
candidate['next_action']='Run preregistered same-captured-prefix native ILA+decoder replay at unchanged1e-6 after full-forward repeat control failed; preserve the failure and interpret local point/query effects only if all new controls pass.4full captures+8suffix calls,0optimizer.'
candidate['diagnostic_protocol_revisions']=[{'revision':1,'scope':'capture/replay matching only, not model revision','model_sources_changed':False}]
for name in ('trained_feature_execution_attempt.json','trained_suffix_prereg.md','trained_protocol_revision1.json',target.name,'trained_suffix_manifest.json'):
    path=OUT/name;candidate['evidence'].append({'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)})
guard();tick.save(ROOT/'pipeline/research_work.json',work)
manager=(OUT/'run_trained_feature.py').read_text(encoding='utf-8')
for before,after in (
    ('trained_feature_native.py','trained_feature_suffix_native.py'),
    ('trained_feature_manifest.json','trained_suffix_manifest.json'),
    ('trained_feature_prereg.md','trained_suffix_prereg.md'),
    ('trained_feature_execution_attempt.json','trained_suffix_execution_attempt.json'),
    ('trained_feature_result.json','trained_suffix_result.json'),
    ("candidate['stage']=='diagnosis'","candidate['stage']=='validation'"),
    ("result['native_forwards']==12","result['native_forwards']==4")):
    assert before in manager,before
    manager=manager.replace(before,after)
(OUT/'run_trained_suffix.py').write_text(manager,encoding='utf-8',newline='\n')
compile(manager,'run_trained_suffix.py','exec')
print('Diagnostic matching revision1 preregistered; original failed1e-6control retained; model/gates unchanged.')
