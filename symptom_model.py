"""Train and evaluate a small contrastive symptom text encoder."""

import csv
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).parent
ARTIFACTS = ROOT / "artifacts"


def phrases():
    with (ROOT / "data" / "phrases.csv").open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def metrics(rows, codes, similarities):
    predicted = np.argsort(-similarities, axis=1)
    targets = np.array([codes.index(row["evidence_id"]) for row in rows])
    return {
        "count": len(rows),
        "top1": round(float(np.mean(predicted[:, 0] == targets)), 4),
        "top3": round(float(np.mean([target in order[:3] for target, order in zip(targets, predicted)])), 4),
    }


def train():
    torch.manual_seed(7)
    rows = phrases()
    evidences = json.loads((ROOT / "data" / "raw" / "release_evidences.json").read_text(encoding="utf-8"))
    codes = sorted({row["evidence_id"] for row in rows})
    labels = [evidences[code]["question_en"] for code in codes]
    splits = {name: [row for row in rows if row["split"] == name] for name in ("train", "val", "test")}
    assert all(splits.values()) and all(code in evidences for code in codes)
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=2048)
    vectorizer.fit(labels + [row["text"] for row in splits["train"]])
    label_vectors = vectorizer.transform(labels).toarray().astype("float32")
    train_vectors = vectorizer.transform([row["text"] for row in splits["train"]]).toarray().astype("float32")
    val_vectors = vectorizer.transform([row["text"] for row in splits["val"]]).toarray().astype("float32")
    model = nn.Linear(train_vectors.shape[1], 64, bias=False)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    labels_tensor = torch.from_numpy(label_vectors)
    train_tensor = torch.from_numpy(train_vectors)
    targets = torch.tensor([codes.index(row["evidence_id"]) for row in splits["train"]])
    best_state, best_val, best_epoch = None, -1.0, 0

    for epoch in range(1, 101):
        model.train()
        logits = F.normalize(model(train_tensor), dim=1) @ F.normalize(model(labels_tensor), dim=1).T / 0.1
        loss = F.cross_entropy(logits, targets)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if epoch % 5 == 0:
            with torch.no_grad():
                scores = F.normalize(model(torch.from_numpy(val_vectors)), dim=1) @ F.normalize(model(labels_tensor), dim=1).T
            val_top1 = metrics(splits["val"], codes, scores.numpy())["top1"]
            if val_top1 > best_val:
                best_state, best_val, best_epoch = deepcopy(model.state_dict()), val_top1, epoch

    model.load_state_dict(best_state)
    report = {"method": "char TF-IDF plus 64D contrastive projection", "classes": len(codes), "best_epoch": best_epoch}
    for split in ("val", "test"):
        vectors = vectorizer.transform([row["text"] for row in splits[split]]).toarray().astype("float32")
        baseline = vectors @ label_vectors.T
        with torch.no_grad():
            projected = F.normalize(model(torch.from_numpy(vectors)), dim=1) @ F.normalize(model(labels_tensor), dim=1).T
        report[split] = {
            "tfidf": metrics(splits[split], codes, baseline),
            "contrastive": metrics(splits[split], codes, projected.numpy()),
        }

    ARTIFACTS.mkdir(exist_ok=True)
    joblib.dump(vectorizer, ARTIFACTS / "vectorizer.joblib")
    torch.save({"state": model.state_dict(), "codes": codes, "labels": labels}, ARTIFACTS / "projection.pt")
    (ARTIFACTS / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


@lru_cache(maxsize=1)
def load():
    vectorizer = joblib.load(ARTIFACTS / "vectorizer.joblib")
    saved = torch.load(ARTIFACTS / "projection.pt", map_location="cpu", weights_only=True)
    model = nn.Linear(len(vectorizer.get_feature_names_out()), 64, bias=False)
    model.load_state_dict(saved["state"])
    model.eval()
    labels = torch.from_numpy(vectorizer.transform(saved["labels"]).toarray().astype("float32"))
    with torch.no_grad():
        label_embeddings = F.normalize(model(labels), dim=1)
    return vectorizer, model, saved["codes"], label_embeddings


def predict(text, top_k=3):
    vectorizer, model, codes, label_embeddings = load()
    vector = torch.from_numpy(vectorizer.transform([text]).toarray().astype("float32"))
    with torch.no_grad():
        scores = (F.normalize(model(vector), dim=1) @ label_embeddings.T)[0].numpy()
    return [(codes[index], round(float(scores[index]), 3)) for index in np.argsort(-scores)[:top_k]]


if __name__ == "__main__":
    train()
