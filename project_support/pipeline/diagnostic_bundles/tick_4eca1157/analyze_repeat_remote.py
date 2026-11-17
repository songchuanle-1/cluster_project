"""Read frozen original-repeat tensors and RNG/gradient evidence on remoteCPU."""
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parent
rows={}
for tag in ('m95','fle'):
    dirs=[root/('repeat_'+tag+'_'+str(i)) for i in (1,2)]
    results=[json.loads((d/'native_full_backward_result.json').read_text()) for d in dirs]
    assert all(r['passed'] and r['condition']=='original' and r['optimizer_steps']==0 for r in results)
    assert results[0]['input_sha256']==results[1]['input_sha256']
    arrays=[np.load(d/'prefix_arrays.npz',allow_pickle=False) for d in dirs]
    assert set(arrays[0].files)==set(arrays[1].files)
    comparison={}
    for key in arrays[0].files:
        a,b=arrays[0][key],arrays[1][key]
        assert a.shape==b.shape and a.dtype==b.dtype
        if np.issubdtype(a.dtype,np.floating):
            diff=a.astype(np.float64)-b.astype(np.float64)
            comparison[key]={'elements':a.size,'different':int(np.count_nonzero(a!=b)),
                'max_absolute':float(np.max(np.abs(diff))) if a.size else 0.,
                'mean_absolute':float(np.mean(np.abs(diff))) if a.size else 0.,
                'relative_l2':float(np.linalg.norm(diff.ravel())/max(np.linalg.norm(a.astype(np.float64).ravel()),1e-300))}
        else:comparison[key]={'elements':a.size,'different':int(np.count_nonzero(a!=b)),
                             'integer_or_mask_equal':bool(np.array_equal(a,b))}
    rows[tag]={'input_equal':True,'prefix_bitwise_equal':results[0]['prefix_sha256']==results[1]['prefix_sha256'],
        'rng_equal':{key:results[0]['rng_sha256'][key]==results[1]['rng_sha256'][key] for key in results[0]['rng_sha256']},
        'arrays':comparison,'loss_abs_difference':abs(results[0]['loss']-results[1]['loss']),
        'target_gradient_norm_abs_differences':{key:abs(results[0]['target_gradient_norms_before_clip'][key]-results[1]['target_gradient_norms_before_clip'][key])
             for key in results[0]['target_gradient_norms_before_clip']},
        'missing_gradient_names':results[0]['trainable_missing_gradient_names'],
        'scope':'ONEoriginalrepeatpair permodel,not trainingseedvariance/CI/efficacy;no toleranceadjustment'}
result={'passed':True,'observed_at':datetime.now(timezone.utc).isoformat(),'models':rows,'native_forwards':0,
        'new_training':False,'optimizer_steps':0}
with (root/'repeat_analysis_result.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps({tag:{key:value for key,value in row.items() if key!='arrays'} for tag,row in rows.items()}))
