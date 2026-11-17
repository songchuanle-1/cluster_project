"""Retest affected native matched controls on exact final independent R2 source."""
import ast
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT
c.guard(1500)
protocol=c.save('r2_matched_retest_preregistration.json',{'at':c.now(),'candidate_id':c.CID,'revision':2,
    'rationale':'R1 feature reduction and R2 active-encoder canonical ordering change numerical realization; repeat affected8scene/32expr fixed content-vs-strict controls on exact R2. No data/threshold/affinity/head/seed change.',
    'reference':'In the actual independent R2 package, disable only _sibling_fine during frozen native prefix capture. This no-transport reference uses the SAME R2 canonical ordering/CSR in every arm. Freeze its native final query; no query selected by target. It is the matched operational reference, not an exact original-M95-source replay.',
    'intervention':'Capture PRE-TRANSPORT refined tokens from this no-transport native forward. Use exactly one content transport, exactly one all-cycle mismatch, exactly one equal-mass strict mismatch. Never apply transport twice. Keep canonical receiver row alignment internally and inverse-restored masks/GT externally.',
    'alignment':'After native capture, original bank.cluster_ids_list[0] is restored by encoder wrapper. Use those original point→fine IDs for label-only target-leaf readouts; use gathered canonical IDs for the actual fine readback. Fine token IDs and masses identical either row order.',
    'controls':'Primitive unchanged, native frozen identity/readback/head<=1e-6, weighted fine pre-fusion mean and strict conjugacy<=1e-6; report all failures and every task arm. Original R0 adverse evidence remains immutable.',
    'new_training':0,'optimizer_steps':0})
worker=(OUT/'worker.py').read_text(encoding='utf-8')
worker=worker.replace('    bank=attention=None','    bank=attention=None\n    original_sibling=None\n    module=None')
worker=worker.replace('torch,gorilla,cfg,model,metadata=setup()',"from validation_core import setup as candidate_setup\n        torch,gorilla,cfg,model,qualified=candidate_setup('candidate')")
worker=worker.replace("module=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')","module=importlib.import_module(qualified+'.hier_postprocess')\n        original_sibling=module._sibling_fine\n        module._sibling_fine=lambda fine,identifiers,heads:fine")
worker=worker.replace("            features,refined,identifiers,padding=held['gather_args']","            held['original_point_ids']=clone(bank.cluster_ids_list[0])\n            features,refined,identifiers,padding=held['gather_args']")
worker=worker.replace("b=offset+local_expression;ids=identifiers[0][b].long();parent=identifiers[1][b].long();n=len(ids)","b=offset+local_expression;ids=held['original_point_ids'][b].long();parent=identifiers[1][b].long();n=len(ids)")
worker=worker.replace('        if bank is not None and original_build is not None:', '        if module is not None and original_sibling is not None:module._sibling_fine=original_sibling\n        if bank is not None and original_build is not None:')
worker=worker.replace('native_transport_result.json','r2_matched_result.json')
ast.parse(worker)
with (OUT/'r2_matched_worker.py').open('x',encoding='utf-8') as stream:stream.write(worker)
# Create a stage controller by adapting the immutable independent-source staging controller.
controller=(OUT/'validation_r2.py').read_text(encoding='utf-8')
controller=controller.replace("STAGE=c.STAGE+'_validation_r2'","STAGE=c.STAGE+'_r2_matched'").replace("VOUT=OUT/'validation_r2'","VOUT=OUT/'r2_matched'")
start=controller.index("    worker=(OUT/'validation_worker_h1.py')")
end=controller.index('    ast.parse(worker)',start)
controller=controller[:start]+"    worker=(OUT/'r2_matched_worker.py').read_text(encoding='utf-8')\n"+controller[end:]
controller=controller.replace("payload={'native_runtime.py':runtime.encode(),'worker.py':worker.encode()}","payload={'native_runtime.py':runtime.encode(),'worker.py':worker.encode(),\n        'validation_core.py':(OUT/'validation_worker_h1.py').read_bytes(),\n        'transport.py':(OUT/'transport.py').read_bytes()}")
controller=controller.replace('validation_r2_execution_preregistration.json','r2_matched_execution_preregistration.json').replace('validation_r2_staging.json','r2_matched_staging.json')
controller=controller.replace("str(stage/'execution_lease.json'),'--mode',MODE,'--target',TARGET]","str(stage/'execution_lease.json')]")
controller=controller.replace("path=stage/(MODE+'_'+TARGET+'_result.json')","path=stage/'r2_matched_result.json'")
controller=controller.replace("'validation_r2_'+label","'r2_matched_'+label")
ast.parse(controller)
with (OUT/'r2_matched.py').open('x',encoding='utf-8') as stream:stream.write(controller)
c.advance([protocol,OUT/'r2_matched_worker.py',OUT/'prepare_r2_controls.py'],'Retest R2 affected8scene fixed-query content controls with exactly-one transport and original/canonical row alignment verified; no admission from incomplete retest.')
print('R2 affected controls prepared')
