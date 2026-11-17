"""Author a fresh, execution-disabled PSC packet from immutable HVD producers."""
from pathlib import Path
import ast
import copy
import datetime
import hashlib
import json
import os
import subprocess

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'native'
PRODUCER = ROOT / 'pipeline/diagnostic_bundles/tick_c7451cf1/hvd_native_prepare/native'
MOTHER = ROOT / 'pipeline/diagnostic_bundles/tick_0f3c54ec/reserve_candidate_prepare'
SOURCE = '0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d'
PARENT = 'd20eb221eff6584b67d4e9b5673559d0e1cb735b'
CANDIDATE = 'hierarchy-native-position-feature-cross-scatter-composition'
RUNTIME_ROOT = '/data/songcl/Project/Cluster_project/Cluster_hvd_20261106'
TEN_NULL = ('current_token', 'stage', 'tick_generated_at', 'deadline_at',
            'physical_gpu', 'gpu_uuid', 'allowed_gpus', 'context_sha256',
            'pending_sha256', 'runtime_code_commit')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else value.encode('utf-8')
    with path.open('xb') as stream:
        stream.write(data)


def save(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def ref(path):
    return {'path': Path(path).relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT / 'Cluster'), *args])


def protected():
    index = ROOT / 'Cluster/.git/index'
    return {
        'head': git('rev-parse', 'HEAD').decode().strip(),
        'index_sha256': sha(index),
        'status_sha256': hashlib.sha256(git('status', '--porcelain=v1', '-z')).hexdigest(),
    }


