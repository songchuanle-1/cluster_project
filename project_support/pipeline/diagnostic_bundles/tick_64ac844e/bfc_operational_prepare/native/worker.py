"""BFC native two-step smoke and original-handler resources; fresh lease required."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1')
import argparse
import copy
import importlib
import importlib.util
import itertools
import json
import logging
from pathlib import Path
import sys
import time
from native_runtime import acquire, release, save, sha, verify, observe, fingerprint, MANIFEST, STAGE, ROOT, NAME



def butterfly_plan_observation(plan):
    """Describe actual disjoint rounds; own state is included, not exclusive."""
    groups=[];owner={};active=[]
    for original in plan['groups']:
        order=list(original['order']);n=len(order);assert n and len(set(order))==n
        m=(n-1).bit_length();bits=list(range(m))+list(range(m-2,-1,-1));assert list(original['bits'])==bits
        group={'parent':original['parent'],'order':order,'n':n,'bits':bits,
            'nonpower_of_two':n>1 and bool(n&(n-1)),'multistage':len(bits)>1}
        groups.append(group)
        for rank,token in enumerate(order):assert token not in owner;owner[token]=(group,rank);active.append(token)
    stages=[]
    for round_index,pairs in enumerate(plan['rounds']):
        used=[]
        for parent,bit,left,right in pairs:
            gl,rl=owner[left];gr,rr=owner[right]
            assert gl is gr and gl['parent']==parent and gl['bits'][round_index]==bit
            assert rl<rr and rr==(rl^(1<<bit));used.extend([left,right])
        assert pairs and len(used)==len(set(used))
        stages.append({'kind':'round','round_index':round_index,'pairs':[list(p) for p in pairs],
            'left_ids':[p[2] for p in pairs],'right_ids':[p[3] for p in pairs],
            'participant_ids':sorted(used),'unpaired_active_ids':sorted(set(active)-set(used))})
    singleton_ids=list(plan['singleton_ids']);assert singleton_ids==[g['order'][0] for g in groups if g['n']==1]
    if singleton_ids:stages.append({'kind':'singleton','original_ids':singleton_ids})
    return groups,stages


def setup(target, mode, result):
    sys.path[:0] = [str(ROOT), str(ROOT / 'framework/lib')]
    # Importing this module installs the project's native torch.load compatibility.
    from tools import train
    import torch
    import gorilla
    import yaml
    from framework import resolve_network
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.75, 0)
    base_name = NAME
    candidate_name = MANIFEST['candidate_name']
    selected_name = candidate_name if target == 'candidate' else base_name
    qualified = 'framework.model.Quard_model.' + selected_name
    original_config = Path(MANIFEST['assets']['config_path'])
    candidate_config = STAGE / 'candidate.yaml'
    parent_values = yaml.safe_load(original_config.read_text())
    candidate_values = yaml.safe_load(candidate_config.read_text())
    assert parent_values == candidate_values, 'Only the config filename may identify the independent model'
    source_config = candidate_config if target == 'candidate' else original_config
    values = copy.deepcopy(candidate_values if target == 'candidate' else parent_values)
    original_work_dir = values.get('work_dir')
    # Approved private output-path adaptation only. All data and training values stay native.
    values['work_dir'] = str(STAGE / ('native_' + mode + '_' + target))
    Path(values['work_dir']).mkdir(exist_ok=False)
    config_dir = STAGE / ('runtime_config_' + mode + '_' + target)
    config_dir.mkdir(exist_ok=False)
    config_path = config_dir / (selected_name + '.yaml')
    with config_path.open('x') as stream:
        yaml.safe_dump(values, stream, sort_keys=False)
    check_values = copy.deepcopy(values)
    check_values['work_dir'] = original_work_dir
    assert check_values == parent_values
    cfg = gorilla.Config.fromfile(str(config_path))
    cfg.dist = False  # tools/train.py main's default single-GPU CLI state.
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
    assert cfg.dataloader.train.batch_size == 2 and cfg.dataloader.train.num_workers == 4
    assert cfg.dataloader.train.persistent_workers is True
    gorilla.set_random_seed(1999)
    source_hashes = {}
    if target == 'candidate':
        directory = STAGE / 'candidate_model'
        for name, expected in MANIFEST['candidate_source_hashes'].items():
            observed = sha(directory / name)
            assert observed == expected, name
            source_hashes[name] = observed
        importlib.import_module('framework.model.Quard_model')
        spec = importlib.util.spec_from_file_location(qualified, directory / '__init__.py',
            submodule_search_locations=[str(directory)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(qualified)
        for name, expected in MANIFEST['assets']['source_hashes'].items():
            observed = sha(ROOT / 'framework/model/Quard_model' / base_name / name)
            assert observed == expected, name
            source_hashes[name] = observed
    network = resolve_network(str(config_path))
    assert network is module.Network, 'Native YAML resolver silently selected another model'
    assert network.__module__ == qualified + '.network', 'Unexpected/fallback native Network module'
    assert cfg.model.dec.cluster_att_num_layers == 1, 'BFC requires only the original final hierarchy injection'
    model = network(**cfg.model).cuda()
    # Match tools.train.main: native optimizer/scheduler construction precedes pretrain loading.
    optimizer = gorilla.build_optimizer(model, cfg.optimizer) if mode == 'smoke' else None
    scheduler = gorilla.build_lr_scheduler(optimizer, cfg.lr_scheduler) if optimizer is not None else None
    assert cfg.train.pretrain, 'Native backbone pretrain is required'
    pretrain = Path(cfg.train.pretrain)
    assert pretrain.is_file()
    full_checkpoint = MANIFEST['assets'].get('checkpoint')
    if full_checkpoint:
        assert pretrain.resolve() != Path(full_checkpoint).resolve(), 'No trained M95 full-model checkpoint initialization'
    gorilla.load_checkpoint(model, str(pretrain), strict=False, map_location='cpu')
    model.eval()
    result.update(source_hashes=source_hashes,
        config_sha256=sha(source_config), runtime_config_sha256=sha(config_path),
        original_config_sha256=sha(original_config), model_package=qualified,
        config_source=str(source_config), runtime_config_path=str(config_path),
        configuration_adaptations={'work_dir': {'from': original_work_dir, 'to': cfg.work_dir},
            'dist': 'False, native single-GPU CLI default'},
        initialization={'kind': 'native_train_pretrain', 'path': str(pretrain),
            'sha256': sha(pretrain), 'loader': 'gorilla.load_checkpoint(strict=False,map_location=cpu)',
            'trained_m95_checkpoint_loaded': False, 'seed': 1999},
        native_train_source_sha256=sha(ROOT / 'tools/train.py'),
        data_source={key: {'data_root': value.get('data_root'), 'prefix': value.get('prefix'),
            'type': value.get('type'), 'training': value.get('training')}
            for key, value in cfg.data.items()})
    if mode == 'smoke':
        excluded = ('dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.middle_butterfly.')
        common = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        result['common_initialized_parameters'] = {
            'scope':'Original common named parameters after native backbone pretrain, before TRAIN loader; exclude exact replaced-middle and new-butterfly prefixes on both targets; retain middle LayerNorm',
            'excluded_name_prefixes':list(excluded), 'names':list(common), 'tensor_count':len(common),
            'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),
            'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; observation only, not a full-common-state gate'}
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler


def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original TRAIN2 with actual BFC hooks; no auxiliary forward/backward/probe."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('bfc-native-smoke'))
    loader = build_dataloader(dataset, dist=cfg.dist, **cfg.dataloader.train)
    assert loader.batch_size == 2 and loader.num_workers == 4 and loader.persistent_workers and loader.drop_last
    class TwoNativeBatches:
        def __init__(self,native):self.native,self.sampler=native,native.sampler
        def __len__(self):return 2
        def __iter__(self):yield from itertools.islice(iter(self.native),2)
    att, bank = model.dec.cluster_att, model.dec.cluster_bank
    candidate = result['target'] == 'candidate'
    assert sum(bool(layer.use_cluster) for layer in model.dec.encoder_layers) == 1
    last_encoder = model.dec.encoder_layers[-1]
    assert last_encoder.use_cluster and last_encoder.cluster_gate_type == 'sigmoid'
    assert last_encoder.cluster_message_type == 'context' and cfg.model.dec.dropout == 0.0
    ffn_levels = (0,2) if candidate else (0,1,2)
    tracked_modules = {'ffn_'+str(i):att.cluster_ffn[i] for i in ffn_levels}
    assert all(sum(p.numel() for p in module.parameters()) == 525568 for module in tracked_modules.values())
    if candidate:
        assert sum(p.numel() for p in att.cluster_ffn[1].parameters()) == 0
        assert sum(p.numel() for p in att.middle_butterfly.mix.parameters()) == 262656
        tracked_modules['butterfly_mix'] = att.middle_butterfly.mix
        assert sum(p.numel() for p in att.middle_butterfly.parameters()) == 262656
    tracked = {name:dict(module.named_parameters()) for name,module in tracked_modules.items()}
    initial = {name:fingerprint(torch,{n:p.detach() for n,p in ps.items()}) for name,ps in tracked.items()}
    calls, rawbanks, csort, readbacks, butterfly_calls, path_records = [], [], [], [], [], []
    losses, steps, batches, backward_records = [], [], [], []
    hooks, replacements, global_replacements = [], [], []
    state = {'forward_index':0}
    def summary(value):
        finite=bool(torch.isfinite(value).all())
        return {'shape':list(value.shape),'dtype':str(value.dtype),'finite':finite,
            'nonfinite_count':int((~torch.isfinite(value)).sum()),
            'abs_max':float(value.detach().float().abs().max().cpu()) if value.numel() and finite else (0.0 if not value.numel() else None)}
    def logvar(value):
        value=torch.as_tensor(value).detach();info=summary(value)
        info['value']=float(value.cpu()) if info['finite'] and value.numel()==1 else None
        return info
    def watch(value,record,key):
        assert value.requires_grad,key
        def receive(gradient):
            info=summary(gradient);record.setdefault(key,[]).append(info)
            assert info['finite'];return None
        hooks.append(value.register_hook(receive))
    def replace(owner,name,replacement):
        assert name not in vars(owner),'Expected inherited original method'
        setattr(owner,name,replacement);replacements.append((owner,name))
    original_build=bank.build_cluster_feats
    def observed_build(sp_feats,batch_offsets):
        output=original_build(sp_feats,batch_offsets)
        record={'forward':state['forward_index'],'raw_sha256':fingerprint(torch,[x.detach().clone() for x in output]),
            'id_sha256':fingerprint(torch,bank.cluster_ids_list),'map_sha256':fingerprint(torch,bank.child_cluster_maps),
            'levels':[summary(x) for x in output]}
        rawbanks.append(record);state['raw_refs'],state['raw_record']=output,record
        return output
    replace(bank,'build_cluster_feats',observed_build)
    def ffn_hook(level):
        def observe_ffn(owner,values,output):
            record={'forward':state['forward_index'],'level':level,'input':summary(values[0]),'output':summary(output)}
            assert record['input']['finite'] and record['output']['finite']
            calls.append(record);state['ffn_snapshots'][level]=output.detach().clone()
            watch(values[0],record,'native_input_gradients');watch(output,record,'native_output_gradients')
        return observe_ffn
    for level in ffn_levels:hooks.append(att.cluster_ffn[level].register_forward_hook(ffn_hook(level)))
    if candidate:
        butterfly_module=importlib.import_module(qualified+'.middle_butterfly');original_plan=butterfly_module.build_butterfly_plan
        def middle_norm_pre(owner,values):
            assert values[0] is state['raw_refs'][1];state['middle_norm_count']+=1
        def middle_norm_post(owner,values,output):state['middle_norm_output_ref']=output
        hooks.extend([att.cluster_ffn_norm[1].register_forward_pre_hook(middle_norm_pre),att.cluster_ffn_norm[1].register_forward_hook(middle_norm_post)])
        def butterfly_pre(owner,values):
            features,positions,parents,supported=values
            assert owner is att.middle_butterfly and features is state['middle_norm_output_ref']
            assert positions is bank.middle_positions and parents is bank.middle_parent_ids and parents is bank.cluster_ids_list[2]
            assert supported is bank.middle_valid and state['middle_norm_count']==1
            record={'forward':state['forward_index'],'input':summary(features),'input_sha256':fingerprint(torch,features),
                'positions_sha256':fingerprint(torch,positions),'ids_sha256':fingerprint(torch,bank.cluster_ids_list),
                'original_middle_norm_calls':state['middle_norm_count'],'original_butterfly_forward_calls':1,
                'mix_calls':[],'batches':[],'groups':[],'self_exclusive_claim':False,
                'offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED',
                'native_observer_scope':'Original plan/old-state inputs/mix/GELU/two outputs; reference only copies actual captured outputs, never replays mix/GELU or backward'}
            geometry=[]
            for b in range(features.shape[0]):
                ids0,ids1,ids2=(level[b] for level in bank.cluster_ids_list);k=ids2.numel();counts=torch.bincount(ids1[ids0],minlength=k);actual_supported=counts>0
                assert torch.equal(actual_supported,supported[b]) and positions[b].shape==(k,3) and not positions[b].requires_grad and parents[b] is ids2
                centers=positions[b].detach().cpu().tolist();pv=parents[b].detach().cpu().tolist();valid=supported[b].detach().cpu().tolist();geometry.append((centers,pv,valid))
                record['batches'].append({'batch':b,'middle_prefix':k,'padded_width':features.shape[1],'centers':centers,'parent_ids':pv,
                    'real_point_counts':counts.cpu().tolist(),'true_supported_original_ids':torch.nonzero(actual_supported,as_tuple=False).flatten().cpu().tolist(),
                    'unsupported_internal_ids':torch.nonzero(~actual_supported,as_tuple=False).flatten().cpu().tolist(),'batch_padding_rows':features.shape[1]-k,
                    'support_formula':'bincount(ids1[ids0],minlength=ids2.numel())>0'})
            assert 'butterfly_context' not in state
            state['butterfly_context']={'record':record,'features':features,'geometry':geometry,'builder_calls':0,'sequence':[],
                'index':0,'working':{},'pending':None,'pending_activation':None}
            watch(features,record,'native_input_gradients')
        def observed_plan(centers,parent_ids,supported,max_middle_tokens):
            context=state['butterfly_context'];b=context['builder_calls'];context['builder_calls']+=1
            assert (centers,parent_ids,supported)==context['geometry'][b]
            original=original_plan(centers,parent_ids,supported,max_middle_tokens);groups,sequence=butterfly_plan_observation(original)
            for group in groups:group['batch']=b;context['record']['groups'].append(group)
            for entry in sequence:entry['batch']=b
            context['sequence'].extend(sequence);context['working'][b]=context['features'][b].detach().clone()
            return original
        setattr(butterfly_module,'build_butterfly_plan',observed_plan);global_replacements.append((butterfly_module,'build_butterfly_plan',original_plan))
        def mix_pre(owner,values):
            context=state['butterfly_context'];assert context['pending'] is None and context['pending_activation'] is None
            expected=context['sequence'][context['index']];b=expected['batch'];value=values[0];c=att.middle_butterfly.channels
            if expected['kind']=='round':
                left=torch.tensor(expected['left_ids'],dtype=torch.long,device=value.device);right=torch.tensor(expected['right_ids'],dtype=torch.long,device=value.device)
                refs=[context['working'][b].index_select(0,left),context['working'][b].index_select(0,right)]
            else:
                ids=torch.tensor(expected['original_ids'],dtype=torch.long,device=value.device);own=context['features'][b].detach().index_select(0,ids)
                refs=[own,torch.zeros_like(own)]
            assert value.shape==(refs[0].shape[0],2*c)
            assert all(fingerprint(torch,value[:,j*c:(j+1)*c])==fingerprint(torch,ref) for j,ref in enumerate(refs))
            record={**expected,'forward':state['forward_index'],'call_index':context['index'],'input':summary(value),
                'input_sha256':fingerprint(torch,value),'left_input':summary(refs[0]),'right_input':summary(refs[1]),
                'actual_both_inputs_from_same_old_state':True,'old_state_sha256':fingerprint(torch,context['working'][b]),
                'no_fake_padded_pair_participant':True}
            assert record['input']['finite'];watch(value,record,'native_input_gradients');context['pending']=record
        def mix_post(owner,values,output):
            context=state['butterfly_context'];record=context['pending']
            record.update(linear_output=summary(output),linear_output_sha256=fingerprint(torch,output));assert record['linear_output']['finite']
            watch(output,record,'native_linear_output_gradients');context['pending_activation']=(record,output)
            context['record']['mix_calls'].append(record);context['index']+=1;context['pending']=None
        def activation_post(owner,values,output):
            context=state['butterfly_context'];record,linear_output=context['pending_activation'];assert values[0] is linear_output
            c=att.middle_butterfly.channels;b=record['batch'];old=context['working'][b]
            record.update(output=summary(output),output_sha256=fingerprint(torch,output),activation_original_calls=1,
                left_output=summary(output[:,:c]),right_output=summary(output[:,c:]))
            assert record['output']['finite'];watch(output,record,'native_output_gradients')
            def halves(gradient):
                observed={'left':summary(gradient[:,:c]),'right':summary(gradient[:,c:])}
                assert observed['left']['finite'] and observed['right']['finite']
                record.setdefault('native_output_half_gradients',[]).append(observed);return None
            hooks.append(output.register_hook(halves))
            if record['kind']=='round':
                left=torch.tensor(record['left_ids'],dtype=torch.long,device=output.device);right=torch.tensor(record['right_ids'],dtype=torch.long,device=output.device)
                updated=old.index_copy(0,left,output.detach()[:,:c]).index_copy(0,right,output.detach()[:,c:])
                carried=torch.tensor(record['unpaired_active_ids'],dtype=torch.long,device=output.device)
                assert fingerprint(torch,updated.index_select(0,carried))==fingerprint(torch,old.index_select(0,carried))
                record['unpaired_carry_reference_exact']=True
            else:
                ids=torch.tensor(record['original_ids'],dtype=torch.long,device=output.device);updated=old.index_copy(0,ids,output.detach()[:,:c])
                record['singleton_private_zero_right_input']=record['right_input']['abs_max']==0;assert record['singleton_private_zero_right_input']
            context['working'][b]=updated;record['writeback_reference_sha256']=fingerprint(torch,updated);context['pending_activation']=None
        hooks.extend([att.middle_butterfly.mix.register_forward_pre_hook(mix_pre),att.middle_butterfly.mix.register_forward_hook(mix_post),att.middle_butterfly.activation.register_forward_hook(activation_post)])
        def butterfly_post(owner,values,output):
            context=state.pop('butterfly_context');record=context['record']
            assert context['pending'] is None and context['pending_activation'] is None and context['index']==len(context['sequence'])
            assert context['builder_calls']==output.shape[0] and output.shape==values[0].shape
            for batch in record['batches']:
                b=batch['batch'];ids=torch.tensor(batch['true_supported_original_ids'],dtype=torch.long,device=output.device)
                reference=output[b].new_zeros(output[b].shape).index_copy(0,ids,context['working'][b].index_select(0,ids))
                assert fingerprint(torch,output[b])==fingerprint(torch,reference)
            record.update(output=summary(output),output_sha256=fingerprint(torch,output),actual_builder_calls=context['builder_calls'],
                original_ID_inverse_scatter_observed=True,returned_original_bank_shape=True,unsupported_and_batch_padding_update_zero=True,
                final_writeback_from_actual_outputs_reference_exact=True,
                actual_n_ge3_supported_parent_groups=sum(g['n']>=3 for g in record['groups']),
                actual_nonpower2_supported_parent_groups=sum(g['nonpower_of_two'] for g in record['groups']),
                actual_multistage_supported_parent_groups=sum(g['multistage'] for g in record['groups']),
                actual_round_mix_calls=sum(c['kind']=='round' for c in record['mix_calls']),
                actual_singleton_mix_calls=sum(c['kind']=='singleton' for c in record['mix_calls']),
                actual_supported_singleton_groups=sum(g['n']==1 for g in record['groups']),
                actual_unsupported_internal_rows=sum(len(x['unsupported_internal_ids']) for x in record['batches']),actual_padding_rows=sum(x['batch_padding_rows'] for x in record['batches']))
            assert record['output']['finite'];record['actual_output_requires_grad']=bool(output.requires_grad)
            coverage=(record['actual_n_ge3_supported_parent_groups']>0 and record['actual_nonpower2_supported_parent_groups']>0 and record['actual_multistage_supported_parent_groups']>0)
            if not coverage:
                record['native_coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_LACKS_REQUIRED_REAL_PARENT_PATH'
                result['coverage_status']=record['native_coverage_status'];butterfly_calls.append(record)
                raise RuntimeError('INCONCLUSIVE_COVERAGE: original fixed TRAIN batch lacks n3/nonpower2/multistage; no replacement sample/seed or whole-mechanism rejection')
            assert output.requires_grad,'Exercised BFC output lost native autograd path'
            watch(output,record,'native_output_gradients');state['butterfly_delta_snapshot']=output.detach().clone();butterfly_calls.append(record)
        hooks.extend([att.middle_butterfly.register_forward_pre_hook(butterfly_pre),att.middle_butterfly.register_forward_hook(butterfly_post)])
    original_csort=att._cross_scale_orth_loss
    def observed_csort(coarse_tokens,fine_tokens,child_maps):
        raw=state['raw_refs'];pair=next((i for i in range(2) if coarse_tokens is raw[i+1] and fine_tokens is raw[i]),None)
        assert pair is not None and child_maps is bank.child_cluster_maps[pair]
        before=fingerprint(torch,[coarse_tokens.detach().clone(),fine_tokens.detach().clone()])
        value=original_csort(coarse_tokens,fine_tokens,child_maps);assert fingerprint(torch,[coarse_tokens,fine_tokens])==before
        csort.append({'forward':state['forward_index'],'pair':pair,'original_raw_objects':True,
            'original_childmap_object':True,'input_sha256':before,'output':logvar(value),'original_calls':1})
        return value
    replace(att,'_cross_scale_orth_loss',observed_csort)
    original_readback=att._cluster_to_points
    def observed_readback(point_feats,refined,ids_list,point_mask):
        assert ids_list is bank.cluster_ids_list
        record={'forward':state['forward_index'],'levels':[summary(x) for x in refined],
            'refined_sha256':fingerprint(torch,[x.detach().clone() for x in refined]),
            'ids_sha256':fingerprint(torch,ids_list),'point_padding':summary(point_mask),'original_residual_levels':{}}
        raw=state['raw_refs']
        for level in ffn_levels:
            exact=fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['ffn_snapshots'][level])
            record['original_residual_levels'][str(level)]=exact;assert exact
        if candidate:
            exact=fingerprint(torch,refined[1])==fingerprint(torch,raw[1].detach()+state['butterfly_delta_snapshot'])
            record['BFC_middle_original_skip_and_exact_HCG_input']=exact;assert exact
        output=original_readback(point_feats,refined,ids_list,point_mask);record['output']=summary(output)
        readbacks.append(record);watch(output,record,'native_point_message_gradients');return output
    replace(att,'_cluster_to_points',observed_readback)
    def last_encoder_pre(owner,values):
        assert state.get('encoder_inst_before') is None
        state['encoder_inst_before']=values[2].detach().clone();state['encoder_gate']=torch.sigmoid(owner.cluster_att_gate).detach().clone()
    def attention_post(owner,values,output):state['cluster_message']=output['point'].detach().clone()
    def ila_pre(owner,values):
        exact=fingerprint(torch,values[1])==fingerprint(torch,state['encoder_inst_before']+state['encoder_gate']*state['cluster_message'])
        record={'forward':state['forward_index'],'inst_before_sha256':fingerprint(torch,state['encoder_inst_before']),
            'cluster_message_sha256':fingerprint(torch,state['cluster_message']),'gate':logvar(state['encoder_gate']),
            'ILA_query_sha256':fingerprint(torch,values[1]),'single_native_inst_update_exact':exact,'new_extra_injection':False}
        assert exact;watch(values[1],record,'native_post_cluster_inst_gradients');path_records.append(record)
    def last_encoder_post(owner,values,output):watch(output[1],path_records[-1],'native_post_ILA_inst_gradients')
    def decoder_post(owner,values,output):watch(output['masks'],path_records[-1],'native_final_mask_gradients')
    hooks.extend([last_encoder.register_forward_pre_hook(last_encoder_pre),att.register_forward_hook(attention_post),
        last_encoder.ila.register_forward_pre_hook(ila_pre),last_encoder.register_forward_hook(last_encoder_post),
        model.dec.register_forward_hook(decoder_post)])
    def native_input(owner,values):
        state['forward_index']+=1;state['ffn_snapshots']={};state['middle_norm_count']=0
        batch=values[0];batches.append({'sha256':fingerprint(torch,batch),'scan_ids':[str(x) for x in batch.get('scan_ids',[])],
            'ann_ids':[int(x) for x in batch.get('ann_ids',[])],'scenes_len':[int(x) for x in batch.get('scenes_len',[])]})
    def native_output(owner,values,output):
        loss,variables=output;result.setdefault('loss_tensor_observations',[]).append(logvar(loss))
        result.setdefault('loss_component_observations',[]).append({k:logvar(v) for k,v in variables.items()})
        assert loss.numel()==1 and bool(torch.isfinite(loss).all())
        losses.append(float(loss.detach().cpu()));result['native_loss_forwards']+=1
        record={'forward':state['forward_index'],'count':0};backward_records.append(record)
        def loss_backward(gradient):
            record['count']+=1;record['gradient']=summary(gradient)
            assert record['count']==1 and record['gradient']['finite'];result['native_criterion_backwards']+=1;return None
        hooks.append(loss.register_hook(loss_backward))
        raw_record=state['raw_record'];raw_record['unchanged_after_full_forward']=fingerprint(torch,state['raw_refs'])==raw_record['raw_sha256']
        raw_record['ids_unchanged_after_full_forward']=fingerprint(torch,bank.cluster_ids_list)==raw_record['id_sha256']
        raw_record['maps_unchanged_after_full_forward']=fingerprint(torch,bank.child_cluster_maps)==raw_record['map_sha256']
        assert all(raw_record[k] for k in ('unchanged_after_full_forward','ids_unchanged_after_full_forward','maps_unchanged_after_full_forward'))
        for key in ('raw_refs','raw_record','butterfly_delta_snapshot','middle_norm_output_ref','encoder_inst_before','encoder_gate','cluster_message'):state.pop(key,None)
        state['ffn_snapshots'].clear()
    def parameter_blocks():
        if not candidate:return {}
        c=att.middle_butterfly.channels;weight=att.middle_butterfly.mix.weight
        return {'left_output_from_left_input':(weight,0,c,0,c),'left_output_from_right_input':(weight,0,c,c,2*c),
            'right_output_from_left_input':(weight,c,2*c,0,c),'right_output_from_right_input':(weight,c,2*c,c,2*c)}
    def before_step(owner,args,kwargs):
        assert backward_records[-1]['count']==1
        if candidate and (butterfly_calls[-1]['actual_n_ge3_supported_parent_groups']==0 or butterfly_calls[-1]['actual_nonpower2_supported_parent_groups']==0 or butterfly_calls[-1]['actual_multistage_supported_parent_groups']==0):
            result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_N_GE3_NONPOWER2_MULTISTAGE_PARENT'
            raise RuntimeError('INCONCLUSIVE_COVERAGE: original fixed TRAIN batch did not exercise n>=3/nonpower2/multistage real butterfly; no replacement sample/seed or mechanism rejection')
        observed={n:p.grad for n,p in model.named_parameters() if p.grad is not None};bad=[n for n,g in observed.items() if not bool(torch.isfinite(g).all())]
        record={'forward':state['forward_index'],'gradient_tensor_count':len(observed),'nonfinite_parameter_names':bad,
            'all_observed_gradients_finite':bool(observed) and not bad,'tracked_module_gradients':{},'optimizer_step_completed':False,
            'module_before_step_hash':{n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()},
            'weight_before_step_hash':{n:fingerprint(torch,{k:p.detach() for k,p in ps.items() if k.endswith('weight')}) for n,ps in tracked.items()}}
        steps.append(record);assert observed and not bad
        for name,parameters in tracked.items():
            gradients={n:summary(p.grad) if p.grad is not None else None for n,p in parameters.items()}
            record['tracked_module_gradients'][name]=gradients
            assert gradients and all(g is not None and g['finite'] for g in gradients.values())
            assert all(g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight')),'Native tracked weight gradient is zero; local path control failed, not whole-mechanism rejection; no seed/readout change'
        record['native_parameter_block_gradients']={}
        record['parameter_block_before_step_hash']={}
        for name,(weight,r0,r1,c0,c1) in parameter_blocks().items():
            assert weight.grad is not None
            info=summary(weight.grad[r0:r1,c0:c1]);record['native_parameter_block_gradients'][name]=info
            assert info['finite'] and info['abs_max']>0,'Native required butterfly quadrant loss gradient missing/zero; local path control, not whole-mechanism rejection'
            record['parameter_block_before_step_hash'][name]=fingerprint(torch,weight.detach()[r0:r1,c0:c1])
    def after_step(owner,args,kwargs):
        record=steps[-1];record['optimizer_step_completed']=True
        record['module_after_step_hash']={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
        record['weight_after_step_hash']={n:fingerprint(torch,{k:p.detach() for k,p in ps.items() if k.endswith('weight')}) for n,ps in tracked.items()}
        assert all(record['module_before_step_hash'][n]!=record['module_after_step_hash'][n] and record['weight_before_step_hash'][n]!=record['weight_after_step_hash'][n] for n in tracked)
        record['parameter_block_after_step_hash']={name:fingerprint(torch,weight.detach()[r0:r1,c0:c1]) for name,(weight,r0,r1,c0,c1) in parameter_blocks().items()}
        assert all(record['parameter_block_before_step_hash'][name]!=record['parameter_block_after_step_hash'][name] for name in record['parameter_block_before_step_hash'])
        result['optimizer_steps']+=1
    hooks.extend([model.register_forward_pre_hook(native_input),model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step),optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False,losses=losses,steps=steps,batches=batches,native_backward_records=backward_records,
        ffn_calls=calls,raw_bank_observations=rawbanks,csort_raw_input_observations=csort,hcg_readbacks=readbacks,
        BFC_butterfly_observations=butterfly_calls,inst_to_mask_path_observations=path_records,native_dataloader_config=dict(cfg.dataloader.train),
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',
        actual_champion_candidate_batch_pairing='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both complete raw batch fingerprints and common named initialization',
        smoke_memory_scope='Two native TRAIN steps including observer hooks, detached snapshots, actual topology/source recording; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; no separate no-observer native TRAIN process pair',auxiliary_autograd_grad_or_backward_used=False,
        native_failure_is_not_whole_mechanism_rejection=True,
        coverage_gate_scope='Original fixed TRAIN batches only; absent n>=3/nonpower2/multistage is inconclusive and no sample replacement is allowed',
        dynamic_parameter_inventory={'original_FFN_parameters_by_level':{str(i):sum(p.numel() for p in att.cluster_ffn[i].parameters()) for i in range(3)},
            'new_declared_parameters':sum(p.numel() for p in att.middle_butterfly.parameters()) if candidate else 0,
            'actual_full_model_parameters':sum(p.numel() for p in model.parameters()),'actual_named_parameter_tensors':sum(1 for _ in model.named_parameters()),
            'state_dict_keys':list(model.state_dict()),'geometry_registered_buffer_names':[n for n,_ in model.named_buffers() if 'middle_positions' in n or 'middle_parent_ids' in n or 'middle_valid' in n]})
    logger=logging.getLogger('bfc-native-smoke');logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
    writer=train.SummaryWriter(cfg.work_dir);torch.cuda.reset_peak_memory_stats()
    try:
        train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer);torch.cuda.synchronize()
    finally:
        for owner,name,original in reversed(global_replacements):setattr(owner,name,original)
        for owner,name in reversed(replacements):delattr(owner,name)
        for hook in hooks:hook.remove()
        state.clear();writer.flush();writer.close()
    assert len(losses)==len(steps)==len(batches)==len(backward_records)==result['optimizer_steps']==result['native_criterion_backwards']==2
    assert len(rawbanks)==len(readbacks)==len(path_records)==2 and len(csort)==4
    assert len(calls)==(4 if candidate else 6) and len(butterfly_calls)==(2 if candidate else 0)
    for forward in (1,2):assert [v['level'] for v in calls if v['forward']==forward]==list(ffn_levels)
    for record in calls+butterfly_calls:
        for key in ('native_input_gradients','native_output_gradients'):assert record.get(key) and all(g['finite'] and g['abs_max']>0 for g in record[key])
    for record in butterfly_calls:
        assert record['actual_n_ge3_supported_parent_groups']>0 and record['actual_nonpower2_supported_parent_groups']>0 and record['actual_multistage_supported_parent_groups']>0,'INCONCLUSIVE_COVERAGE: original fixed TRAIN batch lacks n3/nonpower2/multistage; no replacement sample/seed'
        round_calls=[c for c in record['mix_calls'] if c['kind']=='round']
        assert round_calls and all(c.get('native_output_half_gradients') and all(g['left']['finite'] and g['right']['finite'] for g in c['native_output_half_gradients']) for c in round_calls),'Actual round output-half loss gradient records missing or nonfinite; zero halves are allowed'
        for call in record['mix_calls']:
            for key in ('native_input_gradients','native_output_gradients'):assert call.get(key) and all(g['finite'] for g in call[key])
        # Individual rows/calls/halves may have zero gradients; native four weight quadrants are checked separately.
    for record in readbacks:assert record.get('native_point_message_gradients') and all(g['finite'] and g['abs_max']>0 for g in record['native_point_message_gradients'])
    for record in path_records:
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):assert record.get(key) and all(g['finite'] and g['abs_max']>0 for g in record[key])
    final={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
    assert all(final[n]!=initial[n] for n in tracked);verify()
    result.update(execution_completed=True,native_data_loaded=True,native_train_function_executed=True,backward_finite=True,
        intended_path_observed=(len(butterfly_calls)==2 and all(v['actual_n_ge3_supported_parent_groups']>0 and v['actual_nonpower2_supported_parent_groups']>0 and v['actual_multistage_supported_parent_groups']>0 for v in butterfly_calls)) if candidate else len(calls)==6,
        new_operator_parameters=262656 if candidate else None,native_tracked_initial_hash=initial,native_tracked_after_hash=final,
        native_tracked_each_module_updated=True,observer_readout_complete=True,native_smoke_checks_passed=True,wrappers_and_hooks_restored=True,
        training_checkpoint_saved=False,native_smoke_training=True,new_training=0,optimizer_type=type(optimizer).__name__,
        scheduler_type=type(scheduler).__name__,smoke_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        smoke_peak_reserved_bytes=torch.cuda.max_memory_reserved(),after=observe())


def resources(torch, gorilla, cfg, model, result):
    import numpy as np
    from framework.dataset import build_dataset, build_dataloader
    import fvcore
    from fvcore.nn import FlopCountAnalysis
    profile_cfg = copy.deepcopy(cfg.data.val)
    profile_cfg.lang_num_max = 1
    dataset = build_dataset(profile_cfg, logging.getLogger('mdc-resource-only'))
    loader_cfg = copy.deepcopy(cfg.dataloader.val)
    loader_cfg.batch_size = 1
    loader_cfg.num_workers = 0
    loader_cfg.persistent_workers = False
    gorilla.set_random_seed(1999)
    sample = next(iter(build_dataloader(dataset, training=False, **loader_cfg)))
    assert len(sample['ann_ids']) == len(sample['scan_ids']) == 1
    signature = fingerprint(torch, sample)
    handlers = {name: sha(Path(importlib.import_module('fvcore.nn.' + name).__file__))
        for name in ('flop_count', 'jit_analysis', 'jit_handles')}
    expected = {'flop_count': 'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba',
        'jit_analysis': '110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31',
        'jit_handles': 'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}
    assert handlers == expected, 'Historical profiler handlers must not change'
    model.eval()
    flags = {key: value.requires_grad for key, value in model.named_parameters()}
    with torch.no_grad():
        analysis = FlopCountAnalysis(model, (sample, 'predict'))
        analysis.unsupported_ops_warnings(False)
        analysis.uncalled_modules_warnings(False)
        total = analysis.total()
        result['native_predict_calls'] += 1
        result['profile'] = {'flops': float(total), 'flops_g': float(total / 1e9),
            'within10G': bool(total <= 10e9), 'fvcore_version': fvcore.__version__,
            'profiler_file_sha256': handlers, 'by_operator': {key: float(value) for key, value in analysis.by_operator().items()},
            'unsupported_ops': dict(analysis.unsupported_ops())}
        for _ in range(20):
            model(sample, mode='predict')
            result['native_predict_calls'] += 1
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        times = []
        for _ in range(100):
            torch.cuda.synchronize()
            start = time.perf_counter()
            prediction = model(sample, mode='predict')
            torch.cuda.synchronize()
            times.append((time.perf_counter() - start) * 1000)
            result['native_predict_calls'] += 1
        assert prediction['piou'] and all(bool(torch.isfinite(value).all()) for value in prediction['piou'])
    assert fingerprint(torch, sample) == signature
    assert {key: value.requires_grad for key, value in model.named_parameters()} == flags
    verify()
    result.update(execution_completed=True, input_sha256=signature, scan_ids=sample['scan_ids'],
        ann_ids=sample['ann_ids'], parameters=sum(value.numel() for value in model.parameters()),
        batch_size=1, lang_num_max=1, warmup=20, repeat=100, median_ms=float(np.median(times)),
        p90_ms=float(np.percentile(times, 90)), measurements_ms=times,
        peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved(),
        full_optimizer_training_peak='UNKNOWN; separate resource process, no optimizer or scheduler steps',
        original_no_cluster_resource_delta='UNKNOWN; no-cluster baseline not measured',
        validation_accuracy_evaluated_for_selection=False, parameter_flags_preserved=True,
        source_body_executed_without_replacement=True, after=observe())

def json_safe(value):
    import math
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [json_safe(v) for v in value]
    return value

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--lease',required=True)
    parser.add_argument('--mode',choices=['smoke','resources'],required=True)
    parser.add_argument('--target',choices=['candidate','champion'],required=True)
    args=parser.parse_args()
    result={'execution_completed':False,'mode':args.mode,'target':args.target,
        'candidate_id':MANIFEST.get('candidate_id'),'code_commit':MANIFEST.get('code_commit'),
        'goal_sha256':MANIFEST.get('goal_sha256'),'optimizer_steps':0,'native_loss_forwards':0,
        'native_criterion_backwards':0,'native_predict_calls':0,'new_training':0,
        'native_model_and_yaml_unchanged':False,'source_scope':'Exact native BFC or original M95, original backbone pretrain and native train loop'}
    result.update(experiment_id=MANIFEST['experiment_id'],config=MANIFEST['config'],
        native_manifest_sha256=sha(STAGE/'native_manifest.json'),
        diagnostic_worker_sha256=sha(Path(__file__)),runtime_sha256=sha(STAGE/'native_runtime.py'),
        source_preparation_sha256=MANIFEST['source_preparation_sha256'],
        stage=str(STAGE),physical_gpu=MANIFEST['physical_gpu'],gpu_uuid=MANIFEST['gpu_uuid'],
        current_token=MANIFEST['current_token'],tick_generated_at=MANIFEST['tick_generated_at'],
        deadline_at=MANIFEST['deadline_at'],context_sha256=MANIFEST['context_sha256'],pending_sha256=MANIFEST['pending_sha256'])
    try:
        result['before']=acquire(args.lease)
        torch,gorilla,cfg,model,qualified,train,optimizer,scheduler=setup(args.target,args.mode,result)
        result['native_model_and_yaml_unchanged']=True
        if args.mode=='smoke':
            smoke(torch,gorilla,cfg,model,qualified,train,optimizer,scheduler,result)
        else:
            resources(torch,gorilla,cfg,model,result)
    except BaseException as error:
        import traceback
        result.update(error_type=type(error).__name__,error=str(error))
        traceback.print_exc()
        raise
    finally:
        try:
            save(args.mode+'_'+args.target+'_result.json',json_safe(result))
        finally:
            release()
            print(json.dumps({'execution_completed':result['execution_completed'],
                'optimizer_steps':result['optimizer_steps'],'result_mode':args.mode,'target':args.target}),flush=True)

if __name__=='__main__':
    main()
