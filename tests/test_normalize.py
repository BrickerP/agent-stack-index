import unittest

from agent_stack_index.config import load
from agent_stack_index.normalize import Matcher, canon


class NormalizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = Matcher(load())

    def pick(self, category, raw):
        return self.m.match(category, raw).vendor

    def test_canon_strips_versions(self):
        self.assertEqual(canon("drizzle-orm@^0.36.0"), "drizzle-orm")
        self.assertEqual(canon("celery==5.4.0"), "celery")

    def test_exact_and_package_names(self):
        self.assertEqual(self.pick("auth", "better-auth"), "better-auth")
        self.assertEqual(self.pick("auth", "@clerk/nextjs"), "clerk")
        self.assertEqual(self.pick("llm_sdk", "ai"), "vercel")

    def test_contains_and_parentheses(self):
        self.assertEqual(self.pick("search", "Typesense Cloud"), "typesense")
        self.assertEqual(self.pick("auth", "Auth.js (NextAuth v5)"), "authjs")
        self.assertEqual(self.pick("object_storage", "Cloudflare R2"), "cloudflare")

    def test_specific_beats_generic(self):
        self.assertEqual(self.pick("database_host", "Postgres on Neon"), "neon")
        self.assertEqual(self.pick("database_host", "PostgreSQL"), "postgres-unspecified")

    def test_compound_answers_take_the_first_specific_tool(self):
        self.assertEqual(self.pick("background_jobs", "BullMQ + Redis"), "bullmq")
        self.assertEqual(self.pick("orm", "Prisma with PostgreSQL"), "prisma")

    def test_empty_and_unmatched(self):
        self.assertEqual(self.m.match("cache", "none").how, "empty")
        self.assertEqual(self.m.match("cache", None).how, "missing")
        self.assertEqual(self.m.match("cache", "Zorblax KV").how, "unmatched")


if __name__ == "__main__":
    unittest.main()
