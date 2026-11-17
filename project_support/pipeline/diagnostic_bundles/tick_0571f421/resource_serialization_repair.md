# Shape-metadata serialization repair, before candidate retry

- Candidate resource attempt reached result serialization but JIT tracing left the recorded channels dimension as a Tensor. json.dump rejected that metadata. The original execution and partial result remain unchanged and are not counted as a successful measurement.
- Convert only shape-metadata dimensions to Python int at capture. No model, counters, handlers, timing loops, thresholds, precision or input change. A fresh complete retry is required; do not infer missing fields or overwrite the partial JSON.
- This instrumentation repair is not an implementation revision or an HDS change. Retry under candidate_retry1. Runtime locks are released by process exit; live observation and reacquisition remain mandatory.
