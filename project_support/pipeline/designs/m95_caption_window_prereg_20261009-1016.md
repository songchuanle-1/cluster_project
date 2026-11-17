# Native Caption Window Preregistration

- Stable candidate: m95-native-caption-window-loss; tick e3d3340fabdd45bb9fc636e57be24156.
- Hypothesis: the configured max_des_len=78 truncates native referent/relational context, so a structural chunk-preserving text readout could recover unavailable evidence. This is independent of spatial mask event supervision.
- First test: inspect actual native tokenizer call arguments, then execute the same tokenizer batch call on the original frozen full TRAIN annotations and verify tokens beyond78 are retained unchanged. Compare the deliberately truncated78-token control, not a guessed configuration effect.
- Rejection: reject this window-loss realization if the native collator does not truncate at78 and retains all eligible original tokens. Retain any distinct 256-positive-map or model-context overflow issue as a separately reported limitation, not evidence of this claimed78-window deficit.
- Freeze: whole original TRAIN annotation file hash018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d; canonical dataset source hash2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d. No prediction or correctness selection.
- Matched control: original normalized utterance with native appended ". not mentioned", same tokenizer/cache, explicit truncation=True,max_length=78 only in control.
- Native diagnostic CPU on server6; CUDA disabled; no optimization/training. A direct max-length configuration increase would be tuning, not an admissible structural experiment.
- Existing token-span-integrity failures remain unchanged; this tests actual context truncation rather than graph-span parsing.
