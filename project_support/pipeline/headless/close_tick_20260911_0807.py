"""Validate current tick evidence and replace bounded durable state."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import subprocess
import sys
from close_tick_20260911_0707 import EXPECTED, table, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_instance_20260911-0810"
now = datetime.now()
snapshot_path = Path(sys.argv[1])
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
assert (now - datetime.fromisoformat(snapshot["collected_at"])).total_seconds() < 600
hashes = {f: sha(P / f) for f in EXPECTED}
assert hashes == EXPECTED
assert not subprocess.check_output(["git", "-C", str(ROOT / "Cluster"), "status", "--porcelain"])
inventory = json.loads((P / "reports/research_inventory_20260910-1324.json").read_text(encoding="utf-8"))
assert all(sha(ROOT / r["path"]) == r["sha256"] for r in inventory["analyses"])
audit = json.loads((OUT / "instance_audit.json").read_text(encoding="utf-8"))
v = json.loads((OUT / "verification.json").read_text(encoding="utf-8"))
ex = json.loads((OUT / "execution.json").read_text(encoding="utf-8"))
assert v["status"] == "passed" and v["rows_checked"] == 568
assert sha(OUT / "instance_audit.json") == v["audit_sha256"] and ex["returncode"] == 0
assert not audit["cuda_initialized"]
queue = json.loads((P / "queue.json").read_text(encoding="utf-8"))
entries = [(server, r) for server, rs in queue["gpu_queues"].items() for r in rs]
waiting = [(s, r) for s, r in entries if r["status"] == "waiting"]
running = {r["config"]: r for s, r in entries if r["status"] == "running"}
live = [(s, r) for s, srv in snapshot["servers"].items() for r in srv["runs"]]
assert len(waiting) == len(running) == len(live) == 4
assert {r["config"] for s, r in live} == set(running)
gpu = table(["Server", "GPU", "Util", "Memory MiB", "Process"],
            [(s, g["gpu"], f"{g['util']}%", f"{g['used_mib']}/{g['total_mib']}",
              "; ".join(f"{running[r['config']]['id'].split('-')[0]} PID{r['pid']}"
                        for r in srv["runs"] if str(r["gpu"]) == str(g["gpu"])))
             for s, srv in snapshot["servers"].items() for g in srv["gpus"]])
rtable = table(["ID", "Config", "Server", "GPU", "Epoch", "Best mIoU", "Acc@50", "spmIOU", "No-Impr", "Status"],
               [(running[r["config"]]["id"], Path(r["config"]).stem, s, r["gpu"],
                 f"{r['current_epoch']}/50", f"{r['best']['miou']:.10f}@{r['best']['epoch']}",
                 r["best"]["acc50"], r["best"]["spmiou"], f"{r['no_improve']}/10", "running") for s, r in live])
qtable = table(["Position", "ID", "Config", "Status", "Depends On", "Server"],
               [(i, r["id"], r["config"], "waiting", r.get("depends_on") or "none", s)
                for i, (s, r) in enumerate(waiting, 1)])
questions = [p for p in (P / "decisions").glob("*_question.md")
             if now - timedelta(hours=24) <= datetime.strptime(p.name[:15], "%Y%m%d-%H%M%S") <= now]
decisions = sorted(p for p in (P / "decisions").glob("20260911-*_*.md")
                   if datetime.strptime(p.name[:15], "%Y%m%d-%H%M%S") >= datetime(2026, 9, 11, 8, 7))
stamp = now.strftime("%Y%m%d-%H%M%S")
report_path = P / "reports" / f"summary_{stamp}.md"
assert not report_path.exists()
report = f"""================================================================================
  Research Pipeline Report - cluster_project
  {now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #20260911-0807)
================================================================================

## 0. Goal Status
Target:mIoU>=.5100 | Champion:M95 .5020 ledger | Gap:+.0080 |
Phase:1 NOT YET. Required checker08:08:17exit0; baselineledger.4894.
Diagnostic sample results do not replace historical champion/fullvalidation.

## 1. GPU Overview
Source:{snapshot_path.relative_to(P).as_posix()}. SERVERS allowedcards only.
{gpu}
Free training slots0/4. Actualcapacity4 (server-4one/card,server-6GPU7max2)
overrides nominal5. No GPUdiagnostic/newinference this tick; CPUworker completed.

## 2. Running Experiments
{rtable}
Metrics paired at bestvalidation. Four originalPIDs retained.
Server-6clock differs, no mixed-clockstaleness claim. No newterminal/stop/crash.

## 3. Queue Status
{qtable}
Depth4/capacity4:NEED MORE(target>=5). Scientificadmission overridesrefill.
FIFO/nullGPU/noholds/0claiming unchanged. No globalpause or successorvariants.

## 4. This Tick's Actions
- Read memory first, bothreferences, skill, goal/SERVERS/queue/CSV, recent
  decisions/review/design/bugfix/analysis/report. Unhealthy absent08:07:27.
- Normalmonitor08:07exit0; goalchecker08:08:17exit0; live08:07 and finalabove.
- No newterminal; M186 alreadyarchived/analyzed/oneCSVrow; no duplicateanalysis.
- Fullgoal six-sectionreview and seven-sectiondesign081000; actual protocol
  freeze08:16:16 before attributionworker, protocol.json records exacttimestamp.
- CPU-only standaloneinstanceaudit synced/hashverified tobothservers; no
  activepackage/config/queue/trainingrepo commit/push or deploymentdiffmutation.
- All568banks/284IDs/71scenes joined to rawpointinstanceGT and reindexedsuperpoints
  exactly; no missingjoins, no GPUinitialization.23.694s/743.918MiBpeakRSS.
- Selected/oracle precision/recall/FP/FN and bestoverlapinstance recorded.
  M95recoverable111:63same-semanticwronginstance,25semanticunknown,21no-instance-
  pass50,2differentsemantic. Baseline90:63/13/12/2 respectively.
- M95extra21recoverableerrors are unknownsemantic+12/no-instance-pass+9, NOT
  an increase in same-semanticwronginstance count. Semanticunknown71/284.
- 12fixederrors/9unique same-scenesuccesscontrols;3controls explicitlymissing.
  Bothmodels have6coarseID19 cases within same-semanticwronginstance counts.
  Textgraphs ungrounded; allrelationcause/boundarycause labels remainunknown.
- Eightnewsynthetic tests pass locally/remote;28pipelinetests pass3.674s;
 568localarithmetic/labelchecks pass;71-scene pairedbootstrap recorded.
- Read-only schema probe printedrequested data but PowerShell heredoc terminator
  producedNameError after output; used byte-input launcher foractualaudit.
  No model/worker crash, no repair or training/GPUrerun.
- 223historicalanalysishashes and goal/queue/CSV/running hashes unchanged,
  trainingrepoclean; savecasebook/diagnosticreport and replaceboundedmemory.
- Pendinginside24hquestions checked; genericpull_log issue agedout but unresolved.
- Next: grounded exactidentity/geometric evidence onfixedcases, thenone
  hypothesis with derivation, primarypapers and falsificationcontrols. No noveltyclaim.

## 5. Decisions Made
{chr(10).join('- '+p.relative_to(P).as_posix() for p in decisions)}
All via log_decision.sh; no newquestions.

## \u26a0 Pending User Decisions
{chr(10).join('- '+p.name for p in questions) if questions else 'No type=question records in last24h.'}
Question20260910-075552 agedout08:07; placementresolved but genericpull_log
root/pairedextraction remainsunresolved. Aging is not approval orresolution.

================================================================================
  Next tick: 2026-09-11 09:07 Asia/Shanghai
================================================================================
"""
report_path.write_text(report, encoding="utf-8")
old = (P / "codex_memory.md").read_text(encoding="utf-8")
sections = dict(re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", old, re.M | re.S))
sections["Goal And Phase"] = f"""- Latest tickSep11 08:07; report{report_path.name}; disk overrideschat.
- Normalmonitor08:07/checker08:08:17exit0:Phase1NOTYET,ledgerM95.5020,target.5100,gap+.0080,baseline.4894.
- UserSep10researchrethink binding; goal12constraints/11bans primary; docs/experiment_scope_20260910.md operational.
- Structuralonly/no tuning;seed1999;epochs50/max_iters70;<=10G;no N^2attention. Scientificadmission overridesrefill.
- Sixareas:diagnosis,coremechanism/derivation,primarypaper novelty,matchedcontrols,robustness/generalization,efficiency.
- No newdatasets/externalannotation/multiseed campaigns; Phase2confirmedplanrequired. Actualcapacity4,waiting4;legacyFIFO preserved/notglobalhold.
"""
sections["Active Hypotheses"] = sections["Active Hypotheses"].replace(
    "- NEXT:freezeoperationalboundary/identity/ambiguity/relationlabelrules;inspectfixederrorsandmatchedsuccessnegativesusingexistingassets;reportmissinglabels/disagreements. Thenonehypothesis+N1derivation/primarypapersbeforetraining.\n", "")
sections["Active Hypotheses"] += f"""
- NEW D1INSTANCE complete reports/d1_instance_20260911-0810/{{protocol.json,instance_audit.json,verification.json,casebook.md,diagnostic_report.md}};fullreview/design081000.
- Protocolactualfreeze08:16:16 beforeCPUattribution; all568banks/284IDs/71scenes rawGTinstancejoin andunique-reindexedmappingexact,nomissingjoins.
- Baseline selectedlabels284:171targetpass,71same-semanticwronginstance,17unknownsemanticwronginstance,23no-instance-pass,2differentsemantic.
- M95 selectedlabels284:158targetpass,69same-semanticwronginstance,28unknownsemanticwronginstance,27no-instance-pass,2differentsemantic.
- Recoverable90baseline:63same/13unknown/12no-instance/2different;111M95:63same/25unknown/21no-instance/2different.
- M95extra21 NOTmore same-semanticwronginstance count;unknown+12/no-instance+9. CoarseID19(sem2nyu39)accounts6same-semanticwronginstance eachmodel.
-71/284targetsemanticunknown eachmodel; no majority-imputation. no-instance-pass withtargetbest6baseline/8M95;notproofwrongobject/missingcandidate/boundarycause.
-8synthetic tests local/remote pass,568localarithmetic/labelchecks,paired71scenebootstrap10kseed1999. Conditionalexploratoryuncertainty only.
-12hash-fixedM95recoverablecases/9unique same-scenesuccesscontrols/3missing;casebookdescriptive/outcome-selected,NOTcausalmatchedstudy.
-scene0046target26ann27fails/ann34succeeds bothmodels,sametargetdifferenttext;notcontrolledparaphrase. scene0146target16ann8targetbestbutpartialmask;causeunknown.
-All568relationcause/boundarycauseunknown;242/284parseredgepresent eachmodel notgroundedtruth. No humanadjudication/annotatoragreementclaim.
-CPUaudit23.694s,743.918MiBRSS,threads1,CUDAuninitialized;notfullmodelefficiencybenchmark. Workersyncedbothservers/tmp/cluster_d1_instance_20260911_0810.
- WorkerSHA{audit['worker_sha256']};auditSHAb4ae7b49570af648a336153776bdccbd5ecaf10b20a3281038000f2e3c05df69;fixedlauncheroutputsEXISTdonotblindlyrerun.
- NEXT:groundexactobjectidentities/geometrictextevidence onthese fixedcases,especiallysemanticunknown/coarseID19;retainmissinglabels,thenoneN1hypothesis/stepwisederivation/verifiedprimarypapers/controls. No newmechanism admitted.
"""
sections["Running And Queue"] = (
    f"- Latest{snapshot_path.relative_to(P).as_posix()};4trainers/4waiting/0claiming,ownershipunchanged.\n" +
    "\n".join(f"- {running[r['config']]['id']} {s}GPU{r['gpu']}PID{r['pid']}epoch{r['current_epoch']};best{r['best']['miou']}@{r['best']['epoch']},paired{r['best']['acc50']}/{r['best']['spmiou']},noimprove{r['no_improve']}."
              for s, r in live) +
    "\n- WaitingFIFOserver-4M189/M190/M191/M193;gpu=null/noholds/dependencies. Verifydeploymentwork_dir/data beforedispatch.\n"
    "- CPUworkercomplete,noGPUdiagnostic this tick. Server-6clockdifferent,nomixedclockstaleness.\n")
sections["Open Questions And Risks"] = sections["Open Questions And Risks"].replace(
    "- Pendingquestion20260910-075552:placementresolved;genericpull_log wrongroot/pairedextractionunresolved. Agingoutnotapproval;explicitretrievalbypasses,notglobalrepair.",
    "- Noquestioninside24h at08:07. Question20260910-075552agedout;placementresolved/genericpull_logwrongrootandpairedextractionunresolved. Agingnotapproval/resolution.")
sections["Open Questions And Risks"] = sections["Open Questions And Risks"].replace(
    "28pipelinetestspass07:16in3.550s.", "28pipelinetestspass08:16in3.674s.")
sections["Last Tick"] = f"""- TickSep11 08:07:unhealthyabsent08:07:27,monitor/checkerexit0;no newterminal/stop/modelcrash/traininglaunch.
- CPUinstanceattributioncomplete568banks/71scenes,12fixederrors9controls3missing;no newGPUinference.
-8syntheticlocal/remote tests +28pipelinetests pass;568arithmeticchecks,71scene pairedbootstrap;casebook/diagnosticreport saved.
- Read-onlyschemaprobe heredocNameError afterprintingdata;actualbyte-input workerexit0,no repair/GPUrerun. PriorCPUfloat/UTF8repairsremainhistorical.
- Decisions080905intent/081738interpretation via log_decision.sh; no newquestions/newmechanismadmission.
-223historicalanalysishashesmatch;goal/queue/CSV/runningunchanged;trainingrepoclean; sevenmemorysectionsunder200lines.
- Lastverify{now:%H:%M:%S};report{report_path.name}; finalsnapshot{snapshot_path.parent.name}.
- StateSHAs:goal{EXPECTED['goal.json']};queue{EXPECTED['queue.json']}.
- CSV{EXPECTED['experiments.csv']};running{EXPECTED['running.json']}.
- Nexttick09:07:preservetrainers/FIFO;groundfixedcaseobjectidentitiesanderrorlabels,thenN1singlemechanism/derivation/primarypapers;noautomaticselector/poolingdescendants.
"""
titles = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses", "Closed Or Failed Directions",
          "Running And Queue", "Open Questions And Risks", "Last Tick")
memory = "# Codex Research Memory\n\n" + "\n\n".join(f"## {t}\n{sections[t].strip()}" for t in titles) + "\n"
assert len(memory.splitlines()) < 200
(P / "codex_memory.md").write_text(memory, encoding="utf-8")
final = dict(verified_at=now.isoformat(), state_hashes=hashes, historical_analyses_verified=223,
             report=report_path.name, memory_lines=len(memory.splitlines()), repo_clean=True,
             pending_questions=[p.name for p in questions], audit_sha256=sha(OUT / "instance_audit.json"))
(OUT / "tick_verification.json").write_text(json.dumps(final, indent=2), encoding="utf-8")
print(json.dumps(final, indent=2))
