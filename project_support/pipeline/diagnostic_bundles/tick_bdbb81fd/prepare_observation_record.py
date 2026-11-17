"""Private current projection and neutral epoch-boundary observation recording."""
from datetime import datetime,timezone
from pathlib import Path
import ast
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
guard();q=ROOT/'pipeline/diagnostic_bundles/tick_fd073f88/packet_catalogue.json'
assert sha(q)=='b2e2aabf82b00a7680db0263b10af9a41c369636e8dff2a761e3716f39d1001d'
catalogue=u.read(q);catalogue['owner']=EXPECTED;catalogue['recorded_at']=datetime.now(timezone.utc).isoformat()
catalogue['previous_static_catalogue']=u.ref(q)
catalogue['scope']='Read-only current projection of unchanged reviewed static packets. No new source/tools/release/PASS/lease.'
s=(ROOT/'pipeline/diagnostic_bundles/tick_240fb040/record_observation.py').read_text('utf8')
s=s.replace('tick_240fb040','tick_bdbb81fd').replace('cre_training_progress_observation.json','cre_training_progress_observation_final.json')
needle="        if live_ref not in cre['evidence']:cre['evidence'].append(live_ref)"
extra="""
        transition_refs=[u.ref(HERE/'cre_training_progress_observation.json'),u.ref(HERE/'cre_native_phase_observation.json')]
        for entry in transition_refs:
            if entry not in cre['evidence']:cre['evidence'].append(entry)
        cre['native_epoch_boundary_observation']={'evidence':transition_refs,'scope':'Initial original Train23-end counter unchanged over3s while log grew; exact same PID later naturally Train24 125-to133, then full source/physical check Train24 300-to308. No death inference, signal or relaunch; initial phase not separately classified.'}
"""
assert needle in s;s=s.replace(needle,needle+extra,1);ast.parse(s)
assert not (HERE/'record_observation.py').exists()
u.save(HERE/'packet_catalogue.json',catalogue);guard()
with (HERE/'record_observation.py').open('x',encoding='utf8') as f:f.write(s)
print('PRIVATE_CURRENT_RECORD_AND_CATALOGUE_READY_NO_SHARED_MUTATION')
