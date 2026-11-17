# M95 Repeated-GT Count Rule

2026-09-24 10:12 Asia/Shanghai. Event continuation of the three stable
diagnosis IDs. Read-only server-6 GPU7 observation: external PID 3694608
uses 41,996 MiB; 42,023 MiB used, 39,057 MiB free and instantaneous
utilization 100%. No native execution, sync or external-process action.

In the reviewed M95 loss source (SHA256
`c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5`),
the matcher emits one nearest query per GT in GT order, followed by further
instance-member queries. Masks are expanded in GT order by match counts
`c_g >= 1`, but `loss_masks` indexes that expansion by the unexpanded GT ID.
The expanded block for GT `g` starts at `g + sum_{h<g}(c_h-1)`. Thus all
`c_g` pairs for GT `g` address a wrong mask exactly when some earlier GT has
more than one match. A repeated last GT alone cannot misbind a mask; an
earlier repeat corrupts every subsequent GT's mask target. Pair order affects
which query is harmed, not the number of wrong pairs per GT.

This is a falsifiable source-bound prediction for the ordered 256-row native
capture, not an observed mismatch rate. Exhaustive synthetic counts for
one to four GTs with one to three matches each agree with explicit address
reconstruction; 30 focused count, checker and producer tests pass. The
native producer must first pass checkpoint, data, runtime and provenance
checks. Then compare captured ordered pairs against this count rule and
separately report the six exclusion and seven within-positive rows.

No expression-level causal unit, intervention effect, efficacy, resource
measurement, native backward or admission follows. Keep all three IDs at
diagnosis and the two queue slots empty.
