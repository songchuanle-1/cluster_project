"""Preserve the actual failed finish without changing the closure checker."""
import shutil
from pathlib import Path
from ops import guard, save, advance, evidence, tick, ROOT, OUT, TOKEN

guard()
receipt_path = ROOT / 'pipeline/tick_receipts' / (TOKEN + '.json')
receipt = tick.load(receipt_path)
assert receipt['status'] == 'INCOMPLETE' and receipt['lease_release'] == 'retained'
saved = OUT / 'finish_failed_receipt.json'
if saved.exists():
    assert tick.digest(saved) == tick.digest(receipt_path)
else:
    shutil.copyfile(receipt_path, saved)
save('closure_mismatch.json', {
    'recorded_at': receipt['recorded_at'], 'token': TOKEN,
    'actual_finish_exit': 1,
    'actual_finish_stdout': 'CLOSURE_INCOMPLETE: Blocked GPU candidate has a queue opening\nPOSTFLIGHT FAILED: lease retained; continue this tick or explicitly abort',
    'receipt': evidence(OUT / 'finish_failed_receipt.json'),
    'physical_resource_evidence': evidence(OUT / 'final_environment.json'),
    'checker_source_sha256': tick.digest(
        Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/closure.py')),
    'mismatch': 'Queue-only opening contradicts live foreign compute occupation of both authorized physical GPUs.',
    'scientific_gates_changed': False, 'checker_modified': False,
    'actual_execution_state': 'INCOMPLETE_PENDING_ABORT',
    'next_action': 'Explicit abort with exact mismatch;verify lease and pending state absent;no post-release writes.'})
advance([OUT / 'closure_mismatch.json', OUT / 'finish_failed_receipt.json'])
print({'preserved': True, 'state': 'INCOMPLETE_PENDING_ABORT'})
