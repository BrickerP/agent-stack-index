import unittest
from collections import Counter
from dataclasses import asdict

from agent_stack_index.analyze import summarize, tier, tops_of
from agent_stack_index.config import Analysis, load
from agent_stack_index.narrative import finding_tags, findings, few, lower, word
from agent_stack_index.share import card_contested, card_context, card_default
from agent_stack_index.story import story


def row_for(per_model, per_variant=None):
    per_variant = per_variant or {m: {"pick": c} for m, c in per_model.items()}
    return summarize(per_model, per_variant, Analysis())


class TieTests(unittest.TestCase):
    def test_tops_of_returns_every_tied_vendor(self):
        self.assertEqual(tops_of(Counter({"b": 2, "a": 2, "c": 1, "_none": 5})), ["a", "b"])
        self.assertEqual(tops_of(Counter({"_other": 3})), [])

    def test_a_tied_model_agrees_with_the_pooled_pick(self):
        r = row_for({"m1": Counter({"x": 6, "y": 6}), "m2": Counter({"y": 12}), "m3": Counter({"y": 10, "x": 2})})
        self.assertEqual(r["top"], "y")
        self.assertEqual(r["models_agree"], 3)

    def test_consistency_uses_a_pick_shared_by_every_phrasing(self):
        per_model = {"m1": Counter({"x": 4, "y": 4})}
        consistent = {"m1": {"a": Counter({"x": 2, "y": 2}), "b": Counter({"x": 4})}}
        changed = {"m1": {"a": Counter({"y": 4}), "b": Counter({"x": 4})}}
        self.assertEqual(summarize(per_model, consistent, Analysis())["variant_consistent"], 1)
        self.assertEqual(summarize(per_model, changed, Analysis())["variant_consistent"], 0)

    def test_tiers(self):
        ten = {f"m{i}": Counter({"x": 12}) for i in range(10)}
        self.assertEqual(row_for(ten)["tier"], "default")
        lean = {**{f"m{i}": Counter({"x": 10, "y": 2}) for i in range(8)}, "m8": Counter({"y": 12}), "m9": Counter({"y": 12})}
        self.assertEqual(row_for(lean)["tier"], "leaning")
        split = {**{f"m{i}": Counter({"x": 12}) for i in range(5)}, **{f"n{i}": Counter({"y": 12}) for i in range(5)}}
        self.assertEqual(row_for(split)["tier"], "contested")
        # agreement alone is not enough when the pick wins only a minority of answers
        self.assertEqual(tier({"models_total": 10, "models_agree": 9, "top_share": 0.46}, Analysis()), "contested")


