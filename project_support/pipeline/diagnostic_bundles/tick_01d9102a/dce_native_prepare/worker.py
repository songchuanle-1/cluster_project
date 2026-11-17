"""DCE native two-step smoke and original-handler resources; fresh lease required."""
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



def dce_plan_observation(plan, members):
    ids0,ids1,ids2=members
    fine=sorted(set(ids0));middle=sorted({ids1[i] for i in fine});coarse=sorted({ids2[j] for j in middle})
    assert [plan[k] for k in ('fine_ids','middle_ids','coarse_ids')]==[fine,middle,coarse]
    mp={j:i for i,j in enumerate(middle)};cp={k:i for i,k in enumerate(coarse)}
    fm=[mp[ids1[i]] for i in fine];mc=[cp[ids2[j]] for j in middle]
    fg=[[i for i,p in enumerate(fm) if p==j] for j in range(len(middle))]
    mg=[[j for j,p in enumerate(mc) if p==k] for k in range(len(coarse))]
    assert plan['fine_parent_positions']==fm and plan['middle_parent_positions']==mc
    assert plan['fine_groups']==fg and plan['middle_groups']==mg
    assert plan['fine_counts']==[len(g) for g in fg] and plan['middle_counts']==[len(g) for g in mg]
    assert plan['point_count']==len(ids0)
    return copy.deepcopy(plan)


