"""HVD native two-step smoke and original-handler resources; fresh lease required."""
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



def hvd_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_supported_core_possible':any(x['actual_path_count'] for x in scenes),'total_true_paths':sum(x['actual_path_count'] for x in scenes)}


def hvd_plan_observation(plan,members,valid_count,widths):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[index] for index in fine});coarse=sorted({mc[index] for index in middle})
    assert plan['nodes']==[fine,middle,coarse] and len(points)==valid_count
    expected={'nodes':[fine,middle,coarse],
        'point_to_fine':[fine.index(index) for index in points],
        'fine_to_middle':[middle.index(fm[index]) for index in fine],
        'middle_to_coarse':[coarse.index(mc[index]) for index in middle]}
    assert plan==expected
    output=copy.deepcopy(plan);output.update(point_count=valid_count,true_supported_nodes_by_scale=[len(nodes) for nodes in plan['nodes']],
        unsupported_or_padding_nodes_by_scale=[widths[level]-len(nodes) for level,nodes in enumerate(plan['nodes'])])
    return output


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
    assert cfg.model.dec.cluster_att_num_layers == 1, 'HVD requires only the original final hierarchy injection'
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
        excluded = ('dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.cluster_ffn.2.','dec.cluster_att.variance_decomposition.')
        common = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        result['common_initialized_parameters'] = {
            'scope':'Original common named parameters after native backbone pretrain, before TRAIN loader; exclude only three replaced original FFN prefixes and new variance_decomposition subtree on both targets; retain three original LayerNorms',
            'excluded_name_prefixes':list(excluded), 'names':list(common), 'shapes':{n:list(p.shape) for n,p in common.items()}, 'tensor_count':len(common),
            'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),
            'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; observation only, not a full-common-state gate'}
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler


