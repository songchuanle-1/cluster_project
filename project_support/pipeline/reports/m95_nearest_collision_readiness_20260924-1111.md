# M95 Nearest-Query Collision Readiness

2026-09-24 11:11 Asia/Shanghai. Event continuation of the three stable
diagnosis IDs. One read-only server-6 GPU7 query found external PID 3694608
using 41,996 MiB; GPU7 had 42,023 MiB used, 39,057 MiB free and 100%
instantaneous utilization. No native execution or foreign-process action.

The M95 matcher selects the nearest sampled query independently for each GT
(`loss.py`, lines 365-369). A sampled query may therefore appear in multiple
nearest-GT pairs. This is a separate source-level possibility from expanded
GT-mask misaddressing: it can occur even when every GT has exactly one matched
pair and mask addresses are correct. It also means positive-query counts
must not be confused with matched-pair counts.

The frozen 256-row cause checker now counts rows with nearest collisions and
the extra nearest-GT assignments beyond unique nearest queries, both overall
and by frozen outcome partition. A synthetic two-GT collision with no mask
misbinding exercises this separation. Fifteen checker and nine count-contract
tests pass; changed Python files compile. The checker and test SHA256 values
are recorded in research_work.json.

No collision incidence, native training effect, expression-level causal unit,
resource measurement or admission has been established. Once authorized GPU7
capacity clears, verify runtime/data/checkpoint/producer provenance, capture
the ordered 256 TRAIN rows, then report nearest collisions alongside GT-mask
binding and the existing six-row and four-scene analyses.
