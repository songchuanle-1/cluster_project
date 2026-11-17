import time
import torch
import torch.nn.functional as F
from einops import rearrange, repeat
from issm_triton.issm_combined import ISSM_chunk_scan_combined


def segsum(x):
    """更稳定的分段前缀和 (segment sum) 计算。

    输入:  x, 形状为 (..., T)
    输出: x_segsum, 形状为 (..., T, T)
          对最后一维长度 T 构造一个下三角前缀和矩阵, 供后续构造 exp(累积 A) 使用。
    """
    T = x.size(-1)
    x = repeat(x, "... d -> ... d e", e=T)
    mask = torch.tril(torch.ones(T, T, device=x.device, dtype=bool), diagonal=-1)
    x = x.masked_fill(~mask, 0)
    x_segsum = torch.cumsum(x, dim=-2)
    mask = torch.tril(torch.ones(T, T, device=x.device, dtype=bool), diagonal=0)
    x_segsum = x_segsum.masked_fill(~mask, -torch.inf)
    return x_segsum

def ISSM_minimal_discrete(X, dt, A, B, C, block_len, initial_states=None):
    """PyTorch 参考实现, 对应一个分块(Chunked)的离散 SSM。

    参数:
        X  : (B, L, H, P)  输入序列, B=batch, L=length, H=n_heads, P=d_head
        dt : (B, L, H, N)  步长相关参数, N=d_state
        A  : (B, L, H, N)  SSM A 参数 (已按测试中与 dt 相乘)
        B  : (B, L, H, N)  SSM B 参数
        C  : (B, L, H, N)  SSM C 参数
        block_len: 每个 chunk 的时间长度, 要求 L % block_len == 0
        initial_states: (B, H, P, N), 初始隐状态, 若为 None 则用 0 初始化

    返回:
        Y          : (B, L, H, P), SSM 输出
        final_state: (B, H, P, N), 整个序列末尾的隐状态
    """
    assert X.dtype == A.dtype == B.dtype == C.dtype == dt.dtype
    assert X.shape[1] % block_len == 0

    # 1) 把时间维按 block_len 划分成多个 chunk: L = C * block_len
    X, dt, A, B, C = [rearrange(x, "b (c l) ... -> b c l ...", l=block_len) for x in (X, dt, A, B, C)]

    # 2) 把 A 重排, 便于在时间维 (l) 上做累积和, 得到 per‑chunk 的衰减因子
    A = rearrange(A, "b c l h n -> b h n c l")  # (B, H, N, C, Lc)
    A_cumsum = torch.cumsum(A, dim=-1)  # (B, H, N, C, Lc)
    A_cumsum.retain_grad()

    # 3) 计算 chunk 内的输出 (对应 block 矩阵的对角块)
    L = torch.exp(segsum(A))
    CABT  = torch.einsum("bclhn,bcshn,bhncls,bcshn->bchls", C, B, L, dt)
    Y_diag  = torch.einsum("bchls,bcshp->bclhp", CABT, X)

    # 4) 计算 chunk 内的状态汇总 (off‑diagonal 右因子, B‑term)
    decay_states = torch.exp((A_cumsum[:, :, :, :, -1:] - A_cumsum)) # ddA_next
    states = torch.einsum("bclhn,bhncl,bclhn,bclhp->bchpn", B, decay_states, dt, X)

    # 5) 计算 chunk 间的 SSM 递推, 得到各 chunk 边界处的正确隐状态 (中间 A‑term)
    if initial_states is None:
        initial_states = torch.zeros_like(states[:, :1])
    else:
        initial_states = initial_states.unsqueeze(1)
    new_states1 = torch.cat([initial_states, states], dim=1)
    decay_chunk = torch.exp(segsum(F.pad(A_cumsum[:, :, :, :, -1], (1, 0)))) # ddA_cumsum_prev
    new_states = torch.einsum("bhnzc,bchpn->bzhpn", decay_chunk, new_states1)
    new_states2, final_state = new_states[:, :-1], new_states[:, -1]

    # 6) 把 chunk 边界状态传播到 chunk 内各时间步, 再投影到输出 (左因子 C‑term)
    state_decay_out = torch.exp(A_cumsum) # ddA_cumsum_prev
    Y_off = torch.einsum('bclhn,bchpn,bhncl->bclhp', C, new_states2, state_decay_out)

    # 7) 对角块 + 非对角块输出相加, 再把 chunk 维拼回原始时间维
    Y = rearrange(Y_diag + Y_off, "b c l h p -> b (c l) h p")
    return Y, final_state


