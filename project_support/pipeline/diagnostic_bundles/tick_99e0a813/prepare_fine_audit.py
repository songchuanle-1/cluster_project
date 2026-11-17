"""Register the next structural premise before source/toy/native screening."""
from datetime import datetime,timezone
from ops import guard,save,evidence,tick,ROOT,OUT
from fine_exchange_toy import controls
guard();cid="fine-leaf-local-point-exchange"
work=tick.load(ROOT/"pipeline/research_work.json");assert not any(c["id"]==cid for c in work["candidates"])
candidate={"id":cid,"stage":"diagnosis","kind":"provisional_core_structural_hypothesis",
    "hypothesis":"Native fine leaves mix target/background superpoints; a degree-bounded recipient-specific point exchange represents distinctions absent from a shared fine-bank vector while retaining M95 middle/coarse context. Mixed-leaf absence refutes the sampled prerequisite only.",
    "matched_control":"Existing M95 gathered fine-bank vector and banned attnpool pooled token contrasted against per-recipient outputs;TRAIN native-majority labels used for diagnosis only,not deployment.",
    "next_action":"Execute four source/toy discriminator controls and32frozen TRAIN fine-leaf audits;then independently review novelty/bans and implement isolated point operator with native gradients/resources before any model/admission. No HDSrevision3.",
    "evidence":[evidence(OUT/"fine_exchange_prereg.md"),evidence(OUT/"cooperation_analysis.json"),evidence(ROOT/"Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_attnpool/hier_postprocess.py"),evidence(ROOT/"Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/hier_postprocess.py")],
    "preregistered_at":datetime.now(timezone.utc).isoformat(),"failure_scope":"inconclusive"}
work["candidates"].append(candidate);guard();tick.save(ROOT/"pipeline/research_work.json",work)
save("fine_exchange_cpu_controls.json",controls())
manifest=tick.load(OUT/"cooperation_manifest.json")
manifest["producer_hashes"]={name:tick.digest(OUT/name) for name in ("native_fine_audit.py","matched_control.py")}
save("fine_audit_manifest.json",manifest)
candidate["evidence"].extend(evidence(OUT/name) for name in ("fine_exchange_toy.py","fine_exchange_cpu_controls.json","fine_audit_manifest.json","native_fine_audit.py"))
guard();tick.save(ROOT/"pipeline/research_work.json",work)
print("Core premise registered in diagnosis;4source/toy controls PASS;native audit pending;no model/admission.")
