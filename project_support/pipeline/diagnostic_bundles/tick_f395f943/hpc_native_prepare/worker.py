"""HPC native two-step smoke and original-handler resources; fresh lease required."""
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



def hpc_coverage_preflight(members):
    scenes=[]
    for batch,(ids0,ids1,ids2) in enumerate(members):
        fine=sorted(set(ids0));middle=sorted({ids1[i] for i in fine});coarse=sorted({ids2[j] for j in middle})
        counts={k:0 for k in coarse}
        for i in fine:counts[ids2[ids1[i]]]+=1
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,
            'component_fine_descendant_counts':counts,'real_cross_level_path':bool(fine and middle and coarse),
            'two_fine_component':any(n>=2 for n in counts.values())})
    return {'scenes':scenes,'real_cross_level_component_possible':any(x['real_cross_level_path'] and x['two_fine_component'] for x in scenes)}


def hpc_plan_observation(plan,point_ids,fine_to_middle,middle_to_coarse,widths):
    result=copy.deepcopy(plan);fine=result['fine_ids'];middle=result['middle_ids'];coarse=result['coarse_ids']
    assert fine==sorted(set(point_ids)) and middle==sorted({fine_to_middle[i] for i in fine})
    assert coarse==sorted({middle_to_coarse[j] for j in middle})
    assert result['fine_parent_positions']==[middle.index(fine_to_middle[i]) for i in fine]
    assert result['middle_parent_positions']==[coarse.index(middle_to_coarse[j]) for j in middle]
    fc=[result['fine_parent_positions'].count(j) for j in range(len(middle))]
    mc=[result['middle_parent_positions'].count(k) for k in range(len(coarse))]
    assert result['fine_child_counts']==fc and result['middle_child_counts']==mc
    a1=[2.0+n/2.0 for n in fc];a2=[1.0+n for n in mc]
    for j,k in enumerate(result['middle_parent_positions']):a2[k]-=1.0/a1[j]
    assert result['middle_diagonal']==a1 and result['coarse_diagonal']==a2
    assert result['edge_count']==len(fine)+len(middle) and result['active_node_count']==len(fine)+len(middle)+len(coarse)
    assert result['point_count']==len(point_ids)
    prefixes=[max(ids,default=-1)+1 for ids in (point_ids,fine_to_middle,middle_to_coarse)]
    result['optional_boundary_counts']={'unsupported_internal_rows':[prefixes[l]-len(ids) for l,ids in enumerate((fine,middle,coarse))],
        'batch_padding_rows':[widths[l]-prefixes[l] for l in range(3)],'empty_supported_forest':not bool(fine),
        'singleton_fine_components':sum(n==1 for n in hpc_coverage_preflight([(point_ids,fine_to_middle,middle_to_coarse)])['scenes'][0]['component_fine_descendant_counts'].values())}
    result['numerical_scope']='Exact original Python metadata/Schur coefficients, not a native direct-solve or FP32 residual test'
    return result


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
    assert cfg.model.dec.cluster_att_num_layers == 1, 'HPC requires only the original final hierarchy injection'
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
        common={name:p.detach() for name,p in model.named_parameters()}
        observation={'scope':'Actual entire named-parameter initialization after native backbone pretrain before loader; HPC retains all original parameters/constructors, no exclusions or fixed inferred count',
            'excluded_name_prefixes':[], 'names':list(common), 'shapes':{n:list(p.shape) for n,p in common.items()},
            'tensor_count':len(common),'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both actual complete named sets and fingerprints, buffers/RNG not claimed'}
        result['common_initialized_parameters']=observation
        result['full_named_parameter_initialization']=observation
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler

