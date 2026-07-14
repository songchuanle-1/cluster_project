
"""ClusterAttention vs Self-Attention 效率对比

用法:
  conda activate cluster
  cd /data/songcl/3dres/Cluster_project2/Cluster
  python tools/bench_cluster_att.py
"""
import torch, torch.nn as nn, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def gpu_mem():
    return torch.cuda.memory_allocated() / 1024**2

def peak_mem():
    return torch.cuda.max_memory_allocated() / 1024**2

def reset_mem():
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.empty_cache()

class SelfAttn(nn.Module):
    def __init__(self, dm=256, nh=8):
        super().__init__()
        self.nh, self.dk = nh, dm // nh
        self.scale = self.dk ** -0.5
        self.wq = nn.Linear(dm, dm, bias=False)
        self.wk = nn.Linear(dm, dm, bias=False)
        self.wv = nn.Linear(dm, dm, bias=False)
        self.wo = nn.Linear(dm, dm, bias=False)
    def forward(self, x):
        B,N,C = x.shape
        q = self.wq(x).view(B,N,self.nh,self.dk).transpose(1,2)
        k = self.wk(x).view(B,N,self.nh,self.dk).transpose(1,2)
        v = self.wv(x).view(B,N,self.nh,self.dk).transpose(1,2)
        a = (q@k.transpose(-2,-1))*self.scale
        a = a.softmax(-1)
        o = (a@v).transpose(1,2).reshape(B,N,C)
        return self.wo(o)

class ClusterAttn(nn.Module):
    def __init__(self, dm=256, nh=8, tk=4):
        super().__init__()
        self.nh, self.dk, self.tk = nh, dm//nh, tk
        self.scale = self.dk ** -0.5
        self.wq = nn.Linear(dm, dm, bias=False)
        self.wk = nn.Linear(dm, dm, bias=False)
        self.wv = nn.Linear(dm, dm, bias=False)
        self.wo = nn.Linear(dm, dm, bias=False)
    def forward(self, x, idx):
        B,N,C=x.shape
        H,D,K=self.nh,self.dk,self.tk
        q=self.wq(x).view(B,N,H,D).transpose(1,2)
        k=self.wk(x).view(B,N,H,D).transpose(1,2)
        v=self.wv(x).view(B,N,H,D).transpose(1,2)
        idx=idx.permute(0,3,1,2)
        # fix: expand k,v to 5D before gather
        k5=k.unsqueeze(3).expand(-1,-1,-1,K,-1)
        v5=v.unsqueeze(3).expand(-1,-1,-1,K,-1)
        idx5=idx.unsqueeze(-1).expand(-1,-1,-1,-1,D)
        kg=torch.gather(k5,2,idx5)
        vg=torch.gather(v5,2,idx5)
        a=(q.unsqueeze(-2)*kg).sum(-1)*self.scale
        a=a.softmax(-1)
        o=(a.unsqueeze(-1)*vg).sum(-2).transpose(1,2).reshape(B,N,C)
        return self.wo(o)

def bench(m, x, idx=None, warmup=10, niter=50, bwd=False):
    m = m.cuda(); x = x.cuda()
    if idx is not None: idx = idx.cuda()
    for _ in range(warmup):
        y = m(x) if idx is None else m(x, idx)
        if bwd: y.sum().backward(); m.zero_grad()
    torch.cuda.synchronize()
    reset_mem(); torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(niter):
        y = m(x) if idx is None else m(x, idx)
        if bwd: y.sum().backward(); m.zero_grad()
    torch.cuda.synchronize()
    t = (time.perf_counter()-t0)/niter*1000
    m_mb = peak_mem()
    p = sum(p.numel() for p in m.parameters())
    return {"ms": t, "mem": m_mb, "params": p}

