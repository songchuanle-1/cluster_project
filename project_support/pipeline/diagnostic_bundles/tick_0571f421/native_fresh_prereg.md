# Fresh-initialization executability check

- Same independent FLE source/config; no model revision, training, optimizer update or schedule change. Existing M95-weight diagnostic controls remain separate.
- Construct a new native Network with seed1999, then use the EXACT native gorilla.load_checkpoint(...strict=False,map_location='cpu') for cfg.train.pretrain only. Do not reuse diagnostic M95 heads, decoder or cluster weights. The setup-loaded diagnostic object is discarded before construction; source/assets remain guarded.
- Build native optimizer/scheduler from the unchanged YAML but perform zero optimizer steps. Execute fixed groups0,60,101,124 using original build_dataloader training=True,batch2/workers4/persistent_workers=True/file_system transport. Explicitly shut down workers after collection.
- Require two finite full-native loss/backward completions, nonzero message gradient and18surviving point-path parameter gradients; preserve any missing/nonfinite/zero entries and failure. This is an initialization/transport smoke test, not trained efficacy, full-dataset memory safety, exact RNG identity with the entire native training loop, or a new resume.
