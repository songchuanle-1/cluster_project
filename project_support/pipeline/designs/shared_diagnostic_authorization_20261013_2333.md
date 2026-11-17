# Shared Diagnostic Authorization

- User explicitly directed "够就继续实验啊" after being told GPU7 has
  approximately78GiB free and that the previous guard required no other process.
  This authorizes continuing these diagnostics with sufficient memory while
  preserving resident jobs; it does not authorize eviction, other GPUs, a new
  training variant, altered science gates or scheduler changes.
- Existing frozen role adapter SHA
  d01eab84334844e45c83b9aa0af437848a255203e4aeaf32e72c146ce220c7a0
  stays unchanged: original model/checkpoint/config,16groups64expressions plus
  original first control,2seed1999 trials,strict1e-6,EOS-isolated control.
- Its existing PyTorch allocator fraction0.25 remains unchanged, approximately
 20GiB on this card; this is an allocator cap, not a measured process peak.
  The shared guard requires at least32GiB free, checks exact hostname/UUID and
  acquires both project diagnostic flocks. These flocks serialize this project's
  diagnostics, not foreign processes. Project preflight has0active tasks.
- Original exclusive guard and prior reports remain intact. New shared guard
  records resident processes before/after and runs with600second timeout.
  No foreign process is killed or modified.
- Shared results can diagnose same-forward losses and projected gradients.
  They cannot certify exclusive latency/memory efficiency, trained efficacy,
  new-core independence or full native parameter-backward admission.
- Token3b60320eabb148289911c480f7649b8c; snapshot2026-10-13T15:33:14.570811Z,
  original deadline2026-10-13T16:33:14.570811Z.
- Existing relation adapter SHA
  63e9d86ae227ef82a84152b9fdca77aa886b6f2860e9cd781acb84dbdb320381
  is also retained unchanged. A thin entry wrapper binds its historical TOKEN
  global to this actual tick token, without changing selection or computation.
  Run sequentially after the role diagnostic using the same project flocks,
  memory fraction, free-memory guard and timeout. It retains its first8positive
  scene groups plus original control,2seed1999 trials andstrict1e-6.
