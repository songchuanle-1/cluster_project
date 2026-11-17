"""BTC native two-step smoke and original-handler resources; fresh lease required."""
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



def forest_observation(forest):
    """Read only actual production forest; derive call/source dependencies, not features."""
    groups, plan = [], []
    for parent, root, children, postorder, tokens in forest:
        assert len(tokens) == len(set(tokens)) and tokens
        inside_ids = {token: {token} for token in tokens}
        for node in postorder:
            left, right = children[node]
            assert not inside_ids[left] & inside_ids[right]
            inside_ids[node] = inside_ids[left] | inside_ids[right]
        assert inside_ids[root] == set(tokens)
        outside_ids = {root: set()}
        def entry(kind, node, refs, source_ids):
            return {'map':kind,'parent':parent,'node':node,
                'input_refs':refs,'input_source_ids':[sorted(v) for v in source_ids],
                'output_source_ids':sorted(set().union(*source_ids))}
        for node in postorder:
            if node != root:
                left, right = children[node]
                plan.append(entry('inside',node,[('inside',left),('inside',right)],
                    [inside_ids[left],inside_ids[right]]))
        for node in reversed(postorder):
            left, right = children[node]
            outside_ids[left] = outside_ids[node] | inside_ids[right]
            outside_ids[right] = outside_ids[node] | inside_ids[left]
            assert not outside_ids[left] & inside_ids[left]
            assert not outside_ids[right] & inside_ids[right]
            plan.append(entry('outside',left,[('outside',node),('inside',right)],
                [outside_ids[node],inside_ids[right]]))
            plan.append(entry('outside',right,[('outside',node),('inside',left)],
                [outside_ids[node],inside_ids[left]]))
        for token in tokens:
            assert outside_ids[token] == set(tokens)-{token}
            plan.append(entry('leaf',token,[('inside',token),('outside',token)],
                [{token},outside_ids[token]]))
        n = len(tokens)
        groups.append({'parent':parent,'root':root,'original_middle_ids':list(tokens),
            'n':n,'children':[{'node':node,'left':children[node][0],'right':children[node][1]} for node in postorder],
            'postorder':list(postorder),'root_inside_expected_calls':0,
            'expected_inside_calls':max(0,n-2),'expected_outside_calls':2*max(0,n-1),
            'expected_leaf_calls':n,'leaf_outside_is_exact_structural_complement':True})
    return groups, plan


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
    assert cfg.model.dec.cluster_att_num_layers == 1, 'BTC requires only the original final hierarchy injection'
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
        excluded = ('dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.middle_tree.')
        common = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        result['common_initialized_parameters'] = {
            'scope':'Original common named parameters after native backbone pretrain, before TRAIN loader; exclude exact replaced-middle and new-tree prefixes on both targets; retain middle LayerNorm',
            'excluded_name_prefixes':list(excluded), 'names':list(common), 'tensor_count':len(common),
            'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),
            'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; observation only, not a full-common-state gate'}
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler


