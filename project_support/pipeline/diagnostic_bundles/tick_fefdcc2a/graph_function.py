def check_graph(sample, result):
    import numpy as np
    import time
    original_path = Path('/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a/candidate_model/contact_exchange.py')
    assert sha(original_path) == ORIGINAL_OPERATOR_SHA
    spec = importlib.util.spec_from_file_location('original_contact_graph_control', original_path)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    revised = importlib.import_module('framework.model.Quard_model.' + NAME + '_pce.contact_exchange')
    values = [sample[key].detach().cpu().numpy() for key in
        ('voxel_coords', 'p2v_map', 'superpoints', 'batch_offsets')]
    cases = [('native_resource_geometry', values),
        ('cooccupied_multimembership_and_two_scenes', [
            np.array([[0,0,0,0],[0,1,0,0],[0,2,0,0],[1,0,0,0],[1,0,1,0]]),
            np.array([0,0,0,1,1,2,3,3,4]), np.array([0,1,2,1,2,3,4,5,6]), np.array([0,4,7])])]
    records = []
    for label, args in cases:
        start = time.perf_counter()
        expected = original.contacts(*args)
        original_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        actual = revised.contacts(*args)
        revised_ms = (time.perf_counter() - start) * 1000
        equal = len(expected) == len(actual) and all(np.array_equal(a,b) for a,b in zip(expected,actual))
        records.append({'case': label, 'exact_edge_arrays_equal': equal,
            'edges': [len(value) for value in actual], 'original_ms': original_ms, 'revised_ms': revised_ms})
    result['graph_controls'] = records
    result['graph_controls_passed'] = all(value['exact_edge_arrays_equal'] for value in records)
    assert result['graph_controls_passed'], 'Geometry graph changed; preserve failure, no resource/admission PASS'
