# M95 Capture Header Correction

2026-09-24 17:17 Asia/Shanghai. Post-receipt provenance inspection found
that the exclusion-cause checker expected SHA256
1980ac6fe2731dd5cd3b03194e1529905562e4eeceaac04b96823f6de5da131f
as the native capture manifest header, but the native producer records the
preregistered manifest SHA256
4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023.
The checker now requires the producer's actual manifest identity. A synthetic
capture carrying the former analysis hash is rejected. The previous checker
would have rejected a valid native capture.

38 focused synthetic M95 tests pass. No native execution, training, queue
admission or deployment occurred. The three existing diagnosis IDs remain
blocked by external GPU7 occupancy. Resume the ordered native capture only
after authorized capacity, runtime and provenance are verified.
