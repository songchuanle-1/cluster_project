"""Register the required bounded new diagnosis before broad route review."""
from ops import *
guard(180)
work=tick.load(ROOT/'pipeline/research_work.json')
assert not any(c['id']==CID for c in work['candidates'])
candidate={'id':CID,'stage':'diagnosis','kind':'primary_expression_specific_point_feature_information_diagnosis',
 'created_at':datetime.now(timezone.utc).isoformat(),'hypothesis_id':'same-scene-different-expression-point-message-conditional-effect',
 'hypothesis':'Holding the original recipient finalquery and native point/mask suffix fixed,the trainedM95 hierarchical pointmessage contains useful expression-specific targetinformation beyond generic same-scene context. A preregistered different-target same-scene donor message increases original target mask-probability error versus ownmessage. Positive scene-balanced paired donor-minus-own error is predicted;no cutoff tuning or efficacy/novelty claim.',
 'matched_control':'Same frozenM95epoch16,TRAINscenes,physicalsuperpointorder,originalrecipientquery/weights/targets/native positive matching and unchangedencoder gate/ILA/prediction_head. Swap only complete capturedhierarchy message across different-target expressions withinthesame scene,withfixedcyclicdonorselection,identity andundocontrols. Nochange to scales/fusion/loss/routing/gates/schedule/data.',
 'next_action':'Run cheapest real savedprefix CPU audit of within-scene point/mask/assignment correspondence and message variation;bind deterministic expression donors and inspect native exact suffix. Featuredistance/cotangent is not task diagnosis. Preserve all strict controls and pending scale-responsibility ID.',
 'failure_scope':'inconclusive','gate_result':'Pending source,CPU and native taskcontrols;not a trainablemechanism',
 'gates':{key:{'passed':False,'reason':'Diagnostic bootstrap;required native task/mechanism evidence not collected'} for key in ('diagnosis','controls','native_backward','resources','independence','constraints')},
 'evidence':[evidence(OUT/'expression_message_prereg.md'),evidence(Path(__file__)),evidence(OUT/'ops.py')]}
work['candidates'].append(candidate);guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'id':CID,'stage':'diagnosis','new_candidates':1,'new_training':0,'scientific_passes':0},ensure_ascii=True))
