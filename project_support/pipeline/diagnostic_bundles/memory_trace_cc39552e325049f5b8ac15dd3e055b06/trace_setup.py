memory_trace = []
core_readout_calls = 0
trace_handles = []

def trace_boundary(name, event):
    torch.cuda.synchronize()
    memory_trace.append({
        'module': name, 'event': event,
        'allocated_bytes': torch.cuda.memory_allocated(),
        'reserved_bytes': torch.cuda.memory_reserved(),
        'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
        'peak_reserved_bytes': torch.cuda.max_memory_reserved()})

def before_boundary(name):
    def hook(module, inputs):
        trace_boundary(name, 'enter')
    return hook

def after_boundary(name):
    def hook(module, inputs, output):
        trace_boundary(name, 'exit')
    return hook

for name, traced_module in model.named_modules():
    if name and len(name.split('.')) <= 3:
        trace_handles.append(traced_module.register_forward_pre_hook(before_boundary(name)))
        trace_handles.append(traced_module.register_forward_hook(after_boundary(name)))

original_readout = model.dec.cluster_att._cluster_to_points
def traced_readout(*args, **kwargs):
    global core_readout_calls
    core_readout_calls += 1
    trace_boundary('cluster_to_points', 'enter')
    output = original_readout(*args, **kwargs)
    trace_boundary('cluster_to_points', 'exit')
    return output
model.dec.cluster_att._cluster_to_points = traced_readout
