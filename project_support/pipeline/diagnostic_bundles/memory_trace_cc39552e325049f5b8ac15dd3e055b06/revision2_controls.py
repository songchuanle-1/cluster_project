"""Actual native prefix arguments, paired plain/rematerialized gradients."""
import gc

helper={}
exec(compile(REMATERIALIZATION_SOURCE,'<frozen-prefix-rematerialization>','exec'),helper)
gorilla.set_random_seed(1999)
batches=list(DataLoader(Subset(dataset,[0,60,101,124]),batch_size=2,shuffle=False,
    num_workers=0,collate_fn=dataset.collate_fn))
expected=[(['scene0000_00','scene0002_00'],[0,1,2,3,0,1,2,3],[0,667,2996]),
          (['scene0003_00','scene0004_00'],[0,1,2,3,36,37,38,39],[0,406,1847])]
for entry,(scans,anns,offsets) in zip(batches,expected):
    assert entry['scan_ids']==scans and entry['ann_ids']==anns
    assert entry['batch_offsets'].tolist()==offsets
prefix=[i for i,layer in enumerate(model.dec.encoder_layers) if not layer.use_cluster]
assert prefix==[0,1,2,3,4]
modules={}
for index in prefix:
    modules['encoder_layers.'+str(index)]=model.dec.encoder_layers[index]
    modules['decoder_layers.'+str(index)]=model.dec.decoder_layers[index]
captures=[]
current_pair=None
handles=[]
def capture(name):
    def hook(module,args):
        values=tuple(x.detach().cpu().clone() if torch.is_tensor(x) else copy.deepcopy(x) for x in args)
        captures.append({'pair':current_pair,'name':name,'args':values,
            'cpu_rng':torch.get_rng_state().clone(),'cuda_rng':torch.cuda.get_rng_state().clone()})
    return hook
for name,entry in modules.items():
    handles.append(entry.register_forward_pre_hook(capture(name)))
try:
    for current_pair,entry in enumerate(batches):
        assert (datetime.fromisoformat(FOREGROUND_DEADLINE)-datetime.now(timezone.utc)).total_seconds()>120
        gorilla.set_random_seed(1999)
        with torch.no_grad():
            captured_loss,_=model(copy.deepcopy(entry),mode='loss')
        assert torch.isfinite(captured_loss).all()
        del captured_loss
finally:
    for handle in handles:handle.remove()
assert len(captures)==20
originals={name:entry.forward for name,entry in modules.items()}
installed=helper['install_prefix_rematerialization'](model.dec)
assert set(installed)==set(modules)
records=[]

def flatten(value):
    if torch.is_tensor(value):return [value]
    if isinstance(value,(tuple,list)):
        return [item for entry in value for item in flatten(entry)]
    if isinstance(value,dict):
        return [item for key in sorted(value) for item in flatten(value[key])]
    return []

def replay(record,checkpointed):
    model.zero_grad(set_to_none=True)
    values=[]
    for value in record['args']:
        if torch.is_tensor(value):
            value=value.to('cuda').detach().clone()
            if value.is_floating_point():value.requires_grad_(True)
        else:value=copy.deepcopy(value)
        values.append(value)
    torch.set_rng_state(record['cpu_rng'])
    torch.cuda.set_rng_state(record['cuda_rng'])
    function=modules[record['name']] if checkpointed else originals[record['name']]
    outputs=function(*values)
    tensors=flatten(outputs)
    assert tensors and all(torch.isfinite(x).all() for x in tensors)
    scalar=sum((value*torch.linspace(-1,1,value.numel(),dtype=value.dtype,device=value.device).reshape(value.shape)).sum()/max(value.numel(),1) for value in tensors if value.is_floating_point())
    scalar.backward()
    torch.cuda.synchronize()
    result={'outputs':[x.detach().cpu().clone() for x in tensors],
        'inputs':[None if not torch.is_tensor(x) or x.grad is None else x.grad.detach().cpu().clone() for x in values],
        'parameters':{name:None if p.grad is None else p.grad.detach().cpu().clone() for name,p in modules[record['name']].named_parameters()}}
    del values,outputs,tensors,scalar
    model.zero_grad(set_to_none=True)
    return result

def compare(left,right):
    assert type(left)==type(right)
    if left is None:return 0.0
    if torch.is_tensor(left):
        assert left.shape==right.shape and torch.isfinite(left).all() and torch.isfinite(right).all()
        return float((left-right).abs().max()) if left.numel() else 0.0
    if isinstance(left,list):
        assert len(left)==len(right)
        return max([compare(a,b) for a,b in zip(left,right)]+[0.0])
    assert left.keys()==right.keys()
    return max([compare(left[k],right[k]) for k in left]+[0.0])

for captured in captures:
    assert (datetime.fromisoformat(FOREGROUND_DEADLINE)-datetime.now(timezone.utc)).total_seconds()>120
    plain=replay(captured,False)
    remat=replay(captured,True)
    errors={key:compare(plain[key],remat[key]) for key in plain}
    fingerprints=[hashlib.sha256(x.numpy().tobytes()).hexdigest() if torch.is_tensor(x) else None for x in captured['args']]
    records.append({'pair':captured['pair'],'module':captured['name'],'errors':errors,
        'passed':max(errors.values())<=1e-6,'argument_sha256':fingerprints,
        'argument_shapes':[list(x.shape) if torch.is_tensor(x) else None for x in captured['args']]})
    del plain,remat
    gc.collect()
    torch.cuda.empty_cache()
observations.append(observe('after_native_module_controls'))
result={'observed_at':datetime.now(timezone.utc).isoformat(),'token':FOREGROUND_TOKEN,
    'revision':2,'check_count':len(records),'passed':sum(r['passed'] for r in records),
    'failures':[r for r in records if not r['passed']],'records':records,
    'max_errors':{key:max(r['errors'][key] for r in records) for key in ('outputs','inputs','parameters')},
    'native_capture_forwards':2,'native_module_forwards':40,'native_module_backwards':40,
    'full_model_backward':False,'installed_modules':installed,'allocator_fraction':.25,
    'train_groups':[0,60,101,124],'scenes':4,'expressions':16,'optimizer_steps':0,
    'new_training':False,'observations':observations,
    'scope':'Actual frozen native prefix-module arithmetic/gradient equivalence only, not full-model native backward or resource admission.'}
print('HIER_NATIVE_RESULT='+json.dumps(result))
