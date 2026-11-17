"""Frozen native scale deletion with original final queries and task targets."""
import argparse
import copy
import logging
from native_runtime import acquire, release, setup, save, fingerprint, MANIFEST
from scale_metrics import summarize

parser=argparse.ArgumentParser()
parser.add_argument('--lease',required=True)
parser.add_argument('--pair',type=int,choices=range(4),required=True)
args=parser.parse_args()
result={'execution_completed':False,'scientific_diagnosis_passed':False,'new_training':0,'optimizer_steps':0,'native_backwards':0,'native_task_mask_replays':0,'controls_passed':False,'records':[],'scope':'Conditional fixed-query task diagnosis on frozen TRAIN scenes,not efficacy/admission'}
hooks=[]
original_gather=None
try:
 result['before']=acquire(args.lease)
 torch,gorilla,cfg,model,meta=setup()
 assert meta['epoch']==16
 model.eval()
 from torch.utils.data import DataLoader,Subset
 from framework.dataset import build_dataset
 dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('native-scale'))
 cohort=MANIFEST['cohort'][2*args.pair:2*args.pair+2]
 assert len(cohort)==2
 for scene in cohort:
  group=dataset.scene_inputs[scene['group_index']]
  assert group[0]['scene_id']==scene['scene_id']
  assert [{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]==scene['expression_ids']
 gorilla.set_random_seed(1999)
 batch=next(iter(DataLoader(Subset(dataset,[s['group_index'] for s in cohort]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
 cluster=model.dec.cluster_att
 active=[layer for layer in model.dec.encoder_layers if layer.use_cluster]
 assert len(active)==1 and active[0] is model.dec.encoder_layers[-1]
 assert active[0].cluster_message_type=='context' and active[0].cluster_gate_type=='sigmoid'
 last=model.dec.decoder_layers[-1]
 assert cluster.dropout.p==0
 def clone(value):
  if torch.is_tensor(value):return value.detach().clone()
  if isinstance(value,tuple):return tuple(clone(x) for x in value)
  if isinstance(value,list):return [clone(x) for x in value]
  if isinstance(value,dict):return {k:clone(v) for k,v in value.items()}
  return value
 def error(a,b):return float((a-b).abs().max().cpu())
 held={}
 original_gather=cluster._cluster_to_points
 def capture_gather(*values):
  held['gather']=clone(values)
  return original_gather(*values)
 def capture_cluster(module,values,output):
  held['core']=clone(values);held['message']=clone(output['point'])
 def capture_ila(module,values):held['ila']=clone(values)
 def capture_last(module,values,output):held['last_args']=clone(values);held['last']=clone(output)
 def capture_criterion(module,values):held['criterion']=clone(values)
 cluster._cluster_to_points=capture_gather
 hooks=[cluster.register_forward_hook(capture_cluster),active[0].ila.register_forward_pre_hook(capture_ila),last.register_forward_hook(capture_last),model.criterion.register_forward_pre_hook(capture_criterion)]
 with torch.no_grad():
  native_loss,_=model(copy.deepcopy(batch),mode='loss')
 cluster._cluster_to_points=original_gather
 for handle in hooks:handle.remove()
 hooks=[]
 x,tokens,ids,mask=held['gather']
 assert len(x)==sum(len(scene['expression_ids']) for scene in cohort)==8
 native_output=held['criterion'][0]
 assert torch.equal(native_output['masks'],held['last'][2])
 fixed_query=held['last'][0]
 query_hash=fingerprint(torch,fixed_query)
 # Capture only exact final native loss-mask matching; auxiliary outputs are excluded.
 matches=[]
 original_loss_masks=model.criterion.loss_masks
 def collect_matches(pred_masks,pred_scores,targets,indices,num_boxes):
  final=all(torch.equal(pred_masks[b],native_output['masks'][b,:,~mask[b]]) for b in range(len(pred_masks)))
  if final:matches.append(clone((targets,indices)))
  return original_loss_masks(pred_masks,pred_scores,targets,indices,num_boxes)
 model.criterion.loss_masks=collect_matches
 try:
  with torch.no_grad():model.criterion(*held['criterion'])
 finally:model.criterion.loss_masks=original_loss_masks
 assert len(matches)==1,'Final native matching must be captured unambiguously'
 targets,indices=matches[0]
 def message(active_scales):
  banks=[tokens[i] if i in active_scales else torch.zeros_like(tokens[i]) for i in range(3)]
  return cluster.message_norm(original_gather(x,banks,ids,mask)).masked_fill(mask.unsqueeze(-1),0)
 def suffix(value):
  iargs=list(clone(held['ila']))
  iargs[1]=held['core'][0]+torch.sigmoid(active[0].cluster_att_gate)*value
  features=active[0].ila(*iargs)[0]
  scores,logits=last.prediction_head(fixed_query,features,mask)
  result['native_task_mask_replays']+=1
  assert fingerprint(torch,fixed_query)==query_hash
  return scores,logits,features
 with torch.no_grad():
  base=message((0,1,2));scores,logits,features=suffix(base)
  controls={'message_reconstruction':error(base,held['message']),'native_features_reconstruction':error(features,held['last_args'][2]),'fixed_query_native_mask_reconstruction':error(logits,held['last'][2]),'fixed_query_native_score_reconstruction':error(scores,held['last'][1])}
  idem=suffix(base+torch.zeros_like(base))
  controls['identity_mask']=error(idem[1],logits)
  p=[torch.cat([torch.arange(len(ids[0][b]),device=x.device).roll(1),torch.arange(len(ids[0][b]),x.shape[1],device=x.device)]) for b in range(len(x))]
  px=torch.stack([x[b,index] for b,index in enumerate(p)]);pm=torch.stack([mask[b,index] for b,index in enumerate(p)])
  pi=[[ids[0][b][p[b][:len(ids[0][b])]] for b in range(len(x))],ids[1],ids[2]]
  perm=cluster.message_norm(original_gather(px,tokens,pi,pm)).masked_fill(pm.unsqueeze(-1),0)
  controls['receiver_permutation_message']=error(perm,torch.stack([base[b,index] for b,index in enumerate(p)]))
  result['controls']=controls
  assert max(controls.values())<=1e-6,controls
  result['controls_passed']=True
  variants={'identity':logits}
  for scale,name in enumerate(('delete_fine','delete_middle','delete_coarse')):
   variants[name]=suffix(message([s for s in range(3) if s!=scale]))[1]
  for b,(qi,ti) in enumerate(indices):
   n=len(ids[0][b]);assert int((~mask[b]).sum())==n
   labels=ids[0][b]
   for q,t in zip(qi.tolist(),ti.tolist()):
    target=targets[b]['masks'][t].bool()
    assert len(target)==n and bool(((targets[b]['masks'][t]==0)|(targets[b]['masks'][t]==1)).all())
    mixed=torch.zeros(n,dtype=torch.bool,device=x.device)
    for cell in labels.unique():
     selected=labels==cell
     if target[selected].any() and (~target[selected]).any():mixed[selected]=True
    row={'expression_index':b,'scene_id':cohort[b//4]['scene_id'],'query':q,'native_target':t,'valid':n,'mixed':int(mixed.sum()),'interior':int((~mixed).sum()),'conditions':{}}
    for name,value in variants.items():
     absolute=(value[b,q,:n].sigmoid()-target.float()).abs()
     row['conditions'][name]={group:float(absolute[selected].mean().cpu()) if bool(selected.any()) else None for group,selected in (('mixed',mixed),('interior',~mixed))}
    if row['mixed'] and row['interior']:
     c=row['conditions']
     def contrast(name):return (c[name]['mixed']-c['identity']['mixed'])-(c[name]['interior']-c['identity']['interior'])
     row['fine_vs_coarse_boundary_interaction']=contrast('delete_fine')-contrast('delete_coarse')
    else:row['fine_vs_coarse_boundary_interaction']=None
    result['records'].append(row)
  assert fingerprint(torch,fixed_query)==query_hash
  result['summary']=summarize(result['records'])
  result.update(execution_completed=True,scene_ids=[s['scene_id'] for s in cohort],expression_count=len(x),fixed_query_sha256=query_hash,input_sha256=fingerprint(torch,batch),prefix_sha256=fingerprint(torch,held['gather']),matching_sha256=fingerprint(torch,matches),native_loss=float(native_loss.cpu()),population_uncertainty='UNKNOWN;fixed TRAIN cohort;matched queries and expressions within scenes are correlated')
except BaseException as exc:
 result.update(error_type=type(exc).__name__,error=str(exc))
 raise
finally:
 if original_gather is not None:cluster._cluster_to_points=original_gather
 for handle in hooks:handle.remove()
 try:save('native_scale_task_pair_'+str(args.pair)+'.json',result)
 finally:release()
