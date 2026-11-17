"""Complete only memory/report tail after verified pre-memory prefix failure."""
from pathlib import Path
import hashlib,importlib.util,json,sys,textwrap
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def main():
 owner=guard();assert (HERE/'final_persist_intent.json').exists() and not (HERE/'final_persisted.json').exists()
 assert not (HERE/'audit_prefix_recovery.json').exists() and not (HERE/'report_notes.json').exists()
 work=json.loads((ROOT/'pipeline/research_work.json').read_text('utf8'))
 assert work['tick_attempt']['tick_started_at']==owner['generated_at'] and work['tick_attempt']['result']=='blocked'
 q=json.loads((ROOT/'pipeline/queue.json').read_text('utf8'));task=next(x for x in q['gpu_queues']['server-4'] if x['id']=='M214-CTS');assert task['status']=='waiting' and task.get('pid') is None
 source=HERE/'finalize_gpu0_progress.py';text=source.read_text('utf8')
 start=text.index("  memory_path=ROOT/'pipeline/codex_memory.md'");end=text.index('\n finally:lock.close()',start)
 tail=textwrap.dedent(text[start:end]);old="line('- 采集',";assert tail.count(old)==1;tail=tail.replace(old,"line('- 本轮45eb初严格running observer',")
 spec=importlib.util.spec_from_file_location('audit_tail_source',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 namespace=vars(module).copy();namespace.update(owner=owner,task=task,verified=False)
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();record={'token':owner['token'],'original_helper_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'failure':'Memory prefix collection line renamed in prior45eb; sharedwork save completed before assertion, memory and notes had not been written.','specific_fix':'Extract only audit memory/notes/final-result tail, replace one historical memory-line prefix; no work/queue/receipt/ff/transport replay.','original_intent_preserved':True,'queue_and_work_replayed':False}
  with (HERE/'audit_prefix_recovery.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
  exec(compile(tail,str(HERE/'audit_memory_tail'), 'exec'),namespace)
 finally:lock.close()
if __name__=='__main__':main()