def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original TRAIN2 with actual BTC hooks; no auxiliary forward/backward/probe."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('btc-native-smoke'))
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
        for name in ('inside','outside','leaf'):
            module = getattr(att.middle_tree,name)
            assert sum(p.numel() for p in module.parameters()) == 131328
            tracked_modules['tree_'+name] = module
        assert sum(p.numel() for p in att.middle_tree.parameters()) == 393984
    tracked = {name:dict(module.named_parameters()) for name,module in tracked_modules.items()}
    initial = {name:fingerprint(torch,{n:p.detach() for n,p in ps.items()}) for name,ps in tracked.items()}
    calls, rawbanks, csort, readbacks, tree_calls, path_records = [], [], [], [], [], []
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
        tree_module=importlib.import_module(qualified+'.middle_tree')
        original_forest=tree_module.build_parent_forest
        def middle_norm_pre(owner,values):
            assert values[0] is state['raw_refs'][1]
            state['middle_norm_count']+=1
        def middle_norm_post(owner,values,output):
            state['middle_norm_output_ref']=output
        hooks.extend([att.cluster_ffn_norm[1].register_forward_pre_hook(middle_norm_pre),
            att.cluster_ffn_norm[1].register_forward_hook(middle_norm_post)])
        def tree_pre(owner,values):
            features,positions,parents,supported=values
            assert owner is att.middle_tree and features is state['middle_norm_output_ref']
            assert positions is bank.middle_positions and parents is bank.middle_parent_ids and parents is bank.cluster_ids_list[2]
            assert supported is bank.middle_valid and state['middle_norm_count']==1
            record={'forward':state['forward_index'],'input':summary(features),'input_sha256':fingerprint(torch,features),
                'positions_sha256':fingerprint(torch,positions),'ids_sha256':fingerprint(torch,bank.cluster_ids_list),
                'original_middle_norm_calls':state['middle_norm_count'],'map_calls':[],'batches':[],'groups':[],
                'original_tree_forward_calls':1,'native_observer_scope':'Only original forest call and module inputs/outputs; no feature map replay or auxiliary backward',
                'offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED'}
            geometry=[]
            for b in range(features.shape[0]):
                ids0,ids1,ids2=(level[b] for level in bank.cluster_ids_list)
                k=ids2.numel();counts=torch.bincount(ids1[ids0],minlength=k)
                actual_supported=counts>0
                assert torch.equal(actual_supported,supported[b]) and positions[b].shape==(k,3)
                assert not positions[b].requires_grad and parents[b] is ids2
                centers=positions[b].detach().cpu().tolist();parent_values=parents[b].detach().cpu().tolist();valid=supported[b].detach().cpu().tolist()
                geometry.append((centers,parent_values,valid))
                record['batches'].append({'batch':b,'middle_prefix':k,'padded_width':features.shape[1],
                    'centers':centers,'parent_ids':parent_values,'true_supported_original_ids':torch.nonzero(actual_supported,as_tuple=False).flatten().cpu().tolist(),
                    'real_point_counts':counts.cpu().tolist(),'unsupported_internal_ids':torch.nonzero(~actual_supported,as_tuple=False).flatten().cpu().tolist(),
                    'batch_padding_rows':features.shape[1]-k,'support_formula':'bincount(ids1[ids0],minlength=ids2.numel())>0'})
            assert 'tree_context' not in state
            state['tree_context']={'record':record,'features':features,'geometry':geometry,'builder_calls':0,
                'plan':[],'plan_index':0,'values':{},'pending':None,'pending_activation':None}
            watch(features,record,'native_input_gradients')
        def observed_forest(centers,parent_ids,supported,max_middle_tokens):
            context=state['tree_context'];b=context['builder_calls'];context['builder_calls']+=1
            assert (centers,parent_ids,supported)==context['geometry'][b]
            forest=original_forest(centers,parent_ids,supported,max_middle_tokens)
            groups,plan=forest_observation(forest)
            for group in groups:
                group['batch']=b;context['record']['groups'].append(group)
                parent=group['parent']
                for token in group['original_middle_ids']:
                    context['values'][(b,parent,'inside',token)]=context['features'][b,token].detach()
                context['values'][(b,parent,'outside',group['root'])]=None
            for entry in plan:entry['batch']=b
            context['plan'].extend(plan)
            return forest
        setattr(tree_module,'build_parent_forest',observed_forest)
        global_replacements.append((tree_module,'build_parent_forest',original_forest))
        def map_pre(kind):
            def before(owner,values):
                context=state['tree_context'];assert context['pending'] is None
                assert context['pending_activation'] is None
                expected=context['plan'][context['plan_index']];assert expected['map']==kind
                value=values[0];c=att.middle_tree.channels;assert value.shape==(2*c,)
                pieces=(value[:c],value[c:]);source_matches=[]
                for piece,(source_kind,node) in zip(pieces,expected['input_refs']):
                    reference=context['values'][(expected['batch'],expected['parent'],source_kind,node)]
                    exact=bool(piece.detach().eq(0).all()) if reference is None else fingerprint(torch,piece)==fingerprint(torch,reference)
                    source_matches.append(exact);assert exact
                record={**expected,'forward':state['forward_index'],'call_index':context['plan_index'],
                    'input':summary(value),'input_sha256':fingerprint(torch,value),
                    'actual_input_sources_exact':all(source_matches),'root_outside_zero_observed':
                        any(context['values'][(expected['batch'],expected['parent'],k,n)] is None for k,n in expected['input_refs'])}
                assert record['input']['finite'];watch(value,record,'native_input_gradients')
                context['pending']=record
            return before
        def map_post(kind):
            def after(owner,values,output):
                context=state['tree_context'];record=context['pending'];assert record['map']==kind
                record.update(linear_output=summary(output),linear_output_sha256=fingerprint(torch,output))
                assert record['linear_output']['finite']
                if kind=='leaf':
                    record.update(output=summary(output),output_sha256=fingerprint(torch,output))
                    watch(output,record,'native_output_gradients')
                else:
                    # The node value is the actual shared GELU output, not this
                    # Linear's preactivation. Capture it without replaying GELU.
                    assert context['pending_activation'] is None
                    context['pending_activation']=(record,output)
                    watch(output,record,'native_linear_output_gradients')
                context['record']['map_calls'].append(record)
                context['plan_index']+=1;context['pending']=None
            return after
        for kind in ('inside','outside','leaf'):
            module=getattr(att.middle_tree,kind)
            hooks.extend([module.register_forward_pre_hook(map_pre(kind)),module.register_forward_hook(map_post(kind))])
        def activation_post(owner,values,output):
            context=state['tree_context'];record,linear_output=context['pending_activation']
            assert values[0] is linear_output and record['map'] in ('inside','outside')
            record.update(output=summary(output),output_sha256=fingerprint(torch,output),activation_original_calls=1)
            assert record['output']['finite'];watch(output,record,'native_output_gradients')
            context['values'][(record['batch'],record['parent'],record['map'],record['node'])]=output.detach()
            context['pending_activation']=None
        hooks.append(att.middle_tree.activation.register_forward_hook(activation_post))
        def tree_post(owner,values,output):
            context=state.pop('tree_context');record=context['record']
            assert context['pending'] is None and context['pending_activation'] is None and context['plan_index']==len(context['plan'])
            assert context['builder_calls']==output.shape[0] and output.shape==values[0].shape
            for group in record['groups']:
                calls_here=[v for v in record['map_calls'] if (v['batch'],v['parent'])==(group['batch'],group['parent'])]
                for kind in ('inside','outside','leaf'):
                    assert sum(v['map']==kind for v in calls_here)==group['expected_'+kind+'_calls']
                assert not any(v['map']=='inside' and v['node']==group['root'] for v in calls_here)
            untouched=torch.ones(output.shape[:2],dtype=torch.bool,device=output.device)
            for batch in record['batches']:
                ids=batch['true_supported_original_ids']
                if ids:untouched[batch['batch'],torch.tensor(ids,dtype=torch.long,device=output.device)]=False
            assert bool(output.detach()[untouched].eq(0).all())
            record.update(output=summary(output),output_sha256=fingerprint(torch,output),
                returned_original_bank_shape=True,original_ID_inverse_scatter_observed=True,
                unsupported_and_batch_padding_update_zero=True,actual_builder_calls=context['builder_calls'],
                actual_n_ge3_supported_parent_groups=sum(g['n']>=3 for g in record['groups']),
                actual_singleton_supported_parent_groups=sum(g['n']==1 for g in record['groups']),
                actual_unsupported_internal_rows=sum(len(x['unsupported_internal_ids']) for x in record['batches']),
                actual_padding_rows=sum(x['batch_padding_rows'] for x in record['batches']),
                root_inside_actual_calls=sum(v['map']=='inside' and v['node']==g['root'] for g in record['groups'] for v in record['map_calls'] if (v['batch'],v['parent'])==(g['batch'],g['parent'])))
            # Validate actual output rows against original leaf module outputs by hash.
            for call in record['map_calls']:
                if call['map']=='leaf':assert fingerprint(torch,output[call['batch'],call['node']])==call['output_sha256']
            assert record['output']['finite'];watch(output,record,'native_output_gradients')
            state['tree_delta_snapshot']=output.detach().clone();tree_calls.append(record)
        hooks.extend([att.middle_tree.register_forward_pre_hook(tree_pre),att.middle_tree.register_forward_hook(tree_post)])
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
            exact=fingerprint(torch,refined[1])==fingerprint(torch,raw[1].detach()+state['tree_delta_snapshot'])
            record['BTC_middle_original_skip_and_exact_HCG_input']=exact;assert exact
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
        for key in ('raw_refs','raw_record','tree_delta_snapshot','middle_norm_output_ref','encoder_inst_before','encoder_gate','cluster_message'):state.pop(key,None)
        state['ffn_snapshots'].clear()
    def before_step(owner,args,kwargs):
        assert backward_records[-1]['count']==1
        if candidate and tree_calls[-1]['actual_n_ge3_supported_parent_groups']==0:
            result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_N_GE3_PARENT'
            raise RuntimeError('INCONCLUSIVE_COVERAGE: original fixed TRAIN batch did not exercise proper-inside; no replacement sample/seed or mechanism rejection')
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
    def after_step(owner,args,kwargs):
        record=steps[-1];record['optimizer_step_completed']=True
        record['module_after_step_hash']={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
        record['weight_after_step_hash']={n:fingerprint(torch,{k:p.detach() for k,p in ps.items() if k.endswith('weight')}) for n,ps in tracked.items()}
        assert all(record['module_before_step_hash'][n]!=record['module_after_step_hash'][n] and record['weight_before_step_hash'][n]!=record['weight_after_step_hash'][n] for n in tracked)
        result['optimizer_steps']+=1
    hooks.extend([model.register_forward_pre_hook(native_input),model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step),optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False,losses=losses,steps=steps,batches=batches,native_backward_records=backward_records,
        ffn_calls=calls,raw_bank_observations=rawbanks,csort_raw_input_observations=csort,hcg_readbacks=readbacks,
        BTC_tree_observations=tree_calls,inst_to_mask_path_observations=path_records,native_dataloader_config=dict(cfg.dataloader.train),
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',
        actual_champion_candidate_batch_pairing='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both complete raw batch fingerprints and common named initialization',
        smoke_memory_scope='Two native TRAIN steps including observer hooks, detached snapshots, actual topology/source recording; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; no separate no-observer native TRAIN process pair',auxiliary_autograd_grad_or_backward_used=False,
        native_failure_is_not_whole_mechanism_rejection=True,
        coverage_gate_scope='Original fixed TRAIN batches only; absent n>=3 is inconclusive and no sample replacement is allowed',
        dynamic_parameter_inventory={'original_FFN_parameters_by_level':{str(i):sum(p.numel() for p in att.cluster_ffn[i].parameters()) for i in range(3)},
            'new_declared_parameters':sum(p.numel() for p in att.middle_tree.parameters()) if candidate else 0,
            'actual_full_model_parameters':sum(p.numel() for p in model.parameters()),'actual_named_parameter_tensors':sum(1 for _ in model.named_parameters()),
            'state_dict_keys':list(model.state_dict()),'geometry_registered_buffer_names':[n for n,_ in model.named_buffers() if 'middle_positions' in n or 'middle_parent_ids' in n or 'middle_valid' in n]})
    logger=logging.getLogger('btc-native-smoke');logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
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
    assert len(calls)==(4 if candidate else 6) and len(tree_calls)==(2 if candidate else 0)
    for forward in (1,2):assert [v['level'] for v in calls if v['forward']==forward]==list(ffn_levels)
    for record in calls+tree_calls:
        for key in ('native_input_gradients','native_output_gradients'):assert record.get(key) and all(g['finite'] and g['abs_max']>0 for g in record[key])
    for record in tree_calls:
        assert record['actual_n_ge3_supported_parent_groups']>0,'INCONCLUSIVE_COVERAGE: original fixed TRAIN batch did not exercise proper-inside; no replacement sample/seed'
        assert record['root_inside_actual_calls']==0
        proper=[v for v in record['map_calls'] if v['map']=='inside']
        assert proper and any(g['finite'] and g['abs_max']>0 for v in proper for g in v.get('native_output_gradients',[])),'Actual proper-inside loss dependency not observed; not a whole-mechanism rejection'
        for call in record['map_calls']:
            for key in ('native_input_gradients','native_output_gradients'):assert call.get(key) and all(g['finite'] for g in call[key])
        # Per-call gradients may be zero; only aggregate map weights and an actual proper-inside path are required above.
    for record in readbacks:assert record.get('native_point_message_gradients') and all(g['finite'] and g['abs_max']>0 for g in record['native_point_message_gradients'])
    for record in path_records:
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):assert record.get(key) and all(g['finite'] and g['abs_max']>0 for g in record[key])
    final={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
    assert all(final[n]!=initial[n] for n in tracked);verify()
    result.update(execution_completed=True,native_data_loaded=True,native_train_function_executed=True,backward_finite=True,
        intended_path_observed=(len(tree_calls)==2 and all(v['actual_n_ge3_supported_parent_groups']>0 for v in tree_calls)) if candidate else len(calls)==6,
        new_operator_parameters=393984 if candidate else None,native_tracked_initial_hash=initial,native_tracked_after_hash=final,
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
        'native_model_and_yaml_unchanged':False,'source_scope':'Exact native BTC or original M95, original backbone pretrain and native train loop'}
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
