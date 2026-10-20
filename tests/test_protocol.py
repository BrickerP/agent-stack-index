import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agent_stack_index import protocol, store


def protocol_text(status="confirmatory", skip=(), todo=(), rung="describe"):
    lines = ["# Protocol t: test", "", f"Status: {status}", f"Rung: {rung}", "Written: 2026-11-01", ""]
    for name in protocol.SECTIONS:
        if name in skip:
            continue
        body = {"Goal": "Does X change Y?\n\nDecision: do Z.",
                "Engineering benefit": "Builders: build.\n\nTool makers: make.\n\nHarness: tool."}.get(name, f"{name} text.")
        lines += [f"## {name}", "TODO fill this in" if name in todo else body, ""]
    return "\n".join(lines)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = SimpleNamespace(root=self.tmp)
        (self.tmp / "releases" / "t").mkdir(parents=True)
        (self.tmp / "experiments").mkdir()
        (self.tmp / "protocols").mkdir()
        self.write_release()
        (self.tmp / "experiments" / "t-base.toml").write_text('id = "t-base"\nprobe = "ask"\nrepeats = 2\n')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write_release(self, seed=1):
        (self.tmp / "releases" / "t" / "release.toml").write_text(
            f'id = "t"\nbaseline = "t-base"\nprotocol = "protocols/t.md"\n[analysis]\nseed = {seed}\n')

    def write(self, **kw):
        (self.tmp / "protocols" / "t.md").write_text(protocol_text(**kw), encoding="utf-8")

    def test_a_complete_pilot_protocol_validates(self):
        self.write(status="pilot")
        self.assertEqual(protocol.problems(self.ws, "t"), [])
        info = protocol.summary(self.ws, "t")
        self.assertEqual((info["status"], info["rung"]), ("pilot", "describe"))
        self.assertEqual(info["goal"], "Does X change Y?")
        self.assertEqual(info["benefit"], {"builders": "build.", "tool makers": "make.", "harness": "tool."})

    def test_missing_sections_todos_and_bad_headers_are_reported(self):
        self.write(status="pilot", skip=("Controls",), todo=("Design",))
        text = " | ".join(protocol.problems(self.ws, "t"))
        self.assertIn("'## Controls' is missing", text)
        self.assertIn("'Design' is empty or still has a TODO", text)
        self.write(status="maybe", rung="vibes")
        self.assertEqual(len(protocol.problems(self.ws, "t")), 2)

    def test_release_without_a_protocol_or_analysis_is_reported(self):
        (self.tmp / "releases" / "t" / "release.toml").write_text('id = "t"\nbaseline = "t-base"\n')
        self.assertIn("needs `protocol", protocol.problems(self.ws, "t")[0])
        (self.tmp / "releases" / "t" / "release.toml").write_text('id = "t"\nprotocol = "protocols/t.md"\n')
        self.write(status="pilot")
        self.assertIn("[analysis]", protocol.problems(self.ws, "t")[0])

    def test_a_confirmatory_protocol_must_be_locked_and_stays_locked(self):
        self.write()
        self.assertIn("not locked", protocol.problems(self.ws, "t")[0])
        self.assertIn("not locked", protocol.run_gate(self.ws, "t-base"))
        protocol.lock(self.ws, "t")
        self.assertEqual(protocol.problems(self.ws, "t"), [])
        self.assertIsNone(protocol.run_gate(self.ws, "t-base"))
        self.assertTrue(protocol.summary(self.ws, "t")["locked_at"].endswith("Z"))
        path = self.tmp / "protocols" / "t.md"
        path.write_text(path.read_text() + "- 2026-11-03: dropped one model, it was retired\n")  # Deviations may grow
        self.assertEqual(protocol.problems(self.ws, "t"), [])
        path.write_text(path.read_text().replace("Design text.", "Design text, changed."))  # the pre-registered part may not
        self.assertIn("changed after the lock", protocol.problems(self.ws, "t")[0])

    def test_specs_and_analysis_are_part_of_the_lock(self):
        self.write()
        protocol.lock(self.ws, "t")
        self.write_release(seed=2)
        self.assertIn("changed after the lock", protocol.problems(self.ws, "t")[0])
        self.write_release(seed=1)
        (self.tmp / "experiments" / "t-base.toml").write_text('id = "t-base"\nprobe = "ask"\nrepeats = 3\n')
        self.assertIn("changed after the lock", protocol.problems(self.ws, "t")[0])

    def test_data_older_than_the_lock_is_reported_and_blocks_locking(self):
        self.write()
        store.append(self.tmp, {"experiment": "t-base", "model_id": "m", "trial_id": "x", "ok": True, "ts": "2000-01-01T00:00:00Z"})
        with self.assertRaises(SystemExit):
            protocol.lock(self.ws, "t")
        (self.tmp / "data").rename(self.tmp / "elsewhere")
        protocol.lock(self.ws, "t")
        (self.tmp / "elsewhere").rename(self.tmp / "data")
        self.assertIn("older than the lock", protocol.problems(self.ws, "t")[0])

    def test_pilots_and_unknown_experiments_are_not_gated(self):
        self.write(status="pilot")
        self.assertIsNone(protocol.run_gate(self.ws, "t-base"))
        self.assertIsNone(protocol.run_gate(self.ws, "not-in-any-release"))
        self.write(status="pilot", todo=("Goal",))
        self.assertIn("TODO", protocol.run_gate(self.ws, "t-base"))


if __name__ == "__main__":
    unittest.main()
