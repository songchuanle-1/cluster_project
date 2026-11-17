"""Source-independent native validation in a diagnostic-only artifact directory."""
import argparse
import ast
import base64
from datetime import datetime,timezone
import hashlib
import io
import json
import subprocess
import zipfile
from run import BUNDLE,ROOT,PRIOR,TOKEN,guard,tick,Instrument

NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1'
PARENT=NAME.removesuffix('_hds_canon_r1')
PACKAGE=ROOT/'Cluster/framework/model/Quard_model'/NAME
REMOTE='/sdc1/songcl/Project/Cluster_project/pipeline/revision2_cc39552e'

def inspect_source():
    guard()
    assert tick.load(BUNDLE/'revision2_controls_result.json')['passed']==20
    files=sorted(PACKAGE.glob('*.py'))
    assert len(files)==9 and not PACKAGE.is_symlink()
    parent=PACKAGE.parent/PARENT
    for path in files:
        compile(path.read_text(encoding='utf-8'),str(path),'exec')
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node,ast.ImportFrom):assert not(node.module and PARENT in node.module)
            if isinstance(node,ast.Import):assert not any(PARENT in item.name for item in node.names)
        if path.name not in ('dec.py','hier_postprocess.py','hierarchical_readout.py','rematerialization.py'):
            assert path.read_bytes()==(parent/path.name).read_bytes()
    assert (PACKAGE/'rematerialization.py').read_bytes()==(BUNDLE/'rematerialization.py').read_bytes()
    assert (PACKAGE/'hierarchical_readout.py').read_bytes()==(PRIOR/'canonical_readout.py').read_bytes()
    decoder=ast.parse((PACKAGE/'dec.py').read_text(encoding='utf-8'))
    decoder.body=[node for node in decoder.body if not(isinstance(node,ast.ImportFrom) and node.module=='rematerialization')]
    for node in ast.walk(decoder):
        if isinstance(node,ast.FunctionDef) and node.name=='__init__':
            node.body=[entry for entry in node.body if not(isinstance(entry,ast.Expr) and isinstance(entry.value,ast.Call) and isinstance(entry.value.func,ast.Name) and entry.value.func.id=='install_prefix_rematerialization')]
    assert ast.dump(decoder)==ast.dump(ast.parse((parent/'dec.py').read_text(encoding='utf-8')))
    config=list((ROOT/'Cluster/configs').rglob(NAME+'.yaml'))
    assert len(config)==1
    original=ROOT/('Cluster/configs/Quard/ctf_hcg_csort/'+PARENT+'.yaml')
    assert config[0].read_bytes()==original.read_bytes()
    assert tick.digest(ROOT/'Cluster/scripts/validate_pdc_20261009.py')=='00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26'
    return files+[config[0]]

