"""Preserve the unsupported-constructor capture and prepare one grammar-only control."""
from pathlib import Path
import ast
from anchor import guard
HERE=Path(__file__).resolve().parent
guard();s=(HERE/'run_lark_only_control.py').read_text('utf8')
old="kwargs={k.arg:ast.literal_eval(k.value) for k in call.keywords};out['original_constructor_line']=node.lineno"
new="""kwargs={};omitted={}
   for keyword in call.keywords:
    try:kwargs[keyword.arg]=ast.literal_eval(keyword.value)
    except (ValueError,TypeError):omitted[keyword.arg]=ast.dump(keyword.value)
   assert set(omitted)=={'transformer'},'Only the native user-transformer object may be omitted from this grammar compilation control'
   out['original_constructor_line']=node.lineno;out['omitted_native_constructor_kwargs']=omitted
   out['scope_difference']='Original package grammar and literal parser options only. Native user-transformer construction is omitted; no parse or full pccm import equivalence is claimed.'"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('lark_only_control_intent.json','lark_only_control_r1_intent.json').replace('lark_only_control_result.json','lark_only_control_r1_result.json')
s=s.replace('EXACT_PCCM_GRAMMAR_LARK_CONSTRUCTION','ORIGINAL_GRAMMAR_WITHOUT_USER_TRANSFORMER_LARK_CONSTRUCTION')
s=s.replace('one upstream pure-Lark','one upstream grammar-only pure-Lark')
ast.parse(s);guard()
with (HERE/'run_lark_grammar_control.py').open('x',encoding='utf8') as f:f.write(s)
