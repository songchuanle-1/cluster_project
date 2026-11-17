"""Exact binary-input squared-distance comparisons;no Torch or CUDA imports."""
from datetime import datetime,timezone
from decimal import Decimal,localcontext,Inexact
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import scipy
from scipy.spatial import cKDTree

stage=Path(__file__).resolve().parent;manifest=json.loads((stage/'manifest.json').read_text())
result={'execution_passed':False,'fixtures':[],'real_coordinate_pairs':[],'neural_forwards':0,'native_FPS_calls':0,'optimizer_steps':0}
def fractions(coords):return [[Fraction.from_float(float(v)) for v in row] for row in coords]
def squared(a,b):return sum(((x-y)*(x-y) for x,y in zip(a,b)),Fraction(0))
def sign(value):return (value>0)-(value<0)
def decimal_sign(a,b,c):
    with localcontext() as context:
        context.prec=256;context.traps[Inexact]=True
        def distance(other):return sum(((Decimal.from_float(float(x))-Decimal.from_float(float(y)))**2 for x,y in zip(a,other)),Decimal(0))
        value=distance(b)-distance(c)
        return (value>0)-(value<0)
def analyze(coords,label,full_rank,stored_indices=None,stored_fallback=None):
    assert np.isfinite(coords).all() and len(coords)>=33
    points=fractions(coords)
    distances,indices=cKDTree(coords).query(coords,k=list(range(1,34)))
    observed=distances[:,31]==distances[:,32]
    if stored_indices is not None:assert np.array_equal(indices[:,:32],stored_indices)
    if stored_fallback is not None:assert np.array_equal(observed,stored_fallback)
    rows=[];exact_pair_ties=0;false_ties=0;missed_ties=0;inversions=0;exact_rank_ties=0;rank_disagreements=0
    for i in range(len(coords)):
        j=int(indices[i,31]);k=int(indices[i,32])
        a=squared(points[i],points[j]);b=squared(points[i],points[k]);difference=a-b;comparison=sign(difference)
        tied=comparison==0;exact_pair_ties+=tied
        false_ties+=bool(observed[i]) and not tied;missed_ties+=not bool(observed[i]) and tied
        inversions+=comparison>0
        rank_tied=None
        if full_rank:
            ranked=sorted(squared(points[i],point) for point in points)
            rank_tied=ranked[31]==ranked[32];exact_rank_ties+=rank_tied
            rank_disagreements+=bool(observed[i])!=rank_tied
        if bool(observed[i])!=tied or comparison>0 or (full_rank and bool(observed[i])!=rank_tied):
            confirmed=decimal_sign(coords[i],coords[j],coords[k])
            assert confirmed==comparison
            rows.append({'recipient':i,'neighbor_k32':j,'neighbor_k33':k,'float_distance_k32':float(distances[i,31]),
                'float_distance_k33':float(distances[i,32]),'reported_float_tie':bool(observed[i]),'exact_pair_tie':tied,
                'exact_full_rank_cutoff_tie':rank_tied,'exact_squared_difference_numerator':str(difference.numerator),
                'exact_squared_difference_denominator':str(difference.denominator),'exact_difference_sign':comparison,
                'decimal256_independent_sign_agrees':True})
    return {'sample':label,'recipients':len(coords),'float_cutoff_ties':int(observed.sum()),'exact_reported_pair_ties':int(exact_pair_ties),
        'false_float_pair_ties':int(false_ties),'missed_exact_pair_ties':int(missed_ties),'pair_exact_order_inversions':int(inversions),
        'full_exact_rank_measured':full_rank,'exact_full_rank_cutoff_ties':int(exact_rank_ties) if full_rank else None,
        'float_vs_full_exact_rank_predicate_disagreements':int(rank_disagreements) if full_rank else None,'disagreements':rows}
try:
    for item in manifest['files']:
        assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
    arrays=np.load(manifest['counterexample'],allow_pickle=False)
    result['fixtures'].append(analyze(arrays['coordinates'],'lattice40_original',True,arrays['original_indices'],arrays['original_fallback']))
    result['fixtures'].append(analyze(arrays['transformed'],'lattice40_rotated',True,arrays['transformed_indices'],arrays['transformed_fallback']))
    gaussian=np.random.default_rng(1999).normal(size=(40,3))
    result['fixtures'].append(analyze(gaussian,'prior_gaussian40',True))
    for item in manifest['geometry']:
        data=np.load(item['path'],allow_pickle=False)
        result['real_coordinate_pairs'].append(analyze(data['positions_cpu'].astype(np.float64),item['scene'],False))
    result.update(execution_passed=True,torch_imported='torch' in sys.modules,numpy_version=np.__version__,scipy_version=scipy.__version__,
        coordinate_rounding_alone_explains_all_fixture_predicates=all(r['float_vs_full_exact_rank_predicate_disagreements']==0 for r in result['fixtures']),
        exact_reference='Fraction.from_float;full squared-distance ranks for40point fixtures;reported32/33pair only forrealcoordinate artificialleaf',
        precision='exact rational,noepsilon;independent Decimal256 with Inexact trap on every disagreement',
        limitations='represented coordinates only;artificial single-leaf realdata;no native FPS,trained features,mask harm,source repair or population inference')
    assert result['torch_imported'] is False
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    result['observed_at']=datetime.now(timezone.utc).isoformat()
    with (stage/'exact_distance_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps({'execution_passed':result['execution_passed'],'fixtures':[{k:r[k] for k in ('sample','recipients','float_cutoff_ties','exact_full_rank_cutoff_ties','float_vs_full_exact_rank_predicate_disagreements')} for r in result['fixtures']],
    'real_recipients':sum(r['recipients'] for r in result['real_coordinate_pairs']),'real_pair_disagreements':sum(len(r['disagreements']) for r in result['real_coordinate_pairs']),'torch_imported':result.get('torch_imported')}))
