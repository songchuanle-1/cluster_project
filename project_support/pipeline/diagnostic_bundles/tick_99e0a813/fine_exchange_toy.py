"""Small source discriminator, not model efficacy or a training implementation."""
import math

def exchange(features,positions,leaves,k=32):
    width=len(features[0]);output=[]
    for i,query in enumerate(features):
        candidates=[j for j in range(len(features)) if leaves[j]==leaves[i]]
        candidates.sort(key=lambda j:(sum((a-b)**2 for a,b in zip(positions[i],positions[j])),j))
        selected=candidates[:min(k,len(candidates))]
        scores=[sum(a*b for a,b in zip(query,features[j]))/math.sqrt(width) for j in selected]
        weights=[math.exp(s-max(scores)) for s in scores];total=sum(weights)
        output.append([sum(w*features[j][c] for w,j in zip(weights,selected))/total for c in range(width)])
    return output

def controls():
    features=[[1.,0.],[0.,1.],[2.,0.],[0.,2.]];positions=[[0.,0.],[1.,0.],[10.,0.],[11.,0.]];leaves=[0,0,1,1]
    broadcast=[[.5,.5],[.5,.5],[1.,1.],[1.,1.]]
    assert broadcast[0]==broadcast[1]
    original=exchange(features,positions,leaves)
    assert original[0]!=original[1]
    changed=[list(v) for v in features];changed[1]=[0.,3.]
    altered=exchange(changed,positions,leaves)
    assert altered[0]!=original[0] and altered[2]==original[2]
    permutation=[1,0,3,2]
    reordered=exchange([features[i] for i in permutation],[positions[i] for i in permutation],[leaves[i] for i in permutation])
    assert all(abs(v-original[index][c])<1e-12 for row,index in zip(reordered,permutation) for c,v in enumerate(row))
    return {"passed":True,"controls":["shared_bank_members_equal","point_outputs_distinct","offdiagonal_dependency_without_crossleaf_leakage","permutation_equivariance"],"original_output":original,"native_backward":"unmeasured","native_efficacy":"unmeasured"}
