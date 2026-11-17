# Diagnostic implementation details, frozen before CPU execution

- This is not an admitted-model change. The exact admitted fine_exchange.py provides graph construction/native-output reference. This diagnostic reuses the same arithmetic to capture probabilities/self weights.
- R is stored as native U minus the self term. The separately computed nonself weighted sum must agree at the preregistered tolerance. Intervention output is native U plus (R_replacement minus R),retaining the native summation's rounding residual;identity is therefore exactly native rather than a reordered sum.
- Norm matching is per recipient/head,which also preserves each recipient's whole-vector norm. Eligible donors have strictly positive norm;no numerical cutoff/temperature was tuned. Coordinate-lexicographic cyclic order makes the reassignment independent of storage order.
- An exact coordinate tie in an eligible group uses its symmetric mean as donor. A zero donor cannot be norm-rescaled and retains the original vector;the result is explicitly marked an uninformative identity. The original operator's separate cutoff-tie leaf-mean rule is unchanged.
- CPU contracts include the ragged padded wrapper and C256float32 source/identity checks. Actual native replay remains pending until an authorized exclusive slot exists;CPU analytical fixtures cannot supply trained task evidence.
