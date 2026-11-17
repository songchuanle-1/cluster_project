# Matched Existing M95 Counterpart, No Baseline Patch

The FLE same-shape naturalbatch2 test confirms masked-value dependence;
zero-scale and nonpadded-row nulls are0, native reconstruction is0.
ASTsource review shows the existing M95 gather also uses unmasked
point_feats.mean. Test the EXACT existing available M95epoch16 checkpoint
fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e,
NOT claimed historical champion weights. Use unchanged config/source/data
and SAMEfirst2TRAINscene groups/originalbatch2/seed1999.

Reuse the source-call padding/same-shape protocol and its1e-6identity,
zero-scale and nonpadded-row null controls. M95 has NO fine_message argument
or FLE module: diagnostic adapter removes that optional diagnostic keyword
before calling its exact original bound gather. A zero placeholder for
the absent branch is NEVER fed to M95. No learned source/model code changes.

Report both counterparts' invariance and raw mask-logit effects separately;
they have different trained weights, so differences are not an architecture
effect estimate. No VAL rerun, training, single-op mean fix, efficacy gain,
admission or retroactive reclassification of failed FLE training. Verify
all exact assets plus current GPU0 idle/3locks/lease/deadline before CUDA.
