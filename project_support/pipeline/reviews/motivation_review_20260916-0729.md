# Motivation Review - Target-Supervised Latent Relation Contract
2026-09-16 07:29 Asia/Shanghai. Reference computation, not a new variant.

## 1. Goal
pipeline/goal.json remains authoritative:14constraints11bans, target .51,
ledgerchampion .5020, exactchampion .5024607181549072.
No change to novelty, schedule, resource or deployment requirements.

## 2. Story Status
The category-set-only objective has unobserved within-category directions.
That result does NOT imply that complete target-supervised models cannot learn
auxiliary relations without anchor annotations. Keep these claims separate.

## 3. Experiment Assessment
No new native training results. All earlier rejected mechanisms stay rejected.
The recent boundary audit establishes ownership/anchor ambiguity, not
impossibility of end-to-end latent learning. NS3D original sections3.3-3.4
explicitly learn relations with target/category supervision without relation GT.

## 4. Gap Analysis
A reference complete scalar computation is:
p(i,j)=exp(u_i+a_j+R_ij)/sum_ab exp(u_a+a_b+R_ab);
q_i=sum_j p(i,j); L=-log q_y.
Then dL/dR_ij=p(i,j)-1[i=y]p(j|y) and
dL/da_j=p(j)-p(j|y).
Thus target labels can supervise the latent anchor branch.
For R_ij=b_i+c_j, q is independent of anchor logits and their gradient vanishes.
Simultaneous anchor permutations preserve the target likelihood; shifting a_j
by c_j and subtracting c_j from R_ij is another parameter nonidentifiability.
Nonzero gradients therefore do not establish intended-anchor semantics.

## 5. Design Rationale
Executed seven static contracts including nine finite-difference partials;
maximum error8.164e-12. No native model, optimization or efficacy claim.
This calculation is a standard latent-pair likelihood, not novel research.
It is not an admitted ranking/CPS successor and must not be enqueued.
The purpose is to remove an unsupported universal rejection condition:
auxiliary anchor truth is not mandatory for every future trainable architecture.
Novelty, meaningful controls, native backward and full resource gates remain.
Search tool returned no content twice; relied on already archived primary NS3D
text, not absence of search results as novelty evidence.

## 6. Next Batch
Proceed from the existing stable coverage hypothesis to a complete distinct
instance-conditioned computation. Compare its full forward/loss to NS3D,
InstAlign and HCF-RES; avoid another bare category/set/mixture reference test.
Do not add a synthetic one-step-IoU or fully-identified-anchor gate.
Independent production implementation is still pending a defensible core design.