def main():
    if not torch.cuda.is_available():
        print("No CUDA"); return
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    dm, nh, B = 256, 8, 1

    sep = "-"*75
    # 1. 序列长度扫描
    print("\n"+"="*75)
    print("1. 序列长度扩展性 (K=4, B=1, forward+backward)")
    print("="*75)
    print(f"{'config':<35} {'time_ms':>10} {'mem_mb':>10} {'params':>10}")
    print(sep)
    for N in [512,1024,2048,4096,8192]:
        x = torch.randn(B,N,dm)
        xb = torch.randn(B,N,dm,requires_grad=True)
        idx = torch.randint(0,N,(B,N,4,nh))
        # self-attn
        try:
            r = bench(SelfAttn(dm,nh), xb, bwd=True)
            print(f"{'SelfAttn  N='+str(N):<35} {r['ms']:>10.2f} {r['mem']:>10.1f} {r['params']:>10,}")
        except RuntimeError as e:
            print(f"{'SelfAttn  N='+str(N):<35} {'OOM':>10}")
        # cluster-attn
        try:
            r = bench(ClusterAttn(dm,nh,4), xb, idx, bwd=True)
            print(f"{'Cluster   N='+str(N)+' K=4':<35} {r['ms']:>10.2f} {r['mem']:>10.1f} {r['params']:>10,}")
        except RuntimeError as e:
            print(f"{'Cluster   N='+str(N)+' K=4':<35} {'OOM':>10}")

    # 2. top-K 扫描
    print("\n"+"="*75)
    print("2. Top-K 影响 (N=4096, forward only)")
    print("="*75)
    print(f"{'config':<35} {'time_ms':>10} {'mem_mb':>10} {'params':>10}")
    print(sep)
    N=4096; x=torch.randn(B,N,dm)
    for tk in [1,2,4,8,16]:
        idx=torch.randint(0,N,(B,N,tk,nh))
        r=bench(ClusterAttn(dm,nh,tk),x,idx,bwd=False)
        print(f"{'Cluster K='+str(tk)+' dens='+f'{tk/N*100:.2f}%':<35} {r['ms']:>10.2f} {r['mem']:>10.1f} {r['params']:>10,}")
    r=bench(SelfAttn(dm,nh),x,bwd=False)
    print(f"{'SelfAttn (dense 100%)':<35} {r['ms']:>10.2f} {r['mem']:>10.1f} {r['params']:>10,}")

    # 3. fwd vs fwd+bwd
    print("\n"+"="*75)
    print("3. Forward vs Forward+Backward (N=4096, K=4)")
    print("="*75)
    print(f"{'config':<35} {'time_ms':>10} {'mem_mb':>10}")
    print(sep)
    N=4096; xf=torch.randn(B,N,dm); xb=torch.randn(B,N,dm,requires_grad=True)
    idx=torch.randint(0,N,(B,N,4,nh))
    for name,m,x_use,bwd in [("SelfAttn  fwd",SelfAttn(dm,nh),xf,False),
                               ("SelfAttn  fwd+bwd",SelfAttn(dm,nh),xb,True),
                               ("Cluster   fwd",ClusterAttn(dm,nh,4),xf,False),
                               ("Cluster   fwd+bwd",ClusterAttn(dm,nh,4),xb,True)]:
        r=bench(m, x_use, idx if "Cluster" in name else None, bwd=bwd)
        print(f"{name:<35} {r['ms']:>10.2f} {r['mem']:>10.1f}")

    # 4. 汇总
    print("\n"+"="*75)
    print("4. 汇总 (N=4096, K=4)")
    print("="*75)
    sa_f = bench(SelfAttn(dm,nh), xf, bwd=False)
    ca_f = bench(ClusterAttn(dm,nh,4), xf, idx, bwd=False)
    sa_b = bench(SelfAttn(dm,nh), xb, bwd=True)
    ca_b = bench(ClusterAttn(dm,nh,4), xb, idx, bwd=True)
    print(f"  Forward:    SelfAttn={sa_f['ms']:.1f}ms/{sa_f['mem']:.0f}MB  Cluster={ca_f['ms']:.1f}ms/{ca_f['mem']:.0f}MB  speedup={sa_f['ms']/ca_f['ms']:.1f}x  mem_save={sa_f['mem']/ca_f['mem']:.1f}x")
    print(f"  Fwd+Bwd:    SelfAttn={sa_b['ms']:.1f}ms/{sa_b['mem']:.0f}MB  Cluster={ca_b['ms']:.1f}ms/{ca_b['mem']:.0f}MB  speedup={sa_b['ms']/ca_b['ms']:.1f}x  mem_save={sa_b['mem']/ca_b['mem']:.1f}x")

if __name__=="__main__":
    main()
