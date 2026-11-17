"""Preserve the actual closure outcome without fabricating research exhaustion."""
from datetime import datetime, timezone
import shutil
from ops import guard, save, advance, evidence, tick, ROOT, OUT, TOKEN

owner = guard()
path = ROOT / 'pipeline/tick_receipts' / (TOKEN + '.json')
receipt = tick.load(path)
assert receipt['status'] == 'INCOMPLETE' and receipt['lease_release'] == 'retained'
copy = OUT / 'finish_failed_receipt.json'
assert not copy.exists()
shutil.copyfile(path, copy)
save('finish_failure.json', {
    'recorded_at': receipt['recorded_at'], 'actual_finish_exit': 1,
    'actual_stdout': 'CLOSURE_INCOMPLETE: Capacity gap remains: continue an executable candidate (including a newly created diagnosis candidate) or document a valid design-cycle stop reason\nPOSTFLIGHT FAILED: lease retained; continue this tick or explicitly abort',
    'receipt': evidence(copy), 'scientific_evidence': evidence(OUT / 'analysis_summary.json'),
    'actual_state': 'INCOMPLETE_PENDING_ABORT',
    'remaining_seconds': (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds(),
    'explanation': 'One finite diagnostic is complete but does not prove two independent routes exhausted. No qualified new structure,resource block,phase hold or deadline-near claim invented. Preserve evidence and abort rather than wait/pad or alter checker.',
    'gates_or_checker_changed': False, 'science_completion_is_not_tick_completion': True})
advance([copy, OUT / 'finish_failure.json'])
print({'preserved': True, 'receipt_status': receipt['status'],
       'usage': receipt['usage'], 'outcomes': receipt['outcomes']})
