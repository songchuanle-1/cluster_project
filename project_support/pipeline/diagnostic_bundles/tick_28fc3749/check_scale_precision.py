"""Separate precision diagnostic; preserve the strict float32 failure."""
from ops import *
import ast

guard(180)
measured=tick.load(OUT/'native_scale_cpu_measured.json')
assert measured['contracts_passed'] is False
assert measured['receiver_permutation_max_error']>1e-6
plan={
 'preregistered_at':datetime.now(timezone.utc).isoformat(),
 'question':'Does the permutation discrepancy persist when the SAME frozen float32 fixture/weights are promoted to float64?',
 'change':'Cast the already generated model,points,queries and banks to float64 immediately before the SAME source forward. No new seed,weights,target,index,tolerance or model operation.',
 'prediction':'If the discrepancy is reduction precision rather than indexing,identity and permutation contracts meet the original1e-6 threshold in float64.',
 'original_float32_failed':evidence(OUT/'native_scale_cpu_measured.json'),
 'tolerance':1e-6,'trained_task_evidence':False,
 'interpretation':'Float64 success is numerical discrimination only;it does not overwrite or pass the original float32 gate or scientific diagnosis.'}
save('precision_prereg.json',plan)
source=ast.parse((OUT/'measure_native_scale_cpu.py').read_text(encoding='utf-8'))
program=next(node.value.value for node in source.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='program' for t in node.targets))
marker='with torch.no_grad():\n'
assert program.count(marker)==1
program=program.replace(marker,"model=model.double();points=points.double();query=query.double();banks=[v.double() for v in banks]\n"+marker)
expected=measured['source_sha256']
result=remote('server-4','EXPECTED='+repr(expected)+'\n'+program,conda=True,timeout=150)
result.update(dtype='float64_from_frozen_float32',original_float32_gate_passed=False,scientific_diagnosis_passed=False)
save('native_scale_precision.json',result)
failure={'original_attempt':'test_native_scale_cpu.py','status':'FAILED','exception':'AssertionError at unchanged aggregate numerical threshold1e-6 before result save','subsequent_measurement':evidence(OUT/'native_scale_cpu_measured.json'),'observed_failed_control':'receiver_permutation_max_error','observed_error':measured['receiver_permutation_max_error'],'threshold':1e-6,'original_script':evidence(OUT/'test_native_scale_cpu.py'),'production_modified':False}
save('strict_float32_failure.json',failure)
advance([OUT/'precision_prereg.json',OUT/'native_scale_precision.json',OUT/'strict_float32_failure.json',OUT/'test_native_scale_cpu.py',OUT/'check_scale_precision.py'],failure_scope='inconclusive',gate_result='Original float32 permutation control FAILED at1.0728836059570312e-6 with unchanged1e-6 threshold;separate precision diagnostic recorded without overwriting failure. Task diagnosis still UNPASSED.')
print(json.dumps(result,ensure_ascii=True,indent=2))
