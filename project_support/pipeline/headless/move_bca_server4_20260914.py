"""One-shot user-directed BCA relocation; preserve old attempt and other jobs."""
from pathlib import Path

source = Path("D:/project/cluster_project/pipeline/headless/launch_cps_20260914.py").read_text()
source = source.replace('HOST = "songcl@100.64.3.28"', 'HOST = "songcl@192.168.1.137"')
source = source.replace("/data3/songcl/Project/Cluster_project/Cluster", "/data/songcl/Project/Cluster_project/Cluster")
source = source.replace('ID = "M195-CTF-HCG-CSORT-CPS"', 'ID = "M196-CTF-HCG-CSORT-BCA"')
start = source.index('    origin = ')
end = source.index('    config = task["config"]', start)
source = source[:start] + '''
    origin = "server-6"
    task = next(t for t in queue["gpu_queues"][origin] if t["id"] == ID)
    assert task["status"] == "running" and task["pid"] == 1968342
    assert ssh(f"git -C {CODE} rev-parse HEAD") == task["code_commit"]
    free = int(ssh("nvidia-smi -i 0 --query-gpu=memory.free --format=csv,noheader,nounits"))
    assert free > 22000, free
    running = m.load_running(str(ROOT))
    assert not running.get("server-4", {}).get("0")
    old_attempt = dict(task)
''' + source[end:]
source = source.replace("return v.replace('/home/songcl/data/data','/data3/songcl/data/data_cluster')", "return v.replace('/home/songcl/data/data','/home/songcl/data/data')")
source = source.replace("source /data3/songcl/miniconda3/etc/profile.d/conda.sh", "source /home/dl04/anaconda3/etc/profile.d/conda.sh")
needle = '    now = datetime.now()'
source = source.replace(needle, '''
    # Verify the exact source command and kill its own process group only.
    stop = """
import os,signal,pathlib,time
pid=1968342
cmd=pathlib.Path('/proc/'+str(pid)+'/cmdline').read_bytes().split(b'\\\\0')
assert b'tools/train.py' in cmd and b'configs/Quard/ctf_hcg_csort_bca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca.yaml' in cmd
assert os.getpgid(pid)==pid
os.killpg(pid,signal.SIGTERM)
for _ in range(30):
    if not pathlib.Path('/proc/'+str(pid)).exists(): break
    time.sleep(1)
else: raise RuntimeError('Source process has not stopped')
print('source stopped')
"""
    subprocess.check_call(["ssh","songcl@100.64.3.28","/data3/songcl/miniconda3/envs/project_cluster/bin/python -c "+shlex.quote(stop)])
    queue["gpu_queues"][origin].remove(task)
    queue["gpu_queues"]["server-4"].append(task)
    previous = running["server-6"]["7"]
    assert isinstance(previous,list) and ID in previous
    running["server-6"]["7"] = [x for x in previous if x != ID]
    task.update(status="waiting",server="server-4",gpu=0)
    for key in ("pid","log","launched"):
        task.pop(key,None)
    record = m.load_experiment(str(ROOT),ID) or {}
    record.setdefault("history",[]).append(dict(action="user_relocation_source_stopped",
        ts=datetime.now().isoformat(),previous_attempt=old_attempt,
        note="No checkpoint; restart same seed on server4,not crash repair"))
    record.update(task)
    m.save_experiment(str(ROOT),record)
    m.save_queue(str(ROOT),queue)
    m.save_running(str(ROOT),running)
    origin = "server-4"
''' + needle)
source = source.replace("'--gpu_ids','7'", "'--gpu_ids','0'")
source = source.replace('server="server-6", gpu=7', 'server="server-4", gpu=0')
start = source.index('    if origin != "server-6":')
end = source.index('    record = m.load_experiment', start)
source = source[:start] + '    running.setdefault("server-4", {})["0"] = ID\n' + source[end:]
source = source.replace('"manual_launch"', '"user_relocation_launch_server4"')
source = source.replace('"20260914-194215_manual.md"', '"user-request-server4-20260914"')
exec(compile(source, "<bca-relocation>", "exec"))
