import csv
import tempfile
import unittest
from pathlib import Path

import check_goal
import pipeline_monitor


PROJECT_FIELDS = [
    "id", "status", "server", "gpus", "config", "best_miou",
    "best_acc_05", "best_acc_025", "best_spmiou", "best_epoch", "notes",
]


class AdaresLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / "pipeline").mkdir()
        self.ledger = self.project / "pipeline/experiments.csv"

    def test_mixed_historical_rows_are_read_by_their_own_schema(self):
        with self.ledger.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(PROJECT_FIELDS)
            writer.writerow(["B4", "done_complete", "server-2", "0", "b4.yaml",
                             "0.5094", "", "", "", "30", ""])
            writer.writerow(["2026-09-28 10:46:26", "W2", "w2.yaml", "server-2",
                             "0", "done_complete", "0.5100", "30/30", ""])
        rows = check_goal.load_experiments_csv(self.project)
        self.assertEqual(len(rows), 2)
        self.assertEqual(check_goal.find_champion(rows, {}, "mIoU")["id"], "W2")

    def test_new_terminal_row_respects_existing_project_header(self):
        with self.ledger.open("w", newline="", encoding="utf-8") as output:
            csv.writer(output).writerow(PROJECT_FIELDS)
        pipeline_monitor.ledger_append(
            self.project, finished_at="2026-09-28 11:00:00", id="W2",
            config="w2.yaml", server="server-2", gpu="0",
            state="done_complete", best_miou="0.5100", epochs="30/30")
        with self.ledger.open(newline="", encoding="utf-8") as source:
            rows = list(csv.reader(source))
        self.assertEqual(len(rows[0]), len(rows[1]))
        self.assertEqual(rows[1][0], "W2")
        self.assertEqual(rows[1][1], "done_complete")
        self.assertEqual(rows[1][5], "0.5100")

    def test_unknown_header_refuses_append(self):
        self.ledger.write_text("id,score\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            pipeline_monitor.ledger_append(self.project, id="W2")
        self.assertEqual(self.ledger.read_text(encoding="utf-8"), "id,score\n")


if __name__ == "__main__":
    unittest.main()
