"""Root binds actual reviews into a new exact-owner promotion copy only."""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def funcs(s):return [ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--independent-review',required=True);parser.add_argument('--independent-sha',required=True);args=parser.parse_args()
 o=guard();ind=Path(args.independent_review).resolve();assert ind.is_relative_to(HERE) and sha(ind)==args.independent_sha
 r=read(ind);assert r['status']=='FOUR_ACTUAL_BFC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED' and r['material_concerns']==[] and len(r['raw_results'])==4
 local=HERE/'bfc_execution_review_prepare/actual_four_result_review.json';assert sha(local)=='b8fa916c6c746e86d03fc3aa4fc3325382e11266c6662de85ece09a35934ae4b'
 assert r['anchors']['local_review']==ref(local)
 dest=HERE/'bfc_promotion_execute';common=dest/'promotion_common.py';s=common.read_text('utf8')
 snapshot=dest/'promotion_common_disabled_current_owner.py.txt'
 with snapshot.open('x',encoding='utf8') as f:f.write(s)
 updates={'DRAFT_EXECUTION_ENABLED':True,'SEMANTIC_REVIEW_PATH':ref(local)['path'],'SEMANTIC_REVIEW_SHA':sha(local),'INDEPENDENT_REVIEW_PATH':ref(ind)['path'],'INDEPENDENT_REVIEW_SHA':sha(ind)}
 lines=s.splitlines(keepends=True);patches=[]
 for n in ast.parse(s).body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in updates:
   key=n.targets[0].id;assert ast.literal_eval(n.value) in [False,None];patches.append((n.lineno-1,n.end_lineno,key+' = '+repr(updates[key])+'\n'))
 assert len(patches)==5
 for a,b,text in sorted(patches,reverse=True):lines[a:b]=[text]
 text=''.join(lines);assert funcs(text)==funcs(s);compile(text,str(common),'exec');common.write_text(text,'utf8')
 sys.path.insert(0,str(dest));import promotion_common as module
 assert module.EXPECTED_OWNER=={k:o[k] for k in module.EXPECTED_OWNER} and module.TOKEN==o['token']
 manifest,raws,reviews=module.reviewed_four_raw();module.protected();module.protected_lifecycle()
 maps={n:sha(dest/n) for n in ['promotion_common.py','fast_forward_tested_bfc.py','dispatch_bfc.py']}
 result={'status':'ROOT_ACTUAL_REVIEW_CONSTANTS_BOUND_FUNCTIONS_UNCHANGED_NOT_EXECUTED','owner':module.EXPECTED_OWNER,'actual_semantic_review':ref(local),'actual_independent_review':ref(ind),'actual_cross_review':ref(HERE/'bfc_actual_result_cross_review.json'),'prepared_file_hashes':maps,'functions_AST_unchanged':True,'read_only_current_guards_passed':True,'selected_gpu':manifest['physical_gpu'],'native_raw_hashes':raws,'Git_mutation_or_sync_or_dispatch_performed':False}
 with (dest/'execution_preparation.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 guard();print(json.dumps({'status':result['status'],'preparation':ref(dest/'execution_preparation.json')}))
if __name__=='__main__':main()