def upload():
    files=inspect_source()
    assert not (BUNDLE/'independent_upload.json').exists()
    stream=io.BytesIO()
    manifest={}
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            name=NAME+'/'+path.name if path.suffix=='.py' else 'config/'+path.name
            archive.writestr(name,path.read_bytes())
            manifest[name]=tick.digest(path)
    data=stream.getvalue()
    sha=hashlib.sha256(data).hexdigest()
    payload='import base64,hashlib,io,json,subprocess,zipfile\nfrom pathlib import Path\n'
    payload+="assert subprocess.check_output(['hostname'],text=True).strip()=='sysu311-MS-7C59'\n"
    payload+='data=base64.b64decode('+repr(base64.b64encode(data).decode())+')\n'
    payload+='assert hashlib.sha256(data).hexdigest()=='+repr(sha)+'\n'
    payload+='root=Path('+repr(REMOTE)+')\nassert not root.exists()\n'
    payload+="assert root.parent.resolve()==Path('/sdc1/songcl/Project/Cluster_project/pipeline').resolve()\nroot.mkdir()\n"
    payload+='manifest='+repr(manifest)+'\n'
    payload+="with zipfile.ZipFile(io.BytesIO(data)) as archive:\n assert set(archive.namelist())==set(manifest)\n for name in archive.namelist():\n  assert not Path(name).is_absolute() and '..' not in Path(name).parts\n  target=root/name\n  target.parent.mkdir(parents=True,exist_ok=True)\n  content=archive.read(name)\n  assert hashlib.sha256(content).hexdigest()==manifest[name]\n  target.write_bytes(content)\nprint(json.dumps({'root':str(root),'files':len(manifest),'sha256':hashlib.sha256(data).hexdigest(),'diagnostic_only':True,'production_files_changed':0}))\n"
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=payload,text=True,
        encoding='utf-8',capture_output=True,timeout=40)
    guard()
    record={'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),'returncode':process.returncode,
        'stdout':process.stdout,'stderr':process.stderr,'manifest':manifest,
        'local_files':[{'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)} for path in files],
        'archive_sha256':sha,'runner_sha256':tick.digest(BUNDLE/'independent_native.py')}
    tick.save(BUNDLE/'independent_upload.json',record)
    assert process.returncode==0,process.stderr
    print(process.stdout)

class NativePackage(ast.NodeTransformer):
    def __init__(self):self.count=0
    def visit_Assign(self,node):
        self.generic_visit(node)
        if any(isinstance(target,ast.Name) and target.id=='module' for target in node.targets) and isinstance(node.value,ast.Call):
            self.count+=1
            return ast.parse("module=load_diagnostic_package()\n").body
        if any(isinstance(target,ast.Name) and target.id=='result' for target in node.targets) and isinstance(node.value,ast.Dict):
            for index,key in enumerate(node.value.keys):
                if isinstance(key,ast.Constant) and key.value=='source_independent_model':node.value.values[index]=ast.Constant(True)
            node.value.keys.extend([ast.Constant('source_package'),ast.Constant('source_manifest')])
            node.value.values.extend([ast.Constant(NAME),ast.Name('SOURCE_MANIFEST',ast.Load())])
        return node

def execute(timeout):
    owner=guard()
    files=inspect_source()
    upload=tick.load(BUNDLE/'independent_upload.json')
    assert upload['returncode']==0
    assert all(tick.digest(ROOT/item['path'])==item['sha256'] for item in upload['local_files'])
    attempt=BUNDLE/'independent_native_attempt.json'
    assert not attempt.exists()
    tree=ast.parse((BUNDLE/'native_memory_frozen.py').read_text(encoding='utf-8'))
    transform=NativePackage()
    tree=transform.visit(tree)
    assert transform.count==1
    instrument=Instrument()
    tree=instrument.visit(tree)
    assert instrument.insertions==instrument.result_insertions==1
    payload=ast.unparse(ast.fix_missing_locations(tree))
    timeout=min(timeout,int((datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds())-120)
    prefix='import signal,importlib.util,sys\nfrom pathlib import Path\nsignal.alarm('+str(timeout-15)+')\n'
    prefix+='FOREGROUND_TOKEN='+repr(TOKEN)+'\nFOREGROUND_DEADLINE='+repr(owner['deadline_at'])+'\nMEMORY_CONDITION="baseline"\n'
    prefix+='SOURCE_MANIFEST='+repr(upload['manifest'])+'\n'
    prefix+='DIAGNOSTIC_ROOT='+repr(REMOTE)+'\nDIAGNOSTIC_PACKAGE='+repr(NAME)+'\n'
    prefix+="def load_diagnostic_package():\n import hashlib,importlib\n root=Path(DIAGNOSTIC_ROOT)\n for name,sha in SOURCE_MANIFEST.items():\n  assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha\n importlib.import_module('framework.model.Quard_model')\n qualified='framework.model.Quard_model.'+DIAGNOSTIC_PACKAGE\n spec=importlib.util.spec_from_file_location(qualified,root/DIAGNOSTIC_PACKAGE/'__init__.py',submodule_search_locations=[str(root/DIAGNOSTIC_PACKAGE)])\n module=importlib.util.module_from_spec(spec)\n sys.modules[qualified]=module\n spec.loader.exec_module(module)\n return module\n"
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=prefix+payload,text=True,
        encoding='utf-8',capture_output=True,timeout=timeout)
    guard()
    tick.save(attempt,{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'runner_sha256':tick.digest(BUNDLE/'independent_native.py'),'upload_sha256':tick.digest(BUNDLE/'independent_upload.json'),
        'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
    rows=[json.loads(line.split('=',1)[1]) for line in process.stdout.splitlines() if line.startswith('HIER_NATIVE_RESULT=')]
    if rows:
        assert len(rows)==1
        tick.save(BUNDLE/'independent_native_result.json',{'token':TOKEN,'attempt_sha256':tick.digest(attempt),**rows[0]})
        print(json.dumps({key:value for key,value in rows[0].items() if key not in ('module_trace','source_manifest')},ensure_ascii=False))
    else:print(process.stdout[-6000:])
    print(process.stderr[-5000:])
    print('returncode='+str(process.returncode))
    raise SystemExit(process.returncode)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['upload','native'])
    parser.add_argument('--timeout',type=int,default=360)
    args=parser.parse_args()
    if args.action=='upload':upload()
    else:execute(args.timeout)