def function(text, name):
    return next(ast.get_source_segment(text, node) for node in ast.parse(text).body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def replace_once(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new, 1)


def main():
    assert not NATIVE.exists(), 'Never overwrite an existing packet'
    before = protected()
    assert before['head'] == PARENT
    assert git('rev-list', '--parents', '-n', '1', SOURCE).decode().split() == [SOURCE, PARENT]
    assert sha(PRODUCER / 'worker.py') == 'f91bddf7be81cc2e823f5c2e38a16d3a666e45022d885c6cb7a4ff654806646c'
    old = (PRODUCER / 'worker.py').read_text(encoding='utf-8')
    source = old.replace('variance_decomposition', 'position_feature_scatter').replace('HVD', 'PSC').replace('hvd', 'psc')
    source = source.replace("qualified+'.position_feature_scatter'", "qualified+'.position_scatter'")
    source = source.replace('graph.moment_components', 'graph.cross_scatter_components')
    source = source.replace('graph.pack_moment_rows', 'graph.pack_cross_rows')
    start = source.index('        def exchange_pre(owner,values):')
    end = source.index('        def observed_plan(', start)
    source = source[:start] + (HERE / 'psc_exchange_pre.py.txt').read_text(encoding='utf-8') + source[end:]
    start = source.index('        def observed_group_mean(')
    end = source.index('        def factor_pre(', start)
    source = source[:start] + (HERE / 'psc_moment_observers.py.txt').read_text(encoding='utf-8') + source[end:]
    source = replace_once(source,
        "                stats_observations=[],group_mean_observations=[],pack_observations=[],factor_observations=[],restoration_observations=[])",
        "                actual_centered_cross_calls=0,actual_within_between_add_calls=0,\n"
        "                stats_observations=[],group_mean_observations=[],centered_cross_observations=[],pack_observations=[],factor_observations=[],restoration_observations=[])")
    source = replace_once(source,
        "'stats_active':False,'pack_active':False,'factor_active':False,'restoration_level':0}",
        "'batch':batch,'stats_active':False,'pack_active':False,'factor_active':False,'restoration_level':0,\n"
        "                 'mean_refs':[],'pack_select_refs':[],'pack_cat_refs':[],'selected_normalized_refs':{}}")
    source = replace_once(source,
        "        original_group_mean=graph._group_mean;original_pack=graph.pack_cross_rows",
        "        original_group_mean=graph._group_mean;original_pack=graph.pack_cross_rows\n"
        "        original_cross=graph._centered_cross;original_getitem=torch.Tensor.__getitem__\n"
        "        original_invert=torch.Tensor.__invert__;original_to=torch.Tensor.to\n"
        "        original_add=torch.Tensor.__add__;original_select=torch.Tensor.index_select;original_zeros_like=torch.zeros_like")
    start = source.index("        for name,replacement,original in [('build_support_plan'")
    end = source.index('        hooks.extend([core.factor.register_forward_pre_hook', start)
    source = source[:start] + (HERE / 'psc_installations.py.txt').read_text(encoding='utf-8') + source[end:]
    source = source.replace("item['actual_group_mean_calls']==8", "item['actual_group_mean_calls']==11 and item['actual_centered_cross_calls']==3 and item['actual_within_between_add_calls']==1")
    source = source.replace('actual_group_mean_calls=8*len(active)', 'actual_group_mean_calls=11*len(active),actual_centered_cross_calls=3*len(active),actual_within_between_add_calls=len(active)')
    source = source.replace("record['actual_group_mean_calls']==8*record['actual_supported_scene_count']", "record['actual_group_mean_calls']==11*record['actual_supported_scene_count'] and record['actual_centered_cross_calls']==3*record['actual_supported_scene_count'] and record['actual_within_between_add_calls']==record['actual_supported_scene_count']")
    source = source.replace("v['actual_group_mean_calls']==8*v['actual_supported_scene_count']", "v['actual_group_mean_calls']==11*v['actual_supported_scene_count'] and v['actual_centered_cross_calls']==3*v['actual_supported_scene_count'] and v['actual_within_between_add_calls']==v['actual_supported_scene_count']")
    source = replace_once(source,
        "    def last_encoder_pre(owner,values):\n        assert state.get('encoder_inst_before') is None",
        "    def last_encoder_pre(owner,values):\n"
        "        if candidate:\n"
        "            assert values[5] is state['psc_padded_positions_ref']\n"
        "            state['psc_encoder_positions_ref']=values[5];state['psc_encoder_features_ref']=values[2];state['psc_encoder_mask_ref']=values[3]\n"
        "        assert state.get('encoder_inst_before') is None")
    insert = """
    if candidate:
        def decoder_native_positions(owner,values,kwargs):
            positions=kwargs.get('sp_pos',values[5] if len(values)>5 else None)
            assert positions is not None and positions.shape[-1]==3
            state['psc_decoder_native_positions_ref']=positions
        original_get_batches=model.dec.get_batches
        def observed_get_batches(features,offsets):
            output=original_get_batches(features,offsets)
            if features is state.get('psc_decoder_native_positions_ref'):
                assert 'psc_padded_positions_ref' not in state
                state['psc_padded_positions_ref']=output[0]
                result.setdefault('PSC_native_coordinate_padding_observations',[]).append({
                    'forward':state['forward_index'],'native_unpadded':summary(features),
                    'native_unpadded_sha256':fingerprint(torch,features),'original_padded':summary(output[0]),
                    'original_padded_sha256':fingerprint(torch,output[0]),'original_get_batches_calls':1,
                    'returned_original_objects_unchanged':True,'coordinate_normalization_added':False})
            return output
        replace(model.dec,'get_batches',observed_get_batches)
        hooks.append(model.dec.register_forward_pre_hook(decoder_native_positions,with_kwargs=True))
"""
    source = replace_once(source, '    def native_input(owner,values):', insert + '    def native_input(owner,values):')
    source = replace_once(source,
        "'encoder_inst_before','encoder_gate','cluster_message'):state.pop(key,None)",
        "'encoder_inst_before','encoder_gate','cluster_message','psc_decoder_native_positions_ref','psc_padded_positions_ref','psc_encoder_positions_ref','psc_encoder_features_ref','psc_encoder_mask_ref'):state.pop(key,None)")
    # The resources function is a complete immutable producer function, not a rewritten equivalent.
    assert function(source, 'resources') == function(old, 'resources')
    assert 'variance_decomposition' not in source and 'moment_components' not in source
    assert "graph.pack_cross_rows" in source and '10*core.channels' in source
    compile(source, '<PSC-worker>', 'exec')
    write(NATIVE / 'worker.py', source)

    runtime = (PRODUCER / 'native_runtime.py').read_text(encoding='utf-8')
    runtime = runtime.replace('HVD', 'PSC').replace('hvd', 'psc')
    runtime = runtime.replace('M230-PSC', 'M231-PSC')
    runtime = runtime.replace('hierarchy-native-variance-decomposition-composition', CANDIDATE)
    runtime = runtime.replace('e38d92db60f43dde00ae0e537493dc3f3dfc82db', SOURCE)
    runtime = runtime.replace('6bc36adfe42764aac2209e6600fb3a783e2fa374', PARENT)
    runtime = runtime.replace('ae8baa7a0d6dd0524e2e8fb6bba05ba97dd2410f8fa8c686b1c020c2a77b8dfb', sha(MOTHER / 'preparation.json'))
    runtime = runtime.replace('/data/songcl/Project/Cluster_project/Cluster_nec_20261104', RUNTIME_ROOT)
    runtime = replace_once(runtime,
        "GPU_UUIDS = {0: 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',\n            1: 'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}",
        "GPU_UUIDS = {0: 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'}")
    assert 'DRAFT_EXECUTION_DISABLED = True' in runtime
    compile(runtime, '<PSC-runtime>', 'exec')
    write(NATIVE / 'native_runtime.py', runtime)

    version = json.loads((ROOT / 'pipeline/diagnostic_bundles/tick_12e364dc/psc_compatible_source/compatible_source_version.json').read_text())
    hashes = version['source_files_exact9']
    for path, expected in hashes.items():
        data = git('show', SOURCE + ':' + path)
        assert hashlib.sha256(data).hexdigest() == expected
        assert data == (MOTHER / 'source' / path).read_bytes()
        write(NATIVE / ('candidate.yaml' if path.endswith('.yaml') else 'candidate_model/' + Path(path).name), data)
    candidate_hashes = {Path(path).name: digest for path, digest in hashes.items() if path.endswith('.py')}
    binding = {
        'schema_version': 1, 'candidate_id': CANDIDATE, 'experiment_id': 'M231-PSC',
        'code_commit': SOURCE, 'source_commit': SOURCE, 'parent_commit': PARENT,
        'runtime_expected_commit': PARENT, 'candidate_source_hashes': candidate_hashes,
        'candidate_config_sha256': sha(NATIVE / 'candidate.yaml'), 'source_files': hashes,
        'original_source_preparation_sha256': sha(MOTHER / 'preparation.json'),
        'source_preparation': ref(MOTHER / 'preparation.json'),
        'native_protocol': ref(MOTHER / 'native_protocol.md'),
        'isolated_source_version': ref(ROOT / 'pipeline/diagnostic_bundles/tick_12e364dc/psc_compatible_source/compatible_source_version.json'),
        'independent_source_review': ref(ROOT / 'pipeline/diagnostic_bundles/tick_12e364dc/psc_compatible_source_independent_review.json'),
        'author_provenance_only': {'tick_token': '2e51495f07244023946fc53eec6e6d98',
                                   'actual_child_thread': os.environ.get('CODEX_THREAD_ID'),
                                   'execution_binding': False},
        'draft_execution_disabled': True, 'native_packet_independent_review': None,
        'scope': 'Same nine PSC source bytes on current d20; preparation metadata only. No execution binding.',
    }
    save(NATIVE / 'source_version_binding.json', binding)
    template = json.loads((PRODUCER / 'manifest_template.json').read_text())
    template.update(root=RUNTIME_ROOT, candidate_id=CANDIDATE,
        candidate_name=template['name'] + '_psc', code_commit=SOURCE,
        experiment_id='M231-PSC',
        config='configs/Quard/ctf_hcg_csort_psc/' + template['name'] + '_psc.yaml',
        candidate_source_hashes=candidate_hashes,
        candidate_config_sha256=sha(NATIVE / 'candidate.yaml'),
        source_preparation_sha256=sha(MOTHER / 'preparation.json'),
        base_reference_commit=PARENT, source_version_commit=SOURCE,
        source_version_binding_sha256=sha(NATIVE / 'source_version_binding.json'),
        source_parent_commit=PARENT, future_version_parent=PARENT,
        runtime_expected_commit=PARENT, scientific_admission=False,
        protocol='Original PSC native_protocol98b12c01: original paired naturalTRAIN2/common-init, exact native padded coordinate input reference and original valid-point masking/cast; actual3xC cross-scatter/equal-supported-child within-between/11means/3centered-cross/total1-add/10Cpack/sharedfactor/split/restoration. Whole-core finite original-loss gradient and aggregate weight/module update; no component positivity/FP32/minimum-effect gate. Full original resource function byte-identical. DRAFTTrue/10NULL; no active manifest/lease/request/release/stage.')
    template['assets']['config_path'] = RUNTIME_ROOT + '/configs/Quard/ctf_hcg_csort/' + template['name'] + '.yaml'
    for key in TEN_NULL:
        template[key] = None
    template['diagnostic_files'] = {
        p.relative_to(NATIVE).as_posix(): sha(p) for p in sorted(NATIVE.rglob('*')) if p.is_file()
    }
    save(NATIVE / 'manifest_template.json', template)
    write(NATIVE / 'README.md',
        '# PSC disabled native packet\n\nDRAFT_EXECUTION_DISABLED=True; all ten execution fields NULL.\n'
        'No native_manifest, lease, request, binding, release or remote stage is created.\n'
        'Only the new CPU software checks may run while HVD occupies project GPU0.\n'
        'Torch/full-forward/autograd/native/resources are NOT_RUN. Original resource function is unchanged.\n'
        'Actual future execution requires fresh independently reviewed owner/source/runtime/root/UUID/producer binding.\n')
    after = protected()
    assert before == after
    save(HERE / 'authoring_audit.json', {
        'recorded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'actual_author_thread_id': os.environ.get('CODEX_THREAD_ID'),
        'protected_before': before, 'protected_after': after,
        'old_source_frozen': ref(MOTHER / 'FROZEN.json'),
        'resources_function_exact': True, 'native': 'NOT_RUN', 'resources': 'NOT_RUN',
        'active_materials_created': False, 'source_files_exact9': hashes,
        'worker': ref(NATIVE / 'worker.py'), 'runtime': ref(NATIVE / 'native_runtime.py'),
    })
    print(json.dumps({'worker': sha(NATIVE / 'worker.py'),
                      'runtime': sha(NATIVE / 'native_runtime.py'),
                      'manifest_template': sha(NATIVE / 'manifest_template.json'),
                      'source_version_binding': sha(NATIVE / 'source_version_binding.json')}))


if __name__ == '__main__':
    main()
