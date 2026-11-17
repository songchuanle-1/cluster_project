"""Validate completed evidence and render this tick's bounded memory snapshot."""
import argparse
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
OUT = PIPE / "reports/d1_expansion_20260911-0715"
EXPECTED = {
    "goal.json": "f16c1db985fbeeb97e284b0e8c24140a5a39e56cb64cd099168be03639c65901",
    "queue.json": "f5b26ecb500ef593c485b4a201ced926c164fc94af2d7380954b7c6f5c8ee35e",
    "experiments.csv": "87d73d8fd0b7c039b34d4191ae8df4e4f27a525b51f13589f18d1e989e602679",
    "running.json": "ef3b522a6e7cce5312e24ea1dc7ca0987aa6f61abf75f17e0fab66b92c5e5c05",
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "|" + "|".join("---" for _ in headers) + "|"] +
                     ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    snapshot_path = Path(args.snapshot)
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert (now - datetime.fromisoformat(snapshot["collected_at"])).total_seconds() < 600
    state_hashes = {name: sha(PIPE / name) for name in EXPECTED}
    assert state_hashes == EXPECTED
    assert not subprocess.check_output(["git", "-C", str(ROOT / "Cluster"), "status", "--porcelain"])
    inventory = json.loads((PIPE / "reports/research_inventory_20260910-1324.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT / r["path"]) == r["sha256"] for r in inventory["analyses"])
    verification = json.loads((OUT / "verification.json").read_text(encoding="utf-8"))
    execution = json.loads((OUT / "execution.json").read_text(encoding="utf-8"))
    assert verification["status"] == "passed" and not verification["cuda_initialized"]
    recovery = json.loads((OUT / "recovery_verify.json").read_text(encoding="utf-8"))
    assert recovery["returncode"] == 0 and recovery["gpu_reruns"] == 0
    assert all(v["returncode"] == 0 for v in execution["cases"].values())
    summaries = {name: json.loads((OUT / name / "summary.json").read_text(encoding="utf-8"))
                 for name in ("baseline", "m95")}
    for name, summary in summaries.items():
        assert sha(OUT / name / "summary.json") == verification["models"][name]["summary_sha256"]
        assert all(sha(OUT / name / row["artifact"]) == row["artifact_sha256"]
                   for row in summary["rows"])
    queue = json.loads((PIPE / "queue.json").read_text(encoding="utf-8"))
    waiting = [(server, row) for server, tasks in queue["gpu_queues"].items()
               for row in tasks if row["status"] == "waiting"]
    running = [(server, row) for server, tasks in queue["gpu_queues"].items()
               for row in tasks if row["status"] == "running"]
    assert len(waiting) == len(running) == 4
    by_config = {r["config"]: r for _, r in running}
    live = [(server, run) for server, srv in snapshot["servers"].items() for run in srv["runs"]]
    assert len(live) == 4 and {r["config"] for _, r in live} == set(by_config)
    questions = []
    for path in (PIPE / "decisions").glob("*_question.md"):
        when = datetime.strptime(path.name[:15], "%Y%m%d-%H%M%S")
        if now - timedelta(hours=24) <= when <= now:
            questions.append(path)
    stats = verification["models"]
    fields = ("selected_iou", "oracle_iou", "bank_limitation", "selection_gap",
              "acc50", "recoverable_failure50", "bank_failure50")
    metric_table = table(["Metric", "Baseline", "M95"],
                         [(f, f"{stats['baseline']['description_mean'][f]:.9f}",
                           f"{stats['m95']['description_mean'][f]:.9f}") for f in fields])
    ci = verification["paired_m95_minus_baseline"].get("complete_scene_bootstrap95", {})
    ci_table = table(["M95 minus baseline", "Mean", "95% low", "95% high"],
                     [(f, f"{v['mean']:.9f}", f"{v['low']:.9f}", f"{v['high']:.9f}")
                      for f, v in ci.items()])
    counts = {}
    for name, s in summaries.items():
        counts[name] = dict(
            acc50=sum(r["selected_iou"] > .5 for r in s["rows"]),
            recoverable=sum(r["selected_iou"] <= .5 < r["oracle_iou"] for r in s["rows"]),
            bank_failure=sum(r["oracle_iou"] <= .5 for r in s["rows"]))
    continuity = {}
    for name, s in summaries.items():
        prior = json.loads((PIPE / f"reports/d1_grouping_20260911-0610/{name}/summary.json").read_text(encoding="utf-8"))
        lookup = {(r["scene_id"], r["object_id"], r["ann_id"]): r for r in s["rows"]}
        compared = [(p, lookup[tuple(p["identity"])]) for p in prior["rows"]
                    if tuple(p["identity"]) in lookup]
        continuity[name] = dict(n=len(compared), selected_index_changes=sum(
            p["grouped_metrics"]["selected_index"] != r["selected_index"] for p, r in compared),
            max_selected_iou_delta=max(abs(p["grouped_metrics"]["selected_iou"] - r["selected_iou"])
                                       for p, r in compared),
            max_oracle_iou_delta=max(abs(p["grouped_metrics"]["oracle_iou"] - r["oracle_iou"])
                                     for p, r in compared))
    diag = f"""# D1 Frozen Diagnostic Expansion
Completed evidence reviewed {now:%Y-%m-%d %H:%M:%S} Asia/Shanghai.

## Scope And Provenance
Upstream motivation_review/exp_design_20260911-071200; decision071110.
sample_manifest_v2 SHA84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468.
Expected284 descriptions,71physicalscenes,4each;70reserved scenes never inferred.
Audited fixed baseline/M95 checkpoints, explicitmodule/config/package/source hashes;
two legacy textbuffers omitted only in memory after exactruntime equality.
Original languagegroups, seed1999, no training/config/modelpackage changes.
Historical forwardidentity still not proven; not a fullvalidation replay.

## Denominators And Missingness
{table(["Model", "Descriptions", "Physical scenes", "Complete scenes", "Missing IDs", "Groups", "Context descriptions"],
       [(n, stats[n]["descriptions"], stats[n]["physical_scenes"], stats[n]["complete_scenes"],
         len(stats[n]["missing_ids"]), stats[n]["groups"], stats[n]["unique_context_descriptions"]) for n in stats])}

Groupcontext descriptions outside284IDs are nuisance inputs, not extra observations.
MissingIDs/skippedgroups are explicitly stored in summary.json and verification.json.
Matched denominator: {verification["paired_m95_minus_baseline"]["descriptions"]} descriptions;
{verification["paired_m95_minus_baseline"]["complete_scenes"]} complete physicalscenes.
Eight previously measured IDs included once; expansion adds up to276newIDs/69scenes.

## Error Measurements
{metric_table}

{table(["Model", "Acc50 count", "Selection failure with oracle>.5", "Bank oracle<=.5"],
       [(n, counts[n]["acc50"], counts[n]["recoverable"], counts[n]["bank_failure"]) for n in stats])}
Each row count uses its model's measured denominator above.
Acc50 uses IoU>.5 per tools/train.py; recoverable a<=.5<o; bankfailure o<=.5.
These latter two groups partition threshold failures, not causal failure labels.
The samebank identity1-a=(1-o)+(o-a) holds. It doesnot distinguish absent targets
from inaccurate boundaries or explain selection errors as language/relation faults.
Oracle is an upper-bound diagnostic, never a deployable prediction.

## Scene Uncertainty
{ci_table}

10000 paired physical-scene bootstrap replicates, seed1999, percentile95.
Complete scenes only, no imputation; scene is resampling unit, not description.
These intervals describe conditional exploratory sample uncertainty, not untouched-
test significance or dataset-wide prevalence. No modeltraining multiseed sweep.
Equal-scene sampling is not description-population weighting; validation was mined
historically and the reserved split is prospective, not independent fresh testdata.

## Correctness And Resources
{verification["banks_verified"]} savedbanks verified onCPU; allcandidateIoUs within1e-7,
same selectedindices, probabilities at establishedatol1e-7/rtol1e-6, exactselectedbinarymasks.
Crossmodel GT, GTsuperpoint masks and superpointmaps equal on matchedIDs;
scene point/CLIP/source/graph hashes equal. CUDA uninitialized duringreadback.
Actualget_iou AST equal across baseline/M95, verifiedlocally.
Seven existingIoUtests pass; four scene-statistics tests pass;28pipeline tests pass.
{table(["Model", "Peak allocated MiB", "Peak reserved MiB", "Inference seconds", "Worker exit"],
       [(n, f"{summaries[n]['peak_allocated_mib']:.3f}", f"{summaries[n]['peak_reserved_mib']:.3f}",
         f"{summaries[n]['elapsed_seconds']:.3f}", execution["cases"][n]["returncode"]) for n in stats])}
8GiB launch/5GiB batchfree guards,4GiB allocatorcap,600s inferencebudget.
SharedGPU runtime is not a matched efficiencybenchmark or trainingpeak.
Onecandidateatime O(N)temporary, QxS savedbank; no QxNbank allocation.
Workers completed before final snapshot; helperSHA evidence in execution.json.
CPUverifier retry1 restored omitted pilotrelative tolerance after independentdrift
audit: maxabsolute1.1920928955078125e-7,0binarychanges/all568banks.
Originalfailedlog preserved; see bugfix_20260911-073200.md/recovery_verify.json.
No GPUrerun or changes to IoUthreshold/candidateIoUtolerance.

## Pilot Continuity
```json
{json.dumps(continuity, indent=2)}
```
Only same8IDs compared with previousoriginalgroups; not universalfloatdeterminism.

## Interpretation And Next Work
Measured candidate-bank and selection errors now have a broader frozen denominator.
M95 selectedmean.502217 is belowbaseline.535914 in thissample, whileoracle.848108
exceedsbaseline.834246. Pairedselecteddelta-.033698 has95%CI[-.071752,.004764],
which includeszero. M95selectiongap exceedsbaseline by.047560,
CI[.008933,.085786]; these are exploratory comparisons, not a fullvalregression
claim or untouchedtest confirmation. Thresholdrecoverableerrors111/284vs90/284;
bankfailures15/284vs23/284. Prioritize inspecting why goodcandidates lose,
without assuming that rankingalone, relationbinding or sharedanchors is thecause.
Do not select a mechanism solely from an oraclegap or a positive aggregate delta.
Next D1 task: freeze operational boundary/target-identity/ambiguity/relation labeling
rules; audit fixed errorcases and matched successful negatives from these banks.
Use existing scene assets, report missing labels/disagreements, no externalannotation
API/newdatasets. Then choose at mostone evidenced hypothesis and complete N1
formula derivation, degeneracies/gradient/complexity, primary-paper comparison and
matched falsification controls. No newmechanism trainingadmitted in this tick.
"""
    (OUT / "diagnostic_report.md").write_text(diag, encoding="utf-8")
    gpu_table = table(["Server", "GPU", "Util", "Memory MiB", "Process"],
                     [(server, g["gpu"], f"{g['util']}%", f"{g['used_mib']}/{g['total_mib']}",
                       "; ".join(f"{by_config[r['config']]['id'].split('-')[0]} PID{r['pid']}"
                                 for r in srv["runs"] if str(r["gpu"]) == str(g["gpu"])))
                      for server, srv in snapshot["servers"].items() for g in srv["gpus"]])
    run_table = table(["ID", "Config", "Server", "GPU", "Epoch", "Best mIoU", "Acc@50",
                       "spmIOU", "No-Impr", "Status"],
                      [(by_config[r["config"]]["id"], Path(r["config"]).stem, server, r["gpu"],
                        f"{r['current_epoch']}/50", f"{r['best']['miou']:.10f}@{r['best']['epoch']}",
                        r["best"]["acc50"], r["best"]["spmiou"], f"{r['no_improve']}/10", "running")
                       for server, r in live])
    qtable = table(["Position", "ID", "Config", "Status", "Depends On", "Server"],
                   [(i, r["id"], r["config"], r["status"], r.get("depends_on") or "none", server)
                    for i, (server, r) in enumerate(waiting, 1)])
    decisions = [p for p in (PIPE / "decisions").glob("20260911-*_*.md")
                 if datetime.strptime(p.name[:15], "%Y%m%d-%H%M%S") >= datetime(2026, 9, 11, 7, 7)]
    pending = "\n".join(f"- {p.relative_to(PIPE).as_posix()}: see original text. H100 placement resolved; generic pull_log root/paired extraction unresolved."
                        for p in questions) or "No type=question records within last24h. Aging doesnot imply approval."
    report = f"""================================================================================
  Research Pipeline Report - cluster_project
  {now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #20260911-0707)
================================================================================

## 0. Goal Status
Target:mIoU>=.5100 | Champion:M95 .5020 ledger | Gap:+.0080 |
Phase:1 NOT YET. Required checker07:10:24exit0; baselineledger.4894.
Exacthistoricalcheckpoint metrics supplementary; no newfullvalidation/ledgerchange.

## 1. GPU Overview
Source:{snapshot_path.relative_to(PIPE).as_posix()} after evaluationworkers.
Only SERVERS allowedcards, actualcapacity4; server-2/3emptywhitelists.
{gpu_table}
Free training slots0/4. One/cardserver-4,max2server-6GPU7.
Allbounded diagnosticworkers completed; noextraevaluation left running.

## 2. Running Experiments
{run_table}
Bestmetrics paired at exactbestepoch. Four originaltrainerPIDs retained.
Server-6clock differsfromlocal, no mixed-clockstaleness inference.
No newterminal/earlystop/crash/trainerlaunch. M186already analyzed/archived.

## 3. Queue Status
{qtable}
Depth4/actualcapacity4:NEED MORE(target>=5). Scienceadmission overridesrefill.
PreservedFIFO/nullGPU/noholds/0claiming. No globalpause/newtrainingvariants.

## 4. This Tick's Actions
- Reconciled memory/goal/queue/CSV/SERVERS/recentdocuments; unhealthy absent07:07:23.
- Required monitor07:07exit0 and goalchecker07:10:24exit0; freshpostflight above.
- Six-section fullgoal motivationreview then seven-section design071200.
- Isolated originalgroup expansion helpers synced/hashverified onbothservers;
  activepackages/deploymentdiffs unchanged. No trainingcodecommit/push.
- Baseline:{stats['baseline']['descriptions']}/284; M95:{stats['m95']['descriptions']}/284;
  pairedcomplete scenes:{verification['paired_m95_minus_baseline']['complete_scenes']}/71.
- All{verification['banks_verified']} bankartifacts downloaded/hashverified/CPUrecomputed;
  see d1_expansion_20260911-0715/diagnostic_report.md and verification.json.
- SevenIoU + four scene-statistics +28pipeline tests passed; helperscompile passed.
- No GPUworkercrash or capincrease. CPUverifier retry1 restored pilotprobability
  relative tolerance after568bank drift audit; see bugfix073200. Originalfailurepreserved.
- Measuredoracle gaps are notcausal languageerrors/novelty/deployablegains.
- No newterminal analysis needed;223historicalanalysishashes verifiedunchanged.
- goal/queue/CSV/running hashes unchanged; trainingrepo clean; memoryreplaced
  withsevensectionsunder200lines. Summaryretention onlyexpiredregularsummaryfiles.
- NextD1: expliciterrorlabelrules with fixedcases and matchedsuccesscontrols,
  thenonecoremechanism/derivation/primarypaper novelty review beforetraining.

## 5. Decisions Made
{chr(10).join('- ' + p.relative_to(PIPE).as_posix() for p in sorted(decisions))}
Alldecisions via log_decision.sh. No newquestions; legacyFIFO retained.

## \u26a0 Pending User Decisions
{pending}

================================================================================
  Next tick: 2026-09-11 08:07 Asia/Shanghai
================================================================================
"""
    report_path = PIPE / "reports" / f"summary_{stamp}.md"
    assert not report_path.exists()
    report_path.write_text(report, encoding="utf-8")
    old = (PIPE / "codex_memory.md").read_text(encoding="utf-8")
    sections = dict(re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", old, re.M | re.S))
    memory = "# Codex Research Memory\n\n"
    sections["Goal And Phase"] = f"""- Latest tickSep11 07:07; report{report_path.name}; disk overrideschat.
- Required monitor07:07exit0/checker07:10:24exit0:Phase1 NOT YET; ledgerM95=.5020,target=.5100,gap+.0080,baseline.4894.
- UserSep10 rethink binding: specific errors, core novelty, stepwise formula derivation and six coverageareas; goal.json primary, docs/experiment_scope_20260910.md operational.
- All12constraints/11bans unchanged. Structuralonly/no tuning;seed1999;epochs50/max_iters70;<=10G;no N^2attention.
- Diagnosis->mechanism/derivation->primarypaper novelty->matchedcontrols->robustness/generalization->efficiency. Scienceadmission overridesrefill.
- No newdatasets/externalannotation/multiseed campaigns; Phase2requiresconfirmedplan aftertarget.
- Actualcapacity4:server-4GPU0/1oneeach,server-6GPU7max2. Waiting4triggersreview; legacyFIFO preserved,notglobalhold.
"""
    sections["Active Hypotheses"] = f"""- Shared-anchorconsistency/mass-conservingsubdivision remainsprovisional docs/research_rethink_20260910.md; standardmarginalization/algebra notnovelty. No mechanismadmitted.
- Operational D0->D1->N1->T0->E1->V1->P2. Primarypapers,causalerrorlabels andcoremechanism derivation stillmissing.
- FrozenD0reports/d0_inventory_20260911-0316/sample_manifest_v2.json SHA84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468.
- Source9508uniqueIDs/141physicalscenes;sourceSHA4455b8857ade37aaafa32581537a961a77bcc756b22d8143ed4021bc88b7931f.
-71diagnosticphysicalscenes/284IDs(4each),70reserved/4646IDs;4578othersunsampled. Splitfrozenbeforeinference;physicalgroupsdisjoint;v1superseded.
- Historicallyminedvalidation, reservedprospectivelyonlyNOTuntouchedtest. Equal-scene sampleNOTdescription-populationweightedprevalence.
- Priorpilot reports/d1_pilot_20260911-0516:8IDs/model/2scenes,16banksverified; baselinea/o.538820513/.892994613,M95.550915219/.889365964;both5/8Acc50.
- Prior grouping reports/d1_grouping_20260911-0610:fivecomparisons on8IDs/model;0binary/index/IoUchange, floatdriftmeasured;notuniversalinvariance/historicalreplay.
- NEW expansion reports/d1_expansion_20260911-0715:baseline{stats['baseline']['descriptions']}/284,M95{stats['m95']['descriptions']}/284;matched{verification['paired_m95_minus_baseline']['descriptions']}IDs/{verification['paired_m95_minus_baseline']['complete_scenes']}completephysicalscenes.
- Originalgroups permodel:{stats['baseline']['groups']}/{stats['m95']['groups']};contextIDs:{stats['baseline']['unique_context_descriptions']}/{stats['m95']['unique_context_descriptions']};onlyfrozen284scored,othercontextNOTextraobservations. Noreservedsceneinference.
- MissingIDsbaseline{len(stats['baseline']['missing_ids'])}/M95{len(stats['m95']['missing_ids'])};see summaries/verificationexplicitlists. EightpilotIDs includedONCE;remainingexpansioncompletedasrecorded.
- Baseline measuredselected/oracle/gap: {stats['baseline']['description_mean']['selected_iou']:.9f}/{stats['baseline']['description_mean']['oracle_iou']:.9f}/{stats['baseline']['description_mean']['selection_gap']:.9f};Acc50{counts['baseline']['acc50']}/{stats['baseline']['descriptions']};recoverable{counts['baseline']['recoverable']},bankfailure{counts['baseline']['bank_failure']}.
- M95 measuredselected/oracle/gap: {stats['m95']['description_mean']['selected_iou']:.9f}/{stats['m95']['description_mean']['oracle_iou']:.9f}/{stats['m95']['description_mean']['selection_gap']:.9f};Acc50{counts['m95']['acc50']}/{stats['m95']['descriptions']};recoverable{counts['m95']['recoverable']},bankfailure{counts['m95']['bank_failure']}.
- Pairedscene-bootstrap95(10000,seed1999) inverification.json;conditionalexploratoryuncertainty,notuntouchedtestsignificance/multiseedtraining.
- ActualIoU sigmoid>=.5,GT>.5,union+1e-6;Acc50IoU>.5. Banklimitation1-o andgap o-a identityvalidsamebank;notcoverage/boundary/relationalcausedecomposition.
- {verification['banks_verified']}CPUbankreadbacks passallcandidateIoUatol1e-7,indices/probabilities/binarymasks;crossmodelGT/GTsp/mappingequal,inputhashesequal;CUDAuninitialized.
- Same-forwardoriginalpredict_by_feat equality forselectedoutputs;128candidatebank,softmax(indis)[:,1].argmax;QxSstorage/O(N)temporary,notQxN.
- PeakMiBbaseline{summaries['baseline']['peak_allocated_mib']:.3f}/M95{summaries['m95']['peak_allocated_mib']:.3f};seconds{summaries['baseline']['elapsed_seconds']:.3f}/{summaries['m95']['elapsed_seconds']:.3f}sharedload,NOTefficiencybenchmark.
- BothGPUworkersexit0;8GiBlaunch/5GiBgroupfreeguards,4GiBallocatorcap/600sinferencebudget/720sshelltimeout. No capincrease/trainerkill.
- CPUverifierretry1 restored pilotatol1e-7/rtol1e-6 probabilitycomparison afterdriftauditmax1.1920928955078125e-7/all568banks0bitchanges;binary/indexexact,IoUatol1e-7 unchanged. See bugfix073200/recovery_verify.json,originalreadback.log preserved.
- WorkerSHAaa5ff8c82751f9c9db6b07cf246539146ac33b7820039eebe214600bcabbccd1;helperfbfa5c564d5c9a39491f04cc4c9c5b715911d312b829c83d48c2b7c7e6856f2c;bothservershashsynced/tmp/cluster_d1_expansion_20260911_0715.
- Standalone headless/d1_expansion_20260911.py,run_d1_expansion_20260911.py,verify_d1_expansion_20260911.py;fixedoutputsEXIST,doNOTrerunlauncherblindly.
- NEXT:freezeoperationalboundary/identity/ambiguity/relationlabelrules;inspectfixederrorsandmatchedsuccessnegativesusingexistingassets;reportmissinglabels/disagreements. Thenonehypothesis+N1derivation/primarypapersbeforetraining.
- LegacyM184whole-subtree/M185path-posterior/M187frontier/M188fineargmaxmean;FIFO M189pathmin/M190topdown/M191siblingrelative/M193consensus;noautomaticdescendants.
- AlllegacyTR independent7filecopies,onlydec.pyterminalgraphchange,6filesbyteequal/YAMLnumericsunchanged. AdmissionsM1849.845647916G/M1859.845844524G/M1879.843485228G/M1889.832737324G/M1899.845844524G/M1909.845647916G/M191,M1939.885821484G.
"""
    sections["Running And Queue"] = (
        f"- Latest{snapshot_path.relative_to(PIPE).as_posix()};4trainers/4waiting/0claiming,ownershipunchanged.\n" +
        "\n".join(f"- {by_config[r['config']]['id']} {server}GPU{r['gpu']}PID{r['pid']}epoch{r['current_epoch']};best{r['best']['miou']}@{r['best']['epoch']},paired{r['best']['acc50']}/{r['best']['spmiou']},noimprove{r['no_improve']}."
                  for server, r in live) +
        "\n- WaitingFIFOserver-4M189/M190/M191/M193;gpu=null/noholds/dependencies. Verifydeploymentwork_dir/data beforedispatch.\n"
        "- Bothdiagnosticworkerscompleted;noextraevaluationrunning. Server-6clockdifferent,nomixedclockstaleness.\n"
        "- M188loggerworkroot/..._mqb_tr/20260911_031407/20260911_031407.log. Priorprelaunchstalework_dirfixed03:14;fixedtransitionhelpersstale,doNOTreuseblindly.\n")
    sections["Open Questions And Risks"] = """- Pendingquestion20260910-075552:placementresolved;genericpull_log wrongroot/pairedextractionunresolved. Agingoutnotapproval;explicitretrievalbypasses,notglobalrepair.
- ParserexcludesspmIOU,uniquePIDlogger,mismatchdefersstop;terminal/nullGPUfallbackrepaired.28pipelinetestspass07:16in3.550s.
- NEVERlegacy scripts/sync.sh reset/clean or genericremote_train unconditionalsync. Safeff-onlysyncpreservesdeployment/untracked.
- TrainingrepoCluster cleanHEAD05335bdd15d83d106d410e03498b0c38dc9ad414;notrainingcodecommit/pushthis tick. Isolatedhelperuploads only, deploymentdiffsunchanged.
- LocalpythonNOTORCH;readbackexistingremoteCPUconda withCUDAhidden. Localrg unavailable;PowerShell/gitgrep/structuredparsers. PYTHONPATHroot+framework/lib.
- server-4songcl@192.168.1.137 code/data/songcl/Project/Cluster_project/Cluster;work/data/songcl/Project/Cluster_project/Cluster_checkpoints;conda/home/dl04/anaconda3/etc/profile.d/conda.sh envproject_cluster;data/home/songcl/data/data/.
- server-6songcl@100.64.3.28 code/data3/songcl/Project/Cluster_project/Cluster;work/data3/songcl/Project/Cluster_project/Cluster_checkpoints;conda/data3/songcl/miniconda3/etc/profile.d/conda.sh envproject_cluster;data/data3/songcl/data/data_cluster/. Re-readSERVERSbeforeops.
"""
    sections["Last Tick"] = f"""- TickSep11 07:07 monitor/checkerexit0,unhealthyabsent07:07:23;no newterminal/stop/modelcrash/traininglaunch. CPUverifierrepair1 asrecorded.
- D1frozenoriginalgroup expansion completed;see reports/d1_expansion_20260911-0715/diagnostic_report.md,verification.json,execution.json.
-28pipelinetests+7CPU-IoUtests+4scenestatisticstests pass;compilepass;{verification['banks_verified']}banksCPUrecomputedandlocalhashverified.
- Fullgoalreview/design071200 beforeexecution;decisionsvialog_decision.sh;no newquestions/no newmechanismadmission.
-223historicalanalysishashesmatch;goal/queue/CSV/runningunchanged;trainingrepoclean;sevenmemorysectionsunder200lines.
- Lastverify{now:%H:%M:%S};report{report_path.name}. Summaryretentiononlyexpiredregularsummaryfiles.
- StateSHAs:goal{EXPECTED['goal.json']};queue{EXPECTED['queue.json']}.
- CSV{EXPECTED['experiments.csv']};running{EXPECTED['running.json']}.
- Nexttick08:07:preservetrainers/FIFO;advanceD1errorlabelrulesandmatchednegativecases,thenN1singlemechanism/formuladerivation/verifiedprimarypapers;doNOTrefillwithautomaticselectorvariants.
"""
    for title in ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                  "Closed Or Failed Directions", "Running And Queue",
                  "Open Questions And Risks", "Last Tick"):
        memory += f"## {title}\n{sections[title].strip()}\n\n"
    assert len(memory.splitlines()) < 200
    (PIPE / "codex_memory.md").write_text(memory, encoding="utf-8")
    final = dict(verified_at=now.isoformat(), state_hashes=state_hashes,
                 historical_analyses_verified=len(inventory["analyses"]),
                 memory_lines=len(memory.splitlines()), report=report_path.name,
                 snapshot=str(snapshot_path), banks_verified=verification["banks_verified"],
                 pilot_continuity=continuity, pending_questions=[p.name for p in questions],
                 counts=counts, repo_clean=True)
    (OUT / "tick_verification.json").write_text(json.dumps(final, indent=2))
    print(metric_table)
    print(ci_table)
    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()
