"""End to end on a throwaway copy of the inputs: plan → run (fake model) → release → site → audit."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_stack_index import config, release, site, store
from agent_stack_index.audit import plan_spec, snapshot
from agent_stack_index.config import load, load_experiment, validate
from agent_stack_index.plan import plan
from agent_stack_index.providers import FakeClient
from agent_stack_index.runner import run

REPO = Path(__file__).resolve().parents[1]


def fake_answer(model, prompt):
    if "background_jobs" in prompt and "Inngest is" in prompt:
        return '{"background_jobs": "inngest"}'
    picks = {"auth": "Better Auth", "database_host": "Neon", "payments": "Stripe",
             "transactional_email": "Resend", "error_monitoring": "@sentry/nextjs", "background_jobs": "BullMQ + Redis"}
    keys = [line[2:].split(":")[0] for line in prompt.splitlines() if line.startswith("- ")]
    return "{" + ", ".join(f'"{k}": "{picks.get(k, "Zorblax")}"' for k in keys) + "}"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for name in ("config", "catalog", "tasks", "prompts", "contexts", "site"):
            shutil.copytree(REPO / name, self.tmp / name)
        (self.tmp / "experiments").mkdir()
        (self.tmp / "experiments" / "t-base.toml").write_text(
            'id = "t-base"\nprobe = "ask"\nmodels = ["gpt-6-astra", "glm-5-3"]\ntasks = ["ts-saas-starter", "ts-jobs"]\nvariants = ["pick", "user"]\nrepeats = 2\n')
        (self.tmp / "experiments" / "t-duel.toml").write_text(
            'id = "t-duel"\nprobe = "duel"\nmodels = ["gpt-6-astra"]\nvariants = ["notes"]\n[arms]\nnone = 1\ntrio = 3\nsolo = 1\n'
            '[[duel]]\ntask = "ts-jobs"\ncategory = "background_jobs"\nvendors = ["bullmq", "inngest", "trigger-dev"]\n')
        (self.tmp / "releases" / "t").mkdir(parents=True)
        (self.tmp / "releases" / "t" / "release.toml").write_text('id = "t"\ntitle = "Test"\nbaseline = "t-base"\nduel = "t-duel"\n')
        self.ws = load(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_inputs_validate(self):
        self.assertEqual(validate(load(REPO)), [])
        self.assertEqual(validate(self.ws), [])

    def test_full_pipeline_is_resumable_and_reproducible(self):
        base = load_experiment(self.tmp / "experiments" / "t-base.toml")
        duel = load_experiment(self.tmp / "experiments" / "t-duel.toml")
        client = FakeClient(fake_answer)
        stats = run(self.ws, base, client, workers=4, log=lambda *_: None)
        self.assertEqual(stats["planned"], len(plan(self.ws, base)))
        self.assertEqual(run(self.ws, base, client, log=lambda *_: None)["planned"], 0)  # resumable: nothing left
        run(self.ws, duel, client, log=lambda *_: None)
        self.assertEqual(release.write(self.ws, "t"), [])
        self.assertEqual(release.write(self.ws, "t", check=True), [])
        for seed in ("1", "2"):  # artifacts must not depend on set ordering (hash randomization)
            env = {**os.environ, "ASI_ROOT": str(self.tmp), "PYTHONHASHSEED": seed, "PYTHONPATH": str(REPO / "src")}
            proc = subprocess.run([sys.executable, "-m", "agent_stack_index", "release", "t", "--check"], env=env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = release.build(self.ws, "t")
        jobs = result["baseline"]["background_jobs"]
        self.assertEqual(jobs["top"], "bullmq")
        self.assertEqual(result["baseline"]["auth"]["models_agree"], 2)
        self.assertEqual(result["duel"]["background_jobs"]["solo_win"]["inngest"], 1.0)
        self.assertGreater(result["manifest"]["unmatched_rate"], 0)
        html = (site.build(self.ws, self.tmp / "_site", "t")).read_text()
        self.assertIn("Better Auth", html)
        self.assertIn("BullMQ", snapshot(self.ws, "inngest", "t"))
        spec = plan_spec(self.ws, "inngest", "t", out=self.tmp / "private" / "audit.toml")
        self.assertIn('vendors = ["inngest", "bullmq"', spec.read_text())

    def test_editing_a_prompt_creates_new_trials(self):
        base = load_experiment(self.tmp / "experiments" / "t-base.toml")
        before = {t.trial_id for t in plan(self.ws, base)}
        path = self.tmp / "prompts" / "prompts.toml"
        path.write_text(path.read_text().replace("brand-new project", "new project"))
        after = {t.trial_id for t in plan(load(self.tmp), base)}
        self.assertTrue(before.isdisjoint({t for t in after if t not in before}))
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
