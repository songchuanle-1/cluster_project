# Population Matched Witness-Coherence Control

- Continue the fixed full TRAIN ideal-physical-mask audit, not a new model.
  Prior result SHA256:
  e930143cfd9476c6336ba4f0a89278a86280d6d15d70450c1de30c7bb73a01c5.
- Select every expression whose status is physical_masks_evaluated in the
  complete source result (49 expressions/40 scenes/all237 nonempty physical
  masks), including all zero and nonzero losses. Eligibility comes from
  geometry/category/support availability, never from the effect magnitude.
- Reuse exact frozen raw files, IDs, categories, GT teacher and scalar-query
  normalization. The coherent arm must reproduce every previous scalar
  physical-mask loss exactly. GT-self is evaluated in both arms.
- Intervention: call the unchanged native support_excess with
  fragmented=True versus default False. Only minimum placement differs:
  one whole-mask coherent physical pair versus point-support-wise witnesses.
  No config coefficient, threshold, label, candidate set or input changes.
- Report losses, signed deltas, exact differences and original1e-6 numerical
  differences, scene/expression denominators and missing controls. There is
  no assumed universal inequality after GT subtraction and no gain threshold.
- A separation is operator-level causal behavior on actual ideal physical
  masks, not captured model predictions, task harm, trained efficacy, true
  witness annotation, novelty certification or admission.
- CPU-only server-6, two threads, diagnostic CUDA hidden, timeout600.
  Preserve M201-BPS and foreign processes; no optimizer or extra GPU task.
