#!/usr/bin/env python

import os

from setuptools import setup, find_packages
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

this_file = os.path.dirname(__file__)

# Set CUDA arch list to avoid legacy sm_12 generation and speed up build
# Use TORCH_CUDA_ARCH_LIST in decimal form expected by PyTorch
# Adjust to your GPU: Ampere (8.0/8.6), Ada (8.9)
# Prefer explicit arch list to avoid invalid sm_120 on CUDA 12.x
# Common choices: Ampere A100/RTX30 (8.0/8.6), Ada RTX40 (8.9)
# os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "8.0;8.6;8.9")

exts = []
# if not only_my:
exts.append(
    CUDAExtension(
        "score_computation_cuda",
        [
            "src/score_computation.cpp",
            "src/score_computation_kernal.cu",
        ],
        extra_compile_args={"cxx": ["-g"], "nvcc": ["-O2"]},
        
    )
)
exts.append(
    CUDAExtension(
        "value_aggregation_cuda",
        [
            "src/value_aggregation.cpp", 
            "src/value_aggregation_kernel.cu"
        ],
        extra_compile_args={"cxx": ["-g"], "nvcc": ["-O2"]},

    )
)

# exts.append(
#     CUDAExtension(
#         "my_score_computation_cuda_d",
#         [
#             "src/my_score_computation_d.cpp",
#             "src/my_score_computation_kernal_d.cu",
#         ],
#         extra_compile_args={
#             "cxx": ["-g", "-std=c++17"],
#             "nvcc": [
#                 "-O2",
#                 "--expt-relaxed-constexpr",
#                 "--extended-lambda",
#                 "-Xcompiler",
#                 "-fPIC",
#             ],
#         },
#     )
# )

setup(
    name="cluster_attention_package",
    ext_modules=exts,
    cmdclass={"build_ext": BuildExtension},
)
# python setup.py build_ext --inplace
# python setup.py install  安装到conda包里