# M216-AEF implementation (source/static only)

The five M95 files __init__/backbone/loss/network/sample_model are exact primary
copies. The independent dec/hier files use the already tested primaryCTS geometry
cache plumbing, without changing its FPS/rawmean/IDs/CSORT/HCG algorithms. Cached
positions are exactly original per_layer_coords[2].detach (fine-mean then middle-
mean coordinates), not a new point-weighted pooling. True support is ids1[ids0].
The cache is reset and identity-bound to current ids2 eachforward. Unsupported
rows and batch padding never become MST nodes or transmit a bias.

Only middle FFN is replaced after original3FFN/3LN construction. Oldmiddle FFN1
is replaced by Identity, removing its registered525568parameters; newedge_map is
constructed in torch.random.fork_rng(devices=[]), defaultLinear initialization,
no manual_seed/init search. Originalmiddle LN and sole original cfskip remain.
Fine/coarse FFN/skip and original dropout0 are retained; wrong3level/dropout fails.

Production build_parent_mst is pure metadata code. Parent IDs are not reindexed;
supported originalmiddle rows are grouped by originalids2. Prim starts from the
smallest originalID. Each candidate edge key is (squaredEuclidean distance,
min_originalID,max_originalID); the smallest key is chosen, so all ties are
deterministic. Distinct nodes at zero displacement are legal. Every nonempty
group yields n-1 edges. Pureplan accepts abstract metadata sizes; production
operator enforces originalcfg middle/coarse capacities (native64/8), not a tuned
new cap. Invalid lengths/types/negativeIDs/nonfinitecoords failclosed.

Actual forward gathers both endpoint states from the same normalized input,
packs all E forward orientations followed by E reverse orientations into one
sharedLinear/GELU call, subtracts the two output halves, then functional
index_add left +q/right -q. Features are never detached. No summary/node state
iteration, gate, QKV, routing, learnedscalar or addedresidual exists. n0/n1/empty
support yields zero delta, so those middle rows retain rawcf through originalskip.
This is not a fallback FFN and is a material changed boundary.

C256 source-only parameter inference: Linear(512,256) has131328parameters,
replacing oldmiddle FFN525568, net-394240. Originalthree FFN total1576704 becomes
1182464 across unchangedfine/coarse+AEF. This is not measured fullmodel inventory.
Linear work is4*E*C^2 vs original8*K*C^2, with E<=supportedK-nonemptyparents.
MST metadata is O(sum parent_n^2), O(sum parent_n) working memory; native totalK64.
No pointN^2 matrix/attention is created. Actual totalFLOPs/unsupportedops/CPUlatency/
memory and gradient amplification are UNKNOWN.

Actual software command is recorded in static_validation_run1.json. It executes
the real production builder extracted by AST against independent Kruskal oracle:
129 sizes n0..128 plus7 boundarycases,12 invalid refusals,850assertions including
source/YAML/AST/path checks. n>64 is abstract metadata stress, not native128.
Integer arbitraryflux incidence verifies the algebra on actual producededges,
not Torch32 GELU or learned behavior. Actualforward was source-inspected only;
the independent reviewer may execute a stdlib symboliccarrier separately.
No Torch/model/native/GPU/Git/SSH or sharedsource/ledger operation occurred.
