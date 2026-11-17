"""Magnitude-matched spatial reassignment; measurement only."""
import math

def fixture(values,valid,identity=False):
    result=[list(row) for row in values]
    if identity:return result
    assert valid>1
    for i in range(valid):
        source=values[(i+1)%valid]
        source_norm=math.sqrt(sum(v*v for v in source))
        target_norm=math.sqrt(sum(v*v for v in values[i]))
        assert source_norm>0 and target_norm>0,"Degenerate zero direction"
        result[i]=[v*target_norm/source_norm for v in source]
    return result

def cpu_controls():
    values=[[3.0,4.0],[0.0,2.0],[6.0,8.0],[0.0,0.0]]
    changed=fixture(values,3)
    assert sorted((i+1)%3 for i in range(3))==list(range(3))
    assert all(abs(sum(v*v for v in changed[i])-sum(v*v for v in values[i]))<1e-12 for i in range(3))
    checks=[{"name":"cyclic_bijection_and_recipient_norm","passed":True}]
    assert changed[3]==values[3]
    checks.append({"name":"padding_unchanged","passed":True})
    assert fixture(values,3,identity=True)==values
    checks.append({"name":"identity_exact","passed":True})
    try:fixture([[0.0,0.0],[1.0,0.0]],2)
    except AssertionError:pass
    else:raise AssertionError("Zero direction guard missing")
    checks.append({"name":"zero_direction_guard","passed":True})
    return {"passed":True,"checks":checks,"native_forwards":0,"optimizer_steps":0}

def permute_message(torch,message,padding,identity=False):
    result=message.detach().clone()
    if identity:
        assert torch.equal(result,message)
        return result,{"identity_exact":True}
    errors=[];counts=[]
    for b in range(message.shape[0]):
        indices=(~padding[b]).nonzero(as_tuple=False).flatten()
        assert len(indices)>1
        source=indices.roll(-1)
        assert torch.equal(source.sort()[0],indices.sort()[0])
        original=message[b,indices]
        shifted=message[b,source]
        target_norm=original.norm(dim=-1,keepdim=True)
        source_norm=shifted.norm(dim=-1,keepdim=True)
        assert bool((target_norm>0).all()) and bool((source_norm>0).all()),"Degenerate zero direction"
        result[b,indices]=shifted*(target_norm/source_norm)
        error=float(((result[b,indices].norm(dim=-1,keepdim=True)-target_norm).abs()/target_norm).max().cpu())
        assert error<=1e-6,error
        assert torch.equal(result[b,padding[b]],message[b,padding[b]])
        errors.append(error);counts.append(len(indices))
    return result,{"maximum_relative_norm_error":max(errors),"bijection_valid_counts":counts,"padding_exact":True}
