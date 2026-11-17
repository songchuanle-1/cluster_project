"""Freeze a genuine structural hypothesis before broader route review."""
from datetime import datetime,timezone
from ops import *
guard(600)
protocol={'candidate_id':CID,'preregistered_at':datetime.now(timezone.utc).isoformat(),
 'hypothesis':'At the final point-feature update, different coarse semantic tokens may provide task-relevant full-channel context to receivers outside their own coarse cell. Replace ONLY the coarse gathered message by projection-free point-to-coarse attention,retaining fine/middle CTF and the existing fusion. Nonlocal sensitivity/rank alone is not a diagnosed task deficit.',
 'matched_control':'Same original M95 TRAIN capture,tokens,point inputs,query,supervision,schedule and fine/middle messages. Compare original own-coarse gather,coarse attention,uniform coarse mean and fixed cyclic key-value mismatch. No new language query routing,top-k,gate,scalar,projection or revised loss.',
 'first_test':'Execute actual original HCG gather and frozen prototype on a CPU fixture with one remote coarse value changed;verify distinguishable information paths and gradients.',
 'next_action':'Audit exact legacy overlap/bans,then if eligible execute native same-prefix task-relevant intervention and matched controls with actual mask matching observation.',
 'fixed_choices':{'heads':'Use existing M95nhead8','scale':'Standard sqrt(head_dim),no temperature search','coarse_count':'Existing partitioner8,no count tuning'},
 'native_plan':'Two frozen TRAIN scenes/eight correlated expressions,available M95epoch16. Capture exact message before source replay;preserve original requires_grad flags;full native backward plus paired suffix/criterion and native matching signatures. Identity tolerance1e-6 unchanged.',
 'scientific_limits':['No new efficacy or novelty claim from pretraining probes','Prior finite rank,mean/ancestry/numerical tests not repeated or counted','No FLE/HDS restart or closed route renamed','No admission without diagnosis,controls,native_backward,resources,independence,constraints'],
 'posttraining_plan':{'primary':'ScanRefer mIoU on unchanged VAL split','comparators':['historical M95.5020 with checkpoint provenance caveat','baseline.4894'],
  'sampling_unit':'scene','seed':1999,'epochs':50,'max_iters':70,'efficiency':'same standard FLOPs<=10G,bs1warmup20repeat100median/P90,relative memory15% rule unchanged',
  'subgroups':'predefined same-class distractor and relation language groups;no VAL-based mechanism choice','noise_floor':'UNKNOWN until independent repeats or paired reference available','harm_rule':'Investigate scene-clustered material harm and uncertainty under original project policy;no invented cutoff'},
 'status':'Unrun structural hypothesis,not admitted'}
save('protocol.json',protocol)
work=tick.load(ROOT/'pipeline/research_work.json')
assert not any(c['id']==CID for c in work['candidates']),'Use existing stable ID'
work['candidates'].append({'id':CID,'stage':'diagnosis','kind':'provisional_core_structural_hypothesis',
 'hypothesis':protocol['hypothesis'],'matched_control':protocol['matched_control'],'next_action':protocol['first_test'],
 'created_at':protocol['preregistered_at'],'evidence':[evidence(OUT/'protocol.json'),evidence(OUT/'coarse_cross_attention.py')]})
tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'candidate_id':CID,'stage':'diagnosis','protocol_frozen':True}))