class StoryTests(unittest.TestCase):
    def result(self, with_duel=True):
        ten = {f"m{i}": Counter({"neon": 12}) for i in range(10)}
        split = {**{f"m{i}": Counter({"authjs": 12}) for i in range(5)}, **{f"m{i}": Counter({"clerk": 12}) for i in range(5, 10)}}
        base = {"database_host": {"label": "Postgres hosting", "tasks": ["t1"], **row_for(ten)},
                "auth": {"label": "Authentication", "tasks": ["t1"], **row_for(split)}}
        duel = {}
        if with_duel:
            duel = {"auth": {"label": "Authentication", "vendors": ["authjs", "clerk", "better-auth"],
                             "arms": {"none": {"authjs": 0.7, "clerk": 0.3}, "trio": {"better-auth": 0.5, "authjs": 0.3, "clerk": 0.2}},
                             "solo_win": {"authjs": 1.0, "clerk": 0.9, "better-auth": 0.95}, "lift": {}, "first_position_rate": 0.5}}
        man = {"title": "Agent Stack Index — Test", "data_window": ["2026-10-15", "2026-10-15"], "answers": 1, "unmatched_rate": 0.0,
               "experiments": {"baseline": {"observed": 240, "variants": ["pick"], "repeats": 1}, "duel": {"observed": 60}},
               "analysis": asdict(Analysis()),
               "protocol": {"status": "pilot", "path": "protocols/t.md", "sha": "abc", "goal": "Q?", "benefit": {}},
               "models": {f"m{i}": {"label": f"M{i}", "lab": "L" + str(i % 2), "injected_prompt": i == 0, "params": {}} for i in range(10)}}
        row = lambda changed, null, p: {"pairs": 10, "changed": changed, "null_mean": null, "null_sd": 1.0, "excess": changed - null, "p": p}
        inference = {"wording": {"contested": row(4, 1.2, 0.01), "default": row(0, 0.0, 1.0)}}
        if with_duel:
            def c(v, a, t, delta, shifted):
                return {"category": "auth", "vendor": v, "none": [a, 30], "trio": [t, 60], "delta_points": delta, "shifted": shifted}
            inference["duel"] = {"contrasts": [c("authjs", 21, 12, -35, True), c("clerk", 9, 12, 0, False), c("better-auth", 0, 30, 50, True)],
                                 "mde_points": {"auth": 30}}
            inference["position"] = {"first": 33, "n": 60, "rate": 0.55, "expected": 0.3333, "ci": [0.42, 0.67], "p": 0.001}
        result = {"manifest": man, "baseline": base, "duel": duel, "inference": inference}
        result["story"] = story(result)
        return result

    def test_claims_come_from_the_numbers(self):
        r = self.result()
        st = r["story"]
        self.assertEqual(st["tiers"]["default"], ["database_host"])
        self.assertEqual(st["tiers"]["contested"], ["auth"])
        self.assertEqual(st["flipped"], ["auth"])
        self.assertEqual(st["zero_to_solo"], [["auth", "better-auth", 0.0, 0.95]])
        text = " ".join(findings(load(), r))
        self.assertIn("In 1 of 2 categories every model picks the same tool", text)
        self.assertIn("in authentication, which has no default, the lead flipped", text)

    def test_a_claim_is_worded_by_what_its_test_supports(self):
        r = self.result()
        self.assertIn("also moves with the wording", findings(load(), r)[1])
        r["inference"]["wording"]["contested"]["p"] = 0.4
        r["story"] = story(r)
        self.assertIn("could not detect an effect of wording", findings(load(), r)[1])
        r["inference"]["duel"]["contrasts"][0]["shifted"] = r["inference"]["duel"]["contrasts"][2]["shifted"] = False
        r["story"] = story(r)
        self.assertIn("the lead changed, within noise", findings(load(), r)[2])

    def test_evidence_labels_follow_the_protocol_status(self):
        r = self.result()
        self.assertEqual(finding_tags(r), ["exploratory"] * 3)
        r["manifest"]["protocol"]["status"] = "confirmatory"
        self.assertEqual(finding_tags(r), ["descriptive", "confirmed", "confirmed"])
        r["inference"]["wording"]["contested"]["p"] = 0.4
        r["story"] = story(r)
        self.assertEqual(finding_tags(r)[1], "not detected")

    def test_renders_without_duels_or_pilot(self):
        r = self.result(with_duel=False)
        self.assertEqual(len(findings(load(), r)), 2)
        self.assertIn("Postgres hosting", card_default(load(), r))
        self.assertIn("No default", card_contested(load(), r))

    def test_share_cards_carry_the_numbers(self):
        r = self.result()
        self.assertIn("0% → 95%", card_context(load(), r))

    def test_prose_helpers(self):
        self.assertEqual(word(7), "seven")
        self.assertEqual(word(12, True), "Twelve")
        self.assertEqual(word(31), "31")
        self.assertEqual(few(0, 120), "none")
        self.assertEqual(lower("Rate limiting"), "rate limiting")
        self.assertEqual(lower("Postgres hosting"), "Postgres hosting")
        self.assertEqual(lower("UI components"), "UI components")


if __name__ == "__main__":
    unittest.main()
