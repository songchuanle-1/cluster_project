'Owner-guarded LFT execution adapter. Importing it performs no remote action.\n\nThis prepared program does not create a binding, manifest or lease until its\nexplicit prepare operation succeeds against a current idle authorized card.\nIt never generates admission/queue/PASS artifacts from unexecuted preparation.\n'
import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import uuid
import yaml

PROJECT_ROOT = Path('D:/project/cluster_project')
FROZEN = PROJECT_ROOT/'pipeline/diagnostic_bundles/tick_d94467a9/lft_native_compatible_prepare'
ORIGIN = Path(__file__).resolve().parent
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
PREPARATION_SHA = '6663d50a5f65f0a402075e5516d14dbf7dba01c9b54fc401c195a089be3da2c3'
TEMPLATE_SHA = 'eb503c0ed872f212db14a259803d75cca3a137fc04bdb93e81197f6d9f356bf1'
COMMIT = '4457a46f9075f61e83340aa0f0af87d5bf4e986c'
CANDIDATE = 'hierarchy-nonlinear-lifting-analysis-synthesis'
EXPECTED_RUNTIME_COMMIT = '94c4fe61b38f46f321a7ee84236fea70ade04d9b'
DRAFT_EXECUTION_DISABLED = False
RESOURCE_AUTHORIZATION = {'path': 'pipeline/authorizations/server4_gpu1_20261030.json', 'sha256': '6529ecf4cb9bc39c698650e3116df67870a2f82e76c046296c8a1e74aa0d68c2'}
SERVERS_POLICY_SHA256 = '19b3753d13a8253263c6525f19a739795b816be141e21a9f9b3aaccddf4f8265'
POLICY_GPU_UUIDS = {0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
REMOTE_ROOT = '/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
REMOTE_PARENT = '/data/songcl/Project/Cluster_project/pipeline'
GPU_UUIDS = {1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
PAIRS = (('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate'))


STANDING_AUTHORIZATION = {'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'}
PARENT_EXPERIMENT = 'M226-WFC'
PARENT_CANDIDATE = 'hierarchy-wedge-factor-incidence-composition'
PARENT_CONFIG = 'configs/Quard/ctf_hcg_csort_wfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_wfc.yaml'


def validate_parent_technical_receipt(root,receipt,authorization,artifact_validator,smoke_validator,gates):
    require(isinstance(receipt,dict),'WFC technical receipt must be an object')
    require(authorization==STANDING_AUTHORIZATION and receipt.get('authorization')==authorization,'WFC technical receipt standing authorization mismatch')
    expected={'id':PARENT_EXPERIMENT,'candidate_id':PARENT_CANDIDATE,'config':PARENT_CONFIG,
              'code_commit':EXPECTED_RUNTIME_COMMIT,'goal_sha256':GOAL,'profile':'experiment_first'}
    require(all(receipt.get(k)==v for k,v in expected.items()),'WFC technical receipt identity/version/profile mismatch')
    # These are the canonical existing technical validators only. No candidate
    # stage, training status, completion, accuracy or new scientific gate is read.
    smoke_validator(root,receipt)
    for name in gates:
        gate=receipt.get('gates',{}).get(name,{})
        require(gate.get('passed') is True and isinstance(gate.get('evidence'),list) and bool(gate['evidence']),'WFC technical admission gate incomplete: '+name)
        for entry in gate['evidence']:artifact_validator(root,entry)
    artifact_validator(root,receipt['decision'])
    return receipt


class Refused(RuntimeError): pass
class ReplayRefused(Refused): pass
class Uncertain(Refused): pass


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utcnow():
    return datetime.now(timezone.utc)


def require(condition, reason):
    if not condition:
        raise Refused(reason)


class SSHTransport:
    """Only this class can connect. Unit tests inject an in-memory transport."""
    def __init__(self, origin=ORIGIN):
        self.origin = Path(origin)

    def call(self, operation, payload, server, *, timeout, conda=False):
        require(server.get('user')=='songcl' and server.get('host')=='192.168.1.115','Pinned SSH account/host mismatch')
        source = (self.origin/'remote_ops.py').read_bytes()
        wire = base64.b64encode(json.dumps(payload, allow_nan=False).encode()).decode()
        script = ("import base64,json,socket\nassert socket.gethostname()=='dl04-MS-7E06'\n"
            + "exec(compile(base64.b64decode("+repr(base64.b64encode(source).decode())+"),'lft_remote_ops','exec'))\n"
            + 'payload=json.loads(base64.b64decode('+repr(wire)+'))\n'
            + 'print(json.dumps(dispatch('+repr(operation)+',payload),allow_nan=False))\n')
        python = shlex.join(['/usr/bin/python3','-B','-'])
        if conda:
            python = shlex.join(['bash','-lc','source '+shlex.quote(server['conda_source'])
                +' && conda activate '+shlex.quote(server['conda_env'])+' && python -B -'])
        command = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
            '-o','ConnectTimeout=10',server['user']+'@'+server['host'],python]
        try:
            process = subprocess.run(command,input=script,text=True,encoding='utf-8',
                errors='replace',capture_output=True,timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise Uncertain('SSH timeout; original remote request may still be running') from error
        if process.returncode != 0:
            raise Uncertain('SSH/remote nonzero; reconcile exact request before any further mutation: '+process.stderr[-3000:])
        try:
            result=json.loads(process.stdout)
            require(isinstance(result,dict),'Remote reply must be a JSON object')
            return result
        except (ValueError,Refused) as error:
            raise Uncertain('Unparseable remote reply; reconcile exact original request') from error


class Adapter:
    def __init__(self, root=PROJECT_ROOT, frozen=FROZEN, transport=None, env=None,
                 clock=utcnow, execution_dir=None, origin=ORIGIN):
        self.root=Path(root).resolve(); self.frozen=Path(frozen).resolve()
        self.origin=Path(origin).resolve(); self.transport=transport or SSHTransport(self.origin)
        self.env=os.environ if env is None else env; self.clock=clock
        self.explicit_execution_dir=Path(execution_dir).resolve() if execution_dir is not None else None

    def _frozen_details(self):
        require(isinstance(COMMIT,str) and re.fullmatch(r'[0-9a-f]{40}',COMMIT) is not None,'Exact promoted source commit is required')
        require(sha(self.frozen/'preparation.json')==PREPARATION_SHA,'Frozen preparation changed')
        p=read(self.frozen/'preparation.json')
        require(sha(self.frozen/'manifest_template.json')==TEMPLATE_SHA,'Frozen template changed')
        require(p['source_commit']==COMMIT and p['candidate_id']==CANDIDATE,'Frozen candidate mismatch')
        for name,expected in p['prepared_file_hashes'].items():
            path=(self.frozen/name).resolve()
            require(path.is_relative_to(self.frozen) and sha(path)==expected,'Frozen file changed: '+name)
        return p,read(self.frozen/'manifest_template.json')

    def _release_details(self):
        # This is a static reviewed-module anchor, never a lease or GPU grant.
        release_path=self.origin/'adapter_release.json'
        require(release_path.is_file(),'Reviewed static adapter release missing; no transport or execution material may be created')
        release=read(release_path); template=read(self.origin/'release_template.json')
        require(release==template,'Static release differs from reviewed module/version template')
        require(release.get('candidate_id')==CANDIDATE and release.get('code_commit')==COMMIT
            and release.get('native_preparation_sha256')==PREPARATION_SHA,'Release candidate/version/native packet mismatch')
        require(set(release['source_hashes'])=={'adapter.py','remote_ops.py'},'Incomplete adapter release')
        candidates=read(self.root/'pipeline/research_work.json').get('candidates',[])
        matches=[c for c in candidates if c.get('id')==CANDIDATE]
        require(len(matches)==1 and matches[0].get('code_commit')==COMMIT
            and matches[0].get('goal_sha256')==GOAL,'Current candidate/version for external anchor is missing')
        anchors=matches[0].get('execution_adapter') or {}
        prepared_ref=anchors.get('preparation') or {}; release_ref=anchors.get('release') or {}
        prepared_path=self.origin/'preparation.json'
        require((self.root/prepared_ref.get('path','')).resolve()==prepared_path.resolve()
            and prepared_ref.get('sha256')==sha(prepared_path),'External adapter preparation anchor missing/mismatched')
        prepared=read(prepared_path)
        require(prepared.get('candidate_id')==CANDIDATE and prepared.get('code_commit')==COMMIT,'External preparation identity mismatch')
        require({'adapter.py','remote_ops.py','release_template.json'}<=set(prepared['prepared_file_hashes']),'Incomplete external package map')
        for name,expected in prepared['prepared_file_hashes'].items():
            path=(self.origin/name).resolve()
            require(path.is_relative_to(self.origin) and sha(path)==expected,'Externally anchored package changed: '+name)
        require((self.root/release_ref.get('path','')).resolve()==release_path.resolve()
            and release_ref.get('sha256')==sha(release_path),'External static release anchor missing/mismatched')
        for name,expected in release['source_hashes'].items():
            path=(self.origin/name).resolve()
            require(path.is_relative_to(self.origin) and sha(path)==expected,'Adapter release changed: '+name)
        return release

    def guard(self, required_seconds=0, gpu=None, mutation=False):
        owner=read(self.root/'pipeline/headless/.foreground.lockdir/owner.json')
        mode=read(self.root/'pipeline/execution_mode.json')
        resource_path=(self.root/RESOURCE_AUTHORIZATION['path']).resolve()
        require(resource_path.is_relative_to(self.root) and sha(resource_path)==RESOURCE_AUTHORIZATION['sha256'],'Current explicit retained-GPU0 plus GPU1 resource authorization changed')
        require(mode.get('mode')=='foreground','Foreground mode required')
        require(owner.get('thread_id')==mode.get('target_thread_id')==self.env.get('CODEX_THREAD_ID')==THREAD,
                'Actual owner/environment/execution-mode identity mismatch')
        require(re.fullmatch(r'[0-9a-f]{32}',owner.get('token','')) is not None,'Invalid owner token')
        generated=datetime.fromisoformat(owner['generated_at']); deadline=datetime.fromisoformat(owner['deadline_at'])
        now=self.clock()
        require(generated.tzinfo is not None and deadline.tzinfo is not None and generated<=now<deadline,'Owner lease expired/future/ambiguous')
        require(0<(deadline-generated).total_seconds()<=3600,'Owner deadline window invalid')
        require((deadline-now).total_seconds()>required_seconds,'Insufficient unchanged owner deadline')
        require(sha(self.root/'pipeline/goal.json')==GOAL,'Goal changed')
        require(sha(self.root/'pipeline/headless/.tick_context.json')==owner['context_sha256'],'Current context hash mismatch')
        require(sha(self.root/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256'],'Pending state hash mismatch')
        context=read(self.root/'pipeline/headless/.tick_context.json')
        require(context.get('project')=='cluster_project' and context['generated_at']==owner['generated_at'] and context['deadline_at']==owner['deadline_at'],'Context owner binding mismatch')
        closure_policy=read(self.root/'pipeline/closure_policy.json')
        policy=closure_policy.get('experiment_first',{})
        current=context.get('experiment_first',{})
        if mutation:
            require(closure_policy.get('enabled') is True and policy.get('enabled') is True and current.get('enabled') is True,'Current closure/experiment-first opt-in required')
        require(policy.get('authorization')==current.get('authorization'),'Snapshot authorization mismatch')
        ref=policy['authorization']; path=(self.root/ref['path']).resolve()
        require(path.is_relative_to(self.root) and sha(path)==ref['sha256'],'Authorization hash/path mismatch')
        authorization=read(path)
        require(authorization.get('project')=='cluster_project','Authorization project changed')
        if mutation:
            require(authorization.get('authorization_granted') is True and 'native_checks_on_authorized_resources' in authorization.get('operations',[]),'Native checks not authorized')
        require(sha(self.root/'SERVERS.yaml')==SERVERS_POLICY_SHA256,'Current exact SERVERS resource policy changed')
        server=yaml.safe_load((self.root/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
        require(server.get('user')=='songcl' and server.get('host')=='192.168.1.115' and server.get('expected_hostname')=='dl04-MS-7E06','Pinned server identity changed')
        require(server.get('remote_code_root')==REMOTE_ROOT and server.get('max_tasks_per_gpu')==1,'Runtime root/concurrency contract changed')
        if mutation:
            require(server.get('enabled',True) is True and server.get('dispatch_enabled') is True,'Server/dispatch disabled')
        allowed=server.get('allowed_gpus')
        require(isinstance(allowed,list) and all(type(g) is int and g in POLICY_GPU_UUIDS for g in allowed)
            and len(set(allowed))==len(allowed),'GPU whitelist is unknown or outside the current exact resource policy')
        require(allowed==[0,1],'This LFT policy copy requires exact current [0,1] authorization; selected capability remains GPU1 only')
        uuids={str(k):v for k,v in server['expected_gpu_uuids'].items()}
        require(all(uuids.get(str(g))==POLICY_GPU_UUIDS[g] for g in allowed),'GPU UUID map changed')
        if gpu is not None:
            require(type(gpu) is int and gpu in GPU_UUIDS,'Only physical server4 GPU1 is permitted for this LFT packet')
            if mutation: require(gpu in allowed,'Selected GPU is not currently allowed')
        if mutation:
            require(bool(allowed),'No currently allowed GPU')
            snapshots=[x for x in context.get('queue',{}).get('servers',[]) if x.get('name')=='server-4']
            require(len(snapshots)==1 and snapshots[0].get('allowed_gpus')==allowed
                and snapshots[0].get('max_tasks_per_gpu')==server['max_tasks_per_gpu'],'Snapshot/live resource authorization differs')
            self._require_parent_promotion(ref)
            self._candidate_ready(ref)
        self._frozen_details(); self._release_details()
        require(read(self.root/'pipeline/headless/.foreground.lockdir/owner.json')==owner,'Owner changed during guard')
        return {'owner':owner,'server':server,'authorization':ref,'remaining_seconds':(deadline-now).total_seconds()}

    def _require_parent_promotion(self,authorization):
        require(not DRAFT_EXECUTION_DISABLED,'LFT capability is disabled')
        receipt_path=self.root/'pipeline/admissions/M226-WFC.json'
        require(receipt_path.is_file(),'LFT conditional parent pending: genuine WFC technical receipt is absent; no prepare/stage/run')
        receipt=read(receipt_path)
        import sys
        sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
        import closure,experiment_first
        try:
            validate_parent_technical_receipt(self.root,receipt,authorization,closure.artifact,experiment_first.validate_smoke,experiment_first.GATES)
        except (ValueError,KeyError,TypeError,OSError) as error:
            raise Refused('WFC technical receipt/artifact validation refused: '+str(error)) from error
        # Read-only local HEAD check, never checkout/ff/sync or optional index refresh.
        command=['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-c','core.fsmonitor=false','-C',str(self.root/'Cluster'),'rev-parse','HEAD']
        observed=subprocess.run(command,capture_output=True,text=True,encoding='utf8',timeout=15,
            env=dict(self.env,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
        require(observed.returncode==0 and observed.stdout.strip()==EXPECTED_RUNTIME_COMMIT,
            'LFT conditional parent pending: actual primary HEAD must be promoted WFC94; receipt alone is insufficient')

    def _candidate_ready(self,authorization):
        candidates=read(self.root/'pipeline/research_work.json').get('candidates',[])
        matches=[c for c in candidates if c.get('id')==CANDIDATE]
        require(len(matches)==1,'LFT candidate missing/ambiguous')
        candidate=matches[0]
        require(candidate.get('experiment_id')=='M227-LFT' and candidate.get('code_commit')==COMMIT
            and candidate.get('goal_sha256')==GOAL and candidate.get('authorization')==authorization,'LFT candidate identity/version/authorization changed')
        _,template=self._frozen_details()
        require(candidate.get('config')==template['config'],'LFT candidate native config changed')
        stage=candidate.get('stage');kind=candidate.get('blocker_kind')
        eligible=stage=='validation' or (stage=='blocked' and candidate.get('resume_stage')=='validation'
            and kind in ('resource','exclusive_gpu_slot'))
        require(eligible and kind in (None,'','resource','exclusive_gpu_slot'),'Candidate is not in eligible validation/resource-blocked state')
        holds=('human_hold','scope_hold','numerical_hold','dispatch_hold','admission_error','hold','paused',
               'requires_human','requires_confirmation','needs_confirmation')
        require(not any(candidate.get(k) for k in holds),'Candidate has a human/scope/numerical or dispatch hold')
        require(not candidate.get('revision_history') and not candidate.get('implementation_revision_sha256'),
            'Candidate revision requires separately tested/reviewed implementation binding')
        prepared=candidate.get('worker_preparation',{}).get('preparation')
        if prepared is not None:require(prepared.get('sha256')==PREPARATION_SHA,'Candidate worker preparation changed')

    def _directory(self, current=None):
        if self.explicit_execution_dir is not None:
            path=self.explicit_execution_dir
        else:
            current=current or self.guard()
            path=self.root/'pipeline/diagnostic_bundles'/('tick_'+current['owner']['token'][:8])/'lft_execution'
        require(path.resolve().is_relative_to((self.root/'pipeline/diagnostic_bundles').resolve()),'Execution directory outside project diagnostics')
        return path.resolve()

    def _save(self, directory, name, value):
        current=self.guard()
        require(Path(name).name==name,'Invalid artifact filename')
        directory=Path(directory); require(directory.resolve().is_relative_to((self.root/'pipeline/diagnostic_bundles').resolve()),'Artifact outside diagnostics')
        expected=self.root/'pipeline/diagnostic_bundles'/('tick_'+current['owner']['token'][:8])/'lft_execution'
        require(directory.resolve()==expected.resolve(),'Refuse writing a different/expired tick execution directory')
        directory.mkdir(parents=True,exist_ok=True)
        with (directory/name).open('x',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        return directory/name

    def _local_idle(self,gpu):
        running=read(self.root/'pipeline/running.json').get('server-4',{})
        require(not running.get(str(gpu)) and not running.get(gpu),'Selected GPU has registered running task')
        allowed=yaml.safe_load((self.root/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']['allowed_gpus']
        tasks=read(self.root/'pipeline/queue.json')['gpu_queues'].get('server-4',[])
        for task in tasks:
            status=task.get('status');hold=task.get('dispatch_hold','')
            uncertain_hold=isinstance(hold,str) and hold.startswith(('Interrupted claim;','Launch uncertain;','Process observed'))
            reserved=status in ('claiming','running') or (status=='waiting' and
                (task.get('launch_verification')=='pending_progress' or uncertain_hold))
            if reserved:
                require('gpu' in task,'Active queue task has unknown GPU; reconcile canonical state first')
                value=task['gpu']
                require((type(value) is int and value in POLICY_GPU_UUIDS) or (type(value) is str and value in ('0','1')),'Active queue GPU is malformed/unknown')
                require(int(value) in allowed,'Active queue assignment is outside current whitelist; canonical reconcile required')
                require(int(value)!=gpu,'Selected GPU is reserved by active/pending/launch-uncertain queue task')

    def _check_probe(self, observation, gpu):
        require(observation.get('server_id')=='server-4' and observation.get('hostname')=='dl04-MS-7E06','Remote server identity unknown')
        require(observation.get('root')==REMOTE_ROOT and observation.get('physical_gpu')==gpu
            and observation.get('gpu_uuid')==GPU_UUIDS[gpu],'Remote root/GPU identity mismatch')
        require(observation.get('runtime_code_commit')==EXPECTED_RUNTIME_COMMIT,'Runtime HEAD is not exact expected WFC parent94')
        require(observation.get('idle') is True and not observation.get('contexts'),'Authorized GPU is busy')
        require(observation.get('memory_used_mib',1024)<1024 and observation.get('utilization_percent',100)<10,'GPU idle bounds failed')
        require(observation.get('locks')=={k:'available' for k in ('training','diagnostic','exclusive')},'GPU lock is busy/unknown')

    def probe(self,gpu):
        require(type(gpu) is int and gpu in GPU_UUIDS,'Explicit physical GPU1 is required')
        current=self.guard(150,gpu)
        require(gpu in current['server']['allowed_gpus'],'Selected probe GPU is not currently allowed')
        result=self.transport.call('probe',{'physical_gpu':gpu},current['server'],timeout=30)
        # Probe reports busy without creating a binding; mutations call _check_probe.
        require(result.get('physical_gpu')==gpu and result.get('gpu_uuid')==GPU_UUIDS[gpu]
            and result.get('hostname')=='dl04-MS-7E06','Probe identity mismatch')
        return result

    def prepare(self,gpu):
        require(type(gpu) is int and gpu in GPU_UUIDS,'Explicit physical GPU1 is required')
        current=self.guard(360,gpu,mutation=True); self._local_idle(gpu)
        directory=self._directory(current)
        require(not directory.exists(),'Fresh execution directory required; reconcile existing preparation instead')
        probe=self.probe(gpu); self._check_probe(probe,gpu)
        current=self.guard(360,gpu,mutation=True); self._local_idle(gpu)
        _,template=self._frozen_details(); owner=current['owner']
        manifest=copy.deepcopy(template)
        stage=REMOTE_PARENT+'/lft_'+owner['token'][:8]+'_gpu'+str(gpu)
        manifest.update(current_token=owner['token'],stage=stage,tick_generated_at=owner['generated_at'],deadline_at=owner['deadline_at'],
            physical_gpu=gpu,gpu_uuid=GPU_UUIDS[gpu],allowed_gpus=current['server']['allowed_gpus'],context_sha256=owner['context_sha256'],
            pending_sha256=owner['pending_sha256'],runtime_code_commit=probe['runtime_code_commit'])
        request={'operation':'prepare','request_id':uuid.uuid4().hex,'project':'cluster_project','candidate_id':CANDIDATE,
            'token':owner['token'],'stage':stage,'physical_gpu':gpu,'gpu_uuid':GPU_UUIDS[gpu]}
        self._save(directory,'prepare_request.json',request)
        manifest_path=self._save(directory,'native_manifest.json',manifest)
        lease={'project':'cluster_project','thread_id':THREAD,'native_manifest_sha256':sha(manifest_path),'token':owner['token'],
            'generated_at':owner['generated_at'],'deadline_at':owner['deadline_at'],'server_id':'server-4','physical_gpu':gpu,
            'gpu_uuid':GPU_UUIDS[gpu],'allowed_gpus':current['server']['allowed_gpus'],'goal_sha256':GOAL,
            'context_sha256':owner['context_sha256'],'pending_sha256':owner['pending_sha256']}
        lease_path=self._save(directory,'execution_lease.json',lease)
        binding={'schema_version':1,'project':'cluster_project','candidate_id':CANDIDATE,'code_commit':COMMIT,'goal_sha256':GOAL,
            'frozen_preparation_sha256':PREPARATION_SHA,'frozen_template_sha256':TEMPLATE_SHA,
            'owner':{k:owner[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')},
            'server_binding':{k:current['server'][k] for k in ('host','user','expected_hostname','remote_code_root','allowed_gpus','max_tasks_per_gpu','expected_gpu_uuids','conda_source','conda_env')},
            'physical_gpu':gpu,'gpu_uuid':GPU_UUIDS[gpu],'stage':stage,'runtime_code_commit':probe['runtime_code_commit'],
            'native_manifest_sha256':sha(manifest_path),'execution_lease_sha256':sha(lease_path),'prepare_probe':probe,
            'adapter_release_sha256':sha(self.origin/'adapter_release.json')}
        self._save(directory,'execution_binding.json',binding)
        return binding

    def _binding(self, mutation=False, required_seconds=0):
        current=self.guard(required_seconds)
        directory=self._directory(current); binding=read(directory/'execution_binding.json')
        require(binding.get('project')=='cluster_project' and binding.get('candidate_id')==CANDIDATE
            and binding.get('code_commit')==COMMIT and binding.get('goal_sha256')==GOAL,'Foreign binding refused')
        require(binding['frozen_preparation_sha256']==PREPARATION_SHA and binding['frozen_template_sha256']==TEMPLATE_SHA,'Binding provenance changed')
        gpu=binding['physical_gpu']; require(type(gpu) is int and gpu in GPU_UUIDS and binding['gpu_uuid']==GPU_UUIDS[gpu],'Binding GPU must be physical1 with exact selected UUID')
        old=binding['owner']; require(set(old)=={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'},'Binding owner schema incomplete/expanded')
        require(old['thread_id']==THREAD and re.fullmatch(r'[0-9a-f]{32}',old['token']) is not None,'Binding owner unknown')
        require(all(re.fullmatch(r'[0-9a-f]{64}',old[k]) is not None for k in ('context_sha256','pending_sha256')),'Binding context/pending hash malformed')
        require(binding['stage']==REMOTE_PARENT+'/lft_'+old['token'][:8]+'_gpu'+str(gpu),'Binding stage mismatch')
        require(sha(directory/'native_manifest.json')==binding['native_manifest_sha256'] and sha(directory/'execution_lease.json')==binding['execution_lease_sha256'],'Binding manifest/lease hash changed')
        server=binding['server_binding']
        require(server['user']=='songcl' and server['host']=='192.168.1.115' and server['expected_hostname']=='dl04-MS-7E06' and server['remote_code_root']==REMOTE_ROOT,'Foreign server binding')
        _,template=self._frozen_details()
        expected_manifest=copy.deepcopy(template)
        expected_manifest.update(current_token=old['token'],stage=binding['stage'],tick_generated_at=old['generated_at'],
            deadline_at=old['deadline_at'],physical_gpu=gpu,gpu_uuid=GPU_UUIDS[gpu],allowed_gpus=server['allowed_gpus'],
            context_sha256=old['context_sha256'],pending_sha256=old['pending_sha256'],runtime_code_commit=binding['runtime_code_commit'])
        require(read(directory/'native_manifest.json')==expected_manifest,'Manifest content is not the exact frozen template/current binding')
        expected_lease={'project':'cluster_project','thread_id':THREAD,'native_manifest_sha256':binding['native_manifest_sha256'],
            'token':old['token'],'generated_at':old['generated_at'],'deadline_at':old['deadline_at'],'server_id':'server-4',
            'physical_gpu':gpu,'gpu_uuid':GPU_UUIDS[gpu],'allowed_gpus':server['allowed_gpus'],'goal_sha256':GOAL,
            'context_sha256':old['context_sha256'],'pending_sha256':old['pending_sha256']}
        require(read(directory/'execution_lease.json')==expected_lease,'Lease content differs from exact original binding')
        if mutation:
            require(old=={k:current['owner'][k] for k in old},'Mutation requires this exact current owner/token/context/deadline; old binding is read-only')
            require(binding['adapter_release_sha256']==sha(self.origin/'adapter_release.json'),'Adapter release changed after prepare')
            require(all(current['server'].get(k)==v for k,v in server.items()),'Current server authorization differs from execution binding')
            current=self.guard(required_seconds,gpu,mutation=True)
            require(old=={k:current['owner'][k] for k in old},'Owner changed during mutation guard')
            self._local_idle(gpu)
        return current,directory,binding

    def _identity(self,binding,request_id,operation):
        return {'project':'cluster_project','candidate_id':CANDIDATE,'code_commit':COMMIT,
            'stage':binding['stage'],'token':binding['owner']['token'],'request_id':request_id,'operation':operation,
            'physical_gpu':binding['physical_gpu'],'gpu_uuid':binding['gpu_uuid'],'native_manifest_sha256':binding['native_manifest_sha256']}

    def _read_reconcile(self,current,directory,binding,request_id=None):
        payload={'binding':binding,'request_id':request_id}
        data=self.transport.call('reconcile',payload,current['server'],timeout=40)
        require(data.get('stage')==binding['stage'] and data.get('native_manifest_sha256') in (None,binding['native_manifest_sha256']),
            'Reconcile reply is not the exact original stage/manifest')
        return data

    def reconcile(self,operation_id=None):
        # Current actual owner authorizes read-only observation of an expired old
        # binding. Never refresh or rewrite that old lease or make it executable.
        current,directory,binding=self._binding(mutation=False,required_seconds=60)
        return self._read_reconcile(current,directory,binding,operation_id)

    def status(self,remote=True):
        current,directory,binding=self._binding(mutation=False,required_seconds=60 if remote else 0)
        local={'binding':binding,'current_owner_token':current['owner']['token'],
            'binding_is_current':binding['owner']['token']==current['owner']['token'],
            'request_files':[p.name for p in sorted(directory.glob('*_request.json'))],
            'result_files':[p.name for p in sorted(directory.glob('*_execution.json'))]}
        if remote:
            local['remote']=self._read_reconcile(current,directory,binding)
        return local

    def _no_replay(self,current,directory,binding,name):
        path=directory/(name+'_request.json')
        if path.exists():
            original=read(path)
            observation=self._read_reconcile(current,directory,binding,original['request_id'])
            raise ReplayRefused('Existing request is never replayed; exact read-only reconcile: '+json.dumps(observation,allow_nan=False))

    def _perform(self,operation,request,binding,current,directory,*,timeout,conda=False,payload=None):
        data={'binding':binding,'request':request,**(payload or {})}
        result=None
        try:
            result=self.transport.call(operation,data,current['server'],timeout=timeout,conda=conda)
            expected=self._identity(binding,request['request_id'],operation)
            require(isinstance(result,dict) and result.get('identity')==expected,'Remote request identity mismatch')
            require(result.get('certainty')=='terminal','Remote subprocess is uncertain')
            return result
        except (Uncertain,Refused,KeyError,TypeError) as error:
            record={'certainty':'uncertain','request':request,'error':str(error),'reply':result}
            try: record['reconcile']=self._read_reconcile(self.guard(60),directory,binding,request['request_id'])
            except Exception as followup: record['reconcile_error']=str(followup)
            self._save(directory,'uncertain_'+request['request_id']+'.json',record)
            raise Uncertain('Execution uncertain; exact request reconciled or remains unknown; never replay') from error

    def _raw_result_identity(self,value,binding,mode,target):
        base='framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
        expected={'candidate_id':CANDIDATE,'code_commit':COMMIT,'goal_sha256':GOAL,'mode':mode,'target':target,
            'model_package':base+('_lft' if target=='candidate' else '')}
        return isinstance(value,dict) and all(value.get(k)==v for k,v in expected.items())

    def stage(self):
        current,directory,binding=self._binding(mutation=True,required_seconds=420)
        self._no_replay(current,directory,binding,'stage')
        probe=self.probe(binding['physical_gpu']); self._check_probe(probe,binding['physical_gpu'])
        require(probe['runtime_code_commit']==binding['runtime_code_commit'],'Runtime HEAD changed since prepare')
        current,_,binding=self._binding(mutation=True,required_seconds=420)
        request=self._identity(binding,uuid.uuid4().hex,'stage')
        self._save(directory,'stage_request.json',request)
        _,manifest=self._frozen_details(); payload={}
        for name in manifest['diagnostic_files']:
            path=(self.frozen/name).resolve(); require(path.is_relative_to(self.frozen),'Payload path outside frozen directory')
            payload[name]=path.read_bytes()
        payload['native_manifest.json']=(directory/'native_manifest.json').read_bytes()
        payload['execution_lease.json']=(directory/'execution_lease.json').read_bytes()
        files={name:{'base64':base64.b64encode(value).decode(),'sha256':hashlib.sha256(value).hexdigest()} for name,value in payload.items()}
        result=self._perform('stage',request,binding,current,directory,timeout=240,payload={'files':files})
        self._save(directory,'stage_execution.json',result)
        require(result.get('certainty')=='terminal' and result.get('verified') is True,'Stage incomplete; reconcile without replay')
        return result

    def _previous_complete(self,current,directory,binding):
        for mode,target in PAIRS:
            name=mode+'_'+target
            request_path=directory/(name+'_request.json')
            if request_path.exists():
                request=read(request_path);path=directory/(name+'_execution.json')
                expected={**self._identity(binding,request['request_id'],'run'),'mode':mode,'target':target}
                require(request==expected,'Prior local request identity changed')
                prior=read(path) if path.exists() else None
                if not isinstance(prior,dict) or prior.get('certainty')!='terminal':
                    observation=self._read_reconcile(current,directory,binding,request['request_id'])
                    raise Uncertain('Prior request has no certain terminal result; reconciled, no further run: '+json.dumps(observation))
                require(prior.get('identity')==self._identity(binding,request['request_id'],'run')
                    and prior.get('returncode')==0 and self._raw_result_identity(prior.get('result'),binding,mode,target)
                    and prior['result'].get('execution_completed') is True,'Prior request failed/identity unknown; no further run')

    def run(self,mode,target):
        require((mode,target) in PAIRS,'Unsupported mode/target')
        current,directory,binding=self._binding(mutation=True,required_seconds=1020)
        name=mode+'_'+target; self._no_replay(current,directory,binding,name)
        self._previous_complete(current,directory,binding)
        staged=read(directory/'stage_execution.json')
        stage_request=read(directory/'stage_request.json')
        require(staged.get('identity')==self._identity(binding,stage_request['request_id'],'stage')
            and staged.get('certainty')=='terminal' and staged.get('verified') is True,'Verified original stage required')
        probe=self.probe(binding['physical_gpu']); self._check_probe(probe,binding['physical_gpu'])
        require(probe['runtime_code_commit']==binding['runtime_code_commit'],'Runtime HEAD changed')
        current,_,binding=self._binding(mutation=True,required_seconds=1020)
        request={**self._identity(binding,uuid.uuid4().hex,'run'),'mode':mode,'target':target}
        self._save(directory,name+'_request.json',request)
        result=self._perform('run',request,binding,current,directory,timeout=900,conda=True)
        self._save(directory,name+'_execution.json',result)
        require(result.get('certainty')=='terminal' and result.get('returncode')==0
            and self._raw_result_identity(result.get('result'),binding,mode,target)
            and result['result'].get('execution_completed') is True,'Native process failed/identity unknown; no PASS or replay')
        return result

    def pair(self):
        return [self.run(mode,target) for mode,target in PAIRS]

    def run_pair(self):
        return self.pair()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['probe','prepare','stage','run','pair','run_pair','status','reconcile'])
    parser.add_argument('--gpu',type=int,choices=[1])
    parser.add_argument('--mode',choices=['smoke','resources'])
    parser.add_argument('--target',choices=['champion','candidate'])
    parser.add_argument('--execution-dir')
    parser.add_argument('--request-id')
    parser.add_argument('--local-only',action='store_true')
    args=parser.parse_args(); adapter=Adapter(execution_dir=args.execution_dir)
    if args.operation in ('probe','prepare'):
        require(args.gpu is not None,'Explicit physical --gpu is required')
        result=getattr(adapter,args.operation)(args.gpu)
    elif args.operation=='run': result=adapter.run(args.mode,args.target)
    elif args.operation=='reconcile': result=adapter.reconcile(args.request_id)
    elif args.operation=='status': result=adapter.status(remote=not args.local_only)
    else: result=getattr(adapter,args.operation)()
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))


if __name__=='__main__': main()