def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original TRAIN2 with actual HVD hooks; no auxiliary forward/backward/probe."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('hvd-native-smoke'))
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
    ffn_levels = () if candidate else (0,1,2)
    tracked_modules = {'ffn_'+str(i):att.cluster_ffn[i] for i in ffn_levels}
    assert all(sum(p.numel() for p in module.parameters()) == 525568 for module in tracked_modules.values())
    if candidate:
        tracked_modules['variance_decomposition']=att.variance_decomposition
    tracked = {name:dict(module.named_parameters()) for name,module in tracked_modules.items()}
    initial = {name:fingerprint(torch,{n:p.detach() for n,p in ps.items()}) for name,ps in tracked.items()}
    calls, rawbanks, csort, readbacks, exchange_calls, path_records = [], [], [], [], [], []
    losses, steps, batches, backward_records = [], [], [], []
    hooks, replacements, global_replacements = [], [], []
    installations = []
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
        if candidate:
            members=[tuple(level[b].detach().cpu().tolist() for level in bank.cluster_ids_list) for b in range(len(bank.cluster_ids_list[0]))]
            coverage=hvd_coverage_preflight(members)
            result.setdefault('native_coverage_preflight_observations',[]).append(coverage)
            if not coverage['true_supported_core_possible']:
                result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FOREST'
                raise RuntimeError('INCONCLUSIVE_COVERAGE: original fixed TRAIN batch has no supported fine ancestry path before grad watches; no resampling/seed change or mechanism rejection')
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
        core=att.variance_decomposition;graph=importlib.import_module(qualified+'.variance_decomposition')
        original_plan=graph.build_support_plan;original_components=graph.moment_components
        original_group_mean=graph._group_mean;original_pack=graph.pack_moment_rows
        original_cat=torch.cat;original_split=torch.Tensor.split;original_copy=torch.Tensor.index_copy
        def queue_replace(owner,name,replacement,original):installations.append((owner,name,replacement));global_replacements.append((owner,name,original))
        def norm_pre(level):
            def call(owner,values):assert values[0] is state['raw_refs'][level];state['norm_counts'][level]+=1
            return call
        def norm_post(level):
            def call(owner,values,output):state['norm_outputs'][level]=output
            return call
        for level in range(3):hooks.extend([att.cluster_ffn_norm[level].register_forward_pre_hook(norm_pre(level)),att.cluster_ffn_norm[level].register_forward_hook(norm_post(level))])
        def lite_watch(value,record):
            if value.requires_grad:
                def receive(gradient):record['_internal_gradient_flags'].append(torch.isfinite(gradient).all());return None
                hooks.append(value.register_hook(receive))
        def exchange_pre(owner,values):
            points,point_mask,normalized,ids=values
            assert owner is core and ids is bank.cluster_ids_list and state['norm_counts']==[1,1,1]
            assert all(normalized[level] is state['norm_outputs'][level] for level in range(3))
            members=[tuple(level[batch].detach().cpu().tolist() for level in ids) for batch in range(int(points.shape[0]))]
            record={'forward':state['forward_index'],'point_input':summary(points),'point_padding':summary(point_mask),
                'normalized_inputs':[summary(value) for value in normalized],'normalized_bank_sha256':fingerprint(torch,normalized),
                'scene_observations':[],'_internal_gradient_flags':[],
                'native_observer_scope':'Actual true-support builder, original moment_components and its eight original group means, actual five returned moment tensors, original pack, actual packed shared factor Linear/GELU/Linear, original split and three original-ID index_copy outputs. All wrappers call originals once and return original objects. No statistic/map/feature/model/criterion/backward replay.',
                'extra_FP32_Jacobian_minimum_effect_gate':'NOT_IMPLEMENTED_NOT_REQUIRED'}
            assert 'hvd_context' not in state
            state['hvd_context']={'record':record,'members':members,'normalized':normalized,'ids_ref':ids,
                'widths':[int(value.shape[1]) for value in normalized],'scene_contexts':[],'current_scene':None}
            state['hvd_input_points_ref']=points;state['hvd_point_mask_ref']=point_mask
            for level,value in enumerate(normalized):watch(value,record,'native_normalized_level'+str(level)+'_gradients')
        def observed_plan(ids0,ids1,ids2,valid_count,widths):
            c=state['hvd_context'];batch=len(c['scene_contexts'])
            assert (ids0,ids1,ids2)==c['members'][batch] and widths==c['widths'] and valid_count==len(ids0)
            output=original_plan(ids0,ids1,ids2,valid_count,widths)
            observed=hvd_plan_observation(output,(ids0,ids1,ids2),valid_count,widths)
            observed.update(batch=batch,actual_original_builder_calls=1,actual_stats_calls=0,actual_group_mean_calls=0,
                actual_pack_calls=0,actual_factor_concat_calls=0,actual_factor_calls=0,actual_linear_calls=0,
                actual_GELU_calls=0,actual_split_calls=0,actual_final_index_copy_calls=0,
                stats_observations=[],group_mean_observations=[],pack_observations=[],factor_observations=[],restoration_observations=[])
            c['record']['scene_observations'].append(observed)
            scene={'record':observed,'plan':output,'counts':[len(nodes) for nodes in output['nodes']],
                'stats_active':False,'pack_active':False,'factor_active':False,'restoration_level':0}
            c['scene_contexts'].append(scene);c['current_scene']=scene
            return output
        def observed_group_mean(values,labels,count):
            c=state.get('hvd_context');scene=c.get('current_scene') if c else None
            output=original_group_mean(values,labels,count)
            if scene is not None and scene['stats_active']:
                record=scene['record'];record['actual_group_mean_calls']+=1
                info={'ordinal':record['actual_group_mean_calls'],'input':summary(values),'labels':labels.detach().cpu().tolist(),
                    'declared_groups':int(count),'output':summary(output),'original_calls':1,'returned_original_object_unchanged':True}
                assert info['input']['finite'] and info['output']['finite'];record['group_mean_observations'].append(info);lite_watch(output,c['record'])
            return output
        def observed_components(points,p0,p1,p2,fine_count,middle_count,coarse_count):
            c=state['hvd_context'];scene=c['current_scene'];plan=scene['plan']
            assert [fine_count,middle_count,coarse_count]==scene['counts'] and points.shape[0]==scene['record']['point_count']
            assert [value.detach().cpu().tolist() for value in (p0,p1,p2)]==[plan[key] for key in ('point_to_fine','fine_to_middle','middle_to_coarse')]
            scene['stats_active']=True
            try:output=original_components(points,p0,p1,p2,fine_count,middle_count,coarse_count)
            finally:scene['stats_active']=False
            assert len(output)==5 and scene['record']['actual_group_mean_calls']==8
            scene.update(stats_refs=output,p1=p1,p2=p2)
            record=scene['record'];record['actual_stats_calls']+=1
            info={'point_input':summary(points),'point_input_sha256':fingerprint(torch,points),'actual_mapping_sha256':fingerprint(torch,[p0,p1,p2]),
                'moment_names':['fine_variance','middle_within','middle_between','coarse_within','coarse_between'],
                'outputs':[summary(value) for value in output],'output_sha256':fingerprint(torch,output),
                'original_calls':1,'returned_original_tuple_unchanged':True,'moment_arithmetic_replayed':False,
                'statistic_nonzero_or_minimum_effect_gate':False}
            assert info['point_input']['finite'] and all(value['finite'] for value in info['outputs'])
            record['stats_observations'].append(info)
            for value in output:lite_watch(value,c['record'])
            return output
        def observed_pack(normalized,stats,p1,p2):
            c=state['hvd_context'];scene=c['current_scene']
            assert stats is scene['stats_refs'] and p1 is scene['p1'] and p2 is scene['p2']
            scene['pack_active']=True
            try:output=original_pack(normalized,stats,p1,p2)
            finally:scene['pack_active']=False
            assert len(output)==3
            scene['packed_refs']=output;record=scene['record'];record['actual_pack_calls']+=1
            info={'semantic_inputs':[summary(value) for value in normalized],'moment_inputs_are_actual_returned_objects':True,
                'outputs':[summary(value) for value in output],'output_sha256':fingerprint(torch,output),
                'original_calls':1,'returned_original_list_unchanged':True,'packing_replayed':False}
            assert all(value['finite'] for value in info['semantic_inputs']+info['outputs'])
            assert [list(value.shape) for value in output]==[[count,4*core.channels] for count in scene['counts']]
            record['pack_observations'].append(info)
            for value in output:lite_watch(value,c['record'])
            return output
        def observed_cat(values,*args,**kwargs):
            c=state.get('hvd_context');scene=c.get('current_scene') if c else None
            output=original_cat(values,*args,**kwargs)
            if scene is not None and 'packed_refs' in scene and not scene['pack_active'] and not scene['factor_active']:
                dim=kwargs.get('dim',args[0] if args else 0)
                assert dim==0 and len(values)==3 and all(value is scene['packed_refs'][level] for level,value in enumerate(values))
                scene['factor_input_ref']=output;scene['record']['actual_factor_concat_calls']+=1
            return output
        def factor_pre(owner,values):
            c=state['hvd_context'];scene=c['current_scene']
            assert owner is core.factor and values[0] is scene['factor_input_ref']
            scene['factor_active']=True;scene['record']['actual_factor_calls']+=1
        def linear_post(which):
            def call(owner,values,output):
                c=state['hvd_context'];scene=c['current_scene'];record=scene['record']
                if which==0:assert values[0] is scene['factor_input_ref'];scene['first_linear_ref']=output
                else:assert values[0] is scene['activation_ref'];scene['second_linear_ref']=output
                info={'kind':'first_linear' if which==0 else 'second_linear','input':summary(values[0]),'output':summary(output),'original_calls':1}
                assert info['input']['finite'] and info['output']['finite'];record['actual_linear_calls']+=1
                record['factor_observations'].append(info);lite_watch(output,c['record'])
            return call
        def activation_post(owner,values,output):
            c=state['hvd_context'];scene=c['current_scene'];assert values[0] is scene['first_linear_ref']
            scene['activation_ref']=output;scene['record']['actual_GELU_calls']+=1
            info={'kind':'original_GELU','input':summary(values[0]),'output':summary(output),'original_calls':1}
            assert info['input']['finite'] and info['output']['finite'];scene['record']['factor_observations'].append(info);lite_watch(output,c['record'])
        def factor_post(owner,values,output):
            c=state['hvd_context'];scene=c['current_scene'];assert output is scene['second_linear_ref']
            scene['factor_output_ref']=output;scene['factor_active']=False
        def observed_split(tensor,sections,*args,**kwargs):
            c=state.get('hvd_context');scene=c.get('current_scene') if c else None
            output=original_split(tensor,sections,*args,**kwargs)
            if scene is not None and tensor is scene.get('factor_output_ref'):
                assert list(sections)==scene['counts'] and kwargs.get('dim',args[0] if args else 0)==0 and len(output)==3
                scene['split_refs']=output;scene['record']['actual_split_calls']+=1
            return output
        def observed_copy(tensor,dim,index,source,*args,**kwargs):
            c=state.get('hvd_context');scene=c.get('current_scene') if c else None
            output=original_copy(tensor,dim,index,source,*args,**kwargs)
            if scene is not None and 'split_refs' in scene:
                level=scene['restoration_level'];assert level<3 and dim==0
                assert index.detach().cpu().tolist()==scene['plan']['nodes'][level] and source is scene['split_refs'][level]
                assert list(tensor.shape)==[c['widths'][level],core.channels] and bool((tensor==0).all())
                info={'level':level,'original_node_ids':list(scene['plan']['nodes'][level]),'output':summary(output),
                    'source_is_actual_factor_split':True,'zero_initialized_destination':True,'original_calls':1,'returned_original_object_unchanged':True}
                assert info['output']['finite'];scene['record']['restoration_observations'].append(info)
                scene['restoration_level']+=1;scene['record']['actual_final_index_copy_calls']+=1
            return output
        for name,replacement,original in [('build_support_plan',observed_plan,original_plan),('moment_components',observed_components,original_components),('_group_mean',observed_group_mean,original_group_mean),('pack_moment_rows',observed_pack,original_pack)]:queue_replace(graph,name,replacement,original)
        for owner,name,replacement,original in [(torch,'cat',observed_cat,original_cat),(torch.Tensor,'split',observed_split,original_split),(torch.Tensor,'index_copy',observed_copy,original_copy)]:queue_replace(owner,name,replacement,original)
        hooks.extend([core.factor.register_forward_pre_hook(factor_pre),core.factor.register_forward_hook(factor_post),
            core.factor[0].register_forward_hook(linear_post(0)),core.factor[1].register_forward_hook(activation_post),core.factor[2].register_forward_hook(linear_post(1))])
        def exchange_post(owner,values,output):
            c=state.pop('hvd_context');record=c['record'];assert len(c['scene_contexts'])==len(c['members'])
            active=[scene for scene in c['scene_contexts'] if scene['counts'][0]]
            for scene in active:
                item=scene['record'];assert item['actual_stats_calls']==item['actual_pack_calls']==item['actual_factor_concat_calls']==item['actual_factor_calls']==item['actual_GELU_calls']==item['actual_split_calls']==1
                assert item['actual_group_mean_calls']==8 and item['actual_linear_calls']==2 and item['actual_final_index_copy_calls']==3
            for level,value in enumerate(output):
                assert list(value.shape)==list(c['normalized'][level].shape);watch(value,record,'native_output_level'+str(level)+'_gradients')
            record.update(outputs=[summary(value) for value in output],actual_true_fine_paths=sum(scene['counts'][0] for scene in active),
                actual_supported_scene_count=len(active),actual_stats_calls=len(active),actual_group_mean_calls=8*len(active),
                actual_pack_calls=len(active),actual_factor_calls=len(active),actual_linear_calls=2*len(active),actual_GELU_calls=len(active),
                actual_final_index_copy_calls=3*len(active),actual_three_LN_calls=list(state['norm_counts']),
                statistics_and_packing_from_actual_production_calls=True,no_feature_or_statistic_replay=True)
            state['hvd_delta_snapshots']=[value.detach().clone() for value in output];exchange_calls.append(record)
        hooks.extend([core.register_forward_pre_hook(exchange_pre),core.register_forward_hook(exchange_post)])

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
        if candidate:assert point_feats is state['hvd_input_points_ref'] and point_mask is state['hvd_point_mask_ref']
        record={'forward':state['forward_index'],'levels':[summary(x) for x in refined],
            'refined_sha256':fingerprint(torch,[x.detach().clone() for x in refined]),
            'ids_sha256':fingerprint(torch,ids_list),'point_padding':summary(point_mask),'original_residual_levels':{}}
        raw=state['raw_refs']
        for level in (() if candidate else ffn_levels):
            exact=fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['ffn_snapshots'][level])
            record['original_residual_levels'][str(level)]=exact;assert exact
        if candidate:
            exact=[fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['hvd_delta_snapshots'][level]) for level in range(3)]
            record['HVD_original_three_skips_and_exact_HCG_inputs']=exact;assert all(exact)
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
        state['forward_index']+=1;state['ffn_snapshots']={};state['norm_counts']=[0,0,0];state['norm_outputs']={}
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
        for key in ('raw_refs','raw_record','hvd_delta_snapshots','norm_outputs','hvd_input_points_ref','hvd_point_mask_ref','encoder_inst_before','encoder_gate','cluster_message'):state.pop(key,None)
        state['ffn_snapshots'].clear()
    def parameter_blocks():
        return {}  # HVD trainability is assessed across the whole new core.
    def before_step(owner,args,kwargs):
        assert backward_records[-1]['count']==1
        if candidate and not exchange_calls[-1]['actual_true_fine_paths']:
            result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FOREST'
            raise RuntimeError('INCONCLUSIVE_COVERAGE: no true HVD ancestry core, no replacement sample/seed')
        observed={n:p.grad for n,p in model.named_parameters() if p.grad is not None};bad=[n for n,g in observed.items() if not bool(torch.isfinite(g).all())]
        record={'forward':state['forward_index'],'gradient_tensor_count':len(observed),'nonfinite_parameter_names':bad,
            'all_observed_gradients_finite':bool(observed) and not bad,'tracked_module_gradients':{},'optimizer_step_completed':False,
            'module_before_step_hash':{n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()},
            'weight_before_step_hash':{n:fingerprint(torch,{k:p.detach() for k,p in ps.items() if k.endswith('weight')}) for n,ps in tracked.items()},
            'individual_parameter_before_step_hash':{n:{k:fingerprint(torch,p.detach()) for k,p in ps.items()} for n,ps in tracked.items()}}
        steps.append(record);assert observed and not bad
        for name,parameters in tracked.items():
            gradients={n:summary(p.grad) if p.grad is not None else None for n,p in parameters.items()}
            record['tracked_module_gradients'][name]=gradients
            assert gradients and all(g is None or g['finite'] for g in gradients.values())
            if candidate and name=='variance_decomposition':
                assert any(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight')),'Whole variance_decomposition aggregate original-loss weight gradient is zero; local control inconclusive, not whole-mechanism rejection'
            else:
                assert all(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight'))
            record['gradient_gate_scope']='New variance_decomposition core aggregate only; original FFNs on champion retain original weight gates. Individual new maps/rows/bias may be zero or unexercised.'
            if candidate and name=='variance_decomposition':
                weights=[g for n,g in gradients.items() if n.endswith('weight') and g is not None]
                record['whole_variance_decomposition_weight_gradient']={'finite':all(g['finite'] for g in weights),'abs_max':max(g['abs_max'] for g in weights),'observed_weight_tensors':len(weights),'scope':'Aggregate across entire variance_decomposition; individual map zeros/unused legal'}
        record['native_parameter_block_gradients']={}
        record['parameter_block_before_step_hash']={}
        for name,(weight,r0,r1,c0,c1) in parameter_blocks().items():
            info=summary(weight.grad[r0:r1,c0:c1]) if weight.grad is not None else None;record['native_parameter_block_gradients'][name]=info
            assert info is None or info['finite'];record.setdefault('block_gradient_gate_scope','Any optional parameter-block report is descriptive; whole variance_decomposition aggregate weight is the only new nonzero gate.')
            record['parameter_block_before_step_hash'][name]=fingerprint(torch,weight.detach()[r0:r1,c0:c1])
    def after_step(owner,args,kwargs):
        record=steps[-1];record['optimizer_step_completed']=True
        record['module_after_step_hash']={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
        record['weight_after_step_hash']={n:fingerprint(torch,{k:p.detach() for k,p in ps.items() if k.endswith('weight')}) for n,ps in tracked.items()}
        record['individual_parameter_after_step_hash']={n:{k:fingerprint(torch,p.detach()) for k,p in ps.items()} for n,ps in tracked.items()}
        record['individual_parameter_changed']={n:{k:record['individual_parameter_before_step_hash'][n][k]!=record['individual_parameter_after_step_hash'][n][k] for k in ps} for n,ps in tracked.items()}
        record['bias_update_scope']='Recorded only; zero bias gradient or unchanged bias is legal, no separate nonzero/update gate'
        assert all(record['module_before_step_hash'][n]!=record['module_after_step_hash'][n] and record['weight_before_step_hash'][n]!=record['weight_after_step_hash'][n] for n in tracked)
        if candidate:
            record['whole_variance_decomposition_weight_updated']=record['weight_before_step_hash']['variance_decomposition']!=record['weight_after_step_hash']['variance_decomposition']
            record['whole_variance_decomposition_module_updated']=record['module_before_step_hash']['variance_decomposition']!=record['module_after_step_hash']['variance_decomposition']
        record['parameter_block_after_step_hash']={name:fingerprint(torch,weight.detach()[r0:r1,c0:c1]) for name,(weight,r0,r1,c0,c1) in parameter_blocks().items()}
        record['descriptive_parameter_block_changed']={name:record['parameter_block_before_step_hash'][name]!=record['parameter_block_after_step_hash'][name] for name in record['parameter_block_before_step_hash']}
        result['optimizer_steps']+=1
    hooks.extend([model.register_forward_pre_hook(native_input),model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step),optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False,losses=losses,steps=steps,batches=batches,native_backward_records=backward_records,
        ffn_calls=calls,raw_bank_observations=rawbanks,csort_raw_input_observations=csort,hcg_readbacks=readbacks,
        HVD_variance_decomposition_observations=exchange_calls,inst_to_mask_path_observations=path_records,native_dataloader_config=dict(cfg.dataloader.train),
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',
        actual_champion_candidate_batch_pairing='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both complete raw batch fingerprints and common named initialization',
        smoke_memory_scope='Two native TRAIN steps including observer hooks, detached snapshots, actual topology/source recording; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; no separate no-observer native TRAIN process pair',auxiliary_autograd_grad_or_backward_used=False,
        native_failure_is_not_whole_mechanism_rejection=True,
        coverage_gate_scope='Each original fixed TRAIN forward needs at least one true supported forest core. Singleton and degree boundaries are optional NOT_EXERCISED when absent; no resampling. Individual statistic components/maps/rows/columns/biases descriptive only; no component positivity, FP32, minimum-effect/Jacobian or optional coverage gate.',
        dynahvd_parameter_inventory={'original_FFN_parameters_by_level':{str(i):sum(p.numel() for p in att.cluster_ffn[i].parameters()) for i in range(3)},
            'new_declared_parameters':sum(p.numel() for p in att.variance_decomposition.parameters()) if candidate else 0,
            'actual_full_model_parameters':sum(p.numel() for p in model.parameters()),'actual_named_parameter_tensors':sum(1 for _ in model.named_parameters()),
            'state_dict_keys':list(model.state_dict()),'geometry_registered_buffer_names':[n for n,_ in model.named_buffers() if 'middle_positions' in n or 'middle_parent_ids' in n or 'middle_valid' in n]})
    logger=logging.getLogger('hvd-native-smoke');logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
    writer=train.SummaryWriter(cfg.work_dir);torch.cuda.reset_peak_memory_stats()
    try:
        for owner,name,replacement in installations:setattr(owner,name,replacement)
        train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer);torch.cuda.synchronize()
    finally:
        for owner,name,original in reversed(global_replacements):setattr(owner,name,original)
        for owner,name in reversed(replacements):delattr(owner,name)
        for hook in hooks:hook.remove()
        state.clear();writer.flush();writer.close()
    assert len(losses)==len(steps)==len(batches)==len(backward_records)==result['optimizer_steps']==result['native_criterion_backwards']==2
    assert len(rawbanks)==len(readbacks)==len(path_records)==2 and len(csort)==4
    assert len(calls)==(0 if candidate else 6) and len(exchange_calls)==(2 if candidate else 0)
    for forward in (1,2):assert [v['level'] for v in calls if v['forward']==forward]==list(ffn_levels)
    for record in calls:
        for key in ('native_input_gradients','native_output_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    for record in exchange_calls:
        assert record['actual_true_fine_paths']>0 and record['actual_supported_scene_count']>0 and record['actual_stats_calls']==record['actual_pack_calls']==record['actual_factor_calls']==record['actual_GELU_calls']==record['actual_supported_scene_count'] and record['actual_group_mean_calls']==8*record['actual_supported_scene_count'] and record['actual_linear_calls']==2*record['actual_supported_scene_count'] and record['actual_final_index_copy_calls']==3*record['actual_supported_scene_count']
        for level in range(3):
            for key in ('native_normalized_level'+str(level)+'_gradients','native_output_level'+str(level)+'_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
        flags=record.pop('_internal_gradient_flags');record['actual_internal_backward_callbacks']=len(flags)
        record['all_observed_internal_gradients_finite']=bool(torch.stack(flags).all()) if flags else None
        if flags:assert record['all_observed_internal_gradients_finite']
        record['internal_gradient_scope']='Only finite flags aggregated, no per-call/branch/row positivity or callback-completeness gate. Whole HVD-core original-loss gradient/update controls trainability.'
    for record in readbacks:assert record.get('native_point_message_gradients') and all(g['finite'] for g in record['native_point_message_gradients'])
    for record in path_records:
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    final={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
    assert all(final[n]!=initial[n] for n in tracked);verify()
    result.update(execution_completed=True,native_data_loaded=True,native_train_function_executed=True,backward_finite=True,
        intended_path_observed=(len(exchange_calls)==2 and all(v['actual_true_fine_paths']>0 and v['actual_stats_calls']==v['actual_pack_calls']==v['actual_factor_calls']==v['actual_GELU_calls']==v['actual_supported_scene_count'] and v['actual_group_mean_calls']==8*v['actual_supported_scene_count'] and v['actual_final_index_copy_calls']==3*v['actual_supported_scene_count'] for v in exchange_calls)) if candidate else len(calls)==6,
        new_operator_parameters=sum(p.numel() for p in att.variance_decomposition.parameters()) if candidate else None,native_tracked_initial_hash=initial,native_tracked_after_hash=final,
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
        # Private device flags are normally reduced/popped after successful TRAIN2.
        # On an earlier failure, never synchronize CUDA or mask the original error.
        output={str(k):json_safe(v) for k,v in value.items() if k!='_internal_gradient_flags'}
        if '_internal_gradient_flags' in value:
            output['internal_gradient_finiteness_status']='NOT_REDUCED_ON_FAILURE'
            output['unreduced_internal_gradient_callback_count']=len(value['_internal_gradient_flags'])
        return output
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
        'native_model_and_yaml_unchanged':False,'source_scope':'Exact native HVD or original M95, original backbone pretrain and native train loop'}
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
