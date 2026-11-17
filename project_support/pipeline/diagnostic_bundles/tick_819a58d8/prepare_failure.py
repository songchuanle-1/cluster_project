"""Bind the byte-identical prior test launcher to the current lease helpers."""
import shutil
from ops import guard, advance, save, evidence, tick, ROOT, OUT

guard(500)
source = ROOT / 'pipeline/diagnostic_bundles/tick_d8b27109/run_channel_failure.py'
target = OUT / 'run_channel_failure.py'
assert not target.exists()
shutil.copyfile(source, target)
assert tick.digest(source) == tick.digest(target)
save('launcher_binding.json', {'source': evidence(source), 'current': evidence(target),
                              'scientific_test_changed': False,
                              'changes': 'Only current ops.py token/deadline/stage binding; original frozen source test unchanged'})
advance([OUT / 'resource_recheck.json', OUT / 'launcher_binding.json'],
        stage='validation', blocker=None, blocker_kind=None, retry_after=None,
        unblock_condition=None,
        gate_result='Actual server4GPU0 resource release observed; preparing the single frozen native failure measurement,not a scientific gate PASS.',
        next_action='Run once the frozen expression0/lastvalid native failure capture with current lease and all3 runtime flocks;keep strict1e-6 and original failure.')
print({'prepared': True, 'launcher_sha256': tick.digest(target)})