def test_correctness_triton():
    torch.manual_seed(42)

    ## Dimensions
    batch, seqlen, chunk_size, dim, headdim = 1, 512, 256, 256, 32
    nheads = dim // headdim 
    ngroups = 1
    dstate = 256
    dtype = torch.float32
    device = "cuda"

    x_ref = torch.randn(batch, seqlen, nheads, headdim, dtype=dtype, device=device).requires_grad_()
    initial_states_ref = torch.randn(batch, nheads, headdim, dstate, dtype=dtype, device=device).requires_grad_()
    # dt_ref: (B, L, H, N), 正值的步长参数, 使用 softplus 保证 > 0, 前面减 4 让值更小更稳定
    dt_ref = F.softplus(torch.randn(batch, seqlen, nheads, dstate, dtype=torch.float32, device=device) - 4).requires_grad_()
    # A_ref: (H, N), 连续时间 A 的对角参数, 通过 -exp(rand) 保证为负, 使 SSM 稳定
    A_ref = (-torch.exp(torch.rand(nheads, dstate, dtype=torch.float32, device=device))).requires_grad_()
    # B_ref: (B, L, G, N), SSM 的 B 矩阵, 这里 G=ngroups=1, 后续会在实现内部按 head 广播
    B_ref = torch.randn(batch, seqlen, ngroups, dstate, dtype=dtype, device=device).requires_grad_()
    # C_ref: (B, L, G, N), SSM 的 C 矩阵, 形状与 B_ref 相同, 也是按 group 定义
    C_ref = torch.randn(batch, seqlen, ngroups, dstate, dtype=dtype, device=device).requires_grad_()
    y_ref, final_state_ref = ISSM_minimal_discrete(x_ref, dt_ref, A_ref*dt_ref, B_ref, C_ref, chunk_size, initial_states=initial_states_ref)

    x = x_ref.detach().clone().requires_grad_()
    dt = dt_ref.detach().clone().requires_grad_()
    A = A_ref.detach().clone().requires_grad_()
    B = B_ref.detach().clone().requires_grad_()
    C = C_ref.detach().clone().requires_grad_()
    initial_states = initial_states_ref.detach().clone().requires_grad_()
    y, final_state = ISSM_chunk_scan_combined(x, dt, A, B, C, chunk_size, D=None, initial_states=initial_states, return_final_states=True)
    
    print(f'Output mean diff (%): {((y - y_ref)/ (y_ref)).abs().mean().item()}')
    print(f'Final state mean diff (%): {((final_state - final_state_ref)/ (final_state_ref)).abs().mean().item()}')

    loss_func = torch.nn.MSELoss()
    loss = loss_func(y, torch.ones_like(y)) * 10000
    loss.backward()
    loss_ref = loss_func(y_ref, torch.ones_like(y_ref)) * 10000
    loss_ref.backward()

    print(f'dx mean diff (%): {((x.grad - x_ref.grad) / (x_ref.grad)).abs().mean().item()}')
    print(f'ddt mean diff (%): {((dt.grad - dt_ref.grad) / (dt_ref.grad)).abs().mean().item()}')
    print(f'dA mean diff (%): {((A.grad - A_ref.grad)/ (A_ref.grad)).abs().mean().item()}')
    print(f'dB mean diff (%): {((B.grad - B_ref.grad) / (B_ref.grad)).abs().mean().item()}')
    print(f'dC mean diff (%): {((C.grad - C_ref.grad) / (C_ref.grad)).abs().mean().item()}')
    print(f'dinitial_states mean diff (%): {((initial_states.grad - initial_states_ref.grad) / (initial_states_ref.grad)).abs().mean().item()}')

def test_speed_triton():
    torch.manual_seed(42)

    ## Dimensions
    batch, seqlen, chunk_size, dim, headdim = 1, 512, 256, 256, 32
    nheads = dim // headdim 
    ngroups = 1
    dstate = 256
    dtype = torch.float32
    device = "cuda"

    x = torch.randn(batch, seqlen, nheads, headdim, dtype=dtype, device=device).requires_grad_()
    dt = F.softplus(torch.randn(batch, seqlen, nheads, dstate, dtype=torch.float32, device=device) - 4).requires_grad_()
    A = (-torch.exp(torch.rand(nheads, dstate, dtype=torch.float32, device=device))).requires_grad_()
    B = torch.randn(batch, seqlen, ngroups, dstate, dtype=dtype, device=device).requires_grad_()
    C = torch.randn(batch, seqlen, ngroups, dstate, dtype=dtype, device=device).requires_grad_()
    initial_states = torch.randn(batch, nheads, headdim, dstate, dtype=dtype, device=device).requires_grad_()

    for i in range(100):
        start = time.process_time()
        y, final_state = ISSM_chunk_scan_combined(x, dt, A, B, C, chunk_size, D=None, initial_states=initial_states, return_final_states=True)
        end = time.process_time()
        print(f'{i}: Time taken: {end - start} seconds')


if __name__ == "__main__":
    test_correctness_triton()
    test_speed_triton()