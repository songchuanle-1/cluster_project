"""Persist same-standard resource comparison and new-operator contracts."""
from datetime import datetime,timezone
from ops import *
guard(300)
base_path=OUT/'independent_package/native_package_champion_result.json'
candidate_path=OUT/'package_isolated/native_package_candidate_isolated_result.json'
base=tick.load(base_path);candidate=tick.load(candidate_path)
assert base['execution_completed'] and candidate['execution_completed']
assert base['resource_input_sha256']==candidate['resource_input_sha256']
assert base['parameters']==candidate['parameters']
assert base['profile']['profiler_file_sha256']==candidate['profile']['profiler_file_sha256']
pairs=[]
for left,right in zip(base['train_records'],candidate['train_records']):
    assert (left['workers'],left['batch_index'],left['input_sha256'])==(right['workers'],right['batch_index'],right['input_sha256'])
    pairs.append({'workers':left['workers'],'batch_index':left['batch_index'],'input_sha256':left['input_sha256'],
        'M95_peak_bytes':left['peak_allocated_bytes'],'candidate_peak_bytes':right['peak_allocated_bytes'],
        'relative_increase':right['peak_allocated_bytes']/left['peak_allocated_bytes']-1,
        'actual_new_attention_loss_gradient_norm':right['actual_attention_loss_gradient_norm']})
comparison={'observed_at':datetime.now(timezone.utc).isoformat(),'evidence':[evidence(base_path),evidence(candidate_path)],
 'standard_FLOPs':{'M95':base['profile']['flops'],'candidate':candidate['profile']['flops'],
   'increment':candidate['profile']['flops']-base['profile']['flops'],'candidate_within10G':candidate['profile']['within10G'],'changed_handlers':False},
 'latency':{'M95_median_ms':base['median_ms'],'candidate_median_ms':candidate['median_ms'],
   'relative_median_increase':candidate['median_ms']/base['median_ms']-1,'M95_P90_ms':base['p90_ms'],'candidate_P90_ms':candidate['p90_ms']},
 'inference_peak':{'M95_bytes':base['peak_allocated_bytes'],'candidate_bytes':candidate['peak_allocated_bytes'],
   'relative_increase':candidate['peak_allocated_bytes']/base['peak_allocated_bytes']-1},
 'parameters':candidate['parameters'],'new_parameters':0,'batch_size':1,'warmup':20,'repeat':100,
 'matched_training_memory':pairs,'original_baseline_resource_delta':'UNKNOWN;original no-cluster config unavailable',
 'full_optimizer_peak':'UNKNOWN;no optimizer instantiated or stepped','trained_efficacy':'UNKNOWN',
 'passed_measured_budget':bool(candidate['profile']['within10G'] and all(p['relative_increase']<=.15 for p in pairs)),
 'not_admission':'Resources/native graph do not independently pass task diagnosis or scientific admission'}
save('resource_comparison.json',comparison)
prototype=(OUT/'raw_key_revision1/coarse_cross_attention_r1.py').read_text()
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),'scope':'New coarse attention OPERATOR only,not old full-model padding/kernel audit',
 'controls':['joint key-value permutation invariance','point permutation equivariance','padding output and input-gradient zero','padded-query extension leaves valid operator outputs unchanged','identical keys reduce to uniform values','autograd finite-difference check'],
 'dtype':'float64 CPU','tolerance':1e-6,'coarse_count':8,'heads':8,'semantic_efficacy':False}
save('operator_contract_protocol.json',protocol)
program='''import os,socket,json
assert socket.gethostname()=='dl04-MS-7E06'
os.environ['CUDA_VISIBLE_DEVICES']=''
import torch
exec(PROTOTYPE)
torch.set_num_threads(1)
torch.manual_seed(1999)
x=torch.randn(2,7,256,dtype=torch.float64,requires_grad=True)
key=torch.randn(2,8,256,dtype=torch.float64,requires_grad=True)
value=torch.randn(2,8,256,dtype=torch.float64,requires_grad=True)
mask=torch.zeros(2,7,dtype=torch.bool);mask[0,-2:]=True
out,_=coarse_readback(x,value,mask,key_features=key)
order=torch.tensor([4,3,7,1,5,2,0,6])
permuted,_=coarse_readback(x,value[:,order],mask,key_features=key[:,order])
points=torch.tensor([6,1,2,0,4,5,3])
point_permuted,_=coarse_readback(x[:,points],value,mask[:,points],key_features=key)
extended,_=coarse_readback(torch.cat([x,torch.ones(2,3,256,dtype=x.dtype)],1),value,torch.cat([mask,torch.ones(2,3,dtype=torch.bool)],1),key_features=key)
constant_key=key[:,:1].expand_as(key)
uniform,_=coarse_readback(x,value,mask,key_features=constant_key)
expected=value.mean(1,keepdim=True).expand_as(out).masked_fill(mask.unsqueeze(-1),0)
gradient=torch.autograd.grad(out.sum(),x,retain_graph=True)[0]
errors={'joint_key_value_permutation':float((out-permuted).abs().max()),'point_permutation':float((out[:,points]-point_permuted).abs().max()),'padding_extension':float((out-extended[:,:7]).abs().max()),'padding_output':float(out.masked_select(mask.unsqueeze(-1)).abs().max()),'padding_query_gradient':float(gradient.masked_select(mask.unsqueeze(-1)).abs().max()),'identical_keys_uniform':float((uniform-expected).abs().max())}
sx=torch.randn(1,2,16,dtype=torch.float64,requires_grad=True)
sk=torch.randn(1,3,16,dtype=torch.float64,requires_grad=True)
sv=torch.randn(1,3,16,dtype=torch.float64,requires_grad=True)
sm=torch.zeros(1,2,dtype=torch.bool)
finite_difference=bool(torch.autograd.gradcheck(lambda a,b,c:coarse_readback(a,c,sm,key_features=b)[0],(sx,sk,sv),fast_mode=True))
print(json.dumps({'errors':errors,'strict1e_minus6_passed':max(errors.values())<=1e-6,'finite_difference_gradcheck':finite_difference,'cuda_calls':0,'task_deficit_established':False}))
'''.replace('PROTOTYPE',repr(prototype))
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B -c '+shlex.quote(program)
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],120)
save('operator_contract_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
assert result.returncode==0,result.stderr
contracts=json.loads(result.stdout)
save('operator_contracts.json',contracts)
save('primary_source_review.json',{'checked_at':datetime.now(timezone.utc).isoformat(),
 'primary_paper':{'title':'Perceiver IO: A General Architecture for Structured Inputs & Outputs','authors':'Andrew Jaegle et al.','identifier':'arXiv:2107.14795','source':'https://arxiv.org/abs/2107.14795','read_section':'Abstract and architecture2.1/2.2'},
 'established_prior_art':'Output queries cross-attending a small latent representation are existing methods. Ordinary cross-attention,latent bottleneck andlinear-in-pointcount claims are not this project contribution.',
 'current_candidate_difference':'Tests only the asymmetric coarse semantic bank->existing point-mask-feature update while retaining native fine/middle paths and supervision;projection-free raw-key/refined-value connection. Local implementation difference is not proof of material novelty.',
 'material_novelty':'UNKNOWN;no claim of a new attention primitive or a literature-complete contribution',
 'other_search_result_not_used':'Do not use the incorrectly matched unrelated service-worker paper as evidence'})
advance([OUT/'resource_comparison.json',OUT/'operator_contracts.json',OUT/'operator_contract_protocol.json',OUT/'primary_source_review.json'],
 next_action='Interpret frozen eight-scene semantic-key controls and actual errors;resources/native/independence are measured but task diagnosis and admission remain unpassed')
print(json.dumps({'resource_comparison':comparison,'operator_contracts':contracts},ensure_ascii=False))
