# Native Mask-Center Prototype and Attribution Corrections

- Initial broad inventory scene0005/18 table/table includes an unrelated
  non-BETWEEN table; scene0008/10 chair/window includes a non-BETWEEN chair.
  Their raw pair scores remain archived but are WITHDRAWN as actual two-role
  BETWEEN binding evidence. Typed direct-role inventory is separate.
- The strict support-gap slab is a proposed proxy, NOT proved necessary or
  sufficient for natural-language BETWEEN. Withdraw earlier "necessary"
  wording; preserve its pre-registration/raw results, no silent replacement.
- Freeze ALL8typed native groups and every companion expression from manifest
  between_pair_typed_66fa1e81aec94d5eb10265ea533669ac.manifest.json. No
  prediction selection, scene replacement, seed change or optimizer.
- Group original root BETWEEN edges by their actual stored relation_idx
  positions whose utterance token is "between". Different events stay
  separate. One plural node alone does not identify two physical roles;
  missing candidates/zero reference separation/overlap gaps remain unknown.
- In the unchanged augmented native batch, use native superpoint-majority
  instance labels for reference support points. Report this approximation,
  not exact raw physical witness identity. Define query mask center using
  native point counts and native support coordinate means, not unweighted
  superpoints. Reference IDs remain candidate identities, not true labels.
- For each valid pair p, a_p/b_p are projected reference support gap bounds,
  e_p its oriented axis. Proposed per-event readout:
  h_p(c)=[(relu(a_p-c dot e_p)+relu(c dot e_p-b_p))/(b_p-a_p)]^2;
  L_event=min_p h_p(c); L_grouped=mean_event L_event.
  Compare flat min over all pairs, which can ignore an event, as a diagnostic
  negative control. This is a standalone readout, no selected loss weight.
- Evaluate ALL original positive matched queries for eligible frozen
  expressions, original GT masks and all native non-sentinel instance masks.
  Companion noneligible expressions bypass exactly. Record event schema,
  unavailable events, same-capture loss/mask-gradient repeat1e-6, final-query
  gradient finiteness/nonzero, and actual GT/distractor proxy scores.
- Native forward/checkpoint/config/source frozen; exact final projected
  tensor identity and original loss agreement1e-6. Keep old whole-forward
  strict failures. A prototype on original parameters is not independent
  candidate backward, uniform efficiency, trained efficacy or admission.
- NS3D already includes ternary relation reasoning; EDA already includes
  decoupled dense semantic/position alignment. Neither high arity nor role
  decomposition can be claimed new. Whole-mechanism novelty and independent
  implementation remain unverified; no new training from this probe.
- Shared server-6GPU7 only, das/exactUUID/free>=32768MiB/bothflocks,
  allocator fraction.25/timeout600; preserve foreign processes.
