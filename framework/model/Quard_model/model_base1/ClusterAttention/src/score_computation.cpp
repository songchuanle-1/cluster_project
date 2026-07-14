#include "score_computation.h"
#include <torch/extension.h>
#include <vector>
#include<iostream>
#include<stdio.h>
#define CHECK_CUDA(x) TORCH_CHECK(x.type().is_cuda(), #x " must be a CUDA tensor")
#define CHECK_CONTIGUOUS(x) TORCH_CHECK(x.is_contiguous(), #x " must be contiguous")
#define CHECK_INPUT(x) CHECK_CUDA(x); CHECK_CONTIGUOUS(x)

// == Forward
std::vector<torch::Tensor> score_cuda_forward(torch::Tensor input1, // B, N, H, D
                      torch::Tensor input2, // B, M, H, D
                      torch::Tensor index) // B, N, K, H
{
    CHECK_INPUT(input1);
    CHECK_INPUT(input2);
    CHECK_INPUT(index);
    return ScoreData_ongpu(input1, input2, index);

}

std::vector<torch::Tensor> score_cuda_backward(torch::Tensor grad_output1, // B, N, K, H
                      torch::Tensor input1, // B, N, H, D
                      torch::Tensor input2, // B, M, H, D
                      torch::Tensor index) // B, N, K, H
{
    CHECK_INPUT(grad_output1);
    CHECK_INPUT(input1);
    CHECK_INPUT(input2);
    CHECK_INPUT(index);
    return ScoreData_backward_ongpu(grad_output1, input1, input2, index);
}


PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("score_forward", &score_cuda_forward, "score forward (CUDA)");
  m.def("score_backward", &score_cuda_backward, "score forward (CUDA)");
}