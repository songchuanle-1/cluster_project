"""Measure contact construction separately from attention, without tuning."""
from pathlib import Path
import control as c

c.guard(600)
protocol = c.save('section_profile_protocol.json', {'preregistered_at': c.now(), 'candidate_id': c.CID,
    'test': 'Same resource-only input; two warmup and three instrumented native predicts; synchronize around contact exchange and time CPU graph construction.',
    'purpose': 'Localize the remaining833ms bottleneck before choosing any revision2; not a replacement for formal20/100 timing.',
    'changes': 'Observational wrappers only; no weights/topology/precision/schedule change or accuracy selection.'})
stage = '/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a/implementation_r1'
code = '''
import copy,importlib,json,logging,sys,time
from pathlib import Path
sys.path.insert(0,STAGE)
import worker
from native_runtime import acquire,release,save,observe
r={'execution_completed':False,'scientific_admission':False,'records':[],'optimizer_steps':0}
try:
 r['before']=acquire(str(Path(STAGE)/'execution_lease.json'))
 torch,gorilla,cfg,model,qualified=worker.setup('candidate')
 from framework.dataset import build_dataset,build_dataloader
 cfg.data.val.lang_num_max=1
 dataset=build_dataset(copy.deepcopy(cfg.data.val),logging.getLogger('sections-only'))
 lc=copy.deepcopy(cfg.dataloader.val)
 lc.batch_size=1
 lc.num_workers=0
 lc.persistent_workers=False
 gorilla.set_random_seed(1999)
 sample=next(iter(build_dataloader(dataset,training=False,**lc)))
 network=importlib.import_module(qualified+'.network')
 hierarchy=importlib.import_module(qualified+'.hier_postprocess')
 old_contact,old_exchange=network.contacts,hierarchy.exchange
 durations={'contacts':[],'exchange':[]}
 def contacts(*args,**kwargs):
  start=time.perf_counter()
  value=old_contact(*args,**kwargs)
  durations['contacts'].append((time.perf_counter()-start)*1000)
  return value
 def exchange(*args,**kwargs):
  torch.cuda.synchronize()
  start=time.perf_counter()
  value=old_exchange(*args,**kwargs)
  torch.cuda.synchronize()
  durations['exchange'].append((time.perf_counter()-start)*1000)
  return value
 network.contacts,hierarchy.exchange=contacts,exchange
 try:
  with torch.no_grad():
   for i in range(5):
    durations={'contacts':[],'exchange':[]}
    torch.cuda.synchronize()
    start=time.perf_counter()
    model(sample,mode='predict')
    torch.cuda.synchronize()
    row={'repeat':i,'warmup':i<2,'total_ms':(time.perf_counter()-start)*1000,'contacts_ms':sum(durations['contacts']),'exchange_ms':sum(durations['exchange'])}
    r['records'].append(row)
 finally:network.contacts,hierarchy.exchange=old_contact,old_exchange
 r.update(execution_completed=True,after=observe(),scope='Instrumented diagnostic,not formal20/100 resource replacement')
except BaseException as error:
 r.update(error_type=type(error).__name__,error=str(error))
 raise
finally:
 try:save('section_profile_result.json',r)
 finally:release()
print(json.dumps(r))
'''
observed = c.remote('STAGE=' + repr(stage) + '\n' + code, timeout=400, conda=True)
observation = c.save('section_profile_execution.json', observed)
assert observed['returncode'] == 0
result = c.save('section_profile_result.json', observed['data'])
c.advance([protocol, observation, result, Path(__file__)],
    'Use measured section breakdown to choose one bounded revision or preserve an inconclusive implementation; original numerical gates remain.')
print(observed['data'])
