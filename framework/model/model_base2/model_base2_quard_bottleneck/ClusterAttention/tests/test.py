import torch



def com(query, key, value, index):
    q = query[0,0,0,:]
    ind = index[0,0,:,0]
    k = key[0,ind,0,:]
    v = value[0,ind,0,:]
    sums = []
    for a in range(len(k)):
        sum=0
        for i in range(len(q)):
            sum+= q[i]*k[a,i]
        sums.append(sum)
    weights = torch.stack(sums)

    sums = []
    for a in range(len(k)):
        sum= weights[a]*v[a]
        sums.append(sum)
    sums = torch.stack(sums)
    sums = sums.sum(0)
    return weights,sums



def com_mamtul(query, key, value, index):
    q = query[0,0,0,:]
    ind = index[0,0,:,0]
    k = key[0,ind,0,:]
    v = value[0,ind,0,:]
    weights = torch.matmul(k.unsqueeze(0), q)
    sums = torch.matmul(weights.unsqueeze(0), v)
    return weights,sums


