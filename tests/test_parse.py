import unittest

from agent_stack_index.parse import parse_answer
from agent_stack_index.providers import clean_text


class ParseTests(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(parse_answer('{"auth": "better-auth", "orm": "drizzle-orm"}', ["auth", "orm"]),
                         {"auth": "better-auth", "orm": "drizzle-orm"})

    def test_fenced_json_with_chatter(self):
        text = 'Sure.\n```json\n{"search": "Typesense Cloud"}\n```\nHope this helps {not json}'
        self.assertEqual(parse_answer(text, ["search"]), {"search": "Typesense Cloud"})

    def test_key_variants_and_nested_values(self):
        text = '{"Database Host": {"name": "Neon"}, "payments": ["Stripe", "Paddle"]}'
        self.assertEqual(parse_answer(text, ["database_host", "payments"]), {"database_host": "Neon", "payments": "Stripe"})

    def test_missing_items_are_none(self):
        self.assertEqual(parse_answer('{"auth": "Clerk"}', ["auth", "orm"]), {"auth": "Clerk", "orm": None})

    def test_bare_single_answer(self):
        self.assertEqual(parse_answer("inngest", ["background_jobs"]), {"background_jobs": "inngest"})

    def test_garbage(self):
        self.assertIsNone(parse_answer("I would need more information about your stack.", ["auth", "orm"]))

    def test_think_blocks_are_removed(self):
        self.assertEqual(clean_text('<think>pondering {"auth": "x"}</think>{"auth": "Clerk"}'), '{"auth": "Clerk"}')


if __name__ == "__main__":
    unittest.main()
