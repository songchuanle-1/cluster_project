import register
c=register.c
p=register.OUT
c.guard(1500)
protocol=c.save('numeric_trace_preregistration.json',{'at':c.now(),'candidate_id':c.CID,
    'question':'Does divergence first appear in original scatter_mean bank feature pooling or in cloned input layout/new transport/suffix?',
    'test':'One fixed original two-scene native forward, then twice exact original-reference active-encoder replay and twice cloned-input replay. Capture full-source rawbanks/refined/gather/encoder and input values,strides,offset. No frozen bank, no model mutation, no threshold/dtype changes.',
    'result_interpretation':'Attribute first divergence only from actual trace; do not assume oldPCE source or declare mechanism false.',
    'failure':c.evidence(p/'validation_h2_controls_candidate_result.json')})
worker=(p/'validation_worker_h1.py').read_text(encoding='utf-8')
worker=worker.replace('\ndef main():','\n'+(p/'trace_function.py').read_text(encoding='utf-8')+'\ndef main():')
worker=worker.replace("choices=('resources','controls')","choices=('resources','controls','trace')")
worker=worker.replace("if args.mode=='resources':resources(torch,gorilla,cfg,model,result)","if args.mode=='trace':trace(torch,gorilla,cfg,model,qualified,result)\n        elif args.mode=='resources':resources(torch,gorilla,cfg,model,result)")
with (p/'validation_worker_trace.py').open('x',encoding='utf-8') as stream:stream.write(worker)
controller=(p/'validation_h2.py').read_text(encoding='utf-8').replace('_validation_h2','_validation_trace').replace("OUT/'validation_h2'","OUT/'validation_trace'")
controller=controller.replace('validation_worker_h1.py','validation_worker_trace.py').replace('validation_h2_preregistration','validation_trace_preregistration').replace('validation_h2_staging','validation_trace_staging').replace("'validation_h2_'+label","'validation_trace_'+label").replace("choices=('stage','controls','resources')","choices=('stage','controls','resources','trace')")
with (p/'validation_trace.py').open('x',encoding='utf-8') as stream:stream.write(controller)
c.advance([protocol,p/'trace_function.py',p/'prepare_trace.py'],'Localize original full-source numerical divergence without changing model, then consider only evidenced R1 within original gates.')
print('trace prepared')
