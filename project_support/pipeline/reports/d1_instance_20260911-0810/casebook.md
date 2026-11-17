# Fixed Instance-Diagnostic Casebook

Protocol frozen before instance attribution; 12 hash-selected M95 recoverable errors.

Nine unique same-scene successful controls; three missing, no replacement.

Cases were selected on known M95 outcome, not an unbiased subset or causal matched study.

Descriptions and parser text are source records, not verified scene relations.

Semantic IDs are coarse; ID19 maps to NYU40 ID39 in the local dataset code, not an exact noun match.

All boundary/relationship-cause labels remain unknown. No visual adjudication claimed.


## Case 1: scene0578_00/5/36


### Error: scene0578_00/5/36

Source target name: chair.

Source description: the chair is around the table. it is on the right side and is the one in the front.

Parser utterance: the chair is around the table . it is on the right side and is the one in the front .

Parsed predicates: ["around"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.792686 | 0.792686 | target_pass50 | 5 | 4/4 | 0.8079128440366973 | 0.9767764298093587 | 670 | 67 |
| m95 | 0.000000 | 0.849307 | wrong_instance_same_semantic | 7 | 4/4 | 0.0 | 0.0 | 3351 | 2885 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0578_00/11/38

Source target name: table.

Source description: the table is in the middle of the room. it is brown.

Parser utterance: the table is in the middle of the room . it is brown .

Parsed predicates: ["in the middle of"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.791489 | 0.829497 | target_pass50 | 11 | 6/6 | 0.9708041102593378 | 0.8107887208827135 | 179 | 1389 |
| m95 | 0.833661 | 0.895563 | target_pass50 | 11 | 6/6 | 0.9550224887556222 | 0.867729192208146 | 300 | 971 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


## Case 2: scene0208_00/0/20


### Error: scene0208_00/0/20

Source target name: bookshelf.

Source description: the bookshelf is located on the right wall. it extends the length of the wall, and meets another bookshelf in the corner that extends perpendicular to it.

Parser utterance: the bookshelf is located on the right wall . it extends the length of the wall , and meets another bookshelf in the corner that extends perpendicular to it .

Parsed predicates: ["on", "the length of"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.482681 | 0.554994 | no_instance_pass50 | 0 | 9/9 | 0.8914823914823915 | 0.5128117884157354 | 2385 | 18614 |
| m95 | 0.000000 | 0.690269 | wrong_instance_same_semantic | 106 | 9/9 | 0.0 | 0.0 | 47375 | 38207 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


Control missing: no_unused_same_scene_success_in_frozen_sample.


## Case 3: scene0328_00/24/52


### Error: scene0328_00/24/52

Source target name: kitchen_cabinet.

Source description: the kitchen cabinet is right of the stove. the kitchen cabinet is a dark brown rectangular prism.

Parser utterance: the kitchen cabinet is right of the stove . the kitchen cabinet is a dark brown rectangular prism .

Parsed predicates: ["right of"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.973913 | 0.973913 | target_pass50 | 24 | 2/2 | 0.9739130434782609 | 1.0 | 24 | 0 |
| m95 | 0.000000 | 0.967634 | wrong_instance_same_semantic | 21 | 2/2 | 0.0 | 0.0 | 1664 | 896 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0328_00/17/12

Source target name: microwave.

Source description: black and silver microwave that is above the oven. it has two cabinets to the right and left that it sits in between that are closed.

Parser utterance: black and silver microwave that is above the oven . it has two cabinets to the right and left that it sits in between that are closed .

Parsed predicates: ["above", "has", "left sits"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.878196 | 0.878196 | target_pass50 | 17 | None/None | 0.8781965006729475 | 1.0 | 181 | 0 |
| m95 | 0.878196 | 0.878196 | target_pass50 | 17 | None/None | 0.8781965006729475 | 1.0 | 181 | 0 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


## Case 4: scene0621_00/2/85


### Error: scene0621_00/2/85

Source target name: table.

Source description: this table is in the middle. it is square.

Parser utterance: this table is in the middle . it is square .

Parsed predicates: []

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.000000 | 0.920176 | wrong_instance_same_semantic | 0 | 6/6 | 0.0 | 0.0 | 3395 | 4440 |
| m95 | 0.000000 | 0.937928 | wrong_instance_same_semantic | 3 | 6/6 | 0.0 | 0.0 | 3335 | 4440 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


Control missing: no_unused_same_scene_success_in_frozen_sample.


## Case 5: scene0334_00/5/23


### Error: scene0334_00/5/23

Source target name: coffee_table.

Source description: there is a donut shaped brown coffee table. it is next to a couch.

Parser utterance: there is a donut shaped brown coffee table . it is next to a couch .

Parsed predicates: ["next to"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.976689 | 0.976689 | target_pass50 | 5 | 6/6 | 1.0 | 0.9766892888757746 | 0 | 79 |
| m95 | 0.000000 | 0.968132 | no_instance_pass50 | 2 | 6/5 | 0.0 | 0.0 | 1590 | 3389 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0334_00/7/16

Source target name: bench.

Source description: this is a brown bench. it is to the left of another brown bench.

Parser utterance: this is a brown bench . it is to the left of another brown bench .

Parsed predicates: ["to the left of"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.675514 | 0.850696 | target_pass50 | 7 | 19/19 | 0.6755142667551427 | 1.0 | 1467 | 0 |
| m95 | 0.839703 | 0.850696 | target_pass50 | 7 | 19/19 | 0.839703051965906 | 1.0 | 583 | 0 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


## Case 6: scene0621_00/22/68


### Error: scene0621_00/22/68

Source target name: chair.

Source description: the chair is a dark color. it is the chair with wheels that is at the table closest to the open door.

Parser utterance: the chair is a dark color . it is the chair with wheels that is at the table closest to the open door .

Parsed predicates: ["is", "is", "with", "at", "closest to"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.000000 | 0.773797 | wrong_instance_same_semantic | 21 | 4/4 | 0.0 | 0.0 | 1912 | 1536 |
| m95 | 0.000000 | 1.000000 | wrong_instance_same_semantic | 20 | 4/4 | 0.0 | 0.0 | 1318 | 1536 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


Control missing: no_unused_same_scene_success_in_frozen_sample.


## Case 7: scene0146_00/16/8


### Error: scene0146_00/16/8

Source target name: toilet_paper_dispenser.

Source description: this is a rectangular toilet paper dispenser. it is to the left of the toilet.

Parser utterance: this is a rectangular toilet paper dispenser . it is to the left of the toilet .

Parsed predicates: ["to the left of"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.072362 | 0.531388 | no_instance_pass50 | 7 | None/None | 0.37305699481865284 | 0.08237986270022883 | 121 | 802 |
| m95 | 0.488442 | 0.775910 | no_instance_pass50 | 16 | None/None | 0.800658978583196 | 0.5560640732265446 | 121 | 388 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0146_00/12/19

Source target name: soap_dispenser.

Source description: the wall soap dispenser. the dispenser is right of the sink.

Parser utterance: the wall soap dispenser . the dispenser is right of the sink .

Parsed predicates: ["right of"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 1.000000 | 1.000000 | target_pass50 | 12 | None/None | 1.0 | 1.0 | 0 | 0 |
| m95 | 1.000000 | 1.000000 | target_pass50 | 12 | None/None | 1.0 | 1.0 | 0 | 0 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


## Case 8: scene0249_00/23/41


### Error: scene0249_00/23/41

Source target name: trash_can.

Source description: this is a blue and white recycling trash can. its next to a brown box in front of the entry way.

Parser utterance: this is a blue and white recycling trash can . its next to a brown box in front of the entry way .

Parsed predicates: []

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.960149 | 0.960149 | target_pass50 | 23 | 19/19 | 0.9601487778958555 | 1.0 | 75 | 0 |
| m95 | 0.000000 | 0.960149 | wrong_instance_same_semantic | 28 | 19/19 | 0.0 | 0.0 | 1015 | 1807 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0249_00/24/52

Source target name: table.

Source description: this is a long table. it is in the center of the room.

Parser utterance: this is a long table . it is in the center of the room .

Parsed predicates: ["in the center of"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.913061 | 0.917421 | target_pass50 | 24 | 6/6 | 0.9644083671557915 | 0.9449011585668948 | 912 | 1441 |
| m95 | 0.891535 | 0.897021 | target_pass50 | 24 | 6/6 | 0.9739449541284404 | 0.9133177838106527 | 639 | 2267 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


## Case 9: scene0046_00/26/27


### Error: scene0046_00/26/27

Source target name: door.

Source description: an open white entry door. just in front of the toliet.

Parser utterance: an open white entry door . just in front of the toliet .

Parsed predicates: []

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.000000 | 0.864908 | wrong_instance_same_semantic | 21 | 7/7 | 0.0 | 0.0 | 6515 | 2278 |
| m95 | 0.000000 | 0.888060 | wrong_instance_same_semantic | 21 | 7/7 | 0.0 | 0.0 | 8487 | 2278 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0046_00/26/34

Source target name: door.

Source description: this door is the bathroom door and it's open. the color of the door is white.

Parser utterance: this door is the bathroom door and it is open . the color of the door is white .

Parsed predicates: ["is", "is", "is", "is", "is", "is"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.836270 | 0.898516 | target_pass50 | 26 | 7/7 | 0.8362701908957415 | 1.0 | 446 | 0 |
| m95 | 0.871935 | 0.888060 | target_pass50 | 26 | 7/7 | 0.8850256815487949 | 0.9833187006145742 | 291 | 38 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


## Case 10: scene0426_00/22/24


### Error: scene0426_00/22/24

Source target name: pillow.

Source description: there is a large brown pillow. it is on the bed behind the pile of blankets.

Parser utterance: there is a large brown pillow . it is on the bed behind the pile of blankets .

Parsed predicates: ["on", "behind", "of"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.000000 | 0.801822 | wrong_instance_semantic_unknown | 0 | None/None | 0.0 | 0.0 | 674 | 1438 |
| m95 | 0.000000 | 0.715262 | wrong_instance_semantic_unknown | 0 | None/None | 0.0 | 0.0 | 760 | 1438 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0426_00/24/15

Source target name: bed.

Source description: this is a bed in a bedroom.  it is against the wall under the window.

Parser utterance: this is a bed in a bedroom . it is against the wall under the window .

Parsed predicates: ["in", "against", "under"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.655309 | 0.675108 | target_pass50 | 24 | 3/3 | 0.7632533072023517 | 0.8224920802534319 | 2416 | 1681 |
| m95 | 0.559296 | 0.584537 | target_pass50 | 24 | 3/3 | 0.7376171352074966 | 0.6982048574445617 | 2352 | 2858 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


## Case 11: scene0591_00/14/22


### Error: scene0591_00/14/22

Source target name: pillow.

Source description: the pillow is orange. it is laying on the black couch.

Parser utterance: the pillow is orange . it is laying on the black couch .

Parsed predicates: ["on"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.000000 | 1.000000 | wrong_instance_semantic_unknown | 16 | None/None | 0.0 | 0.0 | 800 | 670 |
| m95 | 0.000000 | 1.000000 | wrong_instance_semantic_unknown | 16 | None/None | 0.0 | 0.0 | 800 | 670 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0591_00/25/30

Source target name: window.

Source description: there is a rectangular window. it is behind a desk with monitors.

Parser utterance: there is a rectangular window . it is behind a desk with monitors .

Parsed predicates: ["behind", "with"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.765058 | 0.779322 | target_pass50 | 25 | 8/8 | 0.8677401340282949 | 0.8660473757547608 | 1421 | 1442 |
| m95 | 0.806600 | 0.806600 | target_pass50 | 25 | 8/8 | 0.9252839210998207 | 0.862796098467255 | 750 | 1477 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


## Case 12: scene0652_00/6/33


### Error: scene0652_00/6/33

Source target name: cabinet.

Source description: there is a wooden filing cabinet. it is the taller of the two.

Parser utterance: there is a wooden filing cabinet . it is the taller of the two .

Parsed predicates: []

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.516459 | 0.915940 | target_pass50 | 6 | 2/2 | 0.5249007027192178 | 0.969799604854643 | 3110 | 107 |
| m95 | 0.069973 | 0.825297 | wrong_instance_semantic_unknown | 27 | 2/None | 0.12793522267206478 | 0.13378492802709568 | 3231 | 3069 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.


### Control: scene0652_00/25/11

Source target name: tv.

Source description: this is a wall mounted television set. it is above the black dresser in the room.

Parser utterance: this is a wall mounted television set . it is above the black dresser in the room .

Parsed predicates: ["in"]

| Model | Selected IoU | Oracle IoU | Overlap label | Best instance | Target/winner semantic | Precision | Recall | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.846930 | 0.944389 | target_pass50 | 25 | None/None | 0.8469301934398654 | 1.0 | 182 | 0 |
| m95 | 0.846930 | 1.000000 | target_pass50 | 25 | None/None | 0.8469301934398654 | 1.0 | 182 | 0 |

Review status: overlap fields verified; physical boundary and language-cause attribution unknown.
