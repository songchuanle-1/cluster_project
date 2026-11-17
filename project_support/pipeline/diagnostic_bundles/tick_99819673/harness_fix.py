import register
c=register.c
p=register.OUT
c.guard(1500)
s=(p/'validation_worker.py').read_text(encoding='utf-8')
assert s.count('parent.C2F_ClusterAttn_CTF_HCG_CSORT.forward')==1
s=s.replace('parent.C2F_ClusterAttn_CTF_HCG_CSORT.forward','parent.C2F_ClusterAttn_CTF.forward')
with (p/'validation_worker_h1.py').open('x',encoding='utf-8') as stream:stream.write(s)
s=(p/'validation.py').read_text(encoding='utf-8')
s=s.replace("STAGE=c.STAGE+'_validation'","STAGE=c.STAGE+'_validation_h1'").replace("VOUT=OUT/'validation'","VOUT=OUT/'validation_h1'")
s=s.replace('validation_worker.py','validation_worker_h1.py').replace('validation_preregistration.json','validation_h1_preregistration.json')
s=s.replace('validation_staging.json','validation_h1_staging.json').replace("'validation_'+label","'validation_h1_'+label")
with (p/'validation_h1.py').open('x',encoding='utf-8') as stream:stream.write(s)
c.save('harness_repair_preregistration.json',{'at':c.now(),'candidate_id':c.CID,
    'scope':'Diagnostic harness only; candidate9source/config hashes unchanged, no implementation revision. Replace invalid parent CSORT method binding (zero-argument super references another class) with verified original CTF feature-return body without super. Parent auxiliary-loss accumulation is not the encoder feature equality being tested. Actual native loss backward retains the complete candidate CSORT.',
    'original_result':c.evidence(p/'validation_controls_candidate_result.json'),
    'preserved_failure':'R0 observed fullsource identity/row1.9073486328125e-6>1e-6; original numerical failure remains.','threshold':1e-6})
print('harness h1 prepared')
