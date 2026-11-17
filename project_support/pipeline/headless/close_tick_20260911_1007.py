"""Render a verified tick snapshot without changing research/training registries."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import sys
from audit_binding_scope_20260911 import P, OUT, sha
from close_tick_20260911_0707 import EXPECTED, table

now = datetime.now()
snapshot_path = Path(sys.argv[1])
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
assert (now - datetime.fromisoformat(snapshot["collected_at"])).total_seconds() < 600
v = json.loads((OUT / "verification.json").read_text(encoding="utf-8"))
assert v["status"] == "passed" and v["formal_tests"] == 13
assert {n: sha(P / n) for n in EXPECTED} == EXPECTED
queue = json.loads((P / "queue.json").read_text(encoding="utf-8"))
entries = [(s, r) for s, rs in queue["gpu_queues"].items() for r in rs]
waiting = [(s, r) for s, r in entries if r["status"] == "waiting"]
running = {r["config"]: r for s, r in entries if r["status"] == "running"}
live = [(s, r) for s, srv in snapshot["servers"].items() for r in srv["runs"]]
assert len(waiting) == len(live) == len(running) == 4
assert {r["config"] for s, r in live} == set(running)
gpu = table(["Server", "GPU", "Util", "Memory MiB", "Process"],
            [(s, g["gpu"], f"{g['util']}%", f"{g['used_mib']}/{g['total_mib']}",
              "; ".join(f"{running[r['config']]['id'].split('-')[0]} PID{r['pid']}"
                        for r in srv["runs"] if str(r["gpu"]) == str(g["gpu"])))
             for s, srv in snapshot["servers"].items() for g in srv["gpus"]])
rt = table(["ID", "Config", "Server", "GPU", "Epoch", "Best mIoU", "Acc@50", "spmIOU", "No-Impr", "Status"],
           [(running[r["config"]]["id"], Path(r["config"]).stem, s, r["gpu"],
             f"{r['current_epoch']}/50", f"{r['best']['miou']:.10f}@{r['best']['epoch']}",
             r["best"]["acc50"], r["best"]["spmiou"], f"{r['no_improve']}/10", "running") for s, r in live])
qt = table(["Position", "ID", "Config", "Status", "Depends On", "Server"],
           [(i, r["id"], r["config"], "waiting", r.get("depends_on") or "none", s)
            for i, (s, r) in enumerate(waiting, 1)])
questions = [p for p in (P / "decisions").glob("*_question.md")
             if now - timedelta(hours=24) <= datetime.strptime(p.name[:15], "%Y%m%d-%H%M%S") <= now]
decisions = [p for p in (P / "decisions").glob("20260911-*_*.md")
             if datetime(2026, 9, 11, 10, 7) <= datetime.strptime(p.name[:15], "%Y%m%d-%H%M%S") <= now]
report_path = P / "reports" / f"summary_{now:%Y%m%d-%H%M%S}.md"
report = f"""================================================================================
  Research Pipeline Report - cluster_project
  {now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #20260911-1007)
================================================================================

## 0. Goal Status
Target:mIoU>=.5100 | Champion:M95 .5020 ledger | Gap:+.0080 |
Phase:1 NOT YET. Required checker10:08:41exit0; baselineledger.4894.
Goal12constraints/11bans unchanged; scientificadmission overrides refill.

## 1. GPU Overview
Source:{snapshot_path.relative_to(P).as_posix()}; whitelist only.
{gpu}
Free training slots0/4. ActualSERVERS capacity4 overrides nominal5; server-4
one/card,server-6GPU7max2. No GPUdiagnostic/newinference this tick.

## 2. Running Experiments
{rt}
Four original PIDs retained;metrics paired atbestvalidation. No newterminal.
Server-6clock differs;do not usemixedclock to inferstaleness.

## 3. Queue Status
{qt}
Depth4/capacity4:NEED MORE(target>=5). Scientificadmission incomplete;no refill.
FIFO/nullGPU/noholds/0claiming unchanged. No globalpause orautomaticdescendants.

## 4. This Tick's Actions
- Read memoryfirst;reconcile goal,queue,CSV,SERVERS,recentdecisions/analyses/
  designs/bugfixes/reports andbothreferences. Unhealthyabsent10:07.
- Required normalmonitor10:07exit0 andchecker10:08:41exit0;initial/final live.
- No newterminal;M186 alreadyarchived/analyzed/oneCSVrow.223historicalanalysis
  hashes verified;no duplicateanalysis. Goal/queue/CSV/runningSHAunchanged.
- Fullgoal six-sectionreview then seven-sectiondesign101200;authoredtext
  scopeaudit on21fixeddescriptions/12errors/9controls,3missingcontrols retained.
  All source spans exactchecked. Unblindedreadings,not independentannotations.
- No confirmed narrowtwo-predicates/same-target-anchor structure underthis
  reading rule;distinctanchors,nestedchains andscopeambiguity retained.
  Eightdescriptions haveemptyexactlexicaldomains;NOT anchorproposal missrate.
  All physicalrelationtruth/cause fieldsunknown;no prevalence/causalclaims.
- 13synthetic formaltests passed:hardbound/counterexample,onepredicate,
  softgapbothsigns,gradientfinite-difference,variationaloptimum,massconservation,
  permutation,zero-mass/invaliddomains,separateanchors andstablelogsumexp.
- Primaryfulltexts NS3D arXiv2303.13483v1 andCSVG arXiv2411.14594v2 retrieved/
  archived/hashchecked;methodsections reviewed. Boundedprioraudit,notexhaustive
  literature clearance. Genericrelational/jointanchorreasoning notnovel.
- Built mechanism_audit.md withhard/softderivation andimplementationgaps.
  V-J not universallynonnegative;do not useas derivedinconsistencyloss.
- Webtool returned no usableoutput;directprimaryHTML retrieval succeeded.
  Initialconsoleprint hadGBKUnicodeEncodeError,UTF8rerun succeeded;noexperiment
  orworkercrash,no modelrepair/rerun. No externalannotation/API labeling.
- Standalonehelper and7auditfiles total hash-synced tobothservers inisolated
  /tmp/cluster_binding_scope_20260911_1012;deploymentdiffs unchanged.
  No trainingcode/config commit/push/enqueue. No remoteauditworker launched.
- Local13tests/helpercompilepassed;prior28pipeline regressiontests historical,
  not rerun. No measuredfullmodel efficacy/latency/memory claim.
- Read-only M95loss.py182-215 andmatchingpath around529:next task iscandidate
  supervision/assignment audit,not an establishedbug or newstructuralproposal.
- Prioridentityresource prose corrected innewmemory fromJSON:2.3718043118715286s,
  580.81640625MiB. Priorreport approximate2.371/580.820 retained ashistorical.
- Pendingquestionwindow checked;retentioncleanup recorded separately below;
  boundedseven-section memory replaced.

## 5. Decisions Made
{chr(10).join('- '+p.relative_to(P).as_posix() for p in sorted(decisions))}
All via log_decision.sh. Mainshared-witness proposal notadmitted now;prior-art/
applicability gaps remain. Not a permanentban on futuregroundedevidence.

## \u26a0 Pending User Decisions
{chr(10).join('- '+p.name for p in questions) if questions else 'No type=question records withinlast24h.'}
Question20260910-075552 agedout;placementresolved/genericpull_logroot/paired
extraction unresolved. Agingnotapproval/resolution.

================================================================================
  Next tick:2026-09-11 11:07 Asia/Shanghai
================================================================================
"""
report_path.write_text(report, encoding="utf-8")
old = (P / "codex_memory.md").read_text(encoding="utf-8")
sections = dict(re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", old, re.M | re.S))
sections["Goal And Phase"] = sections["Goal And Phase"].replace(
    "TickSep11 09:07 complete; reportsummary_20260911-092100.md",
    f"TickSep11 10:07 complete; report{report_path.name}").replace(
    "Monitor09:10/checker09:10:30", "Monitor10:07/checker10:08:41")
sections["Active Hypotheses"] = sections["Active Hypotheses"].replace(
    "CPU2.371s/580.820MiBRSS", "CPU2.3718043118715286s/580.81640625MiBRSS")
sections["Active Hypotheses"] = "\n".join(line for line in sections["Active Hypotheses"].splitlines()
                                         if not line.startswith("- NEXT:")) + """
- NEW scope/formalaudit reports/binding_scope_20260911-1012/{protocol.json,scope_audit.json,case_scope.md,formal_tests.json,mechanism_audit.md,sources.json,verification.json}.
- 21fixeddescriptions12errors9controls,3missing;authored/unblindedtextreadings,notindependentannotation.0confirmed narrowtwo-target-anchor-predicates structure,notzero realbindingfailures.
- Scopecounts:ambiguous1,differentreferents2,single8,scene/unary4,nested2,differentreferents-ambiguous2,comparisonmissing1,pluraldistinct1. Emptyexactlexicaldomains4errors/4controls,NOTmissedphysicalanchors.
- scene0621chair22 at(chair,table)/closest(table,door) nestedchain;scene0426pillow22 distinctbed/blankets+attachmentunknown;scene0578chair5 right/front unspecified;noforcedsharedwitness.
-13formaltests pass;hardC<=U valid finitecommondomain;R1degenerate. SoftV=sumlogEexp(ell),J=logEexp(sumell):V-J bothpositive/negative;NOT nonnegativeinconsistencyloss.
- VariationalJ=max_q E_qE-KL(q||pi),gradientq*,massconservingequalenergyduplication verified;these are mathematicalproperties NOTnovelty/productionforward verification.
- NS3D primary2303.13483v1(Mar23,2023)section3.3 verified:object-centric softbinary andternary referenceexecution;productreferenceweights not intrinsicallydiagonalidentity. No efficacy/incapacityclaim.
- CSVG primary2411.14594v2(Aug11,2025)section3.1-3.3 verified:jointobjectvariables/domainconstraints/backtracking alreadypreserve sharedvariableidentity. Broadjointanchorclaim notnovel.
- BothHTMLfulltexts archived/hashes sources.json;boundedmethodaudit only,notlatest/exhaustivesearch. Webreturnedempty;directurllib succeeded afterUTF8consolefix.
- Existing shared-witnessproposal NOT mainmechanism now:applicabilityunconfirmed,broadprioroverlap,anchor/parse/frame/energy/loss/resources unresolved. No permanentban,neverrenameknownmethodasnovel.
- All21physicalrelation/cause fieldsunknown. No newmodel/inference/dataset/annotationAPI. Helper+auditdocs hash-syncedbothservers/tmp/cluster_binding_scope_20260911_1012,notrainingdiffmutation.
- ScopeSHA08440c9ad7e359287e8f9a857ecde81eecdd3da485f8635e12f9d5ebba4be3ff;formalSHAcd9cdeab076d883be355004a5af8bf8dc5e8028f666cb4a24dce1cdf10f1d71f.
- NEXT:read M95loss.py182-215 loss_indi andmatch_sampled_ins around529 versusnetwork.py188-189 selection. Audit whether usabletarget candidates receive intendeddiscrimination supervision;not yet a provenbug. ThenONE falsifiable discrepancy/derivation/primarycomparison beforeadmission.
"""
sections["Running And Queue"] = (
    f"- Final{snapshot_path.relative_to(P).as_posix()};4trainers/4waiting/0claiming,ownershipunchanged.\n" +
    "\n".join(f"- {running[r['config']]['id']} {s}GPU{r['gpu']}PID{r['pid']} epoch{r['current_epoch']};best{r['best']['miou']}@{r['best']['epoch']},paired{r['best']['acc50']}/{r['best']['spmiou']},noimprove{r['no_improve']}."
              for s, r in live) +
    "\n- WaitingFIFOserver-4M189/M190/M191/M193;nullGPU/noholds/dependencies;verifywork_dir/data beforedispatch.\n"
    "- Capacity4:server-4one/card,server-6GPU7max2. No remoteauditworker/GPUdiagnostic this tick.\n")
sections["Open Questions And Risks"] = sections["Open Questions And Risks"].replace("Noquestioninside24h09:19", "Noquestioninside24h10:19").replace("not rerun09:07tick", "not rerun10:07tick").replace("09:07tick,isolatedhelper", "10:07tick,isolatedhelper")
sections["Last Tick"] = f"""- Sep11 10:07:unhealthyabsent,monitor/checkerexit0;4trainers4waiting;no newterminal/stop/launch.
-21descriptiontextscopeaudit+13formaltests completed;2primarymethodsections verified/HTMLarchived;no same-witnessmainmechanismadmission.
- Decisions100951intent/101644interpretation logged;no newquestions. Bothserversisolatedhelper/docs hashverified,preserveddeploymentdiffs.
- InitialprimaryHTMLconsoleGBKprintfailed;UTF8print succeeded,noexperimentcrash/repair. Productionpipeline testsnotrerun.
-223historicalanalysishashes andgoal/queue/CSV/runningunchanged;trainingrepoclean;noGPUdiagnostic/remoteworker.
- Report{report_path.name};finalsnapshot{snapshot_path.parent.name};memoryboundedsevensections.
- StateSHA goal{EXPECTED['goal.json']};queue{EXPECTED['queue.json']}.
- CSV{EXPECTED['experiments.csv']};running{EXPECTED['running.json']}.
- Next11:07:preserveFIFO;candidateassignment/discrimination supervision audit,notanotherpooling/shared-anchorvariant. Correct evidence thenN1/T0.
"""
titles = ["Goal And Phase", "Champion And Baseline", "Active Hypotheses", "Closed Or Failed Directions",
          "Running And Queue", "Open Questions And Risks", "Last Tick"]
memory = "# Codex Research Memory\n\n" + "\n\n".join(f"## {t}\n{sections[t].strip()}" for t in titles) + "\n"
assert len(memory.splitlines()) < 200
(P / "codex_memory.md").write_text(memory, encoding="utf-8")
(OUT / "tick_verification.json").write_text(json.dumps(dict(
    verified_at=now.isoformat(), report=report_path.name, memory_lines=len(memory.splitlines()),
    pending_questions=[p.name for p in questions], state_hashes=EXPECTED,
    snapshot=str(snapshot_path), historical_analyses=223), indent=2), encoding="utf-8")
print(report_path)
print("MEMORY_LINES", len(memory.splitlines()), "QUESTIONS", len(questions))
