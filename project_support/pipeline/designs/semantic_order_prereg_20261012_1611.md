# Native Instance Semantic Order Diagnosis

Stable ID: m95-native-instance-semantic-order
Hypothesis ID: mixed-instance-semantics-make-context-supervision-order-dependent

The original native context-mask code selects each instance's semantic category
from its first point. The falsifiable prerequisite is that actual annotated
TRAIN instances contain heterogeneous semantic classes and that reversing
within-instance point order changes the native context label. This is distinct
from superpoint boundary quantization, language root-role repair, and the prior
incorrect diagnostic taxonomy adapter.

Use server-6 CPU only. Bind the exact original dataset, original config,
ScanRefer TRAIN annotations, label taxonomy TSV and each native scene file.
Audit all TRAIN scenes and all annotated physical targets, not a guessed
semantic-index-to-category table. Construct the taxonomy using the native
dataset itself. AST-extract only the original context mask assignment and
instance loop, and execute it without changing source. Test original/reversed
point order on heterogeneous actual annotated instances. Matched controls:
uniform semantic category, uniform reversal, deliberately heterogeneous
same-instance labels with a mentioned and unmentioned native category.

Report raw semantic heterogeneity, mapped class heterogeneity, reversals with
changed native masks, annotated target/scene/expression denominators and missing
data. A homogeneous population disconfirms only the mixed-semantic/order
prerequisite; it does not certify all labels or caption category coverage.
Synthetic controls validate sensitivity, not real defect prevalence. Unrun
native model backward/resources/novelty are unknown, never PASS.
