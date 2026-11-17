"""Audit-only continuation: strip function indentation outside literal text."""
from pathlib import Path
import importlib.util,json,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def main():
 owner=guard();assert (HERE/'audit_prefix_recovery.json').exists() and not (HERE/'final_persisted.json').exists() and not (HERE/'report_notes.json').exists()
 task=next(t for t in json.loads((ROOT/'pipeline/queue.json').read_text('utf8'))['gpu_queues']['server-4'] if t['id']=='M214-CTS');assert task['status']=='waiting' and task.get('pid') is None
 source=HERE/'finalize_gpu0_progress.py';text=source.read_text('utf8');start=text.index("  memory_path=ROOT/'pipeline/codex_memory.md'");end=text.index('\n finally:lock.close()',start)
 tail='\n'.join(line[2:] if line.startswith('  ') else line for line in text[start:end].splitlines())
 old="line('- 采集',";assert tail.count(old)==1;tail=tail.replace(old,"line('- 本轮45eb初严格running observer',")
 code=compile(tail,str(HERE/'audit_only_tail_r2'),'exec')
 spec=importlib.util.spec_from_file_location('audit_only_tail_source',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);scope=vars(module).copy();scope.update(owner=owner,task=task,verified=False)
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard()
  with (HERE/'audit_tail_r2_record.json').open('x',encoding='utf8') as f:json.dump({'scope':'Memory/notes only; no work/queue/launch replay','fix':'Remove only leading function2spaces; original string lines do not participate in dedent. Original failed recorder/compilation preserved.'},f);f.write('\n')
  exec(code,scope)
 finally:lock.close()
if __name__=='__main__':main()
