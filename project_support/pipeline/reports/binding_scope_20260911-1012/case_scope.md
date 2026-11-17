# Fixed Description Scope Notes

Text-only applicability notes authored with prior outcomes already known; not blinded/independent annotations or scene-grounded causal labels.

Require at least two explicit target-to-anchor predicates with the same coreferent anchor to confirm narrow shared-witness eligibility. Nested chains, distinct/plural anchors, unary attributes do not qualify automatically. Ambiguous attachment/frame stays unknown. No object synonym or typo correction.

## Errors

### scene0578_00/5/36
the chair is around the table. it is on the right side and is the one in the front.

Scope: scope_ambiguous. Only around explicitly names table; right/front reference frame and attachment unspecified.

| Mention | Exact-label non-target object candidates |
|---|---|
| table | ['10', '11'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0208_00/0/20
the bookshelf is located on the right wall. it extends the length of the wall, and meets another bookshelf in the corner that extends perpendicular to it.

Scope: different_referents. Wall extent and another bookshelf are distinct mentions; it attachment needs adjudication.

| Mention | Exact-label non-target object candidates |
|---|---|
| wall | ['5', '6', '14'] |
| bookshelf | ['1', '2', '3', '106'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0328_00/24/52
the kitchen cabinet is right of the stove. the kitchen cabinet is a dark brown rectangular prism.

Scope: single_relation. One explicit target-anchor predicate; appearance is unary, not a second table/stove relation.

| Mention | Exact-label non-target object candidates |
|---|---|
| stove | missing_exact_label_match |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0621_00/2/85
this table is in the middle. it is square.

Scope: unary_or_scene_relative. Middle lacks specified comparison domain; square is unary shape.

| Mention | Exact-label non-target object candidates |
|---|---|

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0334_00/5/23
there is a donut shaped brown coffee table. it is next to a couch.

Scope: single_relation. One explicit relation plus unary shape/color; two couch candidates not resolved by noun.

| Mention | Exact-label non-target object candidates |
|---|---|
| couch | ['2', '3'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0621_00/22/68
the chair is a dark color. it is the chair with wheels that is at the table closest to the open door.

Scope: nested_chain. At(chair,table) and closest(table,door) share an intermediate table, not two factors of the same target-anchor pair.

| Mention | Exact-label non-target object candidates |
|---|---|
| table | ['0', '1', '2', '3', '4'] |
| door | ['12'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0146_00/16/8
this is a rectangular toilet paper dispenser. it is to the left of the toilet.

Scope: single_relation. Toilet in target noun is not an extra anchor mention; one left predicate.

| Mention | Exact-label non-target object candidates |
|---|---|
| toilet | ['5'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0249_00/23/41
this is a blue and white recycling trash can. its next to a brown box in front of the entry way.

Scope: different_referents_attachment_ambiguous. Front may modify box or target; box and entry way are distinct mentions either way.

| Mention | Exact-label non-target object candidates |
|---|---|
| box | missing_exact_label_match |
| entry way | missing_exact_label_match |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0046_00/26/27
an open white entry door. just in front of the toliet.

Scope: single_relation. Preserve misspelling; no silent mapping to toilet; viewpoint missing.

| Mention | Exact-label non-target object candidates |
|---|---|
| toliet | missing_exact_label_match |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0426_00/22/24
there is a large brown pillow. it is on the bed behind the pile of blankets.

Scope: different_referents_attachment_ambiguous. Behind may modify bed or pillow; no same-anchor conjunction established.

| Mention | Exact-label non-target object candidates |
|---|---|
| bed | ['24'] |
| pile of blankets | missing_exact_label_match |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0591_00/14/22
the pillow is orange. it is laying on the black couch.

Scope: single_relation. One anchor relation plus color; do not assume on(couch) distinguishes the two pillows.

| Mention | Exact-label non-target object candidates |
|---|---|
| couch | ['0'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0652_00/6/33
there is a wooden filing cabinet. it is the taller of the two.

Scope: comparison_domain_missing. The second comparison object is not named; cabinet/dresser ontology cannot be merged silently.

| Mention | Exact-label non-target object candidates |
|---|---|

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

## Controls

### scene0578_00/11/38
the table is in the middle of the room. it is brown.

Scope: unary_or_scene_relative. Room is a scene domain, not necessarily an annotated object.

| Mention | Exact-label non-target object candidates |
|---|---|
| room | missing_exact_label_match |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0328_00/17/12
black and silver microwave that is above the oven. it has two cabinets to the right and left that it sits in between that are closed.

Scope: distinct_plural_anchors. Two cabinet instances are distinct by explicit cardinality; between is higher arity.

| Mention | Exact-label non-target object candidates |
|---|---|
| oven | ['0'] |
| cabinets | missing_exact_label_match |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0334_00/7/16
this is a brown bench. it is to the left of another brown bench.

Scope: single_relation. Another bench explicitly excludes the target, without asserting its physical ID.

| Mention | Exact-label non-target object candidates |
|---|---|
| bench | ['8'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0146_00/12/19
the wall soap dispenser. the dispenser is right of the sink.

Scope: single_relation. One explicit right relation; wall in noun context not automatically another predicate.

| Mention | Exact-label non-target object candidates |
|---|---|
| sink | ['6'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0249_00/24/52
this is a long table. it is in the center of the room.

Scope: unary_or_scene_relative. Long is unary; center domain/frame remains unspecified.

| Mention | Exact-label non-target object candidates |
|---|---|
| room | missing_exact_label_match |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0046_00/26/34
this door is the bathroom door and it's open. the color of the door is white.

Scope: unary_or_scene_relative. Open/color/type are unary; no explicit binary target-anchor relation.

| Mention | Exact-label non-target object candidates |
|---|---|

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0426_00/24/15
this is a bed in a bedroom.  it is against the wall under the window.

Scope: different_referents. Two predicates use different object mentions, not one shared witness.

| Mention | Exact-label non-target object candidates |
|---|---|
| wall | ['13', '15', '18', '19', '21', '29'] |
| window | ['14'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0591_00/25/30
there is a rectangular window. it is behind a desk with monitors.

Scope: nested_chain. Behind(window,desk) plus with(desk,monitors); no same-pair conjunction established.

| Mention | Exact-label non-target object candidates |
|---|---|
| desk | ['5', '19'] |
| monitors | missing_exact_label_match |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

### scene0652_00/25/11
this is a wall mounted television set. it is above the black dresser in the room.

Scope: single_relation. One explicit above relation; wall-mounted is not a second dresser relation.

| Mention | Exact-label non-target object candidates |
|---|---|
| dresser | ['27'] |

Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.

