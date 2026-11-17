def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original native train loop; HAP observers never change model algebra."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('hap-native-smoke'))
    loader = build_dataloader(dataset, dist=cfg.dist, **cfg.dataloader.train)
    assert loader.batch_size == 2 and loader.num_workers == 4 and loader.persistent_workers
    assert loader.drop_last

    class TwoNativeBatches:
        def __init__(self, native):
            self.native, self.sampler = native, native.sampler
        def __len__(self):
            return 2
        def __iter__(self):
            yield from itertools.islice(iter(self.native), 2)

    operator = getattr(model.dec.cluster_att, 'affine_prolongation', None)
    if result['target'] == 'candidate':
        assert operator is not None
        assert sum(p.numel() for p in operator.parameters()) == 0
    tracked = {level: dict(model.dec.cluster_att.cluster_ffn[level].named_parameters())
        for level in range(3)}
    initial_hash = {level: fingerprint(torch, {n:p.detach() for n,p in params.items()})
        for level, params in tracked.items()}
    calls, edges, inverses, losses, steps, batches = [], [], [], [], [], []
    hooks = []
    state = {'inside_operator': False}
    original_pinv = torch.linalg.pinv

    def summary(value):
        finite = bool(torch.isfinite(value).all())
        return {'shape': list(value.shape), 'dtype': str(value.dtype),
            'finite': finite, 'nonfinite_count': int((~torch.isfinite(value)).sum()),
            'abs_max': float(value.detach().float().abs().max().cpu())
                if value.numel() and finite else (0.0 if not value.numel() else None)}

    def logvar(value):
        tensor = torch.as_tensor(value).detach()
        info = summary(tensor)
        info['value'] = float(tensor.cpu()) if info['finite'] and tensor.numel() == 1 else None
        return info

    def observed_pinv(*args, **kwargs):
        # Forward exactly once with all original arguments. Return the same object.
        inverse = original_pinv(*args, **kwargs)
        if state['inside_operator']:
            gram = args[0]
            entry = {'actual_input': summary(gram), 'actual_return': summary(inverse),
                'positional_arguments_after_input': len(args) - 1,
                'provided_kwargs': {k: v if isinstance(v, (str,int,float,bool,type(None)))
                    else repr(v) for k,v in kwargs.items()},
                'provided_tolerances': 'default; no observer-supplied atol/rtol/rcond',
                'pinv_retained_rank': 'UNOBSERVED; diagnostic matrix_rank is a separate API',
                'original_calls_per_observation': 1}
            inverses.append(entry)
            assert gram.shape[-2:] == (3,3)
            assert entry['actual_input']['finite'] and entry['actual_return']['finite']
            with torch.no_grad():
                eigen = torch.linalg.eigvalsh(gram)
                rank = torch.linalg.matrix_rank(gram, hermitian=True)
                projection = gram @ inverse
                entry['diagnostic_eigenvalues'] = eigen.detach().cpu().tolist()
                entry['diagnostic_matrix_rank_default_api'] = rank.detach().cpu().tolist()
                entry['diagnostic_matrix_rank_counts'] = {
                    str(k): int(rank.eq(k).sum()) for k in range(4)}
                entry['symmetry_abs_max'] = float((gram - gram.transpose(-2,-1)).abs().max())
                entry['G_Gplus_trace'] = projection.diagonal(dim1=-2,dim2=-1).sum(-1).cpu().tolist()
                entry['G_Gplus_idempotence_abs_max'] = float((projection @ projection - projection).abs().max())
                entry['spectrum_scope'] = 'Additional diagnostic computation on actual G; not backend pinv internals'
        return inverse

    def enter_operator(owner, values):
        state['inside_operator'] = True

    def observe_operator(owner, values, outputs):
        state['inside_operator'] = False
        record = {'inputs': [summary(values[i]) for i in range(3)],
            'outputs': [summary(value) for value in outputs]}
        calls.append(record)
        assert len(outputs) == 2
        assert all(item['finite'] for item in record['inputs'] + record['outputs'])

    def centered_gradient(gradient, level):
        bank = model.dec.cluster_bank
        maximum, eligible_groups = 0.0, 0
        for b in range(gradient.shape[0]):
            ids = bank.cluster_ids_list[level + 1][b].long()
            occupied = bank.affine_occupied[level][b]
            xyz = bank.affine_positions[level][b].detach().float()
            rows = ids.numel()
            parent_count = bank.affine_positions[level + 1][b].shape[0]
            count = xyz.new_zeros(parent_count)
            count.index_add_(0, ids, occupied.to(xyz.dtype))
            center = xyz.new_zeros(parent_count, 3)
            center.index_add_(0, ids, xyz * occupied.unsqueeze(-1))
            center = center / count.clamp_min(1).unsqueeze(-1)
            delta = (xyz - center[ids]) * occupied.unsqueeze(-1)
            energy = xyz.new_zeros(parent_count)
            energy.index_add_(0, ids, delta.square().sum(-1))
            eligible = count.gt(1) & energy.gt(0)
            eligible_groups += int(eligible.sum())
            g = gradient[b, :rows]
            sums = g.new_zeros(parent_count, g.shape[-1])
            sums.index_add_(0, ids, g * occupied.unsqueeze(-1))
            mean = sums / count.clamp_min(1).unsqueeze(-1)
            selected = occupied & eligible[ids]
            if bool(selected.any()):
                maximum = max(maximum, float((g - mean[ids])[selected].abs().max()))
        return {'eligible_nonconstant_geometry_groups': eligible_groups,
            'group_centered_gradient_abs_max': maximum,
            'scope': 'Only occupied groups with >1 child and nonzero geometric energy; zero-rank groups may be zero'}

    def operator_backward(owner, grad_input, grad_output):
        record = {'inputs': [summary(grad_input[i]) if grad_input[i] is not None else None
                for i in range(3)],
            'outputs': [summary(g) for g in grad_output if g is not None]}
        edges.append(record)
        assert len(record['outputs']) == 2 and all(g['finite'] for g in record['outputs'])
        assert all(g is not None and g['finite'] for g in record['inputs'])
        for level, name in [(0,'fine'), (1,'middle')]:
            info = centered_gradient(grad_input[level], level)
            record[name + '_nonconstant_readout'] = info
            assert info['eligible_nonconstant_geometry_groups'] > 0
            assert info['group_centered_gradient_abs_max'] > 0
        assert record['inputs'][2]['abs_max'] > 0, 'No native-loss gradient through new parent path'
        assert all(g['abs_max'] > 0 for g in record['outputs'])

    def native_input(owner, values):
        batch = values[0]
        batches.append({'sha256': fingerprint(torch, batch),
            'scan_ids': [str(x) for x in batch.get('scan_ids', [])],
            'ann_ids': [int(x) for x in batch.get('ann_ids', [])],
            'scenes_len': [int(x) for x in batch.get('scenes_len', [])]})

    def native_output(owner, values, output):
        loss, variables = output
        result.setdefault('loss_tensor_observations', []).append(logvar(loss))
        result.setdefault('loss_component_observations', []).append({k:logvar(v) for k,v in variables.items()})
        assert loss.numel() == 1 and bool(torch.isfinite(loss).all())
        losses.append(float(loss.detach().cpu()))
        result['native_loss_forwards'] += 1

    def before_step(owner, args, kwargs):
        observed = {n:p.grad for n,p in model.named_parameters() if p.grad is not None}
        bad = [n for n,g in observed.items() if not bool(torch.isfinite(g).all())]
        record = {'gradient_tensor_count': len(observed), 'nonfinite_parameter_names': bad,
            'all_observed_gradients_finite': bool(observed) and not bad,
            'ffn_by_level': {}, 'optimizer_step_completed': False}
        steps.append(record)
        assert observed and not bad
        for level, params in tracked.items():
            weights = {n:summary(p.grad) if p.grad is not None else None
                for n,p in params.items() if n.endswith('weight')}
            record['ffn_by_level'][str(level)] = weights
            assert weights and all(g is not None and g['finite'] for g in weights.values())
            assert any(g['abs_max'] > 0 for g in weights.values())
            # Centered fine/middle output-bias gradients may legitimately be zero.
        result['native_criterion_backwards'] += 1

    def after_step(owner, args, kwargs):
        steps[-1]['optimizer_step_completed'] = True
        result['optimizer_steps'] += 1

    if operator is not None:
        hooks.extend([operator.register_forward_pre_hook(enter_operator),
            operator.register_forward_hook(observe_operator),
            operator.register_full_backward_hook(operator_backward)])
    hooks.extend([model.register_forward_pre_hook(native_input),
        model.register_forward_hook(native_output), optimizer.register_step_pre_hook(before_step),
        optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False, losses=losses, steps=steps, batches=batches,
        affine_operator_calls=calls, affine_operator_backward_edges=edges,
        actual_pinv_observations=inverses, native_dataloader_config=dict(cfg.dataloader.train),
        pinv_observer_scope='Smoke only; original function called once with unchanged args/kwargs and original Tensor returned; never used in resource mode')
    logger = logging.getLogger('hap-native-smoke')
    logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
    writer = train.SummaryWriter(cfg.work_dir)
    torch.cuda.reset_peak_memory_stats()
    try:
        if operator is not None:
            torch.linalg.pinv = observed_pinv
        train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)
        torch.cuda.synchronize()
    finally:
        torch.linalg.pinv = original_pinv
        state['inside_operator'] = False
        for hook in hooks:
            hook.remove()
        writer.flush()
        writer.close()
    assert torch.linalg.pinv is original_pinv
    assert len(losses) == len(steps) == len(batches) == result['optimizer_steps'] == 2
    final_hash = {level:fingerprint(torch, {n:p.detach() for n,p in params.items()})
        for level,params in tracked.items()}
    assert all(final_hash[level] != initial_hash[level] for level in range(3))
    if operator is not None:
        assert len(calls) == len(edges) == 2 and inverses
    verify()
    result.update(execution_completed=True, native_data_loaded=True,
        native_train_function_executed=True, backward_finite=True,
        intended_path_observed=operator is not None and len(edges) == 2,
        new_operator_parameters=0 if operator is not None else None,
        native_ffn_initial_hash_by_level=initial_hash, native_ffn_after_hash_by_level=final_hash,
        native_ffn_each_level_updated=True, pinv_original_restored=True,
        training_checkpoint_saved=False, native_smoke_training=True, new_training=0,
        optimizer_type=type(optimizer).__name__, scheduler_type=type(scheduler).__name__,
        smoke_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        smoke_peak_reserved_bytes=torch.cuda.max_memory_reserved(), after=observe())
