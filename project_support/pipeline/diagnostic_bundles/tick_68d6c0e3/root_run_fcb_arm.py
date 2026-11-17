"""One root-requested arm through the original immutable FCB adapter."""
from pathlib import Path
import argparse, importlib.util, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    ap.add_argument('--mode', choices=('smoke', 'resources'), required=True)
    ap.add_argument('--target', choices=('champion', 'candidate'), required=True)
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_NATIVE_EXECUTION')
        return
    guard()
    bpath = HERE / 'post_aoc_terminal_baseline.json'
    assert bpath.is_file()
    b = u.read(bpath)
    u.primary_protection(b)
    u.lifecycle_protection(b)
    path = ROOT / 'pipeline/diagnostic_bundles/tick_89d05b33/fcb_operational_prepare/adapter.py'
    spec = importlib.util.spec_from_file_location('root_original_fcb_arm_adapter', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        u.primary_protection(b)
        u.lifecycle_protection(b)
        label = a.mode + '_' + a.target
        assert not (HERE / ('root_' + label + '_intent.json')).exists()
        u.save(HERE / ('root_' + label + '_intent.json'), {
            'owner': EXPECTED, 'mode': a.mode, 'target': a.target,
            'adapter': u.ref(path), 'post_terminal_baseline': u.ref(bpath),
            'scope': 'One original FCB adapter.run arm. Original identity, no-replay, fresh resource/three-lock and native protocol safeguards retained; no source, lifecycle or queue change.'})
        adapter = module.Adapter(execution_dir=HERE / 'fcb_execution')
        result = adapter.run(a.mode, a.target)
        assert result['certainty'] == 'terminal' and result['returncode'] == 0
        raw = result['result']
        assert raw['execution_completed'] is True
        guard()
        u.primary_protection(b)
        u.lifecycle_protection(b)
        summary = {'owner': EXPECTED, 'mode': a.mode, 'target': a.target,
                   'certainty': result['certainty'], 'returncode': result['returncode'],
                   'execution': u.ref(HERE / 'fcb_execution' / (label + '_execution.json')),
                   'execution_completed': raw['execution_completed'], 'losses': raw.get('losses'),
                   'optimizer_steps': raw.get('optimizer_steps'), 'profile': raw.get('profile'),
                   'latency_median_ms': raw.get('latency_median_ms'),
                   'latency_p90_ms': raw.get('latency_p90_ms'), 'peak_allocated_bytes': raw.get('peak_allocated_bytes')}
        u.save(HERE / ('root_' + label + '_result.json'), summary)
        print(json.dumps({k: v for k, v in summary.items() if k != 'profile'}, ensure_ascii=False))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
