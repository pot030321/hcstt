"""Small RotatE-style tail-prediction experiment on the authors' AKG split."""

import json
import random
import sqlite3
from collections import Counter, defaultdict

import numpy as np
import torch
from torch import nn

from graph import DB, ROOT


SEED = 42
DIM = 64
EPOCHS = 10
# shortcut: uniform negative tails and fixed epochs; tune sampling and validation for paper-level KGE.


class RotatE(nn.Module):
    def __init__(self, entities, relations):
        super().__init__()
        self.entity = nn.Embedding(entities, DIM * 2)
        self.phase = nn.Embedding(relations, DIM)
        nn.init.uniform_(self.entity.weight, -.1, .1)
        nn.init.uniform_(self.phase.weight, -np.pi, np.pi)

    def forward(self, heads, relations, tails):
        real, imag = self.entity(heads).chunk(2, -1)
        tail_real, tail_imag = self.entity(tails).chunk(2, -1)
        phase = self.phase(relations)
        distance = torch.sqrt((real * phase.cos() - imag * phase.sin() - tail_real).square()
                              + (real * phase.sin() + imag * phase.cos() - tail_imag).square() + 1e-9)
        return 12 - distance.sum(-1)


def data():
    with sqlite3.connect(DB) as db:
        rows = list(db.execute("SELECT split, head, relation, tail FROM triple"))
    train = [(h, r, t) for split, h, r, t in rows if split == "train"]
    test = [(h, r, t) for split, h, r, t in rows if split == "test"]
    names = sorted({x for h, _, t in train for x in (h, t)})
    relations = sorted({r for _, r, _ in train})
    entity_id = {name: i for i, name in enumerate(names)}
    relation_id = {name: i for i, name in enumerate(relations)}
    encoded_train = [(entity_id[h], relation_id[r], entity_id[t]) for h, r, t in train]
    encoded_test = [(entity_id[h], relation_id[r], entity_id[t]) for h, r, t in test
                    if h in entity_id and r in relation_id and t in entity_id]
    return names, relations, encoded_train, encoded_test, len(test)


def train_model(model, triples, entity_count):
    optimizer = torch.optim.Adam(model.parameters(), lr=.002)
    records = torch.tensor(triples, dtype=torch.long)
    for epoch in range(EPOCHS):
        losses = []
        for batch in records[torch.randperm(len(records))].split(512):
            h, r, t = batch.T
            negative = torch.randint(entity_count, (len(batch), 4))
            pos = model(h, r, t)
            neg = model(h[:, None], r[:, None], negative)
            loss = torch.nn.functional.softplus(neg - pos[:, None]).mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        print(f"RotatE epoch {epoch+1}/{EPOCHS}: loss {np.mean(losses):.4f}", flush=True)


def evaluate(model, train, test, entity_count):
    known = defaultdict(set)
    for h, r, t in train + test:
        known[h, r].add(t)
    frequency = defaultdict(Counter)
    for _, r, t in train:
        frequency[r][t] += 1
    ranks, baseline = [], []
    all_tails = torch.arange(entity_count)
    with torch.inference_mode():
        for i, (h, r, t) in enumerate(test, 1):
            scores = model(torch.tensor(h), torch.tensor(r), all_tails).numpy()
            for other in known[h, r] - {t}:
                scores[other] = -np.inf
            ranks.append(int(np.sum(scores > scores[t])) + 1)
            freq_scores = np.zeros(entity_count)
            for candidate, count in frequency[r].items():
                freq_scores[candidate] = count
            for other in known[h, r] - {t}:
                freq_scores[other] = -np.inf
            baseline.append(1 + int(np.sum(freq_scores > freq_scores[t]))
                            + int(np.sum((freq_scores == freq_scores[t]) & (np.arange(entity_count) < t))))
            if i % 300 == 0:
                print(f"KGE evaluated {i}/{len(test)} test triples", flush=True)
    def summary(values):
        a = np.asarray(values)
        return {"hit1": float(np.mean(a <= 1)), "hit3": float(np.mean(a <= 3)),
                "hit10": float(np.mean(a <= 10)), "mrr": float(np.mean(1/a))}
    return summary(ranks), summary(baseline)


def main():
    torch.manual_seed(SEED)
    random.seed(SEED)
    np.random.seed(SEED)
    torch.set_num_threads(4)
    names, relations, train, test, total_test = data()
    model = RotatE(len(names), len(relations))
    train_model(model, train, len(names))
    rotate, frequency = evaluate(model, train, test, len(names))
    result = {"seed": SEED, "epochs": EPOCHS, "dimension": DIM, "train_triples": len(train),
              "test_triples": total_test, "test_seen_entities": len(test),
              "test_excluded_unseen": total_test-len(test), "candidate_entities": len(names),
              "rotate_style": rotate, "relation_frequency_baseline": frequency}
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "entities": names, "relations": relations}, output / "rotate.pt")
    (output / "kge_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    assert RotatE(3, 2)(torch.tensor([0]), torch.tensor([1]), torch.tensor([2])).shape == (1,)
    main()
