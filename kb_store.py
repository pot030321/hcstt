"""Build and read the persistent DDXPlus knowledge base."""

import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "knowledge_base.sqlite3"
SOURCE_URL = "https://doi.org/10.6084/m9.figshare.22687585"

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE source (
  id INTEGER PRIMARY KEY,
  dataset TEXT NOT NULL,
  version TEXT NOT NULL,
  url TEXT NOT NULL,
  conditions_sha256 TEXT NOT NULL,
  evidences_sha256 TEXT NOT NULL
);
CREATE TABLE disease (
  name TEXT PRIMARY KEY,
  icd10 TEXT,
  severity INTEGER CHECK (severity BETWEEN 1 AND 5),
  source_id INTEGER NOT NULL REFERENCES source(id)
);
CREATE TABLE evidence (
  code TEXT PRIMARY KEY,
  question_en TEXT NOT NULL,
  data_type TEXT NOT NULL,
  is_antecedent INTEGER NOT NULL CHECK (is_antecedent IN (0, 1)),
  source_id INTEGER NOT NULL REFERENCES source(id)
);
CREATE TABLE disease_evidence (
  disease_name TEXT NOT NULL REFERENCES disease(name),
  evidence_code TEXT NOT NULL REFERENCES evidence(code),
  relation TEXT NOT NULL CHECK (relation IN ('has_symptom', 'has_antecedent')),
  source_id INTEGER NOT NULL REFERENCES source(id),
  PRIMARY KEY (disease_name, evidence_code, relation)
);
CREATE INDEX idx_relation_evidence ON disease_evidence(evidence_code, relation);
CREATE INDEX idx_relation_disease ON disease_evidence(disease_name, relation);
"""


def connect(path=DB):
    if not Path(path).is_file():
        raise FileNotFoundError(f"Missing knowledge base: {path}. Run: py -3.11 kb_store.py")
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def build(raw=RAW, path=DB):
    raw, path = Path(raw), Path(path)
    conditions_file, evidences_file = raw / "release_conditions.json", raw / "release_evidences.json"
    conditions = json.loads(conditions_file.read_text(encoding="utf-8"))
    evidences = json.loads(evidences_file.read_text(encoding="utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="kb_", suffix=".sqlite3", dir=path.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(temporary)) as db, db:
            db.executescript(SCHEMA)
            db.execute("INSERT INTO source VALUES (1, ?, ?, ?, ?, ?)", (
                "DDXPlus English", "2", SOURCE_URL,
                hashlib.sha256(conditions_file.read_bytes()).hexdigest(),
                hashlib.sha256(evidences_file.read_bytes()).hexdigest(),
            ))
            db.executemany("INSERT INTO disease VALUES (?, ?, ?, 1)", (
                (name, item.get("icd10-id"), item.get("severity")) for name, item in conditions.items()
            ))
            db.executemany("INSERT INTO evidence VALUES (?, ?, ?, ?, 1)", (
                (code, item["question_en"], item["data_type"], int(item["is_antecedent"]))
                for code, item in evidences.items()
            ))
            db.executemany("INSERT INTO disease_evidence VALUES (?, ?, ?, 1)", (
                (name, code, relation)
                for name, item in conditions.items()
                for field, relation in (("symptoms", "has_symptom"), ("antecedents", "has_antecedent"))
                for code in item[field]
            ))
            if db.execute("PRAGMA foreign_key_check").fetchone() or db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Knowledge base failed integrity checks")
            actual = [db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("disease", "evidence", "disease_evidence")]
            expected = [len(conditions), len(evidences), sum(len(item[field]) for item in conditions.values() for field in ("symptoms", "antecedents"))]
            if actual != expected:
                raise ValueError(f"Knowledge base row count mismatch: {actual} vs {expected}")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return summary(path)


def load(path=DB):
    with closing(connect(path)) as db:
        evidences = {
            row["code"]: {"question_en": row["question_en"], "data_type": row["data_type"]}
            for row in db.execute("SELECT code, question_en, data_type FROM evidence")
        }
        conditions = {
            row["name"]: {"icd10-id": row["icd10"], "severity": row["severity"], "symptoms": {}, "antecedents": {}}
            for row in db.execute("SELECT name, icd10, severity FROM disease")
        }
        for row in db.execute("SELECT disease_name, evidence_code, relation FROM disease_evidence"):
            field = "symptoms" if row["relation"] == "has_symptom" else "antecedents"
            conditions[row["disease_name"]][field][row["evidence_code"]] = {}
    return evidences, conditions


def summary(path=DB):
    with closing(connect(path)) as db:
        source = dict(db.execute("SELECT * FROM source WHERE id = 1").fetchone())
        counts = {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("disease", "evidence", "disease_evidence")}
        counts.update({row[0]: row[1] for row in db.execute("SELECT relation, COUNT(*) FROM disease_evidence GROUP BY relation")})
        diseases = [row[0] for row in db.execute("SELECT name FROM disease ORDER BY name")]
    return {"source": source, "counts": counts, "diseases": diseases}


def explain(disease_name, path=DB):
    with closing(connect(path)) as db:
        rows = db.execute("""
            SELECT r.relation, e.code, e.question_en, s.dataset, s.version, s.url
            FROM disease_evidence AS r
            JOIN evidence AS e ON e.code = r.evidence_code
            JOIN source AS s ON s.id = r.source_id
            WHERE r.disease_name = ? ORDER BY r.relation, e.code
        """, (disease_name,)).fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
