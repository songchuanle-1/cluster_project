"""WFC native two-step smoke and original-handler resources; fresh lease required."""
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



def wfc_plan_observation(plan,members):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    keys=[(l,i) for l,rows in enumerate((fine,middle,coarse)) for i in rows];positions={key:i for i,key in enumerate(keys)}
    edges=[(positions[(0,i)],positions[(1,fm[i])]) for i in fine]+[(positions[(1,j)],positions[(2,mc[j])]) for j in middle]
    neighbors=[[] for _ in keys]
    for a,b in edges:neighbors[a].append(b);neighbors[b].append(a)
    for row in neighbors:row.sort()
    wedges=[(a,m,z) for m,row in enumerate(neighbors) for a,z in itertools.combinations(row,2)]
    incidence=[[i for i,wedge in enumerate(wedges) if node in wedge] for node in range(len(keys))]
    expected={'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'node_keys':keys,'neighbors':neighbors,'edges':edges,'wedges':wedges,'incidence':incidence,'factor_count':len(wedges),'point_count':len(points)}
    assert plan==expected;return copy.deepcopy(plan)


def wfc_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_supported_core_possible':any(p['actual_path_count'] for p in scenes),'total_true_paths':sum(p['actual_path_count'] for p in scenes)}


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
    assert cfg.model.dec.cluster_att_num_layers == 1, 'WFC requires only the original final hierarchy injection'
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
        excluded = ('dec.cluster_att.cluster_ffn.0.', 'dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.cluster_ffn.2.', 'dec.cluster_att.wedge_factor.')
        common = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        result['common_initialized_parameters'] = {
            'scope':'Original common named parameters after native backbone pretrain, before TRAIN loader; exclude all three removed FFN prefixes and new-wedge_factor subtree on both targets; retain all three LayerNorms',
            'excluded_name_prefixes':list(excluded), 'names':list(common), 'shapes':{n:list(p.shape) for n,p in common.items()}, 'tensor_count':len(common),
            'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),
            'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; observation only, not a full-common-state gate'}
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler


def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original TRAIN2 with actual WFC hooks; no auxiliary forward/backward/probe."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('wfc-native-smoke'))
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
        assert all(sum(p.numel() for p in att.cluster_ffn[level].parameters())==0 for level in range(3))
        tracked_modules['wedge_factor']=att.wedge_factor
        assert sum(p.numel() for p in att.wedge_factor.parameters())==131328
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
            coverage=wfc_coverage_preflight(members)
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
        wfc_module=importlib.import_module(qualified+'.wedge_factor')
        original_plan=wfc_module.build_wedge_factor_plan;original_prepare=wfc_module.prepare_wedge_factor_plans
        original_mean=wfc_module.mean_wedge_incidence
        original_stack=torch.stack;original_cat=torch.cat
        original_select=torch.Tensor.index_select;original_add=torch.Tensor.index_add;original_copy=torch.Tensor.index_copy
        def queue_replace(owner,name,replacement,original):
            installations.append((owner,name,replacement));global_replacements.append((owner,name,original))
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
            normalized,ids=values;assert owner is att.wedge_factor and ids is bank.cluster_ids_list and state['norm_counts']==[1,1,1]
            assert all(normalized[level] is state['norm_outputs'][level] for level in range(3))
            members=[tuple(level[b].detach().cpu().tolist() for level in ids) for b in range(int(normalized[0].shape[0]))]
            coverage=wfc_coverage_preflight(members)
            if not coverage['true_supported_core_possible']:
                result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FOREST';raise RuntimeError('INCONCLUSIVE_COVERAGE before WFC watches; no resampling')
            record={'forward':state['forward_index'],'inputs':[summary(x) for x in normalized],
                'normalized_bank_sha256':fingerprint(torch,normalized),'original_three_LN_calls':list(state['norm_counts']),
                'plans':[],'map_calls':[],'mean_calls':[],'primitive_calls':[],'_internal_gradient_flags':[],
                'native_observer_scope':'Actual one global factor_map/GELU; scoped stack, cat, select, add, copy and original incidence mean each return passed through once. No learned/mean/model/criterion/backward replay.',
                'FP32_Jacobian_role_coverage_gate':'NOT_IMPLEMENTED_NOT_REQUIRED'}
            assert 'wfc_context' not in state
            state['wfc_context']={'record':record,'normalized':normalized,'ids_ref':ids,'members':members,
                'widths':[int(x.shape[1]) for x in normalized],'phase':'prepare','builder_calls':0,'prepare_calls':0,
                'stack_calls':0,'cat_calls':0,'map_calls':0,'GELU_calls':0,'mean_calls':0,'mean_add_calls':0,
                'map_selects':[],'final_level':0,'final_outputs':[]}
            for level,x in enumerate(normalized):
                if not x.requires_grad:
                    result['coverage_status']='INCONCLUSIVE_CORE_INPUT_NOT_DIFFERENTIABLE';raise RuntimeError('INCONCLUSIVE_COVERAGE original WFC input before watches')
                watch(x,record,'native_normalized_level'+str(level)+'_gradients')
        def observed_plan(points,fm,mc,widths):
            context=state['wfc_context'];b=context['builder_calls'];context['builder_calls']+=1
            assert (points,fm,mc)==context['members'][b] and widths==context['widths']
            output=original_plan(points,fm,mc,widths);record=wfc_plan_observation(output,(points,fm,mc));record['batch']=b
            context['record']['plans'].append(record);return output
        def observed_prepare(levels,ids):
            context=state['wfc_context'];assert context['phase']=='prepare' and ids is context['ids_ref'] and not context['prepare_calls']
            assert all(levels[l] is context['normalized'][l] for l in range(3))
            output=original_prepare(levels,ids);context['prepare_calls']=1;context['plans_ref']=output
            assert context['builder_calls']==len(output)==int(levels[0].shape[0])
            rows=[];left=[];centers=[];right=[];positions=[[],[],[]];destinations=[[],[],[]]
            incidence_sources=[];incidence_receivers=[];counts=[];factor_offset=0
            for b,plan in enumerate(output):
                offset=len(rows)
                for node,(level,original_id) in enumerate(plan['node_keys']):
                    positions[level].append(offset+node);destinations[level].append(b*context['widths'][level]+original_id)
                    rows.append((b,level,original_id))
                for a,m,z in plan['wedges']:left.append(offset+a);centers.append(offset+m);right.append(offset+z)
                for node,incident in enumerate(plan['incidence']):
                    incidence_sources.extend(factor_offset+f for f in incident);incidence_receivers.extend([offset+node]*len(incident));counts.append(len(incident))
                factor_offset+=plan['factor_count']
            assert centers and all(counts)
            context.update(rows=rows,left=left,centers=centers,right=right,positions=positions,destinations=destinations,
                incidence_sources=incidence_sources,incidence_receivers=incidence_receivers,counts=counts,phase='pack')
            return output
        def observed_stack(values,*args,**kwargs):
            context=state.get('wfc_context')
            if context is None:return original_stack(values,*args,**kwargs)
            assert context['phase']=='pack' and len(values)==len(context['rows']) and not context['stack_calls']
            assert all(torch.equal(value,context['normalized'][level][b,original_id]) for value,(b,level,original_id) in zip(values,context['rows']))
            output=original_stack(values,*args,**kwargs);context['nodes_ref']=output;context['stack_calls']=1;context['phase']='map_gathers'
            context['record']['primitive_calls'].append({'kind':'actual_normalized_node_stack','original_calls':1,'returned_original_object_unchanged':True});return output
        def observed_select(tensor,dim,index,*args,**kwargs):
            context=state.get('wfc_context')
            if context is None:return original_select(tensor,dim,index,*args,**kwargs)
            assert dim==0
            phase=context['phase']
            if phase=='map_gathers':
                count=len(context['map_selects']);expected=(context['centers'],context['left'],context['right'])[count]
                assert tensor is context['nodes_ref'] and index.detach().cpu().tolist()==expected
                output=original_select(tensor,dim,index,*args,**kwargs);context['map_selects'].append(output)
                if len(context['map_selects'])==3:context['phase']='map_cat'
                kind='center_left_right_original_gather'
            elif phase=='mean_active':
                assert tensor is context['factors_ref'] and index.detach().cpu().tolist()==context['incidence_sources'] and 'incidence_gather_ref' not in context
                output=original_select(tensor,dim,index,*args,**kwargs);context['incidence_gather_ref']=output;kind='actual_incidence_factor_gather'
            elif phase=='final_scatter':
                level=context['final_level'];assert tensor is context['delta_ref'] and index.detach().cpu().tolist()==context['positions'][level]
                output=original_select(tensor,dim,index,*args,**kwargs);context['scatter_source_ref']=output;context['phase']='final_copy';kind='final_level_original_gather'
            else:raise AssertionError('Unexpected WFC active index_select phase '+phase)
            context['record']['primitive_calls'].append({'kind':kind,'original_calls':1,'returned_original_object_unchanged':True});return output
        def observed_cat(values,*args,**kwargs):
            context=state.get('wfc_context')
            if context is None:return original_cat(values,*args,**kwargs)
            assert context['phase']=='map_cat' and len(values)==2 and values[0] is context['map_selects'][0] and not context['cat_calls']
            assert list(values[1].shape)==list(values[0].shape)
            # Observe the actual endpoint-sum object; do not replay its addition or learned operators.
            context['endpoint_sum_ref']=values[1];output=original_cat(values,*args,**kwargs)
            context['cat_ref']=output;context['cat_calls']=1;context['phase']='map_ready';return output
        def map_pre(owner,values):
            context=state['wfc_context'];assert owner is att.wedge_factor.factor_map and context['phase']=='map_ready' and values[0] is context['cat_ref'] and not context['map_calls']
            context['record']['map_calls'].append({'input':summary(values[0]),'input_sha256':fingerprint(torch,values[0]),
                'actual_center_sha256':fingerprint(torch,context['map_selects'][0]),'actual_left_sha256':fingerprint(torch,context['map_selects'][1]),
                'actual_right_sha256':fingerprint(torch,context['map_selects'][2]),'actual_endpoint_sum_sha256':fingerprint(torch,context['endpoint_sum_ref'])})
        def map_post(owner,values,output):
            context=state['wfc_context'];context['map_ref']=output;context['map_calls']+=1;context['phase']='activation_ready';lite_watch(output,context['record'])
        def activation_post(owner,values,output):
            context=state['wfc_context'];assert owner is att.wedge_factor.activation and context['phase']=='activation_ready' and values[0] is context['map_ref'] and not context['GELU_calls']
            context['factors_ref']=output;context['GELU_calls']=1;context['phase']='mean_ready'
            context['record']['map_calls'][-1].update(actual_GELU_output=summary(output),actual_GELU_sha256=fingerprint(torch,output));lite_watch(output,context['record'])
        def observed_add(tensor,dim,index,source,*args,**kwargs):
            context=state.get('wfc_context')
            if context is None:return original_add(tensor,dim,index,source,*args,**kwargs)
            assert context['phase']=='mean_active' and dim==0 and index.detach().cpu().tolist()==context['incidence_receivers']
            assert source is context['incidence_gather_ref'] and not context['mean_add_calls'] and bool((tensor==0).all())
            output=original_add(tensor,dim,index,source,*args,**kwargs);context['mean_add_calls']=1
            context['record']['primitive_calls'].append({'kind':'actual_incidence_index_add','original_calls':1,'returned_original_object_unchanged':True});return output
        def observed_mean(factors,plans):
            context=state['wfc_context'];assert context['phase']=='mean_ready' and factors is context['factors_ref'] and plans is context['plans_ref'] and not context['mean_calls']
            context['phase']='mean_active';output=original_mean(factors,plans)
            assert context['mean_add_calls']==1 and list(output.shape)==[len(context['rows']),att.wedge_factor.channels]
            context['mean_calls']=1;context['delta_ref']=output;context['phase']='final_scatter'
            context['record']['mean_calls'].append({'input_sha256':fingerprint(torch,factors),'output_sha256':fingerprint(torch,output),
                'output':summary(output),'incidence_sources':list(context['incidence_sources']),'incidence_receivers':list(context['incidence_receivers']),
                'actual_incidence_counts':list(context['counts']),'original_mean_calls':1,'returned_original_object_unchanged':True,
                'mean_replayed_by_observer':False,'normalization_body':'Frozen original mean_wedge_incidence divides actual summed returns by these exact positive counts; no floating mean replay or new tolerance gate.'})
            assert context['record']['mean_calls'][-1]['output']['finite'];lite_watch(output,context['record']);return output
        def observed_copy(tensor,dim,index,source,*args,**kwargs):
            context=state.get('wfc_context')
            if context is None:return original_copy(tensor,dim,index,source,*args,**kwargs)
            level=context['final_level'];assert context['phase']=='final_copy' and dim==0 and level<3
            assert index.detach().cpu().tolist()==context['destinations'][level] and source is context['scatter_source_ref'] and bool((tensor==0).all())
            output=original_copy(tensor,dim,index,source,*args,**kwargs);context['final_outputs'].append(output);context['final_level']+=1
            context['phase']='final_scatter' if context['final_level']<3 else 'complete'
            context['record']['primitive_calls'].append({'kind':'final_original_ID_scatter','original_calls':1,'returned_original_object_unchanged':True});return output
        for name,replacement,original in [('build_wedge_factor_plan',observed_plan,original_plan),('prepare_wedge_factor_plans',observed_prepare,original_prepare),('mean_wedge_incidence',observed_mean,original_mean)]:queue_replace(wfc_module,name,replacement,original)
        for owner,name,replacement,original in [(torch,'stack',observed_stack,original_stack),(torch,'cat',observed_cat,original_cat),(torch.Tensor,'index_select',observed_select,original_select),(torch.Tensor,'index_add',observed_add,original_add),(torch.Tensor,'index_copy',observed_copy,original_copy)]:queue_replace(owner,name,replacement,original)
        hooks.extend([att.wedge_factor.factor_map.register_forward_pre_hook(map_pre),att.wedge_factor.factor_map.register_forward_hook(map_post),att.wedge_factor.activation.register_forward_hook(activation_post)])
        def exchange_post(owner,values,output):
            context=state.pop('wfc_context');record=context['record']
            assert context['phase']=='complete' and len(output)==3 and context['prepare_calls']==context['stack_calls']==context['cat_calls']==context['map_calls']==context['GELU_calls']==context['mean_calls']==context['mean_add_calls']==1
            assert context['final_level']==3 and len(context['map_selects'])==3
            for level,value in enumerate(output):
                assert fingerprint(torch,value.detach().reshape(-1))==fingerprint(torch,context['final_outputs'][level].detach().reshape(-1))
                if not value.requires_grad:result['coverage_status']='INCONCLUSIVE_CORE_OUTPUT_NOT_DIFFERENTIABLE';raise RuntimeError('INCONCLUSIVE WFC output before watches')
                watch(value,record,'native_output_level'+str(level)+'_gradients')
            record.update(outputs=[summary(x) for x in output],output_sha256=fingerprint(torch,output),
                actual_true_fine_paths=sum(len(p['fine_ids']) for p in record['plans']),actual_nodes=len(context['rows']),actual_wedges=len(context['centers']),
                actual_factor_map_calls=context['map_calls'],actual_GELU_calls=context['GELU_calls'],actual_private_incidence_mean_calls=context['mean_calls'],
                actual_original_builder_calls=context['builder_calls'],actual_prepare_calls=context['prepare_calls'],actual_final_index_copy_calls=context['final_level'],
                actual_three_LN_calls=list(state['norm_counts']),final_deltas_from_actual_incidence_mean=True,unsupported_padding_deltas_zero=True,
                actual_optional_boundary_counts=[{'batch':p['batch'],'true_fine':len(p['fine_ids']),'wedges':p['factor_count'],
                    'empty_scene':not p['fine_ids'],'single_true_path':len(p['fine_ids'])==1,
                    'unsupported_or_padding':[context['widths'][l]-len(p[k]) for l,k in enumerate(('fine_ids','middle_ids','coarse_ids'))]} for p in record['plans']])
            state['wfc_delta_snapshots']=[x.detach().clone() for x in output];exchange_calls.append(record)
        hooks.extend([att.wedge_factor.register_forward_pre_hook(exchange_pre),att.wedge_factor.register_forward_hook(exchange_post)])

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
            exact=[fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['wfc_delta_snapshots'][level]) for level in range(3)]
            record['WFC_original_three_skips_and_exact_HCG_inputs']=exact;assert all(exact)
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
        for key in ('raw_refs','raw_record','wfc_delta_snapshots','norm_outputs','encoder_inst_before','encoder_gate','cluster_message'):state.pop(key,None)
        state['ffn_snapshots'].clear()
    def parameter_blocks():
        if not candidate:return {}
        c=att.wedge_factor.channels
        return {role:(att.wedge_factor.factor_map.weight,0,c,col*c,(col+1)*c)
            for col,role in enumerate(('center_columns','endpoint_sum_columns'))}
    def before_step(owner,args,kwargs):
        assert backward_records[-1]['count']==1
        if candidate and not exchange_calls[-1]['actual_nodes']:
            result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FOREST'
            raise RuntimeError('INCONCLUSIVE_COVERAGE: no true wedge-factor path, no replacement sample/seed')
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
            if candidate:
                assert any(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight')),'Whole wedge_factor aggregate original-loss weight gradient is zero; local control inconclusive, not whole-mechanism rejection'
            else:
                assert all(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight'))
            record['gradient_gate_scope']='Candidate whole wedge_factor aggregate only; individual maps/weights/rows/bias may be zero or unexercised, descriptive only'
            if candidate:
                weights=[g for n,g in gradients.items() if n.endswith('weight') and g is not None]
                record['whole_wedge_factor_weight_gradient']={'finite':all(g['finite'] for g in weights),'abs_max':max(g['abs_max'] for g in weights),'observed_weight_tensors':len(weights),'scope':'Aggregate across entire wedge_factor; individual map zeros/unused legal'}
        record['native_parameter_block_gradients']={}
        record['parameter_block_before_step_hash']={}
        for name,(weight,r0,r1,c0,c1) in parameter_blocks().items():
            info=summary(weight.grad[r0:r1,c0:c1]) if weight.grad is not None else None;record['native_parameter_block_gradients'][name]=info
            assert info is None or info['finite'];record.setdefault('block_gradient_gate_scope','Two factor_map input-column blocks descriptive; zeros legal. Whole shared-core aggregate weight is the nonzero gate.')
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
            record['whole_wedge_factor_weight_updated']=record['weight_before_step_hash']['wedge_factor']!=record['weight_after_step_hash']['wedge_factor']
            record['whole_wedge_factor_module_updated']=record['module_before_step_hash']['wedge_factor']!=record['module_after_step_hash']['wedge_factor']
        record['parameter_block_after_step_hash']={name:fingerprint(torch,weight.detach()[r0:r1,c0:c1]) for name,(weight,r0,r1,c0,c1) in parameter_blocks().items()}
        record['descriptive_parameter_block_changed']={name:record['parameter_block_before_step_hash'][name]!=record['parameter_block_after_step_hash'][name] for name in record['parameter_block_before_step_hash']}
        result['optimizer_steps']+=1
    hooks.extend([model.register_forward_pre_hook(native_input),model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step),optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False,losses=losses,steps=steps,batches=batches,native_backward_records=backward_records,
        ffn_calls=calls,raw_bank_observations=rawbanks,csort_raw_input_observations=csort,hcg_readbacks=readbacks,
        WFC_wedge_factor_observations=exchange_calls,inst_to_mask_path_observations=path_records,native_dataloader_config=dict(cfg.dataloader.train),
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',
        actual_champion_candidate_batch_pairing='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both complete raw batch fingerprints and common named initialization',
        smoke_memory_scope='Two native TRAIN steps including observer hooks, detached snapshots, actual topology/source recording; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; no separate no-observer native TRAIN process pair',auxiliary_autograd_grad_or_backward_used=False,
        native_failure_is_not_whole_mechanism_rejection=True,
        coverage_gate_scope='Each original fixed TRAIN forward needs at least one true supported forest core. Singleton and degree boundaries are optional NOT_EXERCISED when absent; no resampling. Both factor-map columns descriptive only; no per-wedge/node/row/column positivity or optional role/degree gate.',
        dynamic_parameter_inventory={'original_FFN_parameters_by_level':{str(i):sum(p.numel() for p in att.cluster_ffn[i].parameters()) for i in range(3)},
            'new_declared_parameters':sum(p.numel() for p in att.wedge_factor.parameters()) if candidate else 0,
            'actual_full_model_parameters':sum(p.numel() for p in model.parameters()),'actual_named_parameter_tensors':sum(1 for _ in model.named_parameters()),
            'state_dict_keys':list(model.state_dict()),'geometry_registered_buffer_names':[n for n,_ in model.named_buffers() if 'middle_positions' in n or 'middle_parent_ids' in n or 'middle_valid' in n]})
    logger=logging.getLogger('wfc-native-smoke');logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
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
        assert record['actual_wedges']>0 and record['actual_factor_map_calls']==record['actual_GELU_calls']==record['actual_private_incidence_mean_calls']==1 and record['actual_final_index_copy_calls']==3
        for level in range(3):
            for key in ('native_normalized_level'+str(level)+'_gradients','native_output_level'+str(level)+'_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
        flags=record.pop('_internal_gradient_flags');record['actual_internal_backward_callbacks']=len(flags)
        record['all_observed_internal_gradients_finite']=bool(torch.stack(flags).all()) if flags else None
        if flags:assert record['all_observed_internal_gradients_finite']
        record['internal_gradient_scope']='Only finite flags aggregated, no per-call/branch/row positivity or callback-completeness gate. Whole shared-core original-loss gradient/update controls trainability.'
    for record in readbacks:assert record.get('native_point_message_gradients') and all(g['finite'] for g in record['native_point_message_gradients'])
    for record in path_records:
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    final={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
    assert all(final[n]!=initial[n] for n in tracked);verify()
    result.update(execution_completed=True,native_data_loaded=True,native_train_function_executed=True,backward_finite=True,
        intended_path_observed=(len(exchange_calls)==2 and all(v['actual_wedges']>0 and v['actual_factor_map_calls']==v['actual_GELU_calls']==v['actual_private_incidence_mean_calls']==1 and v['actual_final_index_copy_calls']==3 for v in exchange_calls)) if candidate else len(calls)==6,
        new_operator_parameters=131328 if candidate else None,native_tracked_initial_hash=initial,native_tracked_after_hash=final,
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
        'native_model_and_yaml_unchanged':False,'source_scope':'Exact native WFC or original M95, original backbone pretrain and native train loop'}
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
