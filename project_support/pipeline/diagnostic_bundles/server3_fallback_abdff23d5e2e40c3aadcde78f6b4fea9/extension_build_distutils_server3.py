"""Build the same frozen extension with setuptools, no Ninja installation."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

ROOT=Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
STAGE=ROOT.parent/'pipeline/server3_fallback_abdff23d'
assert subprocess.check_output(['hostname'],universal_newlines=True,timeout=5).strip()=='sysu311-MS-7C59'
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],universal_newlines=True,timeout=5).strip()=='f8457d3b657e66306a7fce1afb3d81d8ab874669'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',CUDA_HOME='/usr/local/cuda-11.3',
    CC='/usr/bin/gcc-7',CXX='/usr/bin/g++-7',TORCH_CUDA_ARCH_LIST='8.6',
    MAX_JOBS='2',PYTHONDONTWRITEBYTECODE='1')
env['PATH']='/usr/local/cuda-11.3/bin:'+env['PATH']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
sources=sorted((ROOT/'framework/lib/pointgroup_ops/src').rglob('*'))
before={str(p.relative_to(ROOT)):sha(p) for p in sources if p.is_file()}
target=ROOT/'framework/lib/pointgroup_ops/pointgroup_ops_ext.so'
assert not target.exists()
build=STAGE/'pointgroup_build_setuptools_torch112_cu113'
assert not build.exists()
build.mkdir()
code=r'''
import torch
from pathlib import Path
from setuptools import setup
from torch.utils.cpp_extension import BuildExtension,CUDAExtension
root=Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
source=root/'framework/lib/pointgroup_ops/src'
build=root.parent/'pipeline/server3_fallback_abdff23d/pointgroup_build_setuptools_torch112_cu113'
setup(name='pointgroup_ops',ext_modules=[CUDAExtension(name='pointgroup_ops.pointgroup_ops_ext',
    sources=[str(source/n) for n in ('pointgroup_ops.cpp','pointgroup_ops_api.cpp','cuda.cu')],
    extra_compile_args={'cxx':['-g'],'nvcc':['-D__CUDA_NO_HALF_OPERATORS__','-D__CUDA_NO_HALF_CONVERSIONS__','-D__CUDA_NO_HALF2_OPERATORS__']},
    define_macros=[('WITH_CUDA',None)])],cmdclass={'build_ext':BuildExtension.with_options(use_ninja=False)},
    script_args=['build_ext','--build-temp',str(build/'temp'),'--build-lib',str(build/'lib')])
assert not torch.cuda.is_initialized()
print('CPU_BUILD_CUDA_INITIALIZED=False')
'''
process=subprocess.Popen([sys.executable,'-B','-c',code],cwd=str(build),env=env,
    universal_newlines=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
timed_out=False
try:out,err=process.communicate(timeout=600)
except subprocess.TimeoutExpired:
    timed_out=True
    os.killpg(process.pid,signal.SIGTERM)
    try:out,err=process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL)
        out,err=process.communicate(timeout=10)
assert before=={str(p.relative_to(ROOT)):sha(p) for p in sources if p.is_file()}
result={'observed_at':datetime.now(timezone.utc).isoformat(),'returncode':process.returncode,
    'timed_out':timed_out,'source_hashes_unchanged':True,'source_sha256':before,
    'stdout':out[-10000:],'stderr':err[-12000:],'shared_environment_modified':False,'cuda_allocations':0,
    'build_backend':'setuptools with original CUDAExtension; use_ninja=False'}
if process.returncode==0 and not timed_out:
    binaries=list((build/'lib/pointgroup_ops').glob('pointgroup_ops_ext*.so'))
    assert len(binaries)==1 and 'CPU_BUILD_CUDA_INITIALIZED=False' in out
    shutil.copy2(binaries[0],target)
    result.update(installed_path=str(target),extension_sha256=sha(target),built=True)
else:result['built']=False
print('SERVER3_EXTENSION_BUILD_JSON='+json.dumps(result))
raise SystemExit(0 if result['built'] else 1)
