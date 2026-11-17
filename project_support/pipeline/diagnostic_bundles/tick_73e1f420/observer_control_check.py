SPY_SOURCE="def observed_pinv(*args, **kwargs):\n        # Smoke observer only. Preserve exactly one original call and return object.\n        entry = None\n        if state['inside_operator']:\n            gram = args[0]\n            entry = {'actual_input_shape': list(gram.shape),\n                'actual_input_dtype': str(gram.dtype),\n                'positional_arguments_after_input': len(args) - 1,\n                'provided_kwargs': {k: v if isinstance(v, (str,int,float,bool,type(None)))\n                    else repr(v) for k,v in kwargs.items()},\n                'provided_tolerances': 'default; no observer-supplied atol/rtol/rcond',\n                'pinv_retained_rank': 'UNOBSERVED; diagnostic matrix_rank is a separate API',\n                'original_calls_per_observation': 0, 'native_pinv_completed': False,\n                'observer_readout_complete': False}\n            inverses.append(entry)\n            try:\n                entry['actual_input'] = summary(gram)\n            except Exception as error:\n                entry['observer_input_error'] = {'type':type(error).__name__, 'message':str(error)}\n        if entry is not None:\n            entry['original_calls_per_observation'] = 1\n        try:\n            inverse = original_pinv(*args, **kwargs)\n        except BaseException as error:\n            if entry is not None:\n                entry['native_pinv_exception'] = {'type':type(error).__name__, 'message':str(error)}\n            raise\n        if entry is not None:\n            entry['native_pinv_completed'] = True\n            try:\n                entry['actual_return'] = summary(inverse)\n            except Exception as error:\n                entry['observer_return_error'] = {'type':type(error).__name__, 'message':str(error)}\n            assert gram.shape[-2:] == (3,3)\n            if 'actual_input' in entry:\n                assert entry['actual_input']['finite']\n            if 'actual_return' in entry:\n                assert entry['actual_return']['finite']\n            try:\n                with torch.no_grad():\n                    eigen = torch.linalg.eigvalsh(gram)\n                    rank = torch.linalg.matrix_rank(gram, hermitian=True)\n                    projection = gram @ inverse\n                    entry['diagnostic_eigenvalues'] = eigen.detach().cpu().tolist()\n                    entry['diagnostic_matrix_rank_default_api'] = rank.detach().cpu().tolist()\n                    entry['diagnostic_matrix_rank_counts'] = {\n                        str(k): int(rank.eq(k).sum()) for k in range(4)}\n                    entry['symmetry_abs_max'] = float((gram - gram.transpose(-2,-1)).abs().max())\n                    entry['G_Gplus_trace'] = projection.diagonal(dim1=-2,dim2=-1).sum(-1).cpu().tolist()\n                    entry['G_Gplus_idempotence_abs_max'] = float((projection @ projection - projection).abs().max())\n                    entry['spectrum_scope'] = 'Additional diagnostic computation on actual G; not backend pinv internals'\n            except Exception as error:\n                entry['observer_spectrum_error'] = {'type':type(error).__name__, 'message':str(error)}\n            entry['observer_readout_complete'] = all(key in entry for key in\n                ('actual_input','actual_return','spectrum_scope')) and not any(key in entry for key in\n                ('observer_input_error','observer_return_error','observer_spectrum_error'))\n        return inverse"
import sys,json,types,contextlib
assert 'torch' not in sys.modules
class SentinelGram:
 shape=(2,3,3)
 dtype='sentinel_non_tensor'
gram=SentinelGram();inverse=object()
def check(case):
 calls=[];entries=[];native_error=ValueError('native-sentinel')
 def native(*args,**kwargs):
  calls.append((args,kwargs))
  if case=='native_exception':raise native_error
  return inverse
 def summary(value):
  if (case=='input_summary_exception' and value is gram) or (case=='return_summary_exception' and value is inverse):
   raise LookupError('summary-sentinel')
  return {'finite':True,'shape':[2,3,3],'dtype':'sentinel_non_tensor','nonfinite_count':0,'abs_max':None}
 def eigen(value):raise ArithmeticError('observer-spectrum-sentinel')
 env={'state':{'inside_operator':case!='outside_operator'},'inverses':entries,'original_pinv':native,'summary':summary,
  'torch':types.SimpleNamespace(no_grad=contextlib.nullcontext,linalg=types.SimpleNamespace(eigvalsh=eigen))}
 exec(compile(SPY_SOURCE,'extracted_observer_control_only','exec'),env)
 try:
  observed=env['observed_pinv'](gram,hermitian=True)
 except ValueError as error:
  assert case=='native_exception' and error is native_error
  assert entries[0]['native_pinv_exception']['type']=='ValueError' and 'actual_input' in entries[0]
 else:
  assert case!='native_exception' and observed is inverse
 assert len(calls)==1 and calls[0][0][0] is gram and calls[0][1]=={'hermitian':True}
 if case=='outside_operator':assert entries==[]
 else:
  assert len(entries)==1 and entries[0]['original_calls_per_observation']==1
  assert entries[0]['observer_readout_complete'] is False
  if case!='native_exception':
   assert entries[0]['native_pinv_completed'] is True and entries[0]['observer_spectrum_error']['type']=='ArithmeticError'
  if case=='input_summary_exception':assert entries[0]['observer_input_error']['type']=='LookupError'
  if case=='return_summary_exception':assert entries[0]['observer_return_error']['type']=='LookupError'
 return {'case':case,'passed':True,'original_calls':len(calls),'uses_tensor_or_numeric_model':False}
cases=[check(case) for case in ('native_exception','observer_spectrum_exception','input_summary_exception','return_summary_exception','outside_operator')]
assert 'torch' not in sys.modules and 'gorilla' not in sys.modules
print(json.dumps({'cases':cases,'passed':True,'scope':'Pure Python observer exception/call/identity control checks with non-tensor sentinel objects. No torch import, model, numeric algebra, data loading or GPU. Not native smoke/resource evidence.','torch_imported':False,'model_executed':False,'cuda_calls':0}))
