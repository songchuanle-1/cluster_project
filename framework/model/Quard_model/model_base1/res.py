import torch
import triton
import triton.language as tl

@triton.jit
def sparse_gather_matmul_kernel(
    Q_ptr, K_ptr, Idx_ptr, Out_ptr,
    stride_qb, stride_qh, stride_qn, stride_qc,  # Q 的 stride
    stride_kb, stride_kh, stride_km, stride_kc,  # K 的 stride
    stride_ib, stride_ih, stride_in, stride_ik,  # Idx 的 stride
    stride_ob, stride_oh, stride_on, stride_ok,  # Out 的 stride
    B, H, N, M, K_selected, C: tl.constexpr,     # K_selected 是你选出的 k 个
    BLOCK_N: tl.constexpr,                       # 每次处理多少个 Query
    BLOCK_K: tl.constexpr                        # 每次处理多少个 Index
):
    # 1. 确定当前 Program ID 处理的数据位置
    # 我们将 Grid 设置为一维，平铺 (B * H * N)
    # pid 表示当前处理的是第几个 Query (在展平的 BHN 维度上)
    pid = tl.program_id(0)
    
    # 反解出 batch, head, n_idx
    # 假设 Grid 覆盖了 B*H*N/BLOCK_N
    # 为了简化逻辑，这里建议 grid 直接设为 (B*H*N, )，BLOCK_N=1 (每个线程块处理一个 Query)
    # 如果 N 很大，可以优化 BLOCK_N，但为了处理 Indirect Memory Access，BLOCK_N=1 逻辑最清晰
    
    cur_n = pid % N
    cur_h = (pid // N) % H
    cur_b = (pid // (N * H))

    # 2. 定位 Query 的内存指针
    # Q shape: (B, H, N, C)
    q_offset = cur_b * stride_qb + cur_h * stride_qh + cur_n * stride_qn
    Q_block_ptr = Q_ptr + q_offset + tl.arange(0, C) * stride_qc
    
    # 加载当前的一个 Query 向量 (1, C)
    # mask 保护：虽然 C 通常是 2 的幂次 (64, 128)，但加上 mask 更安全
    q_vec = tl.load(Q_block_ptr, mask=tl.arange(0, C) < C)

    # 3. 定位 Index 的内存指针
    # Idx shape: (B, H, N, K_selected)
    # 我们需要遍历 K_selected 维度
    idx_base = cur_b * stride_ib + cur_h * stride_ih + cur_n * stride_in
    
    out_base = cur_b * stride_ob + cur_h * stride_oh + cur_n * stride_on

    # 4. 循环处理 K_selected (分块处理)
    for k_start in range(0, K_selected, BLOCK_K):
        k_offsets = k_start + tl.arange(0, BLOCK_K)
        k_mask = k_offsets < K_selected
        
        # 加载索引: idx_vals 里面存的是在 M 维度上的下标
        idx_ptr = Idx_ptr + idx_base + k_offsets * stride_ik
        idx_vals = tl.load(idx_ptr, mask=k_mask, other=0)
        
        # 5. 核心逻辑：Gather + Dot Product
        # 这是一个 Indirect Load (间接读取)，比较耗时
        # 我们需要计算: sum(Q * K_gathered, dim=-1)
        
        # 计算 Key 的指针位置
        # K shape: (B, H, M, C)
        # 指针 = Batch_offset + Head_offset + M_offset (来自 idx_vals) + C_offset (广播)
        k_base_ptr = K_ptr + cur_b * stride_kb + cur_h * stride_kh
        
        # 构造 Key 的读取指针矩阵: [BLOCK_K, C]
        # idx_vals[:, None] 扩展为 [BLOCK_K, 1]
        # tl.arange(0, C)[None, :] 扩展为 [1, C]
        k_ptrs = k_base_ptr + (idx_vals[:, None] * stride_km) + (tl.arange(0, C)[None, :] * stride_kc)
        
        # 加载 Key 数据 [BLOCK_K, C]
        # 需要处理 mask: 既要保证 k < K_selected，又要保证 c < C
        load_mask = k_mask[:, None] & (tl.arange(0, C)[None, :] < C)
        k_data = tl.load(k_ptrs, mask=load_mask, other=0.0)
        
        # 6. 计算点积
        # q_vec [C] 广播成 [1, C] 与 k_data [BLOCK_K, C] 相乘
        prod = k_data * q_vec[None, :] 
        
        # 在 C 维度求和 -> 得到 [BLOCK_K] 个分数
        score = tl.sum(prod, axis=1)
        
        # 7. 写回结果
        out_ptr_loc = Out_ptr + out_base + k_offsets * stride_ok
        tl.store(out_ptr_loc, score, mask=k_mask)

def sparse_attention_score(query, key, idx):
    """
    query: (B, H, N, C)
    key:   (B, H, M, C)  <-- 注意！请确保是 M, C 布局
    idx:   (B, H, N, K)
    Return: (B, H, N, K)
    """
    B, H, N, C = query.shape
    _, _, M, _ = key.shape
    _, _, _, K_sel = idx.shape
    
    # 确保 contiguous，否则 stride 会乱
    query = query.contiguous()
    key = key.contiguous() 
    idx = idx.contiguous()
    
    out = torch.empty((B, H, N, K_sel), device=query.device, dtype=query.dtype)
    
    # Grid 设定：每个 Block 处理 1 个 Query (N维度)
    # 总共 B*H*N 个 Blocks
    grid = (B * H * N, )
    
    # Block_K 设为 32 或 64 都可以，视 K_sel 大小而定
    # C 作为 constexpr 传入，方便编译器展开循环
    sparse_gather_matmul_kernel[grid](
        query, key, idx, out,
        query.stride(0), query.stride(1), query.stride(2), query.stride(3),
        key.stride(0), key.stride(1), key.stride(2), key.stride(3),
        idx.stride(0), idx.stride(1), idx.stride(2), idx.stride(3),
        out.stride(0), out.stride(1), out.stride(2), out.stride(3),
        B, H, N, M, K_sel, C,
        BLOCK_N=1, BLOCK_K=32
    )
    return out

# --- 测试与验证 ---
if __name__ == "__main__":
    B, H, N, M, C, K = 12, 8, 2048, 2048, 32, 1000
    device = "cuda"

    q = torch.randn(B, H, N, C, device=device, dtype=torch.float16)
    k = torch.randn(B, H, M, C, device=device, dtype=torch.float16)
    # 随机生成一些索引 [0, M)
    idx = torch.randint(0, M, (B, H, N, K), device=device)

    # 1. Triton 自定义算子
    import time
    start = time.time()
    out_triton = sparse_attention_score(q, k, idx)
    end = time.time()
    print(f"Triton 耗时: {end - start:.4f} 秒")

    # 2. PyTorch 原生实现 (用于校验正确性)
    # 先 Gather Key: (B,H,N,K,C)
    # 展平 idx 以便 gather
    idx_expanded = idx.unsqueeze(-1).expand(-1, -1, -1, -1, C) # (B, H, N, K, C)
    # 为了 gather，需要把 key 扩充到 (B, H, N, M, C) -> 太大了，不可行
    # 所以通常做法是 view 成 (B*H, M, C) 然后 gather
    
    # 验证逻辑：手动循环对比一个小块，或者用爱因斯坦求和验证
    # 简单的验证方法：取第一个 batch 第一个 head
    q_0 = q[0,0] # (N, C)
    k_0 = k[0,0] # (M, C)
    idx_0 = idx[0,0] # (N, K)
    
    # 暴力 Gather
    # (N, K, C)
    gathered_k = k_0[idx_0.long()] 
    # (N, 1, C) * (N, K, C) -> sum -> (N, K)
    out_ref = (q_0.unsqueeze(1) * gathered_k).sum(dim=-1)
    
    print("Triton Shape:", out_triton.shape)
    print("Ref Shape:   ", out_ref.shape)
    
    # 比较误差
    diff = (out_triton[0,0] - out_ref).abs().max()
    print(f"最大误差: {diff.item()}")
    
    if diff < 1e-2:
        print("✅ 结果一致！")
    else:
        print("❌ 结果不一致，请检查逻辑。")