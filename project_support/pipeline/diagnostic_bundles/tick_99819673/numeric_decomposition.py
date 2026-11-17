"""A single diagnostic decomposition, not a third implementation revision."""
import argparse
import ast
import json
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT


def prepare():
    c.guard(1200)
    protocol=c.save('numeric_decomposition_preregistration.json',{'preregistered_at':c.now(),'candidate_id':c.CID,
        'held_failure':c.evidence(OUT/'committed_matched_controls_candidate_result.json'),
        'scope':'One fresh fixed8TRAINscene forward capture on exact committed R2, no implementation edit/revision/optimizer. Existing1.027033878e-6 failure remains blocking even if fresh values are below threshold; never select a favorable rerun.',
        'question':'At the actual FP32 P,T, decompose true mass-weighted mean drift into exact-application error from FP32 transition stationarity plus actual FP32 matrix-product rounding.',
        'formula':'w=n.double/sum(n). For eachhead,parent, mean_before=sum(w*T.double); mean_exact=sum(w*(P.double@T.double)); mean_actual=sum(w*Tprime_FP32.double). Drift=(mean_exact-mean_before)+(mean_actual-mean_exact). FP64 is diagnostic arithmetic ONLY; candidate P/T/Tprime remain original FP32.',
        'instrumentation':'Wrap the existing sibling_transport alias and call the identical function once with matrices=True metadata return, return its original output to the actual source. No alternate operator, precision, temperature, head or graph. Save detached pre-token,parent,mass fixtures remotely for audit, no labels.',
        'readouts':'Every group/channel drift, stationarity/rounding maxima, reconstruction residual and components at the same largest-drift coordinate. Report all8scene32expression captures. No sum-of-maxima attribution percentage. Geometry/FPS/backbone stochasticity not assumed solved.',
        'decision':'This is failure localization, not gate revalidation or admission. Any future changed numerical realization would be R3 beyond default2 and needs scoped authorization; no such change made here.',
        'training':0})
    worker=(OUT/'validation_worker_h1.py').read_text(encoding='utf-8')
    function='''
def decompose(torch,gorilla,cfg,model,qualified,result):
    from torch.utils.data import DataLoader,Subset
    from framework.dataset import build_dataset
    hierarchy=importlib.import_module(qualified+'.hier_postprocess')
    original=hierarchy.sibling_transport
    records=[];fixtures=[]
    def capture(tokens,parent,counts,wrong_affinity=False,heads=8,matrices=False):
        output,groups=original(tokens,parent,counts,wrong_affinity,heads,True)
        fixtures.append({'tokens':tokens.detach().cpu(),'parent':parent.detach().cpu(),'counts':counts.detach().cpu()})
        for index,g in enumerate(groups):
            before=g['before'].double();after=g['after'].double();p=g['p'].double()
            mass=counts[g['indices']].double();w=mass/mass.sum()
            exact=torch.matmul(p,before)
            baseline=(before*w[None,:,None]).sum(1)
            exact_mean=(exact*w[None,:,None]).sum(1)
            actual_mean=(after*w[None,:,None]).sum(1)
            drift=actual_mean-baseline;stationarity=exact_mean-baseline;rounding=actual_mean-exact_mean
            coordinate=int(drift.abs().reshape(-1).argmax());head=coordinate//before.shape[-1];channel=coordinate%before.shape[-1]
            records.append({'transport_call':len(fixtures)-1,'parent_group':index,'members':len(g['indices']),
                'max_abs_drift':float(drift.abs().max()),'max_abs_stationarity_application':float(stationarity.abs().max()),
                'max_abs_matmul_rounding':float(rounding.abs().max()),'reconstruction_error':float((drift-stationarity-rounding).abs().max()),
                'largest_coordinate':{'head':head,'channel_in_head':channel,'signed_drift':float(drift[head,channel]),
                    'signed_stationarity_application':float(stationarity[head,channel]),'signed_matmul_rounding':float(rounding[head,channel])}})
        return output
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('rstr-numeric-components'))
    for scene in MANIFEST['cohort']:
        group=dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id']==scene['scene_id']
        assert [{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]==scene['expression_ids']
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,[s['group_index'] for s in MANIFEST['cohort']]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    hierarchy.sibling_transport=capture
    try:
        with torch.no_grad():
            for batch in loader:
                loss,_=model(copy.deepcopy(batch),mode='loss')
                assert bool(torch.isfinite(loss));result['native_loss_forwards']+=1
    finally:hierarchy.sibling_transport=original
    fixture=STAGE/'numeric_fixture.pt';assert not fixture.exists();torch.save(fixtures,fixture)
    maximum=max(records,key=lambda x:x['max_abs_drift'])
    verify();result.update(execution_completed=True,records=records,
        summary={'scenes':8,'expressions':32,'groups':len(records),'transport_calls':len(fixtures),
            'max_abs_drift':maximum['max_abs_drift'],'components_at_same_maximum':maximum['largest_coordinate'],
            'reconstruction_error_max':max(x['reconstruction_error'] for x in records),
            'hold_unchanged':True,'candidate_operator_precision':'FP32','decomposition_precision':'FP64 readout only'},
        fixture={'path':str(fixture),'sha256':sha(fixture),'bytes':fixture.stat().st_size,'contains_labels':False},
        after=observe(),model_source_changed=False,new_implementation_revision=False)
'''
    worker=worker.replace('\ndef main():','\n'+function+'\ndef main():').replace("choices=('resources','controls')","choices=('resources','controls','decompose')")
    worker=worker.replace("if args.mode=='resources':resources(torch,gorilla,cfg,model,result)","if args.mode=='decompose':decompose(torch,gorilla,cfg,model,qualified,result)\n        elif args.mode=='resources':resources(torch,gorilla,cfg,model,result)")
    ast.parse(worker)
    with (OUT/'numeric_decomposition_worker.py').open('x',encoding='utf-8') as stream:stream.write(worker)
    controller=(OUT/'validation_committed.py').read_text(encoding='utf-8').replace('_validation_committed','_numeric_decomposition').replace("OUT/'validation_committed'","OUT/'numeric_decomposition'")
    controller=controller.replace('validation_worker_h1.py','numeric_decomposition_worker.py').replace('validation_committed_execution_preregistration','numeric_decomposition_execution_preregistration').replace('validation_committed_staging','numeric_decomposition_staging').replace("'validation_committed_'+label","'numeric_decomposition_'+label").replace("choices=('stage','controls','resources')","choices=('stage','controls','resources','decompose')")
    ast.parse(controller)
    with (OUT/'numeric_decomposition_controller.py').open('x',encoding='utf-8') as stream:stream.write(controller)
    c.advance([protocol,OUT/'numeric_decomposition_worker.py',__file__], 'Perform one fixed failure-component diagnostic without changing source or releasing the numerical hold; no R3 authorized.')
    print('numeric decomposition prepared; existing failure remains binding')


if __name__=='__main__':prepare()
