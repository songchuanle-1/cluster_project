#include <vector>
#include <stdio.h>
#include <math.h>
#include <float.h>
#include "score_computation.h"

// 移除 MAX_H 定义
// #define MAX_H 8 

#define CUDA_NUM_THREADS 1024
#define WARPS_PER_BLOCK 1
#define THREADS_PER_WARP 32

#define CUDA_KERNEL_LOOP(i, n) for (int i = blockIdx.x * blockDim.x + threadIdx.x; i < (n); i += blockDim.x * gridDim.x)

template <typename scalar_t>
__global__ void ScoreData(
  torch::PackedTensorAccessor32<scalar_t,4,torch::RestrictPtrTraits> query, // B, N1, H, dim
  torch::PackedTensorAccessor32<scalar_t,4,torch::RestrictPtrTraits> key, //B, N2, H, dim
  torch::PackedTensorAccessor32<int64_t,4,torch::RestrictPtrTraits> index, //B, N1, K, H
  torch::PackedTensorAccessor32<scalar_t,4,torch::RestrictPtrTraits> output //B, N1, K, H
  ){
    extern __shared__ char patch_data_char[];
  
  scalar_t *feat1_data = (scalar_t *)patch_data_char;

  
  int b = blockIdx.x;
  int n1 = blockIdx.y;
  // no feature dim
  
  int ch_off = threadIdx.x;
  
  int D=query.size(3);
  int H=query.size(2);
  int HD=H*D;
  int K=index.size(2);

  // score 数组紧接在 feat1_data 之后
  // feat1_data 大小为 HD * sizeof(scalar_t)
  scalar_t *score = (scalar_t *)(feat1_data + HD);

  // 加载 Query 到共享内存
  for(int ch = ch_off; ch < HD; ch += (WARPS_PER_BLOCK*THREADS_PER_WARP)) { // CHANNELS
    feat1_data[ch] = query[b][n1][ch/D][ch%D]; 
  }
  __syncthreads();

  for(int k = ch_off; k < K; k += (WARPS_PER_BLOCK*THREADS_PER_WARP)) { 


      for(int h=0; h<H; h++){ //头维度
	        int score_idx=ch_off*H+h; //score 存储位置
          score[score_idx]=0;
          int idx=index[b][n1][k][h];
          if (idx < 0 || idx >= key.size(1)) continue;
          
          scalar_t temp_sum = 0;
          for(int d=0; d<D; d++){
              temp_sum += feat1_data[h*D+d]*key[b][idx][h][d];
          }
          score[score_idx] = temp_sum;
          output[b][n1][k][h]=score[score_idx];
      }
  }


}


std::vector<torch::Tensor> ScoreData_ongpu(torch::Tensor query, // B, N1, H, dim
  torch::Tensor key, // B, N2, H, dim
  torch::Tensor index) // B, N1, K, H
{

    const auto B = query.size(0);
    const auto N1 = query.size(1);
    const auto H = query.size(2);
    const auto D = query.size(3);
    const auto K = index.size(2);

  auto output = torch::zeros({B, N1, K, H},torch::device(torch::kCUDA));
    
    // === 修改 1 对应 Host 端: 计算所需的动态共享内存大小 ===
    // 1. Query 特征: H * D
    // 2. Score 缓存: THREADS_PER_WARP * H (因为每个线程需要存储 H 个头的中间结果)
    int shared_memory_size = (H * D + THREADS_PER_WARP * H) * sizeof(float); // 假设 float，后面用 sizeof(scalar_t)
    // 注意：如果是 double，需要 sizeof(double)

    dim3 totalBlocks(B, N1, 1);
    dim3 threadsPerBlock(THREADS_PER_WARP);
    AT_DISPATCH_FLOATING_TYPES(query.scalar_type(), "ScoreData_ongpu", ([&] {
      int required_bytes = (H * D + THREADS_PER_WARP * H) * sizeof(scalar_t);// 重新计算 bytes
      ScoreData<scalar_t><<<totalBlocks, threadsPerBlock, required_bytes>>>(
          query.packed_accessor32<scalar_t,4,torch::RestrictPtrTraits>(),
          key.packed_accessor32<scalar_t,4,torch::RestrictPtrTraits>(),
          index.packed_accessor32<int64_t,4,torch::RestrictPtrTraits>(),
          output.packed_accessor32<scalar_t,4,torch::RestrictPtrTraits>());
    }));
  return {output};

}

