NDE M233 implementation revision1 native preparation
===================================================

Source0747f6acec1c61018ec99acf2efa5329c9b3523c, parent/runtimef6257de79148581334ee495e6e2d60ccb525457c. Original46adb90573118902d0a7c7723ce8817a085f38b9 and its original10.036472908G resource failure remain retained. This is the same stable candidate, not a new candidate or an admission.

The revision changes only distribution_embedding.py among the original9 source/config files. At all3 existing analysis stages it factors the first original Linear into its child/parent weight halves, projects each unique parent before the same true-parent gather, adds the original first bias exactly once, then applies the unchanged per-child GELU and second Linear before the original mean. Parameter registration/names/shapes/random draws remain unchanged.

worker.py preserves the original native two TRAIN steps, data, seed1999, common835 observation, loss, finite backward, whole-core aggregate gradient and real weight/module update checks. Three-argument module hooks observe actual child input, unique normalized parent, original weight slices, three actual F.linear operations, parent projection before gather, affine sum, original GELU and second Linear. Passthrough wrappers call originals once and return original objects. resources() and exception_frame_metadata() AST are exact copies of original0d3bac worker. No resource counter, protocol, budget, FP32/per-row-nonzero/minimum-effect gate changed.

No Torch/model/forward/autograd/GPU/native-data/resource execution occurred while preparing this packet. Independent review is pending. The source and native runtime are execution-disabled, template10 execution fields are NULL, and no native_manifest, lease, binding, release, request or stage has been created here.

After actual independent review, the parent must create a separate current-owner operational bundle and bind actual owner/deadline/context/pending/source/runtime/root/GPU UUID/producer hashes. Only the reviewed renderer may enable that operational copy. The native commands remain:

    python -B worker.py --lease <fresh reviewed lease> --mode smoke --target candidate
    python -B worker.py --lease <fresh reviewed lease> --mode resources --target candidate
    python -B worker.py --lease <fresh reviewed lease> --mode resources --target champion

Champion smoke support is retained, but this packet does not require rerunning a valid unchanged historical champion smoke. Any reuse must retain its real previous-owner provenance and original candidate/source binding, plus exact M95 source/YAML/protocol/common835/batch fingerprints. It must never be retokened or represented as this owner executing it.

The optional revision-specific equivalence_diagnostic.py is a separate default-disabled entry point. It never alters worker.py's smoke/resources mode whitelist or its original TRAIN2, and never uses native TRAIN batches. It uses the same native_runtime.acquire/verify/release guard, actual GPU0 UUID, original20000MiB minimum remaining memory and three cooperative locks; no execution is authorized by its existence. A separate reviewed fresh-owner request is necessary before executing it:

    python -B equivalence_diagnostic.py --lease <fresh reviewed lease>

This constructed-core diagnostic compares original46 and revision1 initial states/RNG consumption, all3 outputs/analysis outputs, point/bank and every original parameter gradient, and one identical YAML AdamW update with Torch's unchanged dtype-default assert_close tolerances. Fixed unequal/repeated/unsorted/unsupported/padded/empty and singleton fixtures and wrong-parent controls are preselected; all RNG is restored. It preserves failures and an insensitive negative control as failures/inconclusive without resampling or tolerance relaxation. It explicitly reports its auxiliary backward as true, separately from original native smoke's unchanged false field.

This entry point uses GPU0 under the existing guard. A CPU-only adapter would require its own separately reviewed binding and must state that CPU equivalence does not establish GPU equivalence. This packet supplies no CPU adapter and claims no executed equivalence or counter result. Constructed-core agreement cannot establish full native mask/criterion/task-loss equivalence or training efficacy. Native candidate smoke/resources and any missing champion resources remain real unexecuted checks.
