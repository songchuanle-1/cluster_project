"""NDE native two-step smoke and original-handler resources; fresh lease required."""
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



def nde_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_supported_core_possible':any(x['actual_path_count'] for x in scenes),'total_true_paths':sum(x['actual_path_count'] for x in scenes)}


def nde_plan_observation(plan,members,valid_count,widths):
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
    assert cfg.model.dec.cluster_att_num_layers == 1, 'NDE requires only the original final hierarchy injection'
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
        excluded = ('dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.cluster_ffn.2.','dec.cluster_att.distribution_embedding.')
        common = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        result['common_initialized_parameters'] = {
            'scope':'Original common named parameters after native backbone pretrain, before TRAIN loader; exclude only three replaced original FFN prefixes and new distribution_embedding subtree on both targets; retain three original LayerNorms',
            'excluded_name_prefixes':list(excluded), 'names':list(common), 'shapes':{n:list(p.shape) for n,p in common.items()}, 'tensor_count':len(common),
            'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),
            'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; observation only, not a full-common-state gate'}
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler


def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original TRAIN2 with actual NDE hooks; no auxiliary forward/backward/probe."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('nde-native-smoke'))
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
        tracked_modules['distribution_embedding']=att.distribution_embedding
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
            coverage=nde_coverage_preflight(members)
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
        core=att.distribution_embedding;graph=importlib.import_module(qualified+'.distribution_embedding')
        original_plan=graph.build_support_plan;original_mean=graph._group_mean
        original_getitem=torch.Tensor.__getitem__;original_invert=torch.Tensor.__invert__
        original_select=torch.Tensor.index_select;original_cat=torch.cat
        original_linear=graph.F.linear;original_add=torch.Tensor.__add__
        original_zeros_like=torch.zeros_like;original_copy=torch.Tensor.index_copy
        def queue_replace(owner,name,replacement,original):
            installations.append((owner,name,replacement));global_replacements.append((owner,name,original))
        def norm_pre(level):
            def call(owner,values):
                assert values[0] is state['raw_refs'][level];state['norm_counts'][level]+=1
            return call
        def norm_post(level):
            def call(owner,values,output):state['norm_outputs'][level]=output
            return call
        for level in range(3):
            hooks.extend([att.cluster_ffn_norm[level].register_forward_pre_hook(norm_pre(level)),
                att.cluster_ffn_norm[level].register_forward_hook(norm_post(level))])
        def lite_watch(value,record):
            if value.requires_grad:
                def receive(gradient):
                    record['_internal_gradient_flags'].append(torch.isfinite(gradient).all());return None
                hooks.append(value.register_hook(receive))
        def exchange_pre(owner,values):
            points,point_mask,normalized,ids=values
            assert owner is core and ids is bank.cluster_ids_list and state['norm_counts']==[1,1,1]
            assert points is state['nde_encoder_features_ref'] and point_mask is state['nde_encoder_mask_ref']
            assert all(normalized[level] is state['norm_outputs'][level] for level in range(3))
            record={'forward':state['forward_index'],'point_input':summary(points),
                'exact_original_encoder_feature_and_mask_references':True,
                'normalized_inputs':[summary(x) for x in normalized],
                'scene_observations':[],'_internal_gradient_flags':[],
                'native_observer_scope':'Revision1 actual original-weight affine factoring: child half plus unique supported parent half before gather/add; original per-child GELU and second Linear before each of three private means. Original support/synthesis/restoration/HCG/rawskip/single-inst. Wrappers return original objects unchanged.',
                'per_parameter_nonzero_FP32_minimum_effect_gate_added':False}
            members=[tuple(level[b].detach().cpu().tolist() for level in ids) for b in range(int(points.shape[0]))]
            state['nde_context']={'record':record,'points':points,'mask':point_mask,
                'normalized':normalized,'members':members,'widths':[int(x.shape[1]) for x in normalized],
                'rows':[],'selectors':[],'selected':{},'scenes':[],'scene':None}
            state['nde_input_points_ref']=points;state['nde_point_mask_ref']=point_mask
            for level,value in enumerate(normalized):watch(value,record,'native_normalized_level'+str(level)+'_gradients')
        def observed_getitem(tensor,key):
            output=original_getitem(tensor,key);c=state.get('nde_context')
            if c is None:return output
            scene=c.get('scene');active=scene.get('active_analysis') if scene else None
            if active is not None and tensor is core.analysis[0].weight:
                assert isinstance(key,tuple) and len(key)==2 and key[0]==slice(None)
                col=key[1];assert isinstance(col,slice) and col.step is None
                role='child' if col.start is None and col.stop==core.channels else 'parent'
                if role=='parent':assert col.start==core.channels and col.stop is None
                assert role not in active['weight_views']
                active['weight_views'][role]=output
                assert list(output.shape)==[core.channels,core.channels]
            role=next((name for name,ref in [('points',c['points']),('mask',c['mask'])] if tensor is ref),None)
            if role is None:role=next(('normalized'+str(i) for i,ref in enumerate(c['normalized']) if tensor is ref),None)
            if role is not None and type(key) is int:c['rows'].append((output,role,key))
            else:
                row=next(((role,batch) for ref,role,batch in c['rows'] if tensor is ref),None)
                selector=next((batch for ref,batch in c['selectors'] if key is ref),None)
                if row is not None and row[0]=='points' and selector is not None:
                    role,batch=row;assert batch==selector
                    selected=c['selected'].setdefault(batch,{})
                    assert role not in selected;selected[role]=output;selected[role+'_mask_ref']=key
            return output
        def observed_invert(tensor):
            output=original_invert(tensor);c=state.get('nde_context')
            if c is not None:
                row=next(((role,batch) for ref,role,batch in c['rows'] if tensor is ref),None)
                if row is not None and row[0]=='mask':c['selectors'].append((output,row[1]))
            return output
        def observed_plan(ids0,ids1,ids2,valid_count,widths):
            c=state['nde_context'];batch=len(c['scenes'])
            assert (ids0,ids1,ids2)==c['members'][batch] and widths==c['widths']
            plan=original_plan(ids0,ids1,ids2,valid_count,widths)
            info=nde_plan_observation(plan,(ids0,ids1,ids2),valid_count,widths)
            info.update(batch=batch,actual_original_support_builder_calls=1,actual_group_mean_calls=0,
                actual_analysis_calls=0,actual_synthesis_calls=0,actual_final_index_copy_calls=0,
                actual_parent_context_broadcast_calls=0,
                mean_observations=[],analysis_observations=[],synthesis_observations=[],
                parent_context_observations=[],restoration_observations=[])
            selected=c['selected'][batch]
            assert len(selected['points'])==valid_count
            scene={'record':info,'plan':plan,'counts':[len(x) for x in plan['nodes']],
                'points':selected['points'],'means':[],'selected_normalized':{},
                'context_broadcasts':{},'analysis':[],'synthesis':{},'restored':[],'active_analysis':None}
            info['actual_original_valid_feature_mask_reference']=True
            c['scenes'].append(scene);c['scene']=scene;c['record']['scene_observations'].append(info)
            return plan
        def observed_mean(values,labels,count):
            output=original_mean(values,labels,count);c=state.get('nde_context');scene=c.get('scene') if c else None
            if scene is None:return output
            level=len(scene['means']);mapping=('point_to_fine','fine_to_middle','middle_to_coarse')[level]
            assert len(scene['analysis'])==level+1 and values is scene['analysis'][level]
            assert labels.tolist()==scene['plan'][mapping] and count==scene['counts'][level]
            info={'level':level,'input':summary(values),'output':summary(output),'groups':int(count),
                'original_calls':1,'returned_original_object_unchanged':True,
                'actual_shared_analysis_precedes_private_mean':True,
                'mapping':mapping,'actual_original_parent_ids':True}
            assert info['input']['finite'] and info['output']['finite']
            scene['means'].append(output);scene['record']['actual_group_mean_calls']+=1
            scene['record']['mean_observations'].append(info);lite_watch(output,c['record']);return output
        def observed_select(tensor,dim,index,*args,**kwargs):
            output=original_select(tensor,dim,index,*args,**kwargs);c=state.get('nde_context');scene=c.get('scene') if c else None
            if scene is None:return output
            row=next(((role,batch) for ref,role,batch in c['rows'] if tensor is ref and role.startswith('normalized')),None)
            active=scene.get('active_analysis')
            if row is not None:
                level=int(row[0][-1]);assert dim==0 and index.tolist()==scene['plan']['nodes'][level]
                scene['selected_normalized'][level]=output
            elif active is not None and len(active['linear_outputs'])>=2 and tensor is active['linear_outputs'][1]:
                level=active['level'];mapping=('point_to_fine','fine_to_middle','middle_to_coarse')[level]
                assert dim==0 and index is active['labels'] and index.tolist()==scene['plan'][mapping]
                assert level not in scene['context_broadcasts'] and active['linear_inputs'][1] is active['parent']
                scene['context_broadcasts'][level]=output;active['parent_broadcast']=output
                scene['record']['actual_parent_context_broadcast_calls']+=1
                scene['record']['parent_context_observations'].append({'level':level,'mapping':mapping,
                    'actual_original_normalized_parent_token_ref':True,'actual_original_ancestry_mapping':True,
                    'projected_unique_parent_before_gather':True,'unique_parent_rows':int(active['parent'].shape[0]),
                    'child_rows':int(active['source'].shape[0]),'original_calls':1,'output':summary(output)})
            elif scene['synthesis']:
                level=1 if len(scene['synthesis'])==1 else 0
                assert tensor is scene['synthesis'][level+1] and dim==0
                assert index.tolist()==scene['plan']['middle_to_coarse' if level==1 else 'fine_to_middle']
                scene['downward_ref']=output
            return output
        def observed_linear(*args,**kwargs):
            output=original_linear(*args,**kwargs);c=state.get('nde_context');scene=c.get('scene') if c else None
            active=scene.get('active_analysis') if scene else None
            if active is None:return output
            values=args[0] if args else kwargs['input']
            weight=args[1] if len(args)>1 else kwargs['weight']
            bias=args[2] if len(args)>2 else kwargs.get('bias')
            ordinal=len(active['linear_outputs']);assert ordinal<3
            if ordinal==0:
                assert values is active['source'] and weight is active['weight_views']['child'] and bias is core.analysis[0].bias
                role='actual_child_first_affine_half';bias_once=True
            elif ordinal==1:
                assert values is active['parent'] and weight is active['weight_views']['parent'] and bias is None
                assert values.shape[0]==scene['counts'][active['level']]
                role='actual_unique_parent_first_affine_half';bias_once=False
            else:
                assert values is active['activation_output'] and weight is core.analysis[2].weight and bias is core.analysis[2].bias
                role='actual_original_second_linear';bias_once=None
            info={'role':role,'original_calls':1,'input':summary(values),'weight':summary(weight),
                'output':summary(output),'first_affine_original_bias_applied_here':bias_once,
                'actual_original_parameter_or_slice_reference':True,'returned_original_object_unchanged':True,
                'input_dtype_equals_output_dtype':values.dtype==output.dtype,'FP32_cast_added':False}
            assert info['input']['finite'] and info['weight']['finite'] and info['output']['finite']
            active['linear_inputs'].append(values);active['linear_outputs'].append(output);active['linear_observations'].append(info)
            lite_watch(output,c['record']);return output
        def observed_add(tensor,other,*args,**kwargs):
            output=original_add(tensor,other,*args,**kwargs);c=state.get('nde_context');scene=c.get('scene') if c else None
            active=scene.get('active_analysis') if scene else None
            if active is not None and active['linear_outputs'] and tensor is active['linear_outputs'][0]:
                assert other is active['parent_broadcast'] and len(active['linear_outputs'])==2
                assert 'affine_sum' not in active;active['affine_sum']=output
            return output
        def activation_pre(owner,values):
            active=state['nde_context']['scene']['active_analysis']
            assert owner is core.analysis[1] and values[0] is active['affine_sum']
        def activation_post(owner,values,output):
            c=state['nde_context'];active=c['scene']['active_analysis']
            assert owner is core.analysis[1] and values[0] is active['affine_sum']
            active['activation_output']=output;lite_watch(output,c['record'])
        def observed_zeros_like(tensor,*args,**kwargs):
            output=original_zeros_like(tensor,*args,**kwargs);c=state.get('nde_context');scene=c.get('scene') if c else None
            if scene is not None and len(scene['means'])==3 and tensor is scene['means'][2]:scene['coarse_zero']=output
            return output
        def observed_cat(values,*args,**kwargs):
            output=original_cat(values,*args,**kwargs);c=state.get('nde_context');scene=c.get('scene') if c else None
            if scene is None:return output
            dim=kwargs.get('dim',args[0] if args else 0)
            assert len(scene['analysis'])==len(scene['means'])==3 and scene['active_analysis'] is None
            if len(scene['synthesis'])<3:
                level=2-len(scene['synthesis']);context=scene['coarse_zero'] if level==2 else scene['downward_ref']
                expected=(scene['means'][level],context)
                assert dim==-1 and len(values)==2 and all(x is y for x,y in zip(values,expected))
                assert list(output.shape)==[scene['counts'][level],2*core.channels]
                scene['synthesis_input']=output
            return output
        def stage_pre(kind):
            def call(owner,values):
                scene=state['nde_context']['scene'];assert owner is getattr(core,kind)
                if kind=='analysis':
                    assert len(values)==3;source,parent,labels=values;level=len(scene['analysis'])
                    assert len(scene['means'])==level and scene['active_analysis'] is None
                    expected_source=scene['points'] if level==0 else scene['means'][level-1]
                    mapping=('point_to_fine','fine_to_middle','middle_to_coarse')[level]
                    assert source is expected_source and parent is scene['selected_normalized'][level]
                    assert labels.tolist()==scene['plan'][mapping] and parent.shape[0]==scene['counts'][level]
                    scene['active_analysis']={'level':level,'source':source,'parent':parent,'labels':labels,
                        'weight_views':{},'linear_inputs':[],'linear_outputs':[],'linear_observations':[]}
                else:assert values[0] is scene['synthesis_input']
            return call
        def stage_post(kind):
            def call(owner,values,output):
                c=state['nde_context'];scene=c['scene'];level=len(scene['analysis']) if kind=='analysis' else 2-len(scene['synthesis'])
                info={'level':level,'input':summary(values[0]),'output':summary(output),'original_calls':1,
                    'actual_original_shared_module':True,'no_replay_or_replacement':True}
                assert info['input']['finite'] and info['output']['finite']
                if kind=='analysis':
                    active=scene['active_analysis'];assert active['level']==level and len(scene['means'])==level
                    assert len(active['linear_outputs'])==3 and output is active['linear_outputs'][2]
                    assert set(active['weight_views'])=={'child','parent'}
                    assert scene['context_broadcasts'][level] is active['parent_broadcast']
                    info.update(before_private_mean=True,analysis_source='actual_native_points' if level==0 else 'actual_child_state',
                        parent_input=summary(values[1]),actual_three_argument_analysis=True,
                        affine_factorization_observations=active['linear_observations'],
                        actual_child_and_unique_parent_first_affine_halves=True,
                        actual_original_first_affine_bias_applied_once=True,
                        actual_parent_projection_before_gather=True,
                        original_per_child_GELU_and_second_Linear=True,
                        analysis_first_affine_source_rows=int(active['source'].shape[0]),
                        analysis_first_affine_unique_parent_rows=int(active['parent'].shape[0]),
                        original_parameter_topology_and_precision=True)
                    scene['analysis'].append(output);scene['active_analysis']=None
                else:scene['synthesis'][level]=output
                scene['record'][kind+'_observations'].append(info);scene['record']['actual_'+kind+'_calls']+=1;lite_watch(output,c['record'])
            return call
        def observed_copy(tensor,dim,index,source,*args,**kwargs):
            output=original_copy(tensor,dim,index,source,*args,**kwargs);c=state.get('nde_context');scene=c.get('scene') if c else None
            if scene is not None and len(scene['synthesis'])==3:
                level=len(scene['restored']);assert level<3 and dim==0
                assert source is scene['synthesis'][level] and index.tolist()==scene['plan']['nodes'][level]
                assert list(tensor.shape)==[c['widths'][level],core.channels] and bool((tensor==0).all())
                info={'level':level,'original_node_ids':scene['plan']['nodes'][level],
                    'output':summary(output),'actual_synthesis_delta_ref':True,'original_calls':1,
                    'zero_initialized_destination':True,'returned_original_object_unchanged':True}
                assert info['output']['finite'];scene['record']['restoration_observations'].append(info)
                scene['restored'].append(output);scene['record']['actual_final_index_copy_calls']+=1
            return output
        for name,replacement,original in [('build_support_plan',observed_plan,original_plan),
            ('_group_mean',observed_mean,original_mean)]:queue_replace(graph,name,replacement,original)
        for owner,name,replacement,original in [(torch.Tensor,'__getitem__',observed_getitem,original_getitem),
            (torch.Tensor,'__invert__',observed_invert,original_invert),(torch.Tensor,'index_select',observed_select,original_select),
            (graph.F,'linear',observed_linear,original_linear),(torch.Tensor,'__add__',observed_add,original_add),
            (torch,'cat',observed_cat,original_cat),(torch,'zeros_like',observed_zeros_like,original_zeros_like),
            (torch.Tensor,'index_copy',observed_copy,original_copy)]:queue_replace(owner,name,replacement,original)
        for kind in ('analysis','synthesis'):
            hooks.extend([getattr(core,kind).register_forward_pre_hook(stage_pre(kind)),
                getattr(core,kind).register_forward_hook(stage_post(kind))])
        hooks.extend([core.analysis[1].register_forward_pre_hook(activation_pre),core.analysis[1].register_forward_hook(activation_post)])
        def exchange_post(owner,values,output):
            c=state.pop('nde_context');active=[scene for scene in c['scenes'] if scene['counts'][0]]
            for scene in active:
                item=scene['record']
                assert item['actual_group_mean_calls']==item['actual_parent_context_broadcast_calls']==3
                assert item['actual_analysis_calls']==item['actual_synthesis_calls']==item['actual_final_index_copy_calls']==3
                assert len(scene['means'])==len(scene['analysis'])==3
            record=c['record'];count=len(active)
            for level,value in enumerate(output):
                assert list(value.shape)==list(c['normalized'][level].shape)
                watch(value,record,'native_output_level'+str(level)+'_gradients')
            record.update(outputs=[summary(value) for value in output],
                actual_true_fine_paths=sum(scene['counts'][0] for scene in active),actual_supported_scene_count=count,
                actual_group_mean_calls=3*count,actual_parent_context_broadcast_calls=3*count,
                actual_analysis_calls=3*count,actual_synthesis_calls=3*count,actual_final_index_copy_calls=3*count,
                actual_three_LN_calls=list(state['norm_counts']),actual_production_NDEmbedding_path_observed=True,
                native_point_analysis_precedes_first_private_mean=True,no_feature_or_model_replay=True,
                actual_revision1_affine_factoring_observed=True,implementation_revision=1)
            state['nde_delta_snapshots']=[value.detach().clone() for value in output];exchange_calls.append(record)
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
        if candidate:assert point_feats is state['nde_input_points_ref'] and point_mask is state['nde_point_mask_ref']
        record={'forward':state['forward_index'],'levels':[summary(x) for x in refined],
            'refined_sha256':fingerprint(torch,[x.detach().clone() for x in refined]),
            'ids_sha256':fingerprint(torch,ids_list),'point_padding':summary(point_mask),'original_residual_levels':{}}
        raw=state['raw_refs']
        for level in (() if candidate else ffn_levels):
            exact=fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['ffn_snapshots'][level])
            record['original_residual_levels'][str(level)]=exact;assert exact
        if candidate:
            exact=[fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['nde_delta_snapshots'][level]) for level in range(3)]
            record['NDE_original_three_skips_and_exact_HCG_inputs']=exact;assert all(exact)
        output=original_readback(point_feats,refined,ids_list,point_mask);record['output']=summary(output)
        readbacks.append(record);watch(output,record,'native_point_message_gradients');return output
    replace(att,'_cluster_to_points',observed_readback)
    def last_encoder_pre(owner,values):
        if candidate:
            assert values[5] is state['nde_padded_positions_ref']
            state['nde_encoder_positions_ref']=values[5];state['nde_encoder_features_ref']=values[2];state['nde_encoder_mask_ref']=values[3]
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

    if candidate:
        def decoder_native_positions(owner,values,kwargs):
            positions=kwargs.get('sp_pos',values[5] if len(values)>5 else None)
            assert positions is not None and positions.shape[-1]==3
            state['nde_decoder_native_positions_ref']=positions
        original_get_batches=model.dec.get_batches
        def observed_get_batches(features,offsets):
            output=original_get_batches(features,offsets)
            if features is state.get('nde_decoder_native_positions_ref'):
                assert 'nde_padded_positions_ref' not in state
                state['nde_padded_positions_ref']=output[0]
                result.setdefault('NDE_native_coordinate_padding_observations',[]).append({
                    'forward':state['forward_index'],'native_unpadded':summary(features),
                    'native_unpadded_sha256':fingerprint(torch,features),'original_padded':summary(output[0]),
                    'original_padded_sha256':fingerprint(torch,output[0]),'original_get_batches_calls':1,
                    'returned_original_objects_unchanged':True,'coordinate_normalization_added':False})
            return output
        replace(model.dec,'get_batches',observed_get_batches)
        hooks.append(model.dec.register_forward_pre_hook(decoder_native_positions,with_kwargs=True))
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
        for key in ('raw_refs','raw_record','nde_delta_snapshots','norm_outputs','nde_input_points_ref','nde_point_mask_ref','encoder_inst_before','encoder_gate','cluster_message','nde_decoder_native_positions_ref','nde_padded_positions_ref','nde_encoder_positions_ref','nde_encoder_features_ref','nde_encoder_mask_ref'):state.pop(key,None)
        state['ffn_snapshots'].clear()
    def parameter_blocks():
        return {}  # NDE trainability is assessed across the whole new core.
    def before_step(owner,args,kwargs):
        assert backward_records[-1]['count']==1
        if candidate and not exchange_calls[-1]['actual_true_fine_paths']:
            result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FOREST'
            raise RuntimeError('INCONCLUSIVE_COVERAGE: no true NDE ancestry core, no replacement sample/seed')
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
            if candidate and name=='distribution_embedding':
                assert any(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight')),'Whole distribution_embedding aggregate original-loss weight gradient is zero; local control inconclusive, not whole-mechanism rejection'
            else:
                assert all(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight'))
            record['gradient_gate_scope']='New distribution_embedding core aggregate only; original FFNs on champion retain original weight gates. Individual new maps/rows/bias may be zero or unexercised.'
            if candidate and name=='distribution_embedding':
                weights=[g for n,g in gradients.items() if n.endswith('weight') and g is not None]
                record['whole_distribution_embedding_weight_gradient']={'finite':all(g['finite'] for g in weights),'abs_max':max(g['abs_max'] for g in weights),'observed_weight_tensors':len(weights),'scope':'Aggregate across entire distribution_embedding; individual map zeros/unused legal'}
        record['native_parameter_block_gradients']={}
        record['parameter_block_before_step_hash']={}
        for name,(weight,r0,r1,c0,c1) in parameter_blocks().items():
            info=summary(weight.grad[r0:r1,c0:c1]) if weight.grad is not None else None;record['native_parameter_block_gradients'][name]=info
            assert info is None or info['finite'];record.setdefault('block_gradient_gate_scope','Any optional parameter-block report is descriptive; whole distribution_embedding aggregate weight is the only new nonzero gate.')
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
            record['whole_distribution_embedding_weight_updated']=record['weight_before_step_hash']['distribution_embedding']!=record['weight_after_step_hash']['distribution_embedding']
            record['whole_distribution_embedding_module_updated']=record['module_before_step_hash']['distribution_embedding']!=record['module_after_step_hash']['distribution_embedding']
        record['parameter_block_after_step_hash']={name:fingerprint(torch,weight.detach()[r0:r1,c0:c1]) for name,(weight,r0,r1,c0,c1) in parameter_blocks().items()}
        record['descriptive_parameter_block_changed']={name:record['parameter_block_before_step_hash'][name]!=record['parameter_block_after_step_hash'][name] for name in record['parameter_block_before_step_hash']}
        result['optimizer_steps']+=1
    hooks.extend([model.register_forward_pre_hook(native_input),model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step),optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False,losses=losses,steps=steps,batches=batches,native_backward_records=backward_records,
        ffn_calls=calls,raw_bank_observations=rawbanks,csort_raw_input_observations=csort,hcg_readbacks=readbacks,
        NDE_distribution_embedding_observations=exchange_calls,inst_to_mask_path_observations=path_records,native_dataloader_config=dict(cfg.dataloader.train),
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',
        actual_champion_candidate_batch_pairing='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both complete raw batch fingerprints and common named initialization',
        smoke_memory_scope='Two native TRAIN steps including observer hooks, detached snapshots, actual topology/source recording; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; no separate no-observer native TRAIN process pair',auxiliary_autograd_grad_or_backward_used=False,
        native_failure_is_not_whole_mechanism_rejection=True,
        coverage_gate_scope='Each original fixed TRAIN forward needs at least one true supported forest core. Singleton/empty-supported boundaries are optional NOT_EXERCISED when absent; no resampling. Individual maps/rows/columns/biases descriptive only; no component positivity, FP32, minimum-effect/Jacobian or optional coverage gate.',
        dynande_parameter_inventory={'original_FFN_parameters_by_level':{str(i):sum(p.numel() for p in att.cluster_ffn[i].parameters()) for i in range(3)},
            'new_declared_parameters':sum(p.numel() for p in att.distribution_embedding.parameters()) if candidate else 0,
            'actual_full_model_parameters':sum(p.numel() for p in model.parameters()),'actual_named_parameter_tensors':sum(1 for _ in model.named_parameters()),
            'state_dict_keys':list(model.state_dict()),'geometry_registered_buffer_names':[n for n,_ in model.named_buffers() if 'middle_positions' in n or 'middle_parent_ids' in n or 'middle_valid' in n]})
    logger=logging.getLogger('nde-native-smoke');logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
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
        count=record['actual_supported_scene_count']
        assert record['actual_true_fine_paths']>0 and count>0
        assert all(record[key]==3*count for key in ('actual_group_mean_calls','actual_parent_context_broadcast_calls','actual_analysis_calls','actual_synthesis_calls','actual_final_index_copy_calls'))
        for level in range(3):
            for key in ('native_normalized_level'+str(level)+'_gradients','native_output_level'+str(level)+'_gradients'):
                assert record.get(key) and all(g['finite'] for g in record[key])
        flags=record.pop('_internal_gradient_flags');record['actual_internal_backward_callbacks']=len(flags)
        record['all_observed_internal_gradients_finite']=bool(torch.stack(flags).all()) if flags else None
        if flags:assert record['all_observed_internal_gradients_finite']
        record['internal_gradient_scope']='Finite observed flags only; no per-branch/parameter nonzero or completeness gate; whole-core aggregate controls trainability.'
    for record in readbacks:assert record.get('native_point_message_gradients') and all(g['finite'] for g in record['native_point_message_gradients'])
    for record in path_records:
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    final={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
    assert all(final[n]!=initial[n] for n in tracked);verify()
    result.update(execution_completed=True,native_data_loaded=True,native_train_function_executed=True,backward_finite=True,
        intended_path_observed=(len(exchange_calls)==2 and all(v['actual_production_NDEmbedding_path_observed'] and v['actual_true_fine_paths']>0 for v in exchange_calls)) if candidate else len(calls)==6,
        new_operator_parameters=sum(p.numel() for p in att.distribution_embedding.parameters()) if candidate else None,native_tracked_initial_hash=initial,native_tracked_after_hash=final,
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


def exception_frame_metadata(error):
    """Bounded failure-only type/identity evidence; never records tensor data."""
    import builtins
    import hashlib
    import types
    def describe(value):
        cls=builtins.type(value)
        out={'type_module':cls.__module__,'type_qualname':cls.__qualname__,
            'identity':builtins.id(value),'callable':builtins.callable(value)}
        if isinstance(value,(types.FunctionType,types.BuiltinFunctionType,types.MethodType,types.BuiltinMethodType)):
            out['callable_module']=getattr(value,'__module__',None)
            out['callable_qualname']=getattr(value,'__qualname__',None)
            bound=getattr(value,'__self__',None);function=getattr(value,'__func__',None)
            if bound is not None:
                bound_cls=builtins.type(bound)
                out['bound_self_identity']=builtins.id(bound)
                out['bound_self_type']=bound_cls.__module__+'.'+bound_cls.__qualname__
            if function is not None:out['bound_function_identity']=builtins.id(function)
        return out
    trace=[];current=error.__traceback__
    while current is not None:
        trace.append(current);current=current.tb_next
    selected=trace[-16:];torch_module=sys.modules.get('torch');frames=[];file_hashes={}
    for tb in selected:
        frame=tb.tb_frame;filename=frame.f_code.co_filename
        item={'file':filename,'function':frame.f_code.co_name,'line':tb.tb_lineno,
            'locals_selected_types':{name:describe(frame.f_locals[name]) for name in
                ('torch','memo','fn','func','wrapper','t','param_applied','self','op','operator') if name in frame.f_locals}}
        if 'torch' in frame.f_globals:
            item['globals_torch']=describe(frame.f_globals['torch'])
            item['globals_torch_is_sys_modules_torch']=frame.f_globals['torch'] is torch_module
        path=Path(filename)
        if filename not in file_hashes:
            try:
                if path.is_file() and path.stat().st_size<=1048576:
                    file_hashes[filename]=hashlib.sha256(path.read_bytes()).hexdigest()
            except (OSError,ValueError):pass
        frames.append(item)
    return {'pid':os.getpid(),'frame_count_total':len(trace),'frame_limit':16,
        'frames':frames,'selected_source_sha256':file_hashes,
        'sys_modules_torch':describe(torch_module),
        'scope':'Actual exception frames, types/identities/source hashes only; no tensor values/full locals; original exception re-raised',
        'no_success_gate_or_training_math_change':True}


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
        'exception_frame_capture_status':'NOT_EXERCISED',
        'native_model_and_yaml_unchanged':False,'source_scope':'Exact native NDE or original M95, original backbone pretrain and native train loop'}
    result.update(experiment_id=MANIFEST['experiment_id'],config=MANIFEST['config'],implementation_revision=MANIFEST.get('implementation_revision'),
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
        try:
            result['exception_frame_metadata']=exception_frame_metadata(error)
            result['exception_frame_capture_status']='ACTUAL_FAILURE_CAPTURED'
        except BaseException as capture_error:
            result['exception_frame_capture_status']='CAPTURE_FAILED_ORIGINAL_EXCEPTION_PRESERVED'
            result['exception_frame_capture_error_type']=type(capture_error).__name__
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
