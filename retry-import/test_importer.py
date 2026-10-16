import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from importer import KeyConflict, connect, import_names


class RetrySafeImportTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="case-", dir=".")
        self.addCleanup(self.workspace.cleanup)
        self.path = str(Path(self.workspace.name) / "imports.sqlite")
        self.db = connect(self.path)
        self.addCleanup(self.db.close)

    def counts(self):
        return tuple(self.db.execute("SELECT count(*) FROM " + table).fetchone()[0]
                     for table in ("items", "receipts"))

    def test_successful_retry_returns_original_receipt(self):
        first = import_names(self.db, "batch-1", ["Ada", "Grace"])
        retry = import_names(self.db, "batch-1", ["Ada", "Grace"])
        self.assertEqual(first, retry)
        self.assertEqual(self.counts(), (2, 1))

    def test_lost_response_retry_does_not_repeat_import(self):
        with self.assertRaises(TimeoutError):
            import_names(self.db, "batch-1", ["Ada"], lose_response=True)
        self.assertEqual(self.counts(), (1, 1))
        stored = json.loads(self.db.execute("SELECT result FROM receipts").fetchone()[0])
        self.assertEqual(import_names(self.db, "batch-1", ["Ada"]), stored)
        self.assertEqual(self.counts(), (1, 1))

    def test_changed_payload_rejected_and_original_stays_retriable(self):
        first = import_names(self.db, "batch-1", ["Ada", "Grace"])
        with self.assertRaises(KeyConflict):
            import_names(self.db, "batch-1", ["Grace", "Ada"])
        self.assertEqual(self.counts(), (2, 1))
        self.assertEqual(import_names(self.db, "batch-1", ["Ada", "Grace"]), first)

    def test_precommit_failure_rolls_back_rows_and_receipt(self):
        def fail():
            # Both tables have been written inside the uncommitted transaction.
            self.assertEqual(self.counts(), (2, 1))
            raise RuntimeError("simulated failure before commit")

        with self.assertRaisesRegex(RuntimeError, "before commit"):
            import_names(self.db, "batch-1", ["Ada", "Grace"], before_commit=fail)
        self.assertEqual(self.counts(), (0, 0))
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(import_names(self.db, "batch-1", ["Ada", "Grace"])["count"], 2)
        self.assertEqual(self.counts(), (2, 1))

    def test_receipt_survives_new_process_and_connection(self):
        with self.assertRaises(TimeoutError):
            import_names(self.db, "batch-1", ["Ada"], lose_response=True)
        stored = json.loads(self.db.execute("SELECT result FROM receipts").fetchone()[0])
        self.db.close()
        script = """
import json, sys
from importer import connect, import_names
with connect(sys.argv[1]) as db:
    print(json.dumps(import_names(db, 'batch-1', ['Ada']), sort_keys=True))
    assert db.execute('SELECT count(*) FROM items').fetchone()[0] == 1
    assert db.execute('SELECT count(*) FROM receipts').fetchone()[0] == 1
"""
        completed = subprocess.run(
            [sys.executable, "-B", "-c", script, self.path],
            check=True, text=True, capture_output=True,
        )
        self.assertEqual(json.loads(completed.stdout), stored)


if __name__ == "__main__":
    unittest.main()
