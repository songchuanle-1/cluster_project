"""Render final six-section report with current state and evidence checks."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import subprocess
from prepare_d1_margin_20260911 import ROOT,P,OUT
from d1_candidate_bank_20260911 import sha
from close_tick_20260911_0707 import EXPECTED,table


def main():
    now = datetime.now()
    snap_path = P / "reports/live_20260911-141350/snapshot.json"
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    assert (now-datetime.fromisoformat(snap["collected_at"])).total_seconds() < 600
    assert {n:sha(P/n) for n in EXPECTED} == EXPECTED
    v = json.loads((OUT/"verification.json").read_text())
    ex = json.loads((OUT/"execution.json").read_text())
    assert v["status"] == "passed" and v["records"] == 568
    assert set(ex["deployments"]) == {"server-4","server-6"}
    assert not subprocess.check_output(["git","-C",str(ROOT/"Cluster"),"status","--porcelain"])
    q = json.loads((P/"queue.json").read_text(encoding="utf-8"))
    entries = [(s,r) for s,rs in q["gpu_queues"].items() for r in rs]
    waiting = [(s,r) for s,r in entries if r["status"] == "waiting"]
    running = {r["config"]:r for s,r in entries if r["status"] == "running"}
    live = [(s,r) for s,srv in snap["servers"].items() for r in srv["runs"]]
    assert len(waiting) == len(running) == len(live) == 4
    assert set(running) == {r["config"] for s,r in live}
    gpu = table(["Server","GPU","Util","Memory MiB","Process"],
                [(s,g["gpu"],f"{g['util']}%",f"{g['used_mib']}/{g['total_mib']}",
                  "; ".join(f"{running[r['config']]['id'].split('-')[0]} PID{r['pid']}"
                            for r in srv["runs"] if str(r["gpu"])==str(g["gpu"])))
                 for s,srv in snap["servers"].items() for g in srv["gpus"]])
    rt = table(["ID","Config","Server","GPU","Epoch","Best mIoU","Acc@50","spmIOU","No-Impr","Status"],
               [(running[r["config"]]["id"],Path(r["config"]).stem,s,r["gpu"],
                 f"{r['current_epoch']}/50",f"{r['best']['miou']:.10f}@{r['best']['epoch']}",
                 r["best"]["acc50"],r["best"]["spmiou"],f"{r['no_improve']}/10","running") for s,r in live])
    qt = table(["Position","ID","Config","Status","Depends On","Server"],
               [(i,r["id"],r["config"],"waiting",r.get("depends_on") or "none",s)
                for i,(s,r) in enumerate(waiting,1)])
    questions = [p for p in (P/"decisions").glob("*_question.md")
                 if now-timedelta(hours=24) <= datetime.strptime(p.name[:15],"%Y%m%d-%H%M%S") <= now]
    report = f"""================================================================================
  Research Pipeline Report - cluster_project
  {now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #20260911-1407)
================================================================================

## 0. Goal Status
Target:mIoU>=.5100 | Champion:M95 .5020 ledger | Gap:+.0080 |
Phase:1 NOT YET. Baselineledger.4894.
Normalmonitor14:07/checker14:08:47 exit0. Goal12constraints/11bans unchanged;
scientific admission takes precedence over queue refill.

## 1. GPU Overview
Source:reports/live_20260911-141350/snapshot.json;whitelist only.
{gpu}
Free training slots0/4. Actual SERVERS capacity4 overrides nominal5:
server-4 one/card,server-6GPU7max2. No new inference or GPU worker this tick.

## 2. Running Experiments
{rt}
Four original PIDs retained;metrics paired atbestvalidation. M188newbest
.4916119576 remains belowchampion. No new terminal/stop/launch.
Server-6clock differs;useepoch/log progression,notmixedclock staleness.

## 3. Queue Status
{qt}
Depth4/capacity4:NEED MORE(target>=5). No scientifically admitted newmechanism;
continued diagnostic evidence undergoalprecedence. FIFO/nullGPU/noholds/
claiming0 unchanged. No globalpause orautomaticdescendants.

## 4. This Tick's Actions
- Read memoryfirst;mandatoryreferences,goal/queue/CSV/SERVERS/recent
  decisions/analyses/designs/bugfixes/reports reconciled. Unhealthyabsent14:07.
- Requiredmonitor/checkerexit0;finalreadonlysnapshot. No newterminal;
  M186alreadyanalyzed/archived/oneCSVrow;no duplicateterminalanalysis.
- State goal/queue/CSV/runningSHAunchanged.223historicalanalysis hashes
  verified;224currentfiles. Trainingrepo clean,no productioncode mutation.
- Fullgoal six-sectionreview then seven-sectiondesign141000;protocol
  freeze14:11:55 beforeaudit. Scientificadmissionblocksnewmodelenqueue.
- All568original evaluationbank records/284IDs/model/71scenes verified.
  No new recapture or data/annotationAPI/reservedscene/seedcampaign.
- Derived g=w(p-y)/M;independenttwologit flow dot(d)=-2g;selected-minus-H
  marginvelocity=-2(g_s-g_h). FixedGTeligibleG/H,emptymissing,sameindexzero.
  Globalpositive loss/batchnormalizer rescales,not reversesdirection.
- 568analytic gradients agreewithstoredsourcefloat32autograd:
  maxerror7.21263487824e-8,atol1e-7/rtol1e-5. Newsourceautograd not rerun.
  Independent scalar verification568passes;4labelpairFD tests,tie,
  permutation/saturation pass;actualmissing/identicalcases covered.
  MaxlossFDerror1.304679e-11;directionFDerror2.164613e-11.
- Recoverable baseline90/M95111;Havailable84/99;all84/99Hmarginvelocities
  negative. Selectednegative withH79/97;remaining5/2selectedpositive.
  Same-label contractiondoesnotguaranteeranking inversion:identical scalar
  flowpreservesinitialorder. No actualmodeltrainingforecast.
- BestGmarginincreases1/90baseline,4/111M95;selectedpositive/eligiblenegative.
  Thisislabel/qualitymismatch,not necessarilylabelbug or dominantcause.
- CommonH243IDs/71scenes pairedmeanmargin.827048233/1.022529846,
  delta+.195481614 CI[-.077619641,.500636467]. NotgenerallyworseM95margin.
  All284selectednegative+Hrecoverablerates79/97,delta+.063380282,
  CI[.014084507,.112676056].10000pairedscenebootstrapseed1999,
  conditional/repeatedlyminedvalidation;notcausal/population confirmation.
- Sourceparameterflowuses-JJ^Tg,notindependent-logit-g;optimizer/otherlosses/
  augmentation notmodeled. Rejectmissingcorrectivesupervisionasdominant
  explanation;no automatic rankingloss/selector/pooling variant.
- AuditCPU .2908139s;firstexecutionexit0,0repairs. Notfullefficiencybenchmark.
  Fourhelperscompile. Prior28pipeline tests08:16historical,notrerun.
- Reportrenderer initiallyhitWindowsGBKqueue decodeerror beforewriting;
  helper-onlyrepair1explicitUTF8. No researchworker/trainingcrash.
- Helpers/protocol/review/design/results9files hash-syncedbothserversisolated
  /tmp/cluster_d1_margin_20260911_1410;deploymentdiffs preserved.
  Remote archivalcopies,notstandalonelaunchers;no model/configcommit/push.
- Read M95dec.py256,267-303:indi_embedding consumes decoderquery;
  prediction_head normalizesitslocalquery for masks/scores only. Semantic
  projectionisnotheadinput;next boundedhead-feature/Jacobianaudit needsnew
  predeclaredcapture,notunconditional score-statistic expansion.
- Results/formulas/limits:reports/d1_margin_20260911-1410/
  {{protocol.json,margin.json,verification.json,diagnostic_report.md,execution.json}}.
- Retention14:16:49deleted2expiredsummaryfiles afterpathverification:
  summary_20260910-133700.md andsummary_20260910-141100.md;analysesuntouched.
- Pendingquestion24hwindowchecked;seven-sectionmemoryreplacedunder200lines.

## 5. Decisions Made
- 14:09:14 other:freezeexisting-bankdiscriminator margins/gradientaudit,
  retaintrainers/FIFO. decisions/20260911-140914_other.md.
- 14:16:03 other:rejectdominantmissingcorrectivesignals interpretation;
  examineheadparametercouplingnext,noautomaticloss/enqueue.
  decisions/20260911-141603_other.md.
- 14:18:53 other:report-onlyrepair1explicitUTF8;no statechange.
  decisions/20260911-141853_other.md.
Allviarequiredlog_decision.sh.

## \u26a0 Pending User Decisions
{chr(10).join('- '+p.name for p in questions) if questions else 'No type=question records withinlast24h.'}
Question20260910-075552agedout;placementresolved,genericpull_logroot/paired
extractionunresolved. Agingdoesnotconstituteapprovalorresolution.

================================================================================
  Next tick:2026-09-11 15:07 Asia/Shanghai
================================================================================
"""
    path = P/"reports"/f"summary_{now:%Y%m%d-%H%M%S}.md"
    path.write_text(report,encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
