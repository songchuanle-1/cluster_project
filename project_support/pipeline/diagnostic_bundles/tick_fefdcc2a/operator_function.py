def operator_equivalence(torch, result):
    import numpy as np
    fixture_path = Path('/data/songcl/Project/Cluster_project/pipeline/contact_658721c0/native_contact_fixture.pt')
    assert sha(fixture_path) == '93a4c4ef26668ffdf2c37141b1667906456142ee853b8459e110d91879d59a7b'
    fixture = torch.load(fixture_path, map_location='cpu', weights_only=False)
    original_path = Path('/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a/candidate_model/contact_exchange.py')
    assert sha(original_path) == MANIFEST['original_operator_sha256']
    spec = importlib.util.spec_from_file_location('pce_original_operator_control', original_path)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    revised = importlib.import_module('framework.model.Quard_model.' + NAME + '_pce.contact_exchange')
    features, positions = fixture['features'].cuda(), fixture['positions'].numpy()
    edges = [edge for edge in fixture['physical_edges'] for _ in range(4)]
    result['operator_records'] = []
    def error(a, b):
        return float((a - b).abs().max().detach().cpu())
    for b, identifiers in enumerate(fixture['fine_ids']):
        n = len(identifiers)
        x = features[b, :n].detach().clone().requires_grad_()
        xyz, leaves = positions[b, :n], identifiers.numpy()
        fallback = fixture['refined_banks'][0][b, identifiers.long()].cuda()
        old, degrees = original.exchange(x, xyz, leaves, edges[b], fallback, heads=8)
        new, new_degrees = revised.exchange(x, xyz, leaves, edges[b], fallback, heads=8)
        assert degrees == new_degrees
        probe = torch.linspace(-1, 1, old.numel(), device=x.device).reshape_as(old)
        old_gradient = torch.autograd.grad((old * probe).sum(), x, retain_graph=False)[0]
        new_gradient = torch.autograd.grad((new * probe).sum(), x, retain_graph=False)[0]
        permutation = np.arange(n - 1, -1, -1)
        inverse = np.argsort(permutation)
        with torch.no_grad():
            renamed, _ = revised.exchange(x[permutation.copy()], xyz[permutation], leaves[permutation],
                inverse[edges[b]], fallback[permutation.copy()], heads=8)
            deleted, _ = revised.exchange(x, xyz, leaves, np.empty((0, 2), dtype=np.int64), fallback, heads=8)
            old_rotated, _ = original.exchange(x, xyz, leaves, edges[b], fallback, heads=8, rotate_values=True)
            new_rotated, _ = revised.exchange(x, xyz, leaves, edges[b], fallback, heads=8, rotate_values=True)
        record = {'expression': b, 'supports': n, 'edges': int(len(edges[b])),
            'receivers': sum(value > 0 for value in degrees),
            'output_max_abs': error(old, new), 'input_gradient_max_abs': error(old_gradient, new_gradient),
            'row_permutation_max_abs': error(new, renamed[inverse.copy()]),
            'deleted_contact_max_abs': error(deleted, fallback),
            'rotated_value_max_abs': error(old_rotated, new_rotated),
            'gradient_finite': bool(torch.isfinite(new_gradient).all()),
            'gradient_nonzero': bool((new_gradient != 0).any())}
        result['operator_records'].append(record)
    keys = ('output_max_abs', 'input_gradient_max_abs', 'row_permutation_max_abs',
        'deleted_contact_max_abs', 'rotated_value_max_abs')
    maximum = max(row[key] for row in result['operator_records'] for key in keys)
    result.update(execution_completed=True, tolerance=1e-6, maximum_operator_error=maximum,
        operator_equivalence_passed=maximum <= 1e-6,
        existing_full_source_controls_waived=False, fixture_scope='Same original two scenes/eight expressions; not new independent population samples.',
        after=observe())
