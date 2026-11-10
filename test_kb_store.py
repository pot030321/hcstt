"""Check KB import, foreign keys and parity with the source JSON."""

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from kb_store import RAW, build, connect, load


class StoreTest(unittest.TestCase):
    def test_import_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "kb.sqlite3"
            info = build(RAW, db_path)
            evidences, conditions = load(db_path)
            source = json.loads((RAW / "release_conditions.json").read_text(encoding="utf-8"))
            self.assertEqual(source["Acute laryngitis"]["symptoms"].keys(), conditions["Acute laryngitis"]["symptoms"].keys())
            self.assertEqual((49, 223, 605, 283), tuple(info["counts"][name] for name in ("disease", "evidence", "has_symptom", "has_antecedent")))
            self.assertEqual(223, len(evidences))
            with closing(connect(db_path)) as db:
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("INSERT INTO disease_evidence VALUES (?, ?, 'has_symptom', 1)", ("Unknown disease", "E_91"))


if __name__ == "__main__":
    unittest.main()
