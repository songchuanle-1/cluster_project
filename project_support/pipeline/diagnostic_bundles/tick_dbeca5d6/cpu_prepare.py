"""Exercise native CPU data/model loading; never acquire or initialize CUDA."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
import copy
import importlib
import logging
import sys
from pathlib import Path
from native_runtime import verify,ROOT,NAME,ASSETS,MANIFEST,fingerprint,save

result={'passed':False,'native_forwards':0,'native_backwards':0,'optimizer_steps':0,'batches':[]}
try:
    verify()
    sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
    from tools import train
    import torch,gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized()
    cfg=gorilla.Config.fromfile(ASSETS['config_path'])
    assert Path(cfg.data.train.data_root,'scanrefer/scene_graphs_new_train.json').is_file()
    module=importlib.import_module('framework.model.Quard_model.'+NAME)
    gorilla.set_random_seed(1999)
    model=module.Network(**cfg.model)
    checkpoint=torch.load(ASSETS['checkpoint'],map_location='cpu',weights_only=False,mmap=True)
    state=checkpoint['model'];expected=model.state_dict();extra=set(state)-set(expected)
    assert extra<={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
    assert all(torch.equal(state[k],dict(model.named_buffers())[k]) for k in extra)
    model.load_state_dict({k:v for k,v in state.items() if k not in extra},strict=True)
    result['checkpoint_meta']={k:v for k,v in checkpoint['meta'].items() if isinstance(v,(str,int,float,bool))}
    result['strict_loaded_tensors']=len(expected)
    result['all_parameters_cpu']=all(p.device.type=='cpu' for p in model.parameters())
    assert result['all_parameters_cpu']
    del model,checkpoint,state,expected
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('fle-cpu-prepare'))
    cohort=MANIFEST['cohort']
    for row in cohort:
        group=dataset.scene_inputs[row['group_index']]
        assert group[0]['scene_id']==row['scene_id']
        assert [{'object_id':str(r['object_id']),'ann_id':str(r['ann_id'])} for r in group]==row['expression_ids']
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,[r['group_index'] for r in cohort]),batch_size=1,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    for row,batch in zip(cohort,loader):
        assert batch['scan_ids']==[row['scene_id']]
        assert [str(v) for v in batch['ann_ids']]==[r['ann_id'] for r in row['expression_ids']]
        result['batches'].append({'scene':row['scene_id'],'group_index':row['group_index'],'expressions':len(batch['ann_ids']),
            'collated_input_sha256':fingerprint(torch,batch),'points':len(batch['superpoints'])})
    assert len(result['batches'])==8 and sum(b['expressions'] for b in result['batches'])==32
    assert not torch.cuda.is_initialized()
    verify();result.update(passed=True,cuda_initialized=False,native_model_execution='not_run',
        diagnostic_batch_size=1,diagnostic_workers=0,training_config_unchanged=True,
        limitations='CPU collate fingerprints are preparation receipts;native run must record its own actual augmentation hashes')
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:save('cpu_prepare_result.json',result)
print('FLE_NATIVE_CPU_PREPARATION_PASS')
