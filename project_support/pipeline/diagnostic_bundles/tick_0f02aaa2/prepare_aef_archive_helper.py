"""Adapt only exact task/owner/observation identities in the prior canonical archive helper."""
from pathlib import Path
import ast
from anchor import ROOT,guard
HERE=Path(__file__).resolve().parent
guard()
s=(ROOT/'pipeline/diagnostic_bundles/tick_458bf62f/archive_bec_normal_terminal.py').read_text('utf8')
replacements=[
 ('from anchor_bfc_packet import guard','from anchor import guard'),
 ('458bf62f20024209b63da2009998d280','0f02aaa25b1a4f6e9d27cf8da33b8ca1'),
 ('026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563','56b2a96dc48cc8a88f0f7105527ef448113b1060'),
 ('M215-BEC','M216-AEF'),('1558071','759301'),
 ('113a72afb83c57401d00072b1a723a5cc3094a76a1e2d9acfe75b465f10238dc','041074985258a51cf2a5629dcbf19f55fceb42c5255c78251c1fb9cc680ae9a9'),
 ('bbd04aba05cbac4629cb0a5c96c3598a6f725104b8c1f0cc1318b814475758d3','01ff5497bd7413d238c2e45f002aa5cccfda988eae11d7ac4c6267f3b26fe2ea'),
 ('ctf_hcg_csort_bec','ctf_hcg_csort_aef'),('20261026_231823.log','20261027_124036.log'),
 ('bec_','aef_'),('BEC_','AEF_'),
 ("obs['owner_token']==TOKEN","obs['owner']['token']==TOKEN"),
 ("obs['reviewed_AEF_readonly_probe']","obs['reviewed_CRE_readonly_probe']"),
 ('epoch 24','epoch 23'),('24/50','23/50'),('24of50','23of50'),('0.5001','0.4956')]
for old,new in replacements:
    assert old in s,old
    s=s.replace(old,new)
assert 'M215' not in s and '1558071' not in s and 'epoch 24' not in s
ast.parse(s);guard()
with (HERE/'archive_aef_normal_terminal.py').open('x',encoding='utf8') as f:f.write(s)
print('Exact canonical AEF archive helper prepared; no archive executed.')
