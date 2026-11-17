"""Analytic diagnostic controls only; no CUDA allocation or native model run."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES="",PYTHONDONTWRITEBYTECODE="1",OMP_NUM_THREADS="1")
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import torch
from neighbor_content import decompose,intervention,permute_nonself,padded_intervention

STAGE=Path(__file__).resolve().parent
manifest=json.loads((STAGE/"cpu_manifest.json").read_text())
source=Path(manifest["operator_path"])
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest["operator_sha256"]
spec=importlib.util.spec_from_file_location("admitted_fle_operator",source)
operator=importlib.util.module_from_spec(spec);spec.loader.exec_module(operator)
torch.set_num_threads(1);torch.manual_seed(1999)
result={"passed":False,"checks":[],"cuda_initialized":False,"native_forwards":0,"optimizer_steps":0}
try:
    for tied in (False,True):
        coordinates=np.zeros((40,3)) if tied else np.arange(120,dtype=np.float64).reshape(40,3)
        leaves=np.zeros(40,dtype=np.int64)
        graph=operator.build_graph(coordinates,leaves)
        x=torch.randn(40,16,dtype=torch.float64,requires_grad=True)
        parts=decompose(x,graph)
        exact=operator.exchange(x,graph)
        source_error=float((parts["original"]-exact).abs().max().detach())
        reconstruction=float((parts["self"]+parts["nonself"]-exact).abs().max().detach())
        assert source_error==0 and reconstruction<=1e-12
        assert float(parts["formula_max_error"].detach())<=1e-12
        if tied:
            assert torch.equal(parts["self_mass"],torch.full_like(parts["self_mass"],1/40))
            assert float((parts["self"]-x/40).abs().max().detach())==0
        identity,receipt=intervention(parts,coordinates,leaves,identity=True)
        assert torch.equal(identity,exact)
        altered,receipt=intervention(parts,coordinates,leaves)
        assert receipt["norm_max_error"]<=1e-12 and receipt["changed_rows"]>0
        permutation=torch.randperm(40)
        pgraph=operator.build_graph(coordinates[permutation],leaves[permutation])
        pparts=decompose(x[permutation],pgraph)
        paltered,_=intervention(pparts,coordinates[permutation],leaves[permutation])
        permutation_error=float((paltered-altered[permutation]).abs().max().detach())
        assert permutation_error<=1e-12
        gradients=torch.autograd.grad(altered.square().sum(),x)[0]
        assert bool(torch.isfinite(gradients).all()) and float(gradients.abs().sum())>0
        result["checks"].append({"case":"tied" if tied else "untied","source_error":source_error,"reconstruction_error":reconstruction,
            "formula_error":float(parts["formula_max_error"].detach()),"permutation_error":permutation_error,"intervention":receipt})
    coords=np.array([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]])
    leaves=np.arange(3)
    x=torch.randn(3,16,dtype=torch.float64,requires_grad=True)
    parts=decompose(x,operator.build_graph(coords,leaves))
    assert torch.equal(parts["original"],x) and torch.count_nonzero(parts["nonself"])==0
    actual,receipt=intervention(parts,coords,leaves)
    assert torch.equal(actual,x) and receipt["changed_rows"]==0
    result["checks"].append({"case":"singleton_zero_nonself","passed":True})
    zeros=torch.zeros(5,16,dtype=torch.float64)
    output,receipt=permute_nonself(zeros,np.arange(15).reshape(5,3),np.zeros(5,dtype=np.int64))
    assert torch.equal(output,zeros) and receipt["changed_rows"]==0
    result["checks"].append({"case":"zero_vectors_no_nan","passed":True})
    opposite=torch.stack([torch.ones(16,dtype=torch.float64),-torch.ones(16,dtype=torch.float64)])
    output,receipt=permute_nonself(opposite,np.zeros((2,3)),np.zeros(2,dtype=np.int64))
    assert torch.equal(output,opposite) and receipt["zero_donor_preserved"]==16
    result["checks"].append({"case":"tied_zero_donor_is_inconclusive_identity","passed":True})
    x=torch.arange(96,dtype=torch.float64).reshape(6,16).sin()
    coords=np.arange(18).reshape(6,3);leaves=np.array([0,0,0,1,1,1])
    a,receipt=permute_nonself(x,coords,leaves)
    b,_=permute_nonself(torch.cat([x[:3],x[3:]*3]),coords,leaves)
    assert torch.equal(a[:3],b[:3])
    result["checks"].append({"case":"cross_leaf_isolation","passed":True})
    x=torch.randn(2,7,16,dtype=torch.float64,requires_grad=True)
    coords=torch.arange(42,dtype=torch.float64).reshape(2,7,3)
    padding=torch.tensor([[False]*7,[False]*4+[True]*3])
    ids=[torch.zeros(7,dtype=torch.long),torch.tensor([0,0,1,1])]
    exact=operator.FineLeafExchange().double()(x,padding,coords,ids)
    normal,identity,receipts=padded_intervention(x,padding,coords,ids,operator.build_graph,identity=True)
    assert torch.equal(normal,exact) and torch.equal(identity,exact)
    assert torch.count_nonzero(normal[1,4:])==0
    _,altered,_=padded_intervention(x,padding,coords,ids,operator.build_graph)
    gradient=torch.autograd.grad(altered.sum(),x)[0]
    assert bool(torch.isfinite(gradient).all()) and torch.count_nonzero(gradient[1,4:])==0
    result["checks"].append({"case":"ragged_padding_exact_admitted_module_and_gradients","passed":True})
    coords=np.arange(120,dtype=float).reshape(40,3);leaves=np.zeros(40,dtype=np.int64)
    x=torch.randn(40,256,dtype=torch.float32)
    graph=operator.build_graph(coords,leaves);parts=decompose(x,graph)
    exact=operator.exchange(x,graph)
    assert torch.equal(parts["original"],exact)
    identity,_=intervention(parts,coords,leaves,identity=True)
    assert torch.equal(identity,exact)
    assert float(parts["formula_max_error"])<=1e-6
    result["checks"].append({"case":"native_channel256_float32_identity","passed":True,"formula_error":float(parts["formula_max_error"])})
    result.update(passed=True,operator_sha256=manifest["operator_sha256"],self_mass_range=[0,1],
        cuda_initialized=torch.cuda.is_initialized(),scientific_status="diagnostic_operator_correctness_only_not_native_trained_effect",new_model_revision=False)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    result["observed_at"]=datetime.now(timezone.utc).isoformat()
    with (STAGE/"cpu_contracts_result.json").open("x") as stream:json.dump(result,stream,indent=2,allow_nan=False)
print("FLE_SELF_NONSELF_CPU_CONTRACTS_PASS")
