"""FCB native two-step smoke and original-handler resources; fresh lease required."""
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



def fcb_plan_observation(plan,members):
    points,fm,mc=members;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    parents=[middle.index(fm[i]) for i in fine]
    fp=[f for f in range(len(fine)) for _ in coarse];cp=[c for _ in fine for c in range(len(coarse))]
    expected={'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'fine_parent_positions':parents,
        'middle_fine_counts':[parents.count(j) for j in range(len(middle))],'pair_fine_positions':fp,'pair_coarse_positions':cp,
        'fine_pair_counts':[len(coarse)]*len(fine),'coarse_pair_counts':[len(fine)]*len(coarse),
        'pair_count':len(fp),'point_count':len(points)}
    assert plan==expected
    record=copy.deepcopy(plan);record['observed_nonancestor_pairs']=sum(coarse[c]!=mc[fm[fine[f]]] for f,c in zip(fp,cp))
    return record


def fcb_coverage_preflight(members):
    scenes=[]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
        scenes.append({'batch':batch,'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,
            'actual_path_count':len(fine),'actual_pair_count':len(fine)*len(coarse)})
    return {'scenes':scenes,'true_fine_coarse_pair_possible':any(x['actual_pair_count'] for x in scenes),
        'total_true_paths':sum(x['actual_path_count'] for x in scenes),'total_true_pairs':sum(x['actual_pair_count'] for x in scenes)}


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
    assert cfg.model.dec.cluster_att_num_layers == 1, 'FCB requires only the original final hierarchy injection'
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
        excluded = ('dec.cluster_att.cluster_ffn.0.', 'dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.cluster_ffn.2.', 'dec.cluster_att.fine_coarse_bipartite.')
        common = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        result['common_initialized_parameters'] = {
            'scope':'Original common named parameters after native backbone pretrain, before TRAIN loader; exclude all three removed FFN prefixes and new-fine_coarse_bipartite subtree on both targets; retain all three LayerNorms',
            'excluded_name_prefixes':list(excluded), 'names':list(common), 'shapes':{n:list(p.shape) for n,p in common.items()}, 'tensor_count':len(common),
            'parameter_count':sum(p.numel() for p in common.values()),
            'sha256':fingerprint(torch,common),
            'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; observation only, not a full-common-state gate'}
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler


def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original TRAIN2 with actual FCB hooks; no auxiliary forward/backward/probe."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('fcb-native-smoke'))
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
        tracked_modules['fine_coarse_bipartite']=att.fine_coarse_bipartite
        assert sum(p.numel() for p in att.fine_coarse_bipartite.parameters())==262656
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
            coverage=fcb_coverage_preflight(members)
            result.setdefault('native_coverage_preflight_observations',[]).append(coverage)
            if not coverage['true_fine_coarse_pair_possible']:
                result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FINE_COARSE_PAIR'
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
        fcb_module=importlib.import_module(qualified+'.fine_coarse_bipartite')
        original_plan=fcb_module.build_fine_coarse_plan;original_mean=fcb_module.equal_message_means
        def norm_pre(level):
            def call(owner,values):assert values[0] is state['raw_refs'][level];state['norm_counts'][level]+=1
            return call
        def norm_post(level):
            def call(owner,values,output):state['norm_outputs'][level]=output
            return call
        for level in range(3):hooks.extend([att.cluster_ffn_norm[level].register_forward_pre_hook(norm_pre(level)),att.cluster_ffn_norm[level].register_forward_hook(norm_post(level))])
        def exchange_pre(owner,values):
            normalized,ids=values
            assert owner is att.fine_coarse_bipartite and ids is bank.cluster_ids_list and state['norm_counts']==[1,1,1]
            assert all(normalized[level] is state['norm_outputs'][level] for level in range(3))
            members=[tuple(level[b].detach().cpu().tolist() for level in ids) for b in range(int(normalized[0].shape[0]))]
            coverage=fcb_coverage_preflight(members)
            if not coverage['true_fine_coarse_pair_possible']:
                result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FINE_COARSE_PAIR'
                raise RuntimeError('INCONCLUSIVE_COVERAGE: no true pair before watches; no resampling')
            record={'forward':state['forward_index'],'inputs':[summary(x) for x in normalized],
                'normalized_bank_sha256':fingerprint(torch,normalized),'original_three_LN_calls':list(state['norm_counts']),
                'plans':[],'map_calls':[],'mean_calls':[],'_internal_gradient_flags':[],
                'native_observer_scope':'Actual pair-map/GELU q -> sameq fine/coarse marginals -> actual fine_delta parent mean -> middle-map/GELU. Every original map/activation/mean called once, original mean result object returned, capture-only references; no operator/model/criterion replay or extra backward.',
                'FP32_marginal_or_Jacobian_gate':'NOT_IMPLEMENTED_NOT_REQUIRED'}
            assert 'fcb_context' not in state
            state['fcb_context']={'record':record,'normalized':normalized,'members':members,'widths':[int(x.shape[1]) for x in normalized],
                'builder_calls':0,'ids':[[],[],[]],'pair_fine':[],'pair_coarse':[],'fine_parents':[],
                'fine_counts':[],'coarse_counts':[],'middle_counts':[],'phase':'pair_map','map_count':0,
                'pair_map_count':0,'middle_map_count':0,'GELU_count':0,'mean_count':0,'mean_outputs':[],'mean_snapshots':[]}
            for level,x in enumerate(normalized):
                if not x.requires_grad:
                    result['coverage_status']='INCONCLUSIVE_CORE_INPUT_NOT_DIFFERENTIABLE'
                    raise RuntimeError('INCONCLUSIVE_COVERAGE: original core input not differentiable before watches')
                watch(x,record,'native_normalized_level'+str(level)+'_gradients')
        def observed_plan(ids0,ids1,ids2,widths):
            context=state['fcb_context'];batch=context['builder_calls'];context['builder_calls']+=1
            assert (ids0,ids1,ids2)==context['members'][batch] and widths==context['widths']
            output=original_plan(ids0,ids1,ids2,widths);record=fcb_plan_observation(output,(ids0,ids1,ids2));record['batch']=batch
            context['record']['plans'].append(record);fo,mo,co=(len(values) for values in context['ids'])
            for level,key in enumerate(('fine_ids','middle_ids','coarse_ids')):context['ids'][level].extend(batch*widths[level]+i for i in output[key])
            context['pair_fine'].extend(fo+i for i in output['pair_fine_positions']);context['pair_coarse'].extend(co+i for i in output['pair_coarse_positions'])
            context['fine_parents'].extend(mo+i for i in output['fine_parent_positions'])
            context['fine_counts'].extend(output['fine_pair_counts']);context['coarse_counts'].extend(output['coarse_pair_counts']);context['middle_counts'].extend(output['middle_fine_counts'])
            return output
        setattr(fcb_module,'build_fine_coarse_plan',observed_plan);global_replacements.append((fcb_module,'build_fine_coarse_plan',original_plan))
        def lite_watch(value,record):
            if value.requires_grad:
                def receive(gradient):record['_internal_gradient_flags'].append(torch.isfinite(gradient).all());return None
                hooks.append(value.register_hook(receive))
        def map_pre(kind):
            def call(owner,values):
                context=state['fcb_context'];value=values[0];c=att.fine_coarse_bipartite.channels
                assert context['phase']==kind+'_map' and context[kind+'_map_count']==0 and context['builder_calls']==int(context['normalized'][0].shape[0])
                if kind=='pair':
                    z=[]
                    for level in (0,2):
                        index=torch.tensor(context['ids'][level],device=value.device,dtype=torch.long)
                        z.append(context['normalized'][level].detach().reshape(-1,c).index_select(0,index))
                    fi=torch.tensor(context['pair_fine'],device=value.device,dtype=torch.long);ci=torch.tensor(context['pair_coarse'],device=value.device,dtype=torch.long)
                    expected=torch.cat([z[0].index_select(0,fi),z[1].index_select(0,ci)],dim=-1)
                else:
                    index=torch.tensor(context['ids'][1],device=value.device,dtype=torch.long)
                    middle=context['normalized'][1].detach().reshape(-1,c).index_select(0,index)
                    expected=torch.cat([middle,context['mean_snapshots'][2]],dim=-1)
                assert fingerprint(torch,value)==fingerprint(torch,expected)
                record={'kind':kind,'input':summary(value),'input_sha256':fingerprint(torch,value),
                    'actual_rows':int(value.shape[0]),'input_matches_original_ID_or_actual_mean_captures':True,'original_linear_calls':1}
                assert record['input']['finite'];lite_watch(value,context['record']);context['pending_record']=record
            return call
        def map_post(kind):
            def call(owner,values,output):
                context=state['fcb_context'];record=context['pending_record'];assert record['kind']==kind
                record.update(linear_output=summary(output),linear_output_sha256=fingerprint(torch,output));assert record['linear_output']['finite']
                lite_watch(output,context['record']);context['linear_ref']=output;context['pending_kind']=kind
                context[kind+'_map_count']+=1;context['map_count']+=1;context['phase']='GELU'
            return call
        def activation_post(owner,values,output):
            context=state['fcb_context'];kind=context['pending_kind']
            assert context['phase']=='GELU' and values[0] is context['linear_ref']
            record=context['pending_record'];record.update(output=summary(output),output_sha256=fingerprint(torch,output),original_GELU_calls=1)
            assert record['output']['finite'];lite_watch(output,context['record']);context['record']['map_calls'].append(record)
            if kind=='pair':context['q_ref']=output;context['q_snapshot']=output.detach().clone();context['phase']='fine_mean'
            else:context['middle_snapshot']=output.detach().clone();context['phase']='complete'
            context['GELU_count']+=1
        def observed_mean(messages,positions,counts):
            context=state['fcb_context'];which=context['mean_count'];assert which in (0,1,2)
            phases=('fine_mean','coarse_mean','middle_mean');assert context['phase']==phases[which]
            position_key=('pair_fine','pair_coarse','fine_parents')[which];count_key=('fine_counts','coarse_counts','middle_counts')[which]
            assert positions==context[position_key] and counts==context[count_key]
            assert messages is (context['q_ref'] if which<2 else context['mean_outputs'][0])
            record={'kind':('fine_marginal','coarse_marginal','original_fine_parent')[which],
                'input':summary(messages),'input_sha256':fingerprint(torch,messages),'parent_positions':list(positions),'counts':list(counts),
                'input_is_actual_q_object' :which<2,'input_is_actual_fine_delta_object':which==2,
                'original_mean_function_calls':1,'returned_original_object_unchanged':True,'mean_replayed_by_observer':False,
                'pointcount_weights_or_learned_weights':False}
            lite_watch(messages,context['record']);output=original_mean(messages,positions,counts)
            record.update(output=summary(output),output_sha256=fingerprint(torch,output));assert record['output']['finite']
            lite_watch(output,context['record']);context['mean_outputs'].append(output);context['mean_snapshots'].append(output.detach().clone())
            context['record']['mean_calls'].append(record);context['mean_count']+=1
            context['phase']=('coarse_mean','middle_mean','middle_map')[which]
            return output
        setattr(fcb_module,'equal_message_means',observed_mean);global_replacements.append((fcb_module,'equal_message_means',original_mean))
        hooks.extend([att.fine_coarse_bipartite.pair_map.register_forward_pre_hook(map_pre('pair')),
            att.fine_coarse_bipartite.pair_map.register_forward_hook(map_post('pair')),
            att.fine_coarse_bipartite.middle_map.register_forward_pre_hook(map_pre('middle')),
            att.fine_coarse_bipartite.middle_map.register_forward_hook(map_post('middle')),
            att.fine_coarse_bipartite.activation.register_forward_hook(activation_post)])
        def exchange_post(owner,values,output):
            context=state.pop('fcb_context');record=context['record']
            assert context['phase']=='complete' and len(output)==3 and context['map_count']==context['GELU_count']==2 and context['mean_count']==3
            assert context['pair_map_count']==context['middle_map_count']==1 and context['builder_calls']==int(output[0].shape[0])
            c=att.fine_coarse_bipartite.channels;sources=[context['mean_snapshots'][0],context['middle_snapshot'],context['mean_snapshots'][1]]
            for level in range(3):
                value=output[level];index=torch.tensor(context['ids'][level],device=value.device,dtype=torch.long)
                reference=value.new_zeros((value.shape[0]*value.shape[1],c)).index_copy(0,index,sources[level]).reshape(value.shape)
                assert fingerprint(torch,value)==fingerprint(torch,reference)
                if not value.requires_grad:
                    result['coverage_status']='INCONCLUSIVE_CORE_OUTPUT_NOT_DIFFERENTIABLE'
                    raise RuntimeError('INCONCLUSIVE_COVERAGE: original core output not differentiable before watches')
                watch(value,record,'native_output_level'+str(level)+'_gradients')
            actual_pairs=sum(p['pair_count'] for p in record['plans']);assert actual_pairs>0
            record.update(outputs=[summary(x) for x in output],output_sha256=fingerprint(torch,output),actual_true_pairs=actual_pairs,
                actual_true_fine_paths=sum(len(p['fine_ids']) for p in record['plans']),actual_pair_map_calls=context['pair_map_count'],
                actual_middle_map_calls=context['middle_map_count'],actual_map_calls=context['map_count'],actual_GELU_calls=context['GELU_count'],
                actual_private_mean_calls=context['mean_count'],actual_map_rows={v['kind']:v['actual_rows'] for v in record['map_calls']},
                actual_original_builder_calls=context['builder_calls'],actual_three_LN_calls=list(state['norm_counts']),
                actual_same_q_two_marginals=True,actual_middle_context_from_original_fine_parent_mean=True,
                final_deltas_from_actual_captures_exact=True,unsupported_padding_deltas_zero=True,
                numeric_marginal_or_Jacobian_gate='NOT_IMPLEMENTED_NOT_REQUIRED',
                actual_optional_boundary_counts=[{'batch':p['batch'],'pairs':p['pair_count'],'fine':len(p['fine_ids']),
                    'roots':len(p['coarse_ids']),'nonancestor_pairs':p['observed_nonancestor_pairs'],'empty_scene':not p['fine_ids'],
                    'singleton_fine':len(p['fine_ids'])==1,'singleton_root':len(p['coarse_ids'])==1,
                    'middle_fine_counts':p['middle_fine_counts'],'unsupported_or_padding':[context['widths'][l]-len(p[k]) for l,k in enumerate(('fine_ids','middle_ids','coarse_ids'))]} for p in record['plans']])
            state['fcb_delta_snapshots']=[x.detach().clone() for x in output];exchange_calls.append(record)
        hooks.extend([att.fine_coarse_bipartite.register_forward_pre_hook(exchange_pre),att.fine_coarse_bipartite.register_forward_hook(exchange_post)])

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
            exact=[fingerprint(torch,refined[level])==fingerprint(torch,raw[level].detach()+state['fcb_delta_snapshots'][level]) for level in range(3)]
            record['FCB_original_three_skips_and_exact_HCG_inputs']=exact;assert all(exact)
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
        for key in ('raw_refs','raw_record','fcb_delta_snapshots','norm_outputs','encoder_inst_before','encoder_gate','cluster_message'):state.pop(key,None)
        state['ffn_snapshots'].clear()
    def parameter_blocks():
        if not candidate:return {}
        c=att.fine_coarse_bipartite.channels
        return {name+'_'+side+'_columns':(module.weight,0,c,start,start+c)
            for name,module in [('pair',att.fine_coarse_bipartite.pair_map),('middle',att.fine_coarse_bipartite.middle_map)]
            for side,start in [('first',0),('second',c)]}
    def before_step(owner,args,kwargs):
        assert backward_records[-1]['count']==1
        if candidate and not exchange_calls[-1]['actual_true_pairs']:
            result['coverage_status']='INCONCLUSIVE_ORIGINAL_BATCH_HAS_NO_TRUE_FINE_COARSE_PAIR'
            raise RuntimeError('INCONCLUSIVE_COVERAGE: no true fine_coarse_bipartite path, no replacement sample/seed')
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
                assert any(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight')),'Whole fine_coarse_bipartite aggregate original-loss weight gradient is zero; local control inconclusive, not whole-mechanism rejection'
            else:
                assert all(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight'))
            record['gradient_gate_scope']='Candidate whole fine_coarse_bipartite aggregate only; individual maps/weights/rows/bias may be zero or unexercised, descriptive only'
            if candidate:
                weights=[g for n,g in gradients.items() if n.endswith('weight') and g is not None]
                record['whole_fine_coarse_bipartite_weight_gradient']={'finite':all(g['finite'] for g in weights),'abs_max':max(g['abs_max'] for g in weights),'observed_weight_tensors':len(weights),'scope':'Aggregate across entire fine_coarse_bipartite; individual map zeros/unused legal'}
        record['native_parameter_block_gradients']={}
        record['parameter_block_before_step_hash']={}
        for name,(weight,r0,r1,c0,c1) in parameter_blocks().items():
            info=summary(weight.grad[r0:r1,c0:c1]) if weight.grad is not None else None;record['native_parameter_block_gradients'][name]=info
            assert info is None or info['finite'];record.setdefault('block_gradient_gate_scope','Four map-input-column blocks descriptive; zeros legal. Whole two-map core aggregate weight is the nonzero gate.')
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
            record['whole_fine_coarse_bipartite_weight_updated']=record['weight_before_step_hash']['fine_coarse_bipartite']!=record['weight_after_step_hash']['fine_coarse_bipartite']
            record['whole_fine_coarse_bipartite_module_updated']=record['module_before_step_hash']['fine_coarse_bipartite']!=record['module_after_step_hash']['fine_coarse_bipartite']
        record['parameter_block_after_step_hash']={name:fingerprint(torch,weight.detach()[r0:r1,c0:c1]) for name,(weight,r0,r1,c0,c1) in parameter_blocks().items()}
        record['descriptive_parameter_block_changed']={name:record['parameter_block_before_step_hash'][name]!=record['parameter_block_after_step_hash'][name] for name in record['parameter_block_before_step_hash']}
        result['optimizer_steps']+=1
    hooks.extend([model.register_forward_pre_hook(native_input),model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step),optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False,losses=losses,steps=steps,batches=batches,native_backward_records=backward_records,
        ffn_calls=calls,raw_bank_observations=rawbanks,csort_raw_input_observations=csort,hcg_readbacks=readbacks,
        FCB_fine_coarse_bipartite_observations=exchange_calls,inst_to_mask_path_observations=path_records,native_dataloader_config=dict(cfg.dataloader.train),
        offdiagonal_dependency_probe='NOT_IMPLEMENTED_NOT_MEASURED',
        actual_champion_candidate_batch_pairing='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; compare both complete raw batch fingerprints and common named initialization',
        smoke_memory_scope='Two native TRAIN steps including observer hooks, detached snapshots, actual topology/source recording; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; no separate no-observer native TRAIN process pair',auxiliary_autograd_grad_or_backward_used=False,
        native_failure_is_not_whole_mechanism_rejection=True,
        coverage_gate_scope='Each original fixed TRAIN forward needs at least one true scene-local fine-coarse pair. Singleton and degree boundaries are optional NOT_EXERCISED when absent; no resampling. Four map-column blocks descriptive only; no per-map/pair/row/column positivity gate.',
        dynamic_parameter_inventory={'original_FFN_parameters_by_level':{str(i):sum(p.numel() for p in att.cluster_ffn[i].parameters()) for i in range(3)},
            'new_declared_parameters':sum(p.numel() for p in att.fine_coarse_bipartite.parameters()) if candidate else 0,
            'actual_full_model_parameters':sum(p.numel() for p in model.parameters()),'actual_named_parameter_tensors':sum(1 for _ in model.named_parameters()),
            'state_dict_keys':list(model.state_dict()),'geometry_registered_buffer_names':[n for n,_ in model.named_buffers() if 'middle_positions' in n or 'middle_parent_ids' in n or 'middle_valid' in n]})
    logger=logging.getLogger('fcb-native-smoke');logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
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
        assert record['actual_true_pairs']>0 and record['actual_pair_map_calls']==record['actual_middle_map_calls']==1 and record['actual_GELU_calls']==2 and record['actual_private_mean_calls']==3
        for level in range(3):
            for key in ('native_normalized_level'+str(level)+'_gradients','native_output_level'+str(level)+'_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
        flags=record.pop('_internal_gradient_flags');record['actual_internal_backward_callbacks']=len(flags)
        record['all_observed_internal_gradients_finite']=bool(torch.stack(flags).all()) if flags else None
        if flags:assert record['all_observed_internal_gradients_finite']
        record['internal_gradient_scope']='Only finite flags aggregated, no per-call/branch/row positivity or callback-completeness gate. Whole two-map core original-loss gradient/update controls trainability.'
    for record in readbacks:assert record.get('native_point_message_gradients') and all(g['finite'] for g in record['native_point_message_gradients'])
    for record in path_records:
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):assert record.get(key) and all(g['finite'] for g in record[key])
    final={n:fingerprint(torch,{k:p.detach() for k,p in ps.items()}) for n,ps in tracked.items()}
    assert all(final[n]!=initial[n] for n in tracked);verify()
    result.update(execution_completed=True,native_data_loaded=True,native_train_function_executed=True,backward_finite=True,
        intended_path_observed=(len(exchange_calls)==2 and all(v['actual_true_pairs']>0 and v['actual_pair_map_calls']==v['actual_middle_map_calls']==1 and v['actual_GELU_calls']==2 and v['actual_private_mean_calls']==3 for v in exchange_calls)) if candidate else len(calls)==6,
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
        'native_model_and_yaml_unchanged':False,'source_scope':'Exact native FCB or original M95, original backbone pretrain and native train loop'}
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
