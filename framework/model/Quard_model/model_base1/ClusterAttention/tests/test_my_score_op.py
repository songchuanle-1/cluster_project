import torch
import pytest
import math

# from QuadtreeAttention.functions.quadtree_attention import score_computation_op
from torch.autograd import Function
from einops.einops import rearrange
import time
import score_computation_cuda
import value_aggregation_cuda


class ScoreComputation(Function):
    @staticmethod
    def forward(ctx, query, key, index):
        x = score_computation_cuda.score_forward(query, key, index)
        ctx.save_for_backward(query, key, index)
        return x[0]

    @staticmethod
    def backward(ctx, grad_output):
        input1, input2, index = ctx.saved_tensors
        grad_output = grad_output.contiguous()
        x = score_computation_cuda.score_backward(grad_output, input1, input2, index)
        return x[0], x[1], None


score_computation_op = ScoreComputation.apply





class value_aggregation(Function):
    @staticmethod
    def forward(ctx, score, value, index):
        ctx.save_for_backward(score, value, index)
        f = score.shape[2]
        b, N, _, H = score.shape
        D = value.shape[-1]
        # value [b, M, H, D]
        output = score.new_zeros([b, N, H, D]).contiguous()  # b, 4N, H, D
        value_aggregation_cuda.value_aggregation_forward(score, value, index, output)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        score, value, index = ctx.saved_tensors
        grad_output = grad_output.contiguous()

        grad_score = score.new_zeros(score.shape).contiguous()
        grad_value = value.new_zeros(value.shape).contiguous()

        value_aggregation_cuda.value_aggregation_backward(grad_output, score, value, index, grad_score, grad_value)

        return grad_score, grad_value, None


value_aggregation_op = value_aggregation.apply

def test_backward():
    B, N, M, H, D, K = 12, 2048, 2048, 8, 32, 4
    query = torch.randn(B, N, H, D, device='cuda', requires_grad=True)
    key = torch.randn(B, M, H, D, device='cuda', requires_grad=True)
    value = torch.randn(B, M, H, D, device='cuda', requires_grad=True)

    index = torch.randint(0, M, (B, N, K, H), device='cuda')
    # from test import com,com_mamtul
    # res_weights,res_value = com(query, key, value, index)
    # res2_weights,res2_value = com_mamtul(query, key, value, index)
    out = score_computation_op(query, key, index)
    out2 = value_aggregation_op(out, value, index)
    # res3_weights = out[0,0,:,0]
    # res3_value = out2[0,0,0,:]
    loss2 = out2.sum()
    loss2.backward()
    assert query.grad is not None
    assert key.grad is not None


def test_loss_stability_over_steps():
    """多步反向传播下检查 loss 和梯度的数值稳定性。"""
    device = 'cuda'

    # 使用相对较小的张量规模，保证测试可在 CI 中跑完
    B, N, M, H, D, K = 2, 256, 256, 4, 16, 4

    query = torch.randn(B, N, H, D, device=device, requires_grad=True)
    key = torch.randn(B, M, H, D, device=device, requires_grad=True)
    value = torch.randn(B, M, H, D, device=device, requires_grad=True)

    index = torch.randint(0, M, (B, N, K, H), device=device)

    params = [query, key, value]
    optimizer = torch.optim.Adam(params, lr=1e-3)

    prev_loss = None
    num_steps = 10

    for _ in range(num_steps):
        optimizer.zero_grad()

        out = score_computation_op(query, key, index)
        out2 = value_aggregation_op(out, value, index)
        loss = out2.mean()

        # 1) loss 本身需要是有限值
        assert torch.isfinite(loss), "Loss became non-finite (NaN/Inf) during training steps."

        loss.backward()

        # 2) 检查梯度是否为有限值，且范数不过大
        total_norm_sq = 0.0
        for p in params:
            assert p.grad is not None, "Gradient is None for a parameter during stability test."
            assert torch.isfinite(p.grad).all(), "Gradient contains NaN/Inf values."
            g_norm = p.grad.norm().item()
            total_norm_sq += g_norm * g_norm

        total_norm = math.sqrt(total_norm_sq)
        assert not math.isnan(total_norm) and not math.isinf(total_norm), "Total gradient norm is NaN/Inf."
        # 经验上给一个较大的上界，避免明显梯度爆炸
        assert total_norm < 1e6, f"Gradient norm exploded: {total_norm}"

        optimizer.step()

        # 3) loss 不应该出现剧烈的数量级跳变（允许震荡，但避免爆炸）
        if prev_loss is not None:
            # 允许 loss 上下浮动，但不应该突然大于若干数量级
            assert loss.item() < 10 * (abs(prev_loss) + 1e-6), (
                f"Loss jumped too much between steps: prev={prev_loss}, current={loss.item()}"
            )

        prev_loss = loss.item()

