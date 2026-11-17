from pathlib import Path
import ast,hashlib,json
HERE=Path(__file__).resolve().parent
source=HERE.parent/'tick_45eb3b04/verify_protected_assets_v3.py'
s=source.read_text('utf8');old='48fc302c3c02ffef0b241be3593c386b6b65a72e';assert s.count(old)==1
s=s.replace(old,'4e80006047d5cb3dcdfb9c1102e02c33f354a07d')
needle="'admissions/M213-BFC.json']";assert s.count(needle)==1
s=s.replace(needle,"'admissions/M213-BFC.json','experiments/M214-CTS.json','admissions/M214-CTS.json']")
ast.parse(s);target=HERE/'verify_protected_assets.py'
with target.open('x',encoding='utf8') as f:f.write(s)
with (HERE/'protection_checker_provenance.json').open('x',encoding='utf8') as f:json.dump({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'current_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'changes':'Expected primary nowactual4e8; protect additionallyCTS experiment/admission. Only fresh owner guard imported; no runtime/source mutation.'},f,indent=2);f.write('\n')
