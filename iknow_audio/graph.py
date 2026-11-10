"""Import and query the authors' Audio-centric Knowledge Graph."""

import csv
import io
import sqlite3
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data" / "iknow_source.zip"
DB = ROOT / "data" / "akg.sqlite3"


def build():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing authors' archive: {SOURCE}")
    DB.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE) as archive, sqlite3.connect(DB) as db:
        db.executescript("""
            DROP TABLE IF EXISTS triple;
            CREATE TABLE triple (
                id INTEGER PRIMARY KEY,
                split TEXT NOT NULL CHECK(split IN ('train', 'test')),
                label_name TEXT NOT NULL,
                head TEXT NOT NULL,
                relation TEXT NOT NULL,
                tail TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_row INTEGER NOT NULL,
                UNIQUE(split, source_row)
            );
            CREATE INDEX triple_head_split ON triple(head, split);
        """)
        for split, filename in (("train", "AKG_pruned.tsv"), ("test", "AKG_test.tsv")):
            member = next(name for name in archive.namelist() if name.endswith(filename))
            rows = csv.DictReader(io.StringIO(archive.read(member).decode("utf-8-sig")), delimiter="\t")
            values = []
            for rownum, row in enumerate(rows, 2):
                if row["response"] != "Yes.":
                    raise ValueError(f"Unexpected unfiltered row: {filename}:{rownum}")
                values.append((split, row["label_name"], row["head"], row["relation"], row["tail"], filename, rownum))
            db.executemany("INSERT INTO triple(split,label_name,head,relation,tail,source_file,source_row) VALUES (?,?,?,?,?,?,?)", values)
        counts = dict(db.execute("SELECT split, count(*) FROM triple GROUP BY split"))
        assert counts == {"test": 2039, "train": 18348}, counts
    return counts


def neighbors(db, name, limit=3):
    return [dict(zip(("head", "relation", "tail", "source_file", "source_row"), row))
            for row in db.execute("""SELECT head, relation, tail, source_file, source_row
                                     FROM triple WHERE split='train' AND lower(head)=lower(?)
                                     ORDER BY relation, tail LIMIT ?""", (name, limit))]


if __name__ == "__main__":
    print(build())