def gather_keys_by_mask(mask):
    """
    key:  (B, H, M, C)
    mask: (B, H, N, M)  True表示需要选择
    """
    # B, H, N, M = mask.shape
    # C = key.shape[-1]

    # 1. 计算 K (M维度上 True 最多的数量)
    # 统计每个 query 对应的 true 数量
    num_valid = mask.sum(dim=-1)  # (B, H, N)
    K = num_valid.max().item()    # 获取整个 batch 中最大的 K
    
    print(f"最大选中数量 K = {K}")

    # 2. 获取索引
    # 将 mask 转为 int (True=1, False=0)，然后降序排列
    # 这样所有的 1 (True) 都会跑到前面，0 (False) 跑到后面
    # sorted_indices 包含了我们要 gather 的索引
    # sorted_mask_vals 用于后续把填充的部分置 0
    sorted_mask_vals, sorted_indices = torch.sort(mask.int(), dim=-1, descending=True)
    
    # 3. 截取前 K 个索引
    top_k_indices = sorted_indices[..., :K]      # (B, H, N, K)
    # top_k_mask = sorted_mask_vals[..., :K].bool() # (B, H, N, K) 保存哪些位置是真实有效的

    return top_k_indices


def benchmark(num_iters: int = 10):
    """多次迭代，统计前向+反向时间、显存和 FLOPs。"""

    # 这里保持和 test_backward 相同的张量规模
    B, N, M, H, D, K = 12, 2048, 2048, 8, 32, 4

    device = 'cuda'
    torch.cuda.reset_peak_memory_stats(device)

    # 固定一组输入，模拟训练中重复使用相同 shape 的 batch
    query = torch.randn(B, N, H, D, device=device, requires_grad=True)
    key = torch.randn(B, M, H, D, device=device, requires_grad=True)
    value = torch.randn(B, M, H, D, device=device, requires_grad=True)
    # mask = (torch.rand(B, H, N, M, device=device) > 0.9)
    # index = gather_keys_by_mask(mask).permute(0,2,3,1).contiguous()
    index = torch.randint(0, M, (B, N, K, H), device=device)
    # index[0,0,0,0] = -1
    # 预热几次，稳定性能
    for _ in range(3):
        out = score_computation_op(query, key, index)
        out2 = value_aggregation_op(out, value, index)
        loss = out2.sum()
        loss.backward()
        query.grad = None
        key.grad = None
        value.grad = None

    torch.cuda.synchronize(device)
    torch.cuda.reset_peak_memory_stats(device)

    # 使用 CUDA events 统计时间（毫秒）
    times = []
    for _ in range(num_iters):
        t0 = time.time()
        out = score_computation_op(query, key, index)
        print(out.size())
        out2 = value_aggregation_op(out, value, index)
        loss = out2.sum()
        loss.backward()
        t1 = time.time()
        times.append(t1 - t0)
        # 清空梯度，避免梯度累加干扰显存
        query.grad = None
        key.grad = None
        value.grad = None

    torch.cuda.synchronize(device)

    avg_ms = sum(times)/len(times)

    # 显存占用（峰值）
    max_mem_bytes = torch.cuda.max_memory_allocated(device=device)
    max_mem_mb = max_mem_bytes / 1024 ** 2
    max_mem_gb = max_mem_bytes / 1024 ** 3

    # 简单估算前向 FLOPs（不含 backward）：
    # score_computation: 对每个 (B, N, K, H) 做一个 D 维点积，约 2*D FLOPs
    flops_score_fwd = 2.0 * B * N * K * H * D
    # value_aggregation: 对每个 (B, N, H, D) 聚合 K 个邻居，约 2*K FLOPs
    flops_value_fwd = 2.0 * B * N * H * D * K
    flops_fwd_total = flops_score_fwd + flops_value_fwd

    flops_fwd_g = flops_fwd_total / 1e9

    print(f"\n== Benchmark ({num_iters} iters) ==")
    print(f"avg step time (fwd+backward): {avg_ms:.6f} ms")
    print(f"peak memory: {max_mem_mb:.1f} MB ({max_mem_gb:.3f} GB)")
    print(f"approx forward FLOPs per iter: {flops_fwd_g:.3f} GFLOPs")


if __name__ == "__main__":
    # test_forward_shapes()
    # test_backward()
    benchmark()