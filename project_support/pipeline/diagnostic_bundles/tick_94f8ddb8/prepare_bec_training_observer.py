"""Minimal reuse of readonly original source/process/native-growth observer."""
from pathlib import Path
import ast,hashlib,json
from run_next_bec_arm import guard
HERE=Path(__file__).resolve().parent
def main():
 guard();old=HERE.parent/'tick_150c2902/observe_cts_native_progress.py';b=old.read_bytes();before=hashlib.sha256(b).hexdigest()
 replacements=[(b'CTS0',b'BEC0'),(b'M214-CTS',b'M215-BEC'),(b'4e80006047d5cb3dcdfb9c1102e02c33f354a07d',b'026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'),(b"HERE.parent/'tick_45eb3b04/cts_execution/native_manifest.json'",b"HERE/'bec_r1_execution/native_manifest.json'"),(b'cts_native_progress_observation.json',b'bec_training_progress_observation.json')]
 changes=[]
 for a,c in replacements:
  n=b.count(a);assert n>0;b=b.replace(a,c);changes.append({'before':a.decode(),'after':c.decode(),'count':n})
 ast.parse(b);p=HERE/'observe_bec_training_progress.py'
 with p.open('xb') as f:f.write(b)
 with (HERE/'bec_training_observer_provenance.json').open('x',encoding='utf8') as f:json.dump({'old_sha256':before,'current_sha256':hashlib.sha256(b).hexdigest(),'changes':changes,'scope':'Only actual BEC source/manifest/task/output binding; root currentguard, same strict SSH/own log/source8/GPU0/two samples logic.'},f,indent=2)
 print('BEC_TRAINING_READONLY_OBSERVER_READY')
if __name__=='__main__':main()
