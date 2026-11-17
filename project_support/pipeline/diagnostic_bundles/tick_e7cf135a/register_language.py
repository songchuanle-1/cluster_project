"""Continue a genuinely distinct source-path diagnostic, not a scale replay."""
import json
import register

c=register.c
ROOT,OUT=register.ROOT,register.OUT
LANG='m95-final-ila-expression-source-dependence'


def main():
    c.guard(1200)
    work=c.tick.load(ROOT/'pipeline/research_work.json')
    draft=work.pop('design_cycle',None)
    assert draft and draft['stop_reason']=='no_information_gain'
    review=c.save('stop_independence_review.json',{
        'recorded_at':c.now(),'draft_cycle':draft,'accepted_as_stop_certificate':False,
        'reason':'The scale-contamination and constant-shift diagnostics are sequential alternative explanations on the same intervention line. Distinct IDs do not by themselves establish genuinely independent research routes. Their findings remain valid, but the proposed early no-information-gain certificate is withdrawn before finish.',
        'next_action':'Continue a separately preregistered native source-dependence diagnostic of actual language-to-inst_feats ILA, keeping original point query and readout fixed.'})
    assert sum(item['stage'] not in ('complete','rejected','closed') for item in work['candidates'])==7
    assert not any(item['id']==LANG for item in work['candidates'])
    protocol=c.save('ila_source_preregistration.json',{
        'preregistered_at':c.now(),'candidate_id':LANG,'token':c.TOKEN,
        'hypothesis_id':'final-native-language-to-point-update-is-expression-invariant',
        'hypothesis':'With the receiving point features and final decoder query held fixed, the trained M95 final ILA update is effectively invariant to which within-scene expression supplies the language source; this would reveal a missing expression-specific point-feature path independently of hierarchy scale composition.',
        'source_scope':'Capture actual source/query/mask at final active encoder.ila, not the unused query argument of cluster gather. Replay this unchanged native module directly and the frozen native prediction_head; do not edit an attention formula or train language routing.',
        'cohort':c.evidence(OUT/'cohort.json'),'assets':c.evidence(OUT/'native_manifest.json'),
        'primary_intervention':'Within each native scene language group, use the unique one-position cyclic expression permutation for ILA source language features AND aligned language padding mask. Keep ILA point-query tensor, point order, model weights, final native decoder query and original selected query unchanged. Donor choice never uses GT or model outcomes.',
        'negative_controls':['Same source/native ILA identity<=1e-6',
            'Prediction-head identity<=1e-6',
            'Cycle language source and mask then inverse-restore before ILA, output and mask identity<=1e-6',
            'Direct replay output equals native encoder final inst_feats<=1e-6',
            'Frozen receiving point-query tensor unchanged; source+mask multiset exact under inverse'],
        'readouts':['Native source/query support and shape; changed valid receiver count and inst_feats max delta',
            'Frozen selected-query mask-logit delta and all/foreground/non-target probability-MAE changes',
            'After inference only, label donor pairs as same-object/different-object using preexisting annotations; retain empty strata',
            'Scene means and every expression, no favorable scene or query selection'],
        'falsifier':'Reject the expression-invariance/missing-path explanation on this cohort if correctly controlled within-scene source exchange changes actual valid inst_feats AND fixed-query mask logits beyond original1e-6. Computational sensitivity is not task benefit; mixed error directions cannot establish a new mechanism.',
        'distinction':'Earlier HDS query swap changes cluster query input that is unused given its bank; earlier native hierarchy-message swap changes a hierarchy output while preserving ILA. This test changes the actual language source into unchanged ILA and freezes the receiving point query. It is not a new attention/routing architecture or reopening of HDS/FLE/CPA/PCE.',
        'diagnostic_only':True,'tolerance':1e-6,'new_training':0,'optimizer_steps':0})
    work['candidates'].append({'id':LANG,'stage':'diagnosis',
        'hypothesis_id':'final-native-language-to-point-update-is-expression-invariant',
        'hypothesis':c.tick.load(protocol)['hypothesis'],
        'matched_control':'Native final ILA and fixed-query head replay, within-scene cyclic language source+mask, inverse-restore and unchanged receiver-query controls.',
        'next_action':'Execute original ILA source-dependence and fixed-query masks on frozen8TRAINscenes; labels read only after deterministic source permutation.',
        'evidence':[c.evidence(protocol),c.evidence(review),c.evidence(__file__)],
        'diagnostic_only':True,'scientific_admission':False})
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'early_stop_draft_withdrawn':True,'created':LANG,'pending':8}))


if __name__=='__main__':main()
