"""Unmodified native TRAIN forwards;labels observed only after prediction."""
import argparse,copy,importlib,json,logging
import numpy as np
from native_runtime import acquire,release,verify,observe,setup,save,fingerprint,MANIFEST,NAME
from attention_readout import prepare,mixing
parser=argparse.ArgumentParser();parser.add_argument('--lease',required=True);args=parser.parse_args()
result={'passed':False,'native_forwards':0,'native_backwards':0,'optimizer_steps':0,'scenes':[],'unknown_label_expressions':0,'model_changed':False,'scientific_status':'observational_TRAIN_alignment_not_causal_benefit'}
try:
    result['before']=acquire(args.lease)
    torch,gorilla,cfg,model,meta=setup();assert meta['epoch']==13
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    op=importlib.import_module('framework.model.Quard_model.'+NAME+'.fine_exchange')
    hierarchy=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('targetmix'))
    for row in MANIFEST['cohort']:
        g=dataset.scene_inputs[row['group_index']]
        assert g[0]['scene_id']==row['scene_id'] and [{'object_id':str(r['object_id']),'ann_id':str(r['ann_id'])} for r in g]==row['expression_ids']
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,[r['group_index'] for r in MANIFEST['cohort']]),batch_size=1,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    fine=model.dec.cluster_att.fine_exchange
    def clone(x):
        if torch.is_tensor(x):return x.detach().clone()
        if isinstance(x,(tuple,list)):return type(x)(clone(y) for y in x)
        return x
    with torch.no_grad():
        for scene,batch in zip(MANIFEST['cohort'],loader):
            observe();before=fingerprint(torch,batch);held=[]
            def hook(module,arguments,value):held.append((clone(arguments),clone(value)))
            handle=fine.register_forward_hook(hook);gorilla.set_random_seed(1999)
            try:
                loss,components=model(copy.deepcopy(batch),mode='loss');result['native_forwards']+=1
                assert torch.isfinite(loss) and len(held)==1
            finally:handle.remove()
            assert fingerprint(torch,batch)==before
            arguments,expected=held[0];features,padding,positions,leaves=arguments
            output_before=fingerprint(torch,expected);rows=[]
            for b,ids in enumerate(leaves):
                n=len(ids);assert int((~padding[b]).sum())==n
                graph=op.build_graph(positions[b,:n].cpu().numpy(),ids.cpu().numpy())
                source,state=prepare(features[b,:n],graph)
                error=float((source-expected[b,:n]).abs().max().cpu());assert error<=1e-6
                identity=scene['expression_ids'][b]
                y=batch['gt_spmasks'][b].to(source.device).reshape(-1)
                row={'identity':identity,'superpoints':n,'source_error':error,'labels_known':False}
                if len(y)!=n or not bool(((y==0)|(y==1)).all()):result['unknown_label_expressions']+=1;rows.append(row);continue
                values,raw=mixing(state,y);_,null=mixing(state,torch.zeros_like(y));_,complement=mixing(state,1-y)
                null_error=float(null['cross_mass'].abs().max().cpu());complement_error=float((raw['fraction']-complement['fraction']).abs().max().cpu())
                assert null_error==0 and complement_error<=1e-6
                row.update(labels_known=True,controls={'all_equal_null_error':null_error,'complement_error':complement_error},**values);rows.append(row)
            assert fingerprint(torch,expected)==output_before
            result['scenes'].append({'scene':scene['scene_id'],'group_index':scene['group_index'],'input_sha256':before,'expressions':rows})
            hierarchy.reset_orth_accum();del held,arguments,features,padding,positions,leaves,expected,source,state,loss,components
            torch.cuda.empty_cache()
    verify();result['after']=observe();assert len(result['scenes'])==32 and result['native_forwards']==32
    scene_values=[]
    for scene in result['scenes']:
        values=[r['target_weighted_minus_uniform'] for r in scene['expressions'] if r['labels_known'] and r.get('target_weighted_minus_uniform') is not None]
        if values:scene_values.append({'scene':scene['scene'],'expressions':len(values),'delta':float(np.mean(values))})
    result.update(passed=True,primary_known_scenes=len(scene_values),primary_known_expressions=sum(r['expressions'] for r in scene_values),per_scene_primary=scene_values,checkpoint_epoch=meta['epoch'])
    if len(scene_values)>=10:
        values=np.array([r['delta'] for r in scene_values]);draws=np.random.default_rng(1999).choice(values,(5000,len(values)),replace=True).mean(1)
        result.update(primary_scene_mean=float(values.mean()),primary_scene_ci95=np.quantile(draws,[.025,.975]).tolist())
    else:result.update(primary_scene_mean=None,primary_scene_ci95=None)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:save('native_attention_result.json',result);release()
print(json.dumps({k:result[k] for k in ['passed','native_forwards','unknown_label_expressions','primary_known_scenes','primary_known_expressions','primary_scene_mean','primary_scene_ci95']}))
