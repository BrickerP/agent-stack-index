import math
import random
import unittest
from collections import Counter

from agent_stack_index import infer
from agent_stack_index.config import Analysis, Duel


class StatsTests(unittest.TestCase):
    def test_fisher_matches_known_tables(self):
        self.assertAlmostEqual(infer.fisher(3, 1, 1, 3), 0.4857142857, places=6)  # the tea-tasting table
        self.assertAlmostEqual(infer.fisher(10, 0, 0, 10), 2 / math.comb(20, 10), places=12)
        self.assertEqual(infer.fisher(5, 5, 5, 5), 1.0)

    def test_holm_adjusts_and_keeps_order(self):
        self.assertEqual(infer.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
        self.assertEqual(infer.holm([]), [])

    def test_binomial_tail_and_minimum_detectable_effect(self):
        self.assertAlmostEqual(infer.binom_upper(8, 10, 0.5), 56 / 1024)
        self.assertEqual(infer.mde_points(30, 60, 0.9), 19)  # the October duel arms
        self.assertEqual(infer.mde_points(30, 60, 0.99), 19)  # shares near 0 or 1 are clipped, not treated as free precision


class WordingTests(unittest.TestCase):
    def pairs(self, make, n=40):
        return {(f"c{i}", f"m{i}"): make(i) for i in range(n)}

    def test_a_real_wording_effect_beats_the_shuffled_null(self):
        answers = self.pairs(lambda i: [("t", "a", "x")] * 6 + [("t", "b", "y")] * 6)
        out = infer.wording(answers, {c: "contested" for c, _m in answers}, Analysis(shuffles=200, seed=3))["contested"]
        self.assertEqual((out["pairs"], out["changed"]), (40, 40))
        self.assertGreater(out["excess"], 10)
        self.assertLess(out["p"], 0.01)

    def test_sampling_noise_alone_is_not_called_a_wording_effect(self):
        rng = random.Random(5)
        answers = self.pairs(lambda i: [("t", v, rng.choice("xy")) for v in "abc" for _ in range(4)])
        out = infer.wording(answers, {c: "contested" for c, _m in answers}, Analysis(shuffles=200, seed=3))["contested"]
        self.assertGreater(out["p"], 0.05)

    def test_the_null_is_reproducible(self):
        answers = self.pairs(lambda i: [("t", "a", "x")] * 3 + [("t", "b", "y")] * 3, n=10)
        tiers = {c: "default" for c, _m in answers}
        an = Analysis(shuffles=50, seed=9)
        self.assertEqual(infer.wording(answers, tiers, an), infer.wording(answers, tiers, an))


class DuelTests(unittest.TestCase):
    def arms(self, none, trio):
        return {"auth": {"none": Counter(none), "trio": Counter(trio)}}

    def test_only_corrected_and_large_shifts_count(self):
        duels = [Duel("t", "auth", ("authjs", "clerk", "better-auth"))]
        out = infer.duel_contrasts(self.arms({"authjs": 20, "clerk": 5, "better-auth": 5}, {"authjs": 16, "clerk": 13, "better-auth": 31}), duels, Analysis())
        shifted = {r["vendor"]: r["shifted"] for r in out["contrasts"]}
        self.assertEqual(shifted, {"authjs": True, "clerk": False, "better-auth": True})
        self.assertEqual(out["mde_points"], {"auth": 30})
        self.assertTrue(all(r["p_adj"] >= r["p"] for r in out["contrasts"]))

    def test_a_small_change_on_few_answers_is_not_detected(self):
        duels = [Duel("t", "auth", ("a", "b", "c"))]
        out = infer.duel_contrasts(self.arms({"a": 29, "b": 1}, {"a": 55, "b": 4, "c": 1}), duels, Analysis())
        self.assertFalse(any(r["shifted"] for r in out["contrasts"]))

    def test_first_listed_candidate_is_tested_against_chance(self):
        duels = [Duel("t", "c", ("a", "b", "c"))]
        pos = infer.position([130, 300], duels)
        self.assertEqual((pos["rate"], pos["expected"]), (0.4333, 0.3333))
        self.assertLess(pos["p"], 0.001)
        self.assertGreater(infer.position([100, 300], duels)["p"], 0.3)


if __name__ == "__main__":
    unittest.main()
