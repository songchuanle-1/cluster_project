"""Root catalogue of exact actually frozen and independently reviewed packets."""
from pathlib import Path
from datetime import datetime,timezone
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
def anchored(relative,expected):
    p=ROOT/relative;assert sha(p)==expected,relative
    return u.ref(p)
def main():
    guard();assert sha(HERE/'register_preparations.py')=='d98088fdaafcf7947086a73c448df404ac699d3c1ba19aa33d8ecd985da6a9e0'
    assert sha(HERE/'root_registration_independent_review.json')=='f1bd8b794fdc61d10720d96d8578201fbce692e8d0090a55f7e329bb2240d0db'
    entries=[]
    cases=[
        (u.HPC,'hpc','6282263d805c1741234f97afc981a05aca2ad6e3',[
            ('source_version','pipeline/diagnostic_bundles/tick_fd073f88/hpc_compatible_prepare/version_prepare/isolated_source_version.json','f82a3f05683503ff6e2c0931f93c5afe5af5d095af1453e3fb8f1c0a7327adb9'),
            ('source_review','pipeline/diagnostic_bundles/tick_fd073f88/hpc_compatible_actual_source_version_independent_review.json','24e906ad6b15ffd3efa716026008d66e74a80b129bb5ddc4fa7f4e361b63d8b3'),
            ('native_preparation','pipeline/diagnostic_bundles/tick_fd073f88/hpc_compatible_prepare/native/preparation.json','ab13cba6418ab9ba733e2b0ecfbe203a220b4b472346623a3835ce11803593b3'),
            ('native_review','pipeline/diagnostic_bundles/tick_fd073f88/hpc_compatible_preparation_independent_review.json','74324fbf74085cac96182874b10dcccfbd8372f5d87f740e5c378b1aaf68ddfd'),
            ('operational_preparation','pipeline/diagnostic_bundles/tick_fd073f88/hpc_compatible_prepare/preparation.json','789ccef52b93106b06c1039257436ea67a9415ee0d2d0e2fe98ebe0182d6beb4'),
            ('operational_review','pipeline/diagnostic_bundles/tick_fd073f88/hpc_compatible_preparation_independent_review.json','74324fbf74085cac96182874b10dcccfbd8372f5d87f740e5c378b1aaf68ddfd')]),
        (u.APF,'apf','bf6c3fafe0f690e16e838e7c0192f09e789389f9',[
            ('source_version','pipeline/diagnostic_bundles/tick_01b53a4e/apf_version_prepare/isolated_source_version.json','1155758ae85244a4a6b6d7f90053717c1d2578b8852f7e77c2ea4697b383b2cd'),
            ('source_review','pipeline/diagnostic_bundles/tick_01b53a4e/apf_actual_source_version_independent_review.json','3f02f0828b9a3ff47670cddad3c413ef15e403d115eb5059c6f91ea3d4b50c25'),
            ('native_preparation','pipeline/diagnostic_bundles/tick_fd073f88/apf_native_prepare/preparation.json','4c44cdac3c9a40ba0178eca2b8021debb6e322f3fc172fe1e7e3ae9874fb6f3f'),
            ('native_review','pipeline/diagnostic_bundles/tick_fd073f88/apf_native_preparation_independent_review.json','8ed1773b9c70ec6df04357ebe670b6cf25bab49e8d47b75c4c077c84b9846765'),
            ('operational_preparation','pipeline/diagnostic_bundles/tick_fd073f88/apf_operational_prepare/preparation.json','64f5aafb3230e94e92aa233d245cf95151b0674360220883c8add92ffcb67f3d'),
            ('operational_review','pipeline/diagnostic_bundles/tick_fd073f88/apf_operational_preparation_independent_review.json','c63951a5f9a93d6971864e9f9c2fc81fc9a0f69eb553b551f52ade5a6e85c0f1')])]
    for cid,short,commit,fields in cases:
        entry={'id':cid,'short':short,'code_commit':commit,'source_parent_commit':u.SOURCE,'execution_directory':short+'_execution'}
        for name,path,expected in fields:entry[name]=anchored(path,expected)
        evidence=[]
        for name,_,_ in fields:
            if entry[name] not in evidence:evidence.append(entry[name])
        for name in ('native_preparation','operational_preparation'):
            prepared=u.read(ROOT/entry[name]['path'])
            for k,v in prepared.items():
                if isinstance(v,dict) and set(v)=={'path','sha256'}:
                    u.check_refs([v])
                    if v not in evidence:evidence.append(v)
        entry['evidence']=evidence;entries.append(entry)
    u.save(HERE/'packet_catalogue.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),
        'owner':EXPECTED,'candidates':entries,'registration_program_review':u.ref(HERE/'root_registration_independent_review.json'),
        'scope':'Current static source/native/op catalogue only; exact two existing candidates, no execution binding, GPU grant or native PASS.'})
    print({'catalogue':u.ref(HERE/'packet_catalogue.json'),'existing_candidates':len(entries)})
if __name__=='__main__':main()
