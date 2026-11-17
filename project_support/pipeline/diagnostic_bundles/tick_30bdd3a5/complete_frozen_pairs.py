"""Complete only the remaining predeclared pairs,one exclusive GPU job at a time."""
from gpu1_ops import *
guard(600)
for label in ('expression_fix','scale_fix'):
 initial=tick.load(OUT/(label+'_pair_0_result.json'))
 assert initial['execution_completed'] and initial['controls_passed']
 for pair in (1,2,3):
  guard(360)
  completed=subprocess.run([sys.executable,'-B',str(OUT/'run_native.py'),label,'--pair',str(pair)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=700)
  assert completed.returncode==0,completed.stderr[-5000:]+completed.stdout[-3000:]
  result=tick.load(OUT/(label+'_pair_'+str(pair)+'_result.json'))
  print(json.dumps({'label':label,'pair':pair,'execution_completed':result.get('execution_completed'),'controls_passed':result.get('controls_passed'),'summary':result.get('summary'),'error':result.get('error')},ensure_ascii=True),flush=True)
  assert result['execution_completed'] and result['controls_passed'],'Stopcurrentfrozenseriesonactualfailure;do notsilentlyskiporreselectscenes'
