"""Small checks for metrics and AKG split isolation."""

import sqlite3
import unittest

from experiment import metrics, rank
from graph import DB, neighbors
from kge import RotatE
from make_deliverables import paired_test


class CoreTest(unittest.TestCase):
    def test_metrics(self):
        self.assertEqual(rank([.2, .9, .4], 1), 1)
        self.assertEqual(rank([.2, .9, .4], 0), 3)
        self.assertAlmostEqual(metrics([1, 2, 4])["hit3"], 2/3)

    def test_knowledge_source_and_split(self):
        with sqlite3.connect(DB) as db:
            self.assertEqual(dict(db.execute("SELECT split,count(*) FROM triple GROUP BY split")),
                             {"train": 18348, "test": 2039})
            facts = neighbors(db, "dog", 2)
        self.assertEqual(len(facts), 2)
        self.assertTrue(all(fact["source_file"] == "AKG_pruned.tsv" for fact in facts))
        self.assertTrue(all(fact["source_row"] >= 2 for fact in facts))

    def test_rotate_shape(self):
        import torch
        model = RotatE(3, 2)
        self.assertEqual(tuple(model(torch.tensor([0]), torch.tensor([1]), torch.tensor([2])).shape), (1,))

    def test_paired_test(self):
        rows = [{"baseline_rank": "4", "kg_rank": "3"},
                {"baseline_rank": "2", "kg_rank": "4"}]
        self.assertEqual(paired_test(rows, 3), (1, 1, 1.0))


if __name__ == "__main__":
    unittest.main()
