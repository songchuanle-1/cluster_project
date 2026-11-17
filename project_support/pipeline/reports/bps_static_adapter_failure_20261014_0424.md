# Local Static Adapter Encoding Failure

- First current static check returned exit1 before a manifest or any remote
  transfer/diagnostic. Windows default GBK could not decode existing UTF8
  model source: UnicodeDecodeError, byte0xa8/position79.
- Corrected only static-adapter text readers to explicit UTF8. Existing model
  text/bytes, numerical tolerance, cohort and scientific gates unchanged.
- Not a native/model/scientific rejection or a new preflight. Lease retained.
