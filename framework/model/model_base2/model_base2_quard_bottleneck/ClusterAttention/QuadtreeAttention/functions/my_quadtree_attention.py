import torch
from torch.autograd import Function
try:
    import my_score_computation_cuda
except ImportError:
    import importlib.util, os
    base = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(base, "..", ".."))
    so_mod = None
    for fname in os.listdir(root):
        if fname.startswith("my_score_computation_cuda") and fname.endswith(".so"):
            spec = importlib.util.spec_from_file_location("my_score_computation_cuda", os.path.join(root, fname))
            so_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(so_mod)
            break
    if so_mod is None:
        raise
    my_score_computation_cuda = so_mod

class MyScoreComputation(Function):
    @staticmethod
    def forward(ctx, query, key, index):
        x = my_score_computation_cuda.score_forward(query, key, index)
        ctx.save_for_backward(query, key, index)
        return x[0]

    @staticmethod
    def backward(ctx, grad_output):
        query, key, index = ctx.saved_tensors
        grad_output = grad_output.contiguous()
        x = my_score_computation_cuda.score_backward(grad_output, query, key, index)
        return x[0], x[1], None

my_score_computation_op = MyScoreComputation.apply