def dce_coverage_preflight(members):
    scenes=[]
    for batch,(ids0,ids1,ids2) in enumerate(members):
        fine=sorted(set(ids0));middle=sorted({ids1[i] for i in fine});coarse=sorted({ids2[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'actual_path_count':len(fine)})
    return {'scenes':scenes,'true_cavity_path_possible':any(x['actual_path_count'] for x in scenes),'total_true_paths':sum(x['actual_path_count'] for x in scenes)}


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
    assert cfg.model.dec.cluster_att_num_layers == 1, 'DCE requires only the original final hierarchy injection'
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
        excluded = ('dec.cluster_att.cluster_ffn.0.', 'dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.cluster_ffn.2.', 'dec.cluster_att.cavity.')
        common = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        result['common_initialized_parameters'] = {
            'scope':'Original common named parameters after native backbone pretrain, before TRAIN loader; exclude all three removed FFN prefixes and new-cavity subtree on both targets; retain all three LayerNorms',
            'excluded_name_prefixes':list(excluded), 'names':list(common), 'shapes':{n:list(p.shape) for n,p in common.items()}, 'tensor_count':len(common),
            'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),
            'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; observation only, not a full-common-state gate'}
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler


def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original TRAIN2 with actual DCE hooks; no auxiliary forward/backward/probe."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('dce-native-smoke'))
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
        tracked_modules['cavity']=att.cavity
        assert sum(p.numel() for p in att.cavity.parameters())==787968
    tracked = {name:dict(module.named_parameters()) for name,module in tracked_modules.items()}
    initial = {name:fingerprint(torch,{n:p.detach() for n,p in ps.items()}) for name,ps in tracked.items()}
    calls, rawbanks, csort, readbacks, exchange_calls, path_records = [], [], [], [], [], []
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
            coverage=dce_coverage_preflight(members)
            result.setdefault('native_coverage_preflight_observations',[]).append(coverage)
            if not coverage['true_cavity_path_possible']:
                result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_CAVITY'
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
        dce_module=importlib.import_module(qualified+'.directed_cavity')
        original_plan=dce_module.build_cavity_plan;original_prepare=dce_module.prepare_cavity_plans
        original_mean=dce_module.mean_by_parent;original_exclusive=dce_module.exclusive_group_sums
        names=('up','down_root','down_middle','read_fine','read_middle','read_coarse')
        event_order=['mean_fine','up','act_up','mean_middle','exclusive_middle','down_root','act_down_root','exclusive_fine','down_middle','act_down_middle','read_fine','act_read_fine','read_middle','act_read_middle','read_coarse','act_read_coarse']
        def norm_pre(level):
            def call(owner,values):
                assert values[0] is state['raw_refs'][level];state['norm_counts'][level]+=1
            return call
        def norm_post(level):
            def call(owner,values,output):state['norm_outputs'][level]=output
            return call
        for level in range(3):hooks.extend([att.cluster_ffn_norm[level].register_forward_pre_hook(norm_pre(level)),att.cluster_ffn_norm[level].register_forward_hook(norm_post(level))])
        def optional_watch(value,record,key):
            if value.requires_grad:watch(value,record,key)
            else:record[key+'_scope']='NO_FEATURE_GRAPH_FOR_THIS_OPTIONAL_CALL; no per-call nonzero gate'
        def event(name):
            context=state['dce_context'];assert event_order[len(context['events'])]==name
            context['events'].append(name)
        def exchange_pre(owner,values):
            normalized,ids=values
            assert owner is att.cavity and ids is bank.cluster_ids_list and state['norm_counts']==[1,1,1]
            assert all(normalized[i] is state['norm_outputs'][i] for i in range(3))
            members=[tuple(level[b].detach().cpu().tolist() for level in ids) for b in range(int(normalized[0].shape[0]))]
            coverage=dce_coverage_preflight(members)
            if not coverage['true_cavity_path_possible']:
                result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_CAVITY_PATH'
                raise RuntimeError('INCONCLUSIVE_COVERAGE: no supported original cavity path before watches; no resampling')
            record={'forward':state['forward_index'],'inputs':[summary(x) for x in normalized],
                'normalized_bank_sha256':fingerprint(torch,normalized),'original_three_LN_calls':list(state['norm_counts']),
                'plans':[],'map_calls':[],'mean_calls':[],'exclusive_calls':[],
                'offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED',
                'native_observer_scope':'Capture original helper/map/GELU outputs and subsequent cat/scatter references; no learned/helper replay or auxiliary backward. Per-map/call/row zero legal; aggregate cavity weight training is the gate.'}
            assert 'dce_context' not in state
            state['dce_context']={'record':record,'normalized':normalized,'ids_ref':ids,'members':members,'widths':[int(x.shape[1]) for x in normalized],
                'builder_calls':0,'indices':[[],[],[]],'fm':[],'mc':[],'fg':[],'mg':[],'fc':[],'cc':[],
                'events':[],'means':[],'exclusive':[],'activations':{},'prepared_once':0}
            for level,x in enumerate(normalized):watch(x,record,'native_normalized_level'+str(level)+'_gradients')
        def observed_plan(ids0,ids1,ids2,widths):
            context=state['dce_context'];b=context['builder_calls'];context['builder_calls']+=1
            assert (ids0,ids1,ids2)==context['members'][b] and widths==context['widths']
            plan=original_plan(ids0,ids1,ids2,widths);record=dce_plan_observation(plan,(ids0,ids1,ids2));record['batch']=b
            context['record']['plans'].append(record);fo,mo,co=(len(v) for v in context['indices'])
            for l,key in enumerate(('fine_ids','middle_ids','coarse_ids')):context['indices'][l].extend(b*widths[l]+i for i in plan[key])
            context['fm'].extend(mo+i for i in plan['fine_parent_positions']);context['mc'].extend(co+i for i in plan['middle_parent_positions'])
            context['fg'].extend([[fo+i for i in g] for g in plan['fine_groups']]);context['mg'].extend([[mo+i for i in g] for g in plan['middle_groups']])
            context['fc'].extend(plan['fine_counts']);context['cc'].extend(plan['middle_counts'])
            return plan
        def observed_prepare(levels,ids):
            context=state['dce_context'];assert context['prepared_once']==0 and ids is context['ids_ref'] and all(levels[l] is context['normalized'][l] for l in range(3))
            output=original_prepare(levels,ids);context['prepared_once']=1
            assert context['builder_calls']==len(output)==int(levels[0].shape[0])
            c=att.cavity.channels;context['z']=[]
            for l in range(3):
                index=torch.tensor(context['indices'][l],device=levels[l].device,dtype=torch.long)
                context['z'].append(levels[l].detach().reshape(-1,c).index_select(0,index))
            return output
        def observed_mean(messages,positions,counts):
            context=state['dce_context'];which=len(context['means']);assert which in (0,1)
            event('mean_fine' if which==0 else 'mean_middle')
            expected=context['z'][0] if which==0 else context['activations']['up']
            assert positions==context['fm' if which==0 else 'mc'] and counts==context['fc' if which==0 else 'cc']
            assert fingerprint(torch,messages)==fingerprint(torch,expected)
            record={'which':which,'input':summary(messages),'parent_positions':list(positions),'counts':list(counts),'original_calls':1,'returned_original_object_unchanged':True,'replayed':False}
            optional_watch(messages,record,'native_input_gradients');output=original_mean(messages,positions,counts)
            record.update(output=summary(output),output_sha256=fingerprint(torch,output));assert record['output']['finite']
            optional_watch(output,record,'native_output_gradients');context['means'].append(output.detach().clone());context['record']['mean_calls'].append(record)
            return output
        def observed_exclusive(messages,groups):
            context=state['dce_context'];which=len(context['exclusive']);assert which in (0,1)
            event('exclusive_middle' if which==0 else 'exclusive_fine')
            assert groups==context['mg' if which==0 else 'fg']
            expected=context['activations']['up'] if which==0 else context['z'][0]
            assert fingerprint(torch,messages)==fingerprint(torch,expected)
            assert sorted(i for group in groups for i in group)==list(range(messages.shape[0]))
            record={'which':which,'groups':copy.deepcopy(groups),'input':summary(messages),'original_calls':1,'receiver_branch_excluded_by_original_prefix_suffix_helper':True,
                'singleton_groups':sum(len(g)==1 for g in groups),'returned_original_object_unchanged':True,'replayed':False,
                'scope':'Bank-token reverse branch exclusion only; raw ancestors already contain descendant point evidence.'}
            optional_watch(messages,record,'native_input_gradients');output=original_exclusive(messages,groups)
            record.update(output=summary(output),output_sha256=fingerprint(torch,output));assert record['output']['finite']
            optional_watch(output,record,'native_output_gradients');context['exclusive'].append(output.detach().clone());context['record']['exclusive_calls'].append(record)
            return output
        for name,replacement,original in [('build_cavity_plan',observed_plan,original_plan),('prepare_cavity_plans',observed_prepare,original_prepare),('mean_by_parent',observed_mean,original_mean),('exclusive_group_sums',observed_exclusive,original_exclusive)]:
            setattr(dce_module,name,replacement);global_replacements.append((dce_module,name,original))
        def expected_map(name,context):
            z=context['z'];device=z[0].device;fm=torch.tensor(context['fm'],device=device,dtype=torch.long);mc=torch.tensor(context['mc'],device=device,dtype=torch.long)
            acts=context['activations'];means=context['means'];exc=context['exclusive']
            if name=='up':parts=[z[1],means[0]]
            elif name=='down_root':parts=[z[2].index_select(0,mc),exc[0]/acts['up'].new_tensor([max(context['cc'][k]-1,1) for k in context['mc']]).unsqueeze(-1)]
            elif name=='down_middle':parts=[z[1].index_select(0,fm),(exc[1]+acts['down_root'].index_select(0,fm))/z[0].new_tensor([context['fc'][j] for j in context['fm']]).unsqueeze(-1)]
            elif name=='read_fine':parts=[z[0],acts['down_middle']]
            elif name=='read_middle':parts=[z[1],(means[0]*z[1].new_tensor(context['fc']).unsqueeze(-1)+acts['down_root'])/z[1].new_tensor([n+1 for n in context['fc']]).unsqueeze(-1)]
            else:assert name=='read_coarse';parts=[z[2],means[1]]
            return torch.cat(parts,dim=-1)
        def map_pre(name):
            def call(owner,values):
                context=state['dce_context'];event(name);value=values[0]
                expected=expected_map(name,context);assert fingerprint(torch,value)==fingerprint(torch,expected)
                record={'module':name,'input':summary(value),'input_sha256':fingerprint(torch,value),'actual_original_messages_and_receiver_exclusion_inputs_exact':True,'original_linear_calls':1}
                assert record['input']['finite'];watch(value,record,'native_input_gradients');context['pending_record']=record
            return call
        def map_post(name):
            def call(owner,values,output):
                context=state['dce_context'];record=context['pending_record'];assert record['module']==name
                record.update(linear_output=summary(output),linear_output_sha256=fingerprint(torch,output));assert record['linear_output']['finite']
                watch(output,record,'native_linear_output_gradients');context['pending_linear']=(name,output);context['record']['map_calls'].append(record)
            return call
        def activation_post(owner,values,output):
            context=state['dce_context'];name,linear=context.pop('pending_linear');assert values[0] is linear;event('act_'+name)
            record=context['pending_record'];record.update(output=summary(output),output_sha256=fingerprint(torch,output),original_GELU_calls=1)
            assert record['output']['finite'];watch(output,record,'native_output_gradients');context['activations'][name]=output.detach().clone()
        for name in names:hooks.extend([getattr(att.cavity,name).register_forward_pre_hook(map_pre(name)),getattr(att.cavity,name).register_forward_hook(map_post(name))])
        hooks.append(att.cavity.activation.register_forward_hook(activation_post))
        def exchange_post(owner,values,output):
            context=state.pop('dce_context');record=context['record'];assert context['events']==event_order and len(output)==3
            assert context['prepared_once']==1 and len(context['means'])==len(context['exclusive'])==2 and len(record['map_calls'])==6
            for level,name in enumerate(('read_fine','read_middle','read_coarse')):
                value=output[level];index=torch.tensor(context['indices'][level],device=value.device,dtype=torch.long)
                reference=value.new_zeros((value.shape[0]*value.shape[1],value.shape[2])).index_copy(0,index,context['activations'][name]).reshape(value.shape)
                assert fingerprint(torch,value)==fingerprint(torch,reference)
                assert summary(value)['finite'];watch(value,record,'native_output_level'+str(level)+'_gradients')
            optional=[]
            for p in record['plans']:
                optional.append({'batch':p['batch'],'fine_degree_counts':p['fine_counts'],'middle_degree_counts':p['middle_counts'],
                    'multiple_child_middle':sum(n>1 for n in p['fine_counts']),'multiple_child_coarse':sum(n>1 for n in p['middle_counts']),
                    'singleton_middle':sum(n==1 for n in p['fine_counts']),'singleton_coarse':sum(n==1 for n in p['middle_counts']),
                    'empty_scene':not p['fine_ids'],'unsupported_or_padding':[context['widths'][l]-len(p[k]) for l,k in enumerate(('fine_ids','middle_ids','coarse_ids'))]})
            record.update(outputs=[summary(x) for x in output],output_sha256=fingerprint(torch,output),actual_true_fine_paths=len(context['indices'][0]),
                actual_original_builder_calls=context['builder_calls'],actual_private_mean_calls=2,actual_exclusive_calls=2,actual_map_calls=6,actual_GELU_calls=6,
                actual_three_LN_calls=list(state['norm_counts']),actual_event_order=list(context['events']),actual_optional_boundary_counts=optional,
                three_original_ID_delta_shapes=True,unsupported_padding_deltas_zero=True,final_deltas_from_actual_captures_exact=True)
            state['dce_delta_snapshots']=[x.detach().clone() for x in output];exchange_calls.append(record)
        hooks.extend([att.cavity.register_forward_pre_hook(exchange_pre),att.cavity.register_forward_hook(exchange_post)])
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
            exact=[fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['dce_delta_snapshots'][level]) for level in range(3)]
            record['DCE_original_three_skips_and_exact_HCG_inputs']=exact;assert all(exact)
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
        for key in ('raw_refs','raw_record','dce_delta_snapshots','norm_outputs','encoder_inst_before','encoder_gate','cluster_message'):state.pop(key,None)
        state['ffn_snapshots'].clear()
    def parameter_blocks():
        if not candidate:return {}
        c=att.cavity.channels
        return {name:(getattr(att.cavity,name).weight,0,c,0,2*c) for name in ('up','down_root','down_middle','read_fine','read_middle','read_coarse')}
    def before_step(owner,args,kwargs):
        assert backward_records[-1]['count']==1
        if candidate and not exchange_calls[-1]['actual_true_fine_paths']:
            result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_CAVITY'
            raise RuntimeError('INCONCLUSIVE_COVERAGE: no true cavity path, no replacement sample/seed')
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
                assert any(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight')),'Whole cavity aggregate original-loss weight gradient is zero; local control inconclusive, not whole-mechanism rejection'
            else:
                assert all(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight'))
            record['gradient_gate_scope']='Candidate whole cavity aggregate only; individual maps/weights/rows/bias may be zero or unexercised, descriptive only'
            if candidate:
                weights=[g for n,g in gradients.items() if n.endswith('weight') and g is not None]
                record['whole_cavity_weight_gradient']={'finite':all(g['finite'] for g in weights),'abs_max':max(g['abs_max'] for g in weights),'observed_weight_tensors':len(weights),'scope':'Aggregate across entire cavity; individual map zeros/unused legal'}
        record['native_parameter_block_gradients']={}
        record['parameter_block_before_step_hash']={}
        for name,(weight,r0,r1,c0,c1) in parameter_blocks().items():
            info=summary(weight.grad[r0:r1,c0:c1]) if weight.grad is not None else None;record['native_parameter_block_gradients'][name]=info
            assert info is None or info['finite'];record.setdefault('block_gradient_gate_scope','Six whole-map weights descriptive; individual zero/unused legal. Whole cavity aggregate weight is the native nonzero gate.')
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
            record['whole_cavity_weight_updated']=record['weight_before_step_hash']['cavity']!=record['weight_after_step_hash']['cavity']
            record['whole_cavity_module_updated']=record['module_before_step_hash']['cavity']!=record['module_after_step_hash']['cavity']
        record['parameter_block_after_step_hash']={name:fingerprint(torch,weight.detach()[r0:r1,c0:c1]) for name,(weight,r0,r1,c0,c1) in parameter_blocks().items()}
        record['descriptive_parameter_block_changed']={name:record['parameter_block_before_step_hash'][name]!=record['parameter_block_after_step_hash'][name] for name in record['parameter_block_before_step_hash']}
        result['optimizer_steps']+=1
    hooks.extend([model.register_forward_pre_hook(native_input),model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step),optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False,losses=losses,steps=steps,batches=batches,native_backward_records=backward_records,
        ffn_calls=calls,raw_bank_observations=rawbanks,csort_raw_input_observations=csort,hcg_readbacks=readbacks,
        DCE_directed_cavity_observations=exchange_calls,inst_to_mask_path_observations=path_records,native_dataloader_config=dict(cfg.dataloader.train),
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',
        actual_champion_candidate_batch_pairing='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both complete raw batch fingerprints and common named initialization',
        smoke_memory_scope='Two native TRAIN steps including observer hooks, detached snapshots, actual topology/source recording; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; no separate no-observer native TRAIN process pair',auxiliary_autograd_grad_or_backward_used=False,
        native_failure_is_not_whole_mechanism_rejection=True,
        coverage_gate_scope='Each original fixed TRAIN forward needs at least one true supported fine cavity path. Singleton and degree boundaries are optional NOT_EXERCISED when absent; no resampling. Six map weights descriptive only; no per-map positivity gate.',
        dynamic_parameter_inventory={'original_FFN_parameters_by_level':{str(i):sum(p.numel() for p in att.cluster_ffn[i].parameters()) for i in range(3)},
            'new_declared_parameters':sum(p.numel() for p in att.cavity.parameters()) if candidate else 0,
            'actual_full_model_parameters':sum(p.numel() for p in model.parameters()),'actual_named_parameter_tensors':sum(1 for _ in model.named_parameters()),
            'state_dict_keys':list(model.state_dict()),'geometry_registered_buffer_names':[n for n,_ in model.named_buffers() if 'middle_positions' in n or 'middle_parent_ids' in n or 'middle_valid' in n]})
    logger=logging.getLogger('dce-native-smoke');logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
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
    assert len(calls)==(0 if candidate else 6) and len(exchange_calls)==(2 if candidate else 0)
    for forward in (1,2):assert [v['level'] for v in calls if v['forward']==forward]==list(ffn_levels)
    for record in calls:
        for key in ('native_input_gradients','native_output_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    for record in exchange_calls:
        assert record['actual_true_fine_paths']>0 and record['actual_map_calls']==record['actual_GELU_calls']==6 and record['actual_private_mean_calls']==record['actual_exclusive_calls']==2
        for level in range(3):
            for key in ('native_normalized_level'+str(level)+'_gradients','native_output_level'+str(level)+'_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
        for call in record['map_calls']:
            for key in ('native_input_gradients','native_linear_output_gradients','native_output_gradients'):assert call.get(key) and all(g['finite'] for g in call[key])
        for call in record['mean_calls']+record['exclusive_calls']:
            for key in ('native_input_gradients','native_output_gradients'):
                assert (call.get(key) and all(g['finite'] for g in call[key])) or call.get(key+'_scope')
        # Only whole cavity aggregate weight gradient/update is a nonzero gate. Individual maps/edges/rows may be zero.
    for record in readbacks:assert record.get('native_point_message_gradients') and all(g['finite'] for g in record['native_point_message_gradients'])
    for record in path_records:
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    final={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
    assert all(final[n]!=initial[n] for n in tracked);verify()
    result.update(execution_completed=True,native_data_loaded=True,native_train_function_executed=True,backward_finite=True,
        intended_path_observed=(len(exchange_calls)==2 and all(v['actual_true_fine_paths']>0 and v['actual_private_mean_calls']==2 for v in exchange_calls)) if candidate else len(calls)==6,
        new_operator_parameters=787968 if candidate else None,native_tracked_initial_hash=initial,native_tracked_after_hash=final,
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
        'native_model_and_yaml_unchanged':False,'source_scope':'Exact native DCE or original M95, original backbone pretrain and native train loop'}
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
