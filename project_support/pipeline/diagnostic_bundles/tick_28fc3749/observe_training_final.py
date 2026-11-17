"""Read-only native training progress and validation lines;no restart permission."""
from ops import *
guard(120)
program=r'''import json,re
from pathlib import Path
from datetime import datetime,timezone
path=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log')
text=path.read_text(encoding='utf-8',errors='replace')
text=re.sub(r'\x1b\[[0-9;]*[a-zA-Z]','',text)
metrics=[line for line in text.splitlines() if re.search(r'mIoU|miou|best.*epoch|best.*iou',line,re.I)]
steps=re.findall(r'Train\[(\d+)/50\].*?\|\s*(\d+)/4686',text)
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'pid':1085297,'alive':Path('/proc/1085297').exists(),'latest_native_train_steps':steps[-6:],'validation_lines':metrics[-12:],'traceback_in_recent_tail':'Traceback' in text[-50000:],'log_bytes':path.stat().st_size,'training_modified':False}))
'''
result=remote('server-4',program,timeout=90)
save('training_final_observation.json',result)
print(json.dumps(result,ensure_ascii=True,indent=2))