def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original TRAIN2 with actual HPC hooks; no auxiliary forward/backward/probe."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('hpc-native-smoke'))
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
    ffn_levels=(0,1,2)
    tracked_modules={'ffn_'+str(i):att.cluster_ffn[i] for i in ffn_levels}
    tracked = {name:dict(module.named_parameters()) for name,module in tracked_modules.items()}
    initial = {name:fingerprint(torch,{n:p.detach() for n,p in ps.items()}) for name,ps in tracked.items()}
    calls, rawbanks, csort, readbacks, resolvent_calls, path_records = [], [], [], [], [], []
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
        if candidate:
            members=[tuple(level[b].detach().cpu().tolist() for level in bank.cluster_ids_list) for b in range(len(bank.cluster_ids_list[0]))]
            coverage=hpc_coverage_preflight(members)
            result.setdefault('native_coverage_preflight_observations',[]).append(coverage)
            if not coverage['real_cross_level_component_possible']:
                result['coverage_status']='INCONCLUSIVE_FIXED_BATCH_NO_SUPPORTED_TWO_FINE_COMPONENT'
                raise RuntimeError('INCONCLUSIVE_COVERAGE: original fixed TRAIN batch lacks a supported fine-middle-coarse component with >=2 fine descendants before grad watches; no redraw or mechanism rejection')
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
            state['ffn_counts'][level]+=1;state['ffn_outputs'][level]=output
            if candidate:assert values[0] is state['analyzed_outputs'][level]
            watch(values[0],record,'native_input_gradients');watch(output,record,'native_output_gradients')
        return observe_ffn
    for level in ffn_levels:hooks.append(att.cluster_ffn[level].register_forward_hook(ffn_hook(level)))
    if candidate:
        hpc_module=importlib.import_module(qualified+'.hierarchy_resolvent')
        hierarchy=importlib.import_module(qualified+'.hier_postprocess')
        original_prepare=hierarchy.prepare_resolvent_plans
        original_plan=hpc_module.build_resolvent_plan
        original_solver=hierarchy.solve_resolvent_levels
        def norm_pre(level):
            def call(owner,values):
                assert values[0] is state['raw_refs'][level]
                state['norm_counts'][level]+=1
            return call
        def norm_post(level):
            def call(owner,values,output):
                state['norm_outputs'][level]=output
            return call
        for level in range(3):
            hooks.extend([att.cluster_ffn_norm[level].register_forward_pre_hook(norm_pre(level)),
                att.cluster_ffn_norm[level].register_forward_hook(norm_post(level))])
        def observed_plan(point_ids,fine_to_middle,middle_to_coarse,bank_sizes):
            context=state['hpc_context'];b=len(context['plans'])
            assert (point_ids,fine_to_middle,middle_to_coarse)==context['members'][b]
            assert bank_sizes==context['widths']
            value=original_plan(point_ids,fine_to_middle,middle_to_coarse,bank_sizes)
            record=hpc_plan_observation(value,point_ids,fine_to_middle,middle_to_coarse,bank_sizes)
            record['batch']=b;context['record']['plans'].append(record);context['plans'].append(value)
            return value
        def observed_prepare(levels,ids):
            assert levels is state['raw_refs'] and ids is bank.cluster_ids_list and 'hpc_context' not in state
            members=[tuple(ids[l][b].detach().cpu().tolist() for l in range(3)) for b in range(levels[0].shape[0])]
            coverage=hpc_coverage_preflight(members)
            if not coverage['real_cross_level_component_possible']:
                result['coverage_status']='INCONCLUSIVE_FIXED_BATCH_NO_SUPPORTED_TWO_FINE_COMPONENT'
                raise RuntimeError('INCONCLUSIVE_COVERAGE: original fixed batch lacks a true fine-middle-coarse component with at least two supported fine descendants; no redraw')
            record={'forward':state['forward_index'],'original_prepare_calls':1,'plans':[],
                'coverage':coverage,'solver_calls':[],'native_observer_scope':'Actual original plans and two original solver calls; original gather/add/copy/new_tensor methods once with original return objects. No solver, FFN, forward, backward or residual replay.',
                'offdiagonal_or_Jacobian_probe':'NOT_IMPLEMENTED_NOT_MEASURED','numerical_residual':'NOT_IMPLEMENTED_NOT_A_GATE'}
            state['hpc_context']={'record':record,'members':members,'widths':[int(x.shape[1]) for x in levels],
                'plans':[],'solver_count':0}
            plans=original_prepare(levels,ids)
            assert len(plans)==len(members) and all(a is b for a,b in zip(plans,state['hpc_context']['plans']))
            state['hpc_context']['actual_plans_object']=plans
            return plans
        setattr(hpc_module,'build_resolvent_plan',observed_plan)
        global_replacements.append((hpc_module,'build_resolvent_plan',original_plan))
        setattr(hierarchy,'prepare_resolvent_plans',observed_prepare)
        global_replacements.append((hierarchy,'prepare_resolvent_plans',original_prepare))
        def same_batch_view(value,full,b):
            return (tuple(value.shape)==tuple(full.shape[1:]) and value.device==full.device and value.dtype==full.dtype
                and value.data_ptr()==full.data_ptr()+b*full.stride(0)*full.element_size())
        method_names=('index_select','index_add','index_copy','new_tensor')
        originals={name:getattr(torch.Tensor,name) for name in method_names}
        def observe_operation(context,name,receiver,args,kwargs,output):
            # Only original solver execution enables this context. Observer summaries do not
            # invoke another solver/gather/scatter and never replace the original return.
            b=context['batch'];plans=context['plans']
            assert 0<=b<len(plans) and plans[b]['fine_ids']
            plan=plans[b];count=context['counts'][name];context['counts'][name]+=1
            ids=[plan[k] for k in ('fine_ids','middle_ids','coarse_ids')]
            record={'batch':b,'kind':name,'input':summary(receiver),'output':summary(output)}
            assert record['input']['finite'] and record['output']['finite']
            if name=='index_select':
                assert len(args)==2 and args[0]==0 and not kwargs
                index=args[1].detach().cpu().tolist();record['indices']=index
                if count<3:
                    level=count;role=('fine_gather','middle_gather','coarse_gather')[level]
                    assert index==ids[level] and same_batch_view(receiver,context['levels'][level],b)
                    context['gathered'][level]=output
                else:
                    assert count in (3,4)
                    role=('coarse_to_middle_parent_read','middle_to_fine_parent_read')[count-3]
                    expected=plan['middle_parent_positions'] if count==3 else plan['fine_parent_positions']
                    assert index==expected
                    context['solved'][2 if count==3 else 1]=receiver
                watch(receiver,record,'native_input_gradients');watch(output,record,'native_output_gradients')
            elif name=='new_tensor':
                assert count in (0,1) and len(args)==1 and not kwargs
                level=count+1;key='middle_diagonal' if level==1 else 'coarse_diagonal'
                role='actual_'+key;assert receiver is context['gathered'][level] and list(args[0])==plan[key]
                record['actual_metadata_values']=list(args[0]);record['requires_grad']=bool(output.requires_grad)
            elif name=='index_add':
                assert count in (0,1) and len(args)==3 and args[0]==0 and not kwargs
                level=count+1;role=('fine_to_middle_Schur_rhs','middle_to_coarse_Schur_rhs')[count]
                index=args[1].detach().cpu().tolist();source=args[2]
                assert receiver is context['gathered'][level]
                assert index==(plan['fine_parent_positions'] if count==0 else plan['middle_parent_positions'])
                assert source.shape[0]==len(index) and source.shape[1]==receiver.shape[1]
                record.update(indices=index,source=summary(source))
                assert record['source']['finite']
                context['rhs'][level]=output
                watch(receiver,record,'native_input_gradients');watch(source,record,'native_source_gradients');watch(output,record,'native_output_gradients')
            else:
                assert name=='index_copy' and count in (0,1,2) and len(args)==3 and args[0]==0 and not kwargs
                level=count;role=('fine_original_ID_writeback','middle_original_ID_writeback','coarse_original_ID_writeback')[level]
                index=args[1].detach().cpu().tolist();source=args[2]
                assert index==ids[level] and same_batch_view(receiver,context['levels'][level],b)
                if level in (1,2):assert source is context['solved'][level]
                record.update(indices=index,source=summary(source));assert record['source']['finite']
                context['batch_outputs'][level]=output
                watch(receiver,record,'native_input_gradients');watch(source,record,'native_source_gradients');watch(output,record,'native_output_gradients')
            record['role']=role;context['record']['operations'].append(record)
            if name=='index_copy' and count==2:
                assert context['counts']=={'index_select':5,'index_add':2,'index_copy':3,'new_tensor':2}
                context['record']['actual_batch_operation_counts'].append({'batch':b,**context['counts']})
                context['outputs'][b]=dict(context['batch_outputs'])
                context['batch']=next((j for j in range(b+1,len(plans)) if plans[j]['fine_ids']),len(plans))
                context['counts']={k:0 for k in method_names};context['gathered']={};context['rhs']={};context['solved']={};context['batch_outputs']={}
        def method_wrapper(name):
            original=originals[name]
            def wrapped(receiver,*args,**kwargs):
                output=original(receiver,*args,**kwargs)
                context=state.get('active_hpc_solver')
                if context is not None and not context.get('inside_observer'):
                    context['inside_observer']=True
                    try:observe_operation(context,name,receiver,args,kwargs,output)
                    finally:context['inside_observer']=False
                return output
            return wrapped
        for name in method_names:
            setattr(torch.Tensor,name,method_wrapper(name));global_replacements.append((torch.Tensor,name,originals[name]))
        def observed_solver(levels,plans):
            parent=state['hpc_context'];parent['solver_count']+=1;phase=parent['solver_count']
            assert phase in (1,2) and plans is parent['actual_plans_object']
            expected=state['norm_outputs'] if phase==1 else state['ffn_outputs']
            assert len(levels)==3 and all(levels[l] is expected[l] for l in range(3))
            assert state['norm_counts']==[1,1,1]
            if phase==2:assert state['ffn_counts']==[1,1,1]
            record={'forward':state['forward_index'],'phase':'analysis' if phase==1 else 'synthesis',
                'input':[summary(x) for x in levels],'input_sha256':fingerprint(torch,levels),
                'operations':[],'actual_batch_operation_counts':[],
                'original_solver_calls':1,'outputs_from_actual_index_copy_or_empty_identity':[]}
            for l,x in enumerate(levels):assert record['input'][l]['finite'];watch(x,record,'native_input_level'+str(l)+'_gradients')
            context={'record':record,'levels':levels,'plans':plans,'batch':next((b for b,p in enumerate(plans) if p['fine_ids']),len(plans)),
                'counts':{k:0 for k in method_names},'gathered':{},'rhs':{},'solved':{},'batch_outputs':{},'outputs':{},'inside_observer':False}
            assert state.get('active_hpc_solver') is None;state['active_hpc_solver']=context
            try:output=original_solver(levels,plans)
            finally:state.pop('active_hpc_solver',None)
            assert context['batch']==len(plans) and len(output)==3
            for b,plan in enumerate(plans):
                for l in range(3):
                    actual=context['outputs'][b][l] if plan['fine_ids'] else levels[l][b]
                    exact=fingerprint(torch,output[l][b])==fingerprint(torch,actual)
                    assert exact;record['outputs_from_actual_index_copy_or_empty_identity'].append({'batch':b,'level':l,'exact':exact,'empty_identity':not bool(plan['fine_ids'])})
            record.update(output=[summary(x) for x in output],output_sha256=fingerprint(torch,output),
                actual_supported_batch_count=len(context['outputs']),transparent_original_return=True,
                numerical_residual_gate_added=False,per_row_or_call_nonzero_gate=False)
            for l,x in enumerate(output):assert record['output'][l]['finite'];watch(x,record,'native_output_level'+str(l)+'_gradients')
            parent['record']['solver_calls'].append(record)
            if phase==1:state['analyzed_outputs']=output
            else:state['hpc_delta_snapshots']=[x.detach().clone() for x in output]
            return output
        setattr(hierarchy,'solve_resolvent_levels',observed_solver)
        global_replacements.append((hierarchy,'solve_resolvent_levels',original_solver))

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
        for level in (ffn_levels if not candidate else ()):
            exact=fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['ffn_snapshots'][level])
            record['original_residual_levels'][str(level)]=exact;assert exact
        if candidate:
            exact=[fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['hpc_delta_snapshots'][level]) for level in range(3)]
            record['HPC_original_three_skips_and_exact_HCG_inputs']=exact;assert all(exact)
            context=state['hpc_context'];assert context['solver_count']==2 and state['norm_counts']==[1,1,1] and state['ffn_counts']==[1,1,1]
            context['record'].update(actual_three_LN_calls=list(state['norm_counts']),actual_three_FFN_calls=list(state['ffn_counts']),
                original_two_solver_calls=context['solver_count'],actual_cross_level_component_exercised=True,
                original_three_skips_and_HCG_inputs=exact,graph_reachability_scope='Actual original plan/ordered gather-Schur-add-parent-read-writeback graph and native finite loss gradients; no pairwise Jacobian or auxiliary intervention')
            resolvent_calls.append(context['record'])
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
        state['forward_index']+=1;state['ffn_snapshots']={};state['ffn_counts']=[0,0,0];state['ffn_outputs']={};state['norm_counts']=[0,0,0];state['norm_outputs']={}
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
        for key in ('raw_refs','raw_record','hpc_delta_snapshots','norm_outputs','ffn_outputs','hpc_context','analyzed_outputs','encoder_inst_before','encoder_gate','cluster_message'):state.pop(key,None)
        state['ffn_snapshots'].clear()
    def before_step(owner,args,kwargs):
        assert backward_records[-1]['count']==1
        if candidate:assert resolvent_calls[-1]['original_two_solver_calls']==2 and resolvent_calls[-1]['actual_cross_level_component_exercised']
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
            weights=[g for n,g in gradients.items() if n.endswith('weight')]
            assert weights and all(g is not None and g['finite'] for g in weights)
            assert all(g is None or g['finite'] for g in gradients.values())
            assert any(g['abs_max']>0 for g in weights),'Native original FFN group aggregate weight gradient is zero; local path control, no resampling or whole-mechanism rejection'
            record.setdefault('tracked_group_aggregate_weight_nonzero',{})[name]=True
    def after_step(owner,args,kwargs):
        record=steps[-1];record['optimizer_step_completed']=True
        record['module_after_step_hash']={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
        record['weight_after_step_hash']={n:fingerprint(torch,{k:p.detach() for k,p in ps.items() if k.endswith('weight')}) for n,ps in tracked.items()}
        record['individual_parameter_after_step_hash']={n:{k:fingerprint(torch,p.detach()) for k,p in ps.items()} for n,ps in tracked.items()}
        record['individual_parameter_changed']={n:{k:record['individual_parameter_before_step_hash'][n][k]!=record['individual_parameter_after_step_hash'][n][k] for k in ps} for n,ps in tracked.items()}
        record['bias_update_scope']='Recorded only; zero bias gradient or unchanged bias is legal, no separate nonzero/update gate'
        assert all(record['module_before_step_hash'][n]!=record['module_after_step_hash'][n] and record['weight_before_step_hash'][n]!=record['weight_after_step_hash'][n] for n in tracked)
        result['optimizer_steps']+=1
    hooks.extend([model.register_forward_pre_hook(native_input),model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step),optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False,losses=losses,steps=steps,batches=batches,native_backward_records=backward_records,
        ffn_calls=calls,raw_bank_observations=rawbanks,csort_raw_input_observations=csort,hcg_readbacks=readbacks,
        HPC_resolvent_observations=resolvent_calls,inst_to_mask_path_observations=path_records,native_dataloader_config=dict(cfg.dataloader.train),
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',
        actual_champion_candidate_batch_pairing='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both complete raw batch fingerprints and common named initialization',
        smoke_memory_scope='Two native TRAIN steps including observer hooks, detached snapshots, actual topology/source recording; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; no separate no-observer native TRAIN process pair',auxiliary_autograd_grad_or_backward_used=False,
        native_failure_is_not_whole_mechanism_rejection=True,
        coverage_gate_scope='Each original fixed TRAIN forward needs a true fine-middle-coarse component with at least two supported fine descendants. Optional boundaries/per-call/row/bias zeros legal; no resampling or numerical residual gate.',
        dynamic_parameter_inventory={'original_FFN_parameters_by_level':{str(i):sum(p.numel() for p in att.cluster_ffn[i].parameters()) for i in range(3)},
            'new_declared_parameters':0,
            'actual_full_model_parameters':sum(p.numel() for p in model.parameters()),'actual_named_parameter_tensors':sum(1 for _ in model.named_parameters()),
            'state_dict_keys':list(model.state_dict()),'geometry_registered_buffer_names':[n for n,_ in model.named_buffers() if 'middle_positions' in n or 'middle_parent_ids' in n or 'middle_valid' in n]})
    logger=logging.getLogger('hpc-native-smoke');logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
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
    assert len(calls)==6 and len(resolvent_calls)==(2 if candidate else 0)
    for forward in (1,2):assert [v['level'] for v in calls if v['forward']==forward]==list(ffn_levels)
    for record in calls:
        for key in ('native_input_gradients','native_output_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    for record in resolvent_calls:
        assert record['original_prepare_calls']==1 and record['original_two_solver_calls']==2 and record['actual_three_LN_calls']==record['actual_three_FFN_calls']==[1,1,1]
        assert [call['phase'] for call in record['solver_calls']]==['analysis','synthesis']
        for call in record['solver_calls']:
            for level in range(3):
                for key in ('native_input_level'+str(level)+'_gradients','native_output_level'+str(level)+'_gradients'):
                    assert call.get(key) and all(g['finite'] for g in call[key])
            for operation in call['operations']:
                if operation['kind']=='new_tensor':continue
                for key in ('native_input_gradients','native_output_gradients'):
                    assert operation.get(key) and all(g['finite'] for g in operation[key])
                if operation['kind'] in ('index_add','index_copy'):
                    assert operation.get('native_source_gradients') and all(g['finite'] for g in operation['native_source_gradients'])
        # Each row/call may be zero. Only three original FFN groups have an aggregate nonzero/update gate.
    for record in readbacks:assert record.get('native_point_message_gradients') and all(g['finite'] for g in record['native_point_message_gradients'])
    for record in path_records:
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    final={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
    assert all(final[n]!=initial[n] for n in tracked);verify()
    result.update(execution_completed=True,native_data_loaded=True,native_train_function_executed=True,backward_finite=True,
        intended_path_observed=(len(resolvent_calls)==2 and all(v['original_two_solver_calls']==2 and v['actual_cross_level_component_exercised'] for v in resolvent_calls)) if candidate else len(calls)==6,
        new_operator_parameters=0,native_tracked_initial_hash=initial,native_tracked_after_hash=final,
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
        'native_model_and_yaml_unchanged':False,'source_scope':'Exact native HPC or original M95, original backbone pretrain and native train loop'}
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
