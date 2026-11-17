"""Invoke one unchanged native adapter arm and print only bounded result metadata."""
from pathlib import Path
import hashlib,json,subprocess,sys
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
PACKETS={'cts':HERE.parent/'tick_6bdbcf77/cts_operational_prepare','bec':HERE.parent/'tick_521a6f59/bec_operational_prepare'}
def main():
 candidate,mode,target=sys.argv[1:];assert candidate in PACKETS and mode in ['smoke','resources'] and target in ['champion','candidate']
 guard();execution=HERE/(candidate+'_execution');out=execution/('cli_'+mode+'_'+target+'_stdout.txt')
 assert not out.exists() and not (execution/(mode+'_'+target+'_execution.json')).exists()
 cmd=[sys.executable,'-B','-X','utf8',str(PACKETS[candidate]/'adapter.py'),'run','--mode',mode,'--target',target,'--execution-dir',str(execution)]
 with out.open('xb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 result_path=execution/(mode+'_'+target+'_execution.json');summary={'candidate':candidate,'mode':mode,'target':target,'adapter_returncode':r.returncode,'CLI_output':str(out),'canonical_result_exists':result_path.exists()}
 if result_path.exists():
  d=json.loads(result_path.read_text('utf8'));raw=d.get('result') or {}
  summary.update(certainty=d.get('certainty'),native_returncode=d.get('returncode'),execution_completed=raw.get('execution_completed'),optimizer_steps=raw.get('optimizer_steps'),backward_finite=raw.get('backward_finite'),intended_path_observed=raw.get('intended_path_observed'),native_smoke_checks_passed=raw.get('native_smoke_checks_passed'),canonical_result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest())
 print(json.dumps(summary,ensure_ascii=False))
 raise SystemExit(r.returncode)
if __name__=='__main__':main()
