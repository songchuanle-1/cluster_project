"""Prepare M95 on CPU, or capture its unchanged feature path under GPU guards."""
import argparse
import copy
import datetime
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
ROOT=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
CHECKPOINT=ROOT.parent/'Cluster_checkpoints'/MODEL/'20260815_101011/best.pth'
CHECKPOINT_SHA='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
UUID='GPU-7f82edb9-f620-8045-caea-a75232265cd1'
GROUPS=(0,60,101,124)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def resource_guard():
    raw=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
    cells=[x.strip() for x in raw.split(',')]
    assert cells[:2]==['0',UUID]
    processes=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
    own=0
    for row in processes.splitlines():
        pid,memory=[int(x.strip()) for x in row.split(',')]
        assert pid==os.getpid(),'Other NVML context present; do not launch'
        own+=memory
    assert int(cells[4])+own>=30000,'Original idle-equivalent memory guard refused'
    assert own<=int(int(cells[2])*.25)+1024,'Original diagnostic allocator guard refused'
    return {'gpu':raw,'processes':processes,'observed_at':datetime.datetime.now().astimezone().isoformat()}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--output')
    parser.add_argument('--token',required=True)
    args=parser.parse_args()
    assert len(args.token)==32 and all(c in '0123456789abcdef' for c in args.token)
    assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
    os.environ.update(CUDA_VISIBLE_DEVICES='' if args.prepare_only else '0',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
    locks=[]
    try:
        if not args.prepare_only:
            resource_guard()
            for name in ('/tmp/cluster_project_gpu0_m201_migration.lock','/tmp/cluster_project_gpu0_exclusive.lock','/tmp/cluster_project_gpu0_parameter_transport.lock'):
                handle=open(name,'a+b')
                fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                locks.append(handle)
            resource_guard()
        sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
        import torch,gorilla
        torch.set_num_threads(1)
        assert not torch.cuda.is_initialized()
        config=ROOT/'configs/Quard/ctf_hcg_csort'/(MODEL+'.yaml')
        assert sha(config)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
        assert sha(ROOT/'framework/model/Quard_model'/MODEL/'hier_postprocess.py')=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
        assert sha(CHECKPOINT)==CHECKPOINT_SHA
        cfg=gorilla.Config.fromfile(str(config))
        assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
        cfg.model.data_root=cfg.data.train.data_root='/home/songcl/data/data/'
        gorilla.set_random_seed(1999)
        mod=importlib.import_module('framework.model.Quard_model.'+MODEL)
        model=mod.Network(**cfg.model)
        state=torch.load(CHECKPOINT,map_location='cpu',weights_only=False,mmap=True)['model']
        extra=set(state)-set(model.state_dict())
        allowed={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
        assert extra<=allowed,extra
        buffers=dict(model.named_buffers())
        for key in extra:
            assert key in buffers and torch.equal(state[key],buffers[key])
        incompatible=model.load_state_dict({k:v for k,v in state.items() if k not in extra},strict=True)
        assert not incompatible.missing_keys and not incompatible.unexpected_keys
        preparation={'token':args.token,'checkpoint_sha256':CHECKPOINT_SHA,'config_sha256':sha(config),'strict_state_load':True,
                     'serialized_buffer_keys_verified':sorted(extra),'model_parameter_tensors':len(tuple(model.parameters())),
                     'frozen_groups':list(GROUPS),'cuda_initialized':torch.cuda.is_initialized(),'native_network_forwards':0,
                     'scope':'CPU model construction and exact weight load only; no native forward/backward or resource admission.'}
        if args.prepare_only:
            assert not torch.cuda.is_initialized()
            print('FEATURE_NATIVE_PREPARE_JSON='+json.dumps(preparation))
            return
        assert args.output
        output=Path(args.output).resolve()
        assert output.is_relative_to(ROOT.parent/'pipeline') and not output.exists()
        from framework.dataset import build_dataset
        import logging
        from torch.utils.data import DataLoader,Subset
        dataset=build_dataset(cfg.data.train,logging.getLogger('m95-feature-native'))
        loader=DataLoader(Subset(dataset,list(GROUPS)),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
        torch.cuda.set_per_process_memory_fraction(.25,0)
        model.cuda().train()
        records=[]
        def cpu(value):
            if torch.is_tensor(value):return value.detach().cpu().clone()
            if isinstance(value,dict):return {k:cpu(v) for k,v in value.items()}
            if isinstance(value,list):return [cpu(v) for v in value]
            if isinstance(value,tuple):return tuple(cpu(v) for v in value)
            return copy.deepcopy(value)
        held={}
        def cluster_hook(module,inputs,result):
            held['cluster']={'inputs':cpu(inputs),'point_message':cpu(result['point']),'state':cpu(module.state_dict())}
        def decoder_hook(module,inputs,result):
            held['head']={'raw_query':cpu(result[0]),'normalized_query':cpu(module.out_norm(result[0])),
                          'inst_feats':cpu(inputs[2]),'batch_mask':cpu(inputs[3]),'pred_masks':cpu(result[2])}
        hooks=[model.dec.cluster_att.register_forward_hook(cluster_hook),model.dec.decoder_layers[-1].register_forward_hook(decoder_hook)]
        try:
            for trial in range(2):
                gorilla.set_random_seed(1999)
                for pair,batch in enumerate(loader):
                    resource_guard()
                    held.clear()
                    with torch.no_grad():loss,_=model(copy.deepcopy(batch),mode='loss')
                    assert torch.isfinite(loss).all()
                    assert set(held)=={'cluster','head'}
                    records.append({'trial':trial,'pair':pair,'ann_ids':batch['ann_ids'],'scan_ids':batch['scan_ids'],
                                    'batch_offsets':cpu(batch['batch_offsets']),'scenes_len':cpu(batch['scenes_len']),**held})
        finally:
            for hook in hooks:hook.remove()
        output.parent.mkdir(parents=True,exist_ok=True)
        torch.save({'preparation':preparation,'records':records,'optimizer_steps':0,'training_started':False},output)
        print('FEATURE_NATIVE_CAPTURE_JSON='+json.dumps({'path':str(output),'sha256':sha(output),'network_forwards':len(records),'optimizer_steps':0}))
    finally:
        for handle in reversed(locks):handle.close()


if __name__=='__main__':
    main()
