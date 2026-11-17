# M95 Explicit Contact-Language Diagnostic Preregistration

Stable ID `m95-contact-support-relation`. This independent, read-only TRAIN
screen asks whether descriptions that explicitly specify physical support
or contact have a distinct deployed failure pattern. This is not a generic
relation head, geometry threshold, mask selector or training proposal.

Use exactly the manifest, native TRAIN descriptions and deployed outcomes
bound in `m95_color_language_screen_20260926-1618.json` (SHA256
`44b6833d717401b691236e14f42a3849b6b66ebc466ab3ee4cfb195b7bc007a`).
Join on scene, annotation and target object, rejecting missing/duplicate
matches. Feature computation must precede outcome inspection.

The fixed contact phrase set, case-insensitive with word boundaries:
`on top of`, `on the top of`, `sitting on`, `standing on`, `resting on`,
`under`, `underneath`, `below`, `against`, `attached to`, `hanging from`,
`leaning against`. Do not count bare `on`, `next to`, or `near`.
Control: fixed noncontact directional phrases `left`, `right`, `front`,
`behind`, `near`, `next`. Report contact incidence and failure rate in
128 ambiguous and 128 class-unique rows, the 16 no-acceptable-mask rows,
and same-scene contact-discordant pairs. A lack of contact-bearing
failures or no enrichment against within-stratum controls rejects this
diagnostic route. Association alone never passes admission: any signal
would require target-blind scene contact-graph extraction, a same-scene
shuffled-contact native control, a differentiable structural path and the
other hard gates. Do not reuse a closed generic relation or selector
proposal under this name.
