"""Evaluate disease ranking on a fixed sample of DDXPlus synthetic test patients."""

import ast
import csv
import json
import random
import zipfile
from pathlib import Path

from kb import load_kb, rank


ROOT = Path(__file__).parent
SAMPLE_SIZE = 1000
SEED = 7


def sample_patients():
    rng = random.Random(SEED)
    sample = []
    with zipfile.ZipFile(ROOT / "data" / "raw" / "release_test_patients.zip") as archive:
        with archive.open("release_test_patients") as file:
            rows = csv.DictReader((line.decode("utf-8") for line in file))
            for index, row in enumerate(rows):
                if index < SAMPLE_SIZE:
                    sample.append(row)
                else:
                    chosen = rng.randrange(index + 1)
                    if chosen < SAMPLE_SIZE:
                        sample[chosen] = row
    return sample, index + 1


def scores(rows, conditions, weighted):
    hits1 = hits5 = reciprocal = evaluated = 0
    symptom_codes = {code for condition in conditions.values() for code in condition["symptoms"]}
    for row in rows:
        codes = {item.split("_@_")[0] for item in ast.literal_eval(row["EVIDENCES"])} & symptom_codes
        if not codes:
            continue
        if weighted:
            names = [name for _, name, _ in rank(conditions, codes)]
        else:
            names = [
                name for name, condition in sorted(
                    conditions.items(),
                    key=lambda item: (-len(codes & item[1]["symptoms"].keys()), item[0]),
                )
                if codes & condition["symptoms"].keys()
            ]
        evaluated += 1
        if row["PATHOLOGY"] in names:
            position = names.index(row["PATHOLOGY"]) + 1
            hits1 += position == 1
            hits5 += position <= 5
            reciprocal += 1 / position
    return {
        "evaluated": evaluated,
        "top1": round(hits1 / evaluated, 4),
        "recall_at_5": round(hits5 / evaluated, 4),
        "mrr": round(reciprocal / evaluated, 4),
    }


def main():
    _, conditions = load_kb()
    rows, total = sample_patients()
    report = {
        "source": "DDXPlus English v2 synthetic test patients",
        "total_test_rows": total,
        "sample_size": len(rows),
        "seed": SEED,
        "ranking_from": "positive symptom codes only; categorical values ignored",
        "unweighted_overlap": scores(rows, conditions, False),
        "idf_weighted_overlap": scores(rows, conditions, True),
    }
    output = ROOT / "artifacts" / "kb_eval.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