template <typename scalar_t>
__global__ void ScoreDataBackward(
  torch::PackedTensorAccessor32<scalar_t,4,torch::RestrictPtrTraits> grad, //B, N1, K, H
  torch::PackedTensorAccessor32<scalar_t,4,torch::RestrictPtrTraits> query, //B, N1, H, dim
  torch::PackedTensorAccessor32<scalar_t,4,torch::RestrictPtrTraits> key, // B, N2, H, dim
  torch::PackedTensorAccessor32<int64_t,4,torch::RestrictPtrTraits> index,// B, N1, K, H
  torch::PackedTensorAccessor32<scalar_t,4,torch::RestrictPtrTraits> query_grad, //B, N1, H, D
  torch::PackedTensorAccessor32<scalar_t,4,torch::RestrictPtrTraits> key_grad //B, N2, H, D
  ){
  int b = blockIdx.x;
  int n1 = blockIdx.y;
  // no feature dim
  
  extern __shared__ char patch_data_char[];
  

  int ch_off = threadIdx.x;
  
  int D=query.size(3);
  int H=query.size(2);
  int HD=H*D;
  int K=index.size(2);
  // 指针布局规划:
  // 1. Query Data: [HD]
  // 2. Grad Input: [K*H] (注意: 如果 K 很大，这里会溢出共享内存，需谨慎)
  // 3. Query Grad Buffer: [HD] (新增: 用于 Shared Memory 累加)
  
  scalar_t *query_data = (scalar_t *)patch_data_char;
  scalar_t *grad_data = (scalar_t *)(query_data + HD);
  // === 修改 2: 新增 Query 梯度缓存 ===
  scalar_t *q_grad_buff = (scalar_t *)(grad_data + K*H); 

  // 初始化 Query 梯度缓存为 0
  for(int i = ch_off; i < HD; i += THREADS_PER_WARP){
      q_grad_buff[i] = 0;
  }

  // 加载 Query
  for(int ch = ch_off; ch < HD; ch += THREADS_PER_WARP) {
    query_data[ch] = query[b][n1][ch/D][ch%D];
  }
  // 加载 Grad Output
  for(int ch = ch_off; ch < K*H; ch += THREADS_PER_WARP) {
    grad_data[ch] = grad[b][n1][ch/H][ch%H];
  }
  __syncthreads(); // 必须等待初始化和加载完成
  
   for(int k = ch_off; k < K; k += THREADS_PER_WARP) {
      for(int h = 0; h < H; h++){   
          int idx = index[b][n1][k][h];
          if (idx < 0 || idx >= key.size(1)) continue;
          
          scalar_t g = grad_data[k*H+h]; // 读取当前边的梯度权重
          
          for(int d = 0; d < D; d++){
              scalar_t val_for_query = g * key[b][idx][h][d];
              scalar_t val_for_key   = g * query_data[h*D+d];

              // === 修改 2 核心: 优化 Query Grad ===
              // Query 梯度: 写入 Shared Memory (极大减少全局内存原子争用)
              atomicAdd(&q_grad_buff[h*D+d], val_for_query);
              
              // Key 梯度: 必须写入 Global Memory (因为 idx 是随机的，无法在 Block 内聚合)
              // 这里的原子操作是无法避免的，属于 Scatter 操作
              atomicAdd(&key_grad[b][idx][h][d], val_for_key);
          }
      }
  }
  
  __syncthreads(); // 等待所有线程完成累加

  // === 修改 2 结尾: 将缓存写回 Global Memory ===
  // 只需要一个 Warp 协作写回即可
  // 因为每个 Block 独占 query_grad[b][n1]，所以可以直接赋值 (不需要 atomicAdd)
  // 除非有多个 Block 处理同一个 n1 (当前 Grid 设置为 N1，所以是一对一的)
  for(int i = ch_off; i < HD; i += THREADS_PER_WARP){
      // 直接写入，无需 atomic，比 atomicAdd 快
      query_grad[b][n1][i/D][i%D] = q_grad_buff[i]; 
  }
}

std::vector<torch::Tensor> ScoreData_backward_ongpu(torch::Tensor grad_output1, //B, N1, K, H
                      torch::Tensor query, //B, N1, H, dim
                      torch::Tensor key, //B, N2, H, dim
                      torch::Tensor index) //B, N1, K, H

{

    const auto B = grad_output1.size(0);
    const auto N1 = grad_output1.size(1);
    const auto N2 = key.size(1);
    const auto K = grad_output1.size(2);
    const auto H = key.size(2);
    const auto D = key.size(3);


    auto query_grad = torch::zeros({B, N1, H, D},torch::device(torch::kCUDA));
    
    auto key_grad = torch::zeros({B, N2, H, D},torch::device(torch::kCUDA));
    
    // === 修改 2 对应 Host 端: 增加 Shared Memory 大小 ===
    // 包含: Query(HD) + Grad(KH) + Q_Grad_Buffer(HD)
    int shared_memory_per_block = (2 * H * D + K * H);
   
    dim3 totalBlocks(B, N1, 1);
    dim3 threadsPerBlock(THREADS_PER_WARP);
    
    AT_DISPATCH_FLOATING_TYPES(key.scalar_type(), "ScoreDatabackward_ongpu", ([&] {
      ScoreDataBackward<scalar_t><<<totalBlocks, threadsPerBlock, shared_memory_per_block * sizeof(scalar_t)>>>(
          grad_output1.packed_accessor32<scalar_t,4,torch::RestrictPtrTraits>(),
          query.packed_accessor32<scalar_t,4,torch::RestrictPtrTraits>(),
          key.packed_accessor32<scalar_t,4,torch::RestrictPtrTraits>(),
          index.packed_accessor32<int64_t,4,torch::RestrictPtrTraits>(),
          query_grad.packed_accessor32<scalar_t,4,torch::RestrictPtrTraits>(),
          key_grad.packed_accessor32<scalar_t,4,torch::RestrictPtrTraits>()
          );
    }));

  return {query_grad, key_grad};

}

