"""Лоцман: the generator's output assembles on every hill we run, its numbers
come from the hill's constants, and its brain picks strategies the way the
model below says. Run from the repository root:

  CW=/path/to/cw python3 -m unittest tests.test_lotsman

Without cw (CW or `cw` on PATH) the tests that play are skipped.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import lotsman  # noqa: E402

CW = os.environ.get("CW") or shutil.which("cw") or os.path.expanduser(
    "~/projects/board-corewar/target/release/cw")
HAVE_CW = os.path.exists(CW)
TESTDATA = os.path.expanduser("~/projects/board-corewar/testdata")

# The hills we play on: season one, season two, and a prime core for season three.
HILLS = {
    "s1": ["-s", "8000", "-c", "80000", "-p", "8000", "-l", "100", "-d", "100"],
    "s2": ["-s", "8192", "-c", "65536", "-p", "8192", "-l", "128", "-d", "128"],
    "prime": ["-s", "8191", "-c", "65536", "-p", "8191", "-l", "100", "-d", "100"],
}
SITTER = ";redcode-94\n;name Sitter\n;author test\n        JMP     0\n"


def run(args, **kw):
    return subprocess.run([CW] + args, capture_output=True, text=True, **kw)


class Text(unittest.TestCase):
    def test_no_number_of_a_core_is_written_in(self):
        text = lotsman.lotsman()
        self.assertNotIn("8000", text)
        self.assertNotIn("8192", text)
        self.assertNotRegex(text, r"(?m)^;assert")

    def test_the_warrior_credits_the_carpet_that_ends_on_its_own(self):
        # The scanner's carpet stops when its pointer comes round, as in
        # Ледоход: the published text says so.
        self.assertRegex(lotsman.lotsman(), r"(?m)^;strategy .*Ледоход by neva-sandbox")

    def test_the_warrior_credits_the_trap(self):
        # Writing another warrior's P-space through a cell it runs: the
        # published text says whose idea it is.
        self.assertRegex(lotsman.lotsman(), r"(?m)^;strategy .*Контратип by xboss-xoxomo")

    def test_the_brain_model_tries_the_scanner_after_ties_in_a_row(self):
        # Paper ties, the scanner loses: a try of two rounds after 9 ties,
        # the next after 18, then after 36.
        seq = "".join(map(str, lotsman.brain_model({0: 2, 1: 0}, 40)))
        self.assertEqual(seq, "0" * 9 + "11" + "0" * 18 + "11" + "0" * 9)

    def test_the_brain_model_grows_the_threshold_by_its_factor(self):
        # grow=2: the threshold goes 9, 36, 144 (two doublings a failed try).
        seq = "".join(map(str, lotsman.brain_model({0: 2, 1: 0}, 60, grow=2)))
        self.assertEqual(seq, "0" * 9 + "11" + "0" * 36 + "11" + "0" * 11)

    def test_the_brain_model_never_tries_against_a_paper_that_wins_or_loses(self):
        # An opponent that ties paper now and then, but never 9 times in a
        # row, never sees the scanner, nor one that only beats paper.
        self.assertEqual(set(lotsman.brain_model({0: [1, 2, 2, 1, 2, 0], 1: 1}, 60)), {0})
        self.assertEqual(set(lotsman.brain_model({0: 0, 1: 1}, 60)), {0})

    def test_the_brain_model_stays_with_a_winning_scanner(self):
        seq = "".join(map(str, lotsman.brain_model({0: 2, 1: 1}, 30)))
        self.assertEqual(seq, "0" * 9 + "1" * 21)

    def test_the_brain_model_counts_scanner_wins_as_trust(self):
        # The scanner wins one round in three: trust 2, +1, -1, -1, ... so a
        # try lasts 6 rounds.
        seq = "".join(map(str, lotsman.brain_model({0: 2, 1: [1, 0, 0]}, 40)))
        self.assertEqual(seq, "0" * 9 + "1" * 6 + "0" * 18 + "1" * 6 + "0")

    @staticmethod
    def code():
        lines = [ln for ln in lotsman.lotsman().splitlines() if ln and not ln.startswith(";")]
        start = re.search(r"(?m)^\s+ORG\s+(\w+)", "\n".join(lines)).group(1)
        code = [ln for ln in lines if not re.match(r"\s+(ORG|END)|\w+\s+EQU", ln)]
        at = {ln.split()[0]: n for n, ln in enumerate(code) if not ln.startswith(" ")}
        return start, code, at

    def test_after_a_paper_win_the_paper_starts_on_the_fifth_instruction(self):
        # Against a fast scanner every cycle before the paper costs points.
        start, code, at = self.code()
        i = at[start]
        ops = [ln[8:].split()[0] for ln in code[i:i + 5]]
        self.assertEqual(ops, ["LDP.AB", "LDP.AB", "SEQ.AB", "JMP", "JMN.B"])
        self.assertEqual(at["paper"], i + 5)

    def test_the_paper_comes_last(self):
        # Silk copies the 2**k cells from its start on; past them lies nothing
        # of ours.
        start, code, at = self.code()
        self.assertEqual(at["pbomb"], len(code) - 1)

    def test_every_p_space_write_is_erased_by_the_eraser(self):
        # A process of ours that ran an STP later, from a cell the opponent
        # had overwritten, would store junk: the eraser erases them all. The
        # traps are data the brain never runs.
        start, code, at = self.code()
        stps = {n for n, ln in enumerate(code) if ln[8:].startswith("STP") and not ln.startswith("trap")}
        erased = set()
        for ln in code:
            m = re.match(r"MOV\.I\s+(?:dbomb|trap\d),\s+(\w+)(?:\+(\d+))?$", ln[8:].strip())
            if m:
                erased.add(at[m.group(1)] + int(m.group(2) or 0))
        self.assertTrue(stps)
        self.assertEqual(stps - erased, set())

    def test_the_eraser_leaves_traps_where_the_brain_wrote(self):
        # In place of the brain's writes, by turns, STP.AB #1, #7 and
        # STP.AB #1000, #9: a brain that keeps its choice in cell 7 and its
        # scanner's trust in cell 9, as Постовой does, and runs one plays its
        # scanner, and with that much trust it stays on it.
        start, code, at = self.code()
        traps = [ln[8:].strip() for ln in code if ln.startswith("trap")]
        self.assertEqual(traps, ["STP.AB  #1, #7", "STP.AB  #1000, #9"])
        erased = [re.match(r"MOV\.I\s+(\w+),", ln[8:].strip()).group(1)
                  for ln in code[at["er"]:at["er"] + 10]]
        self.assertEqual(erased, ["trap1", "trap2"] * 5)

    def test_the_traps_write_no_cell_our_brain_reads(self):
        # A process of ours that runs a trap changes nothing we read: not the
        # result, not the brain's cells, not the test builds' counters.
        key = lotsman.DEFAULTS["key"]
        ours = {0} | {key + i for i in range(4)} | {key + 20, key + 21}
        cells = {lotsman.DEFAULTS["t1c"], lotsman.DEFAULTS["t2c"]}
        self.assertEqual(cells & ours, set())

    def test_without_traps_the_eraser_writes_dat(self):
        text = lotsman.lotsman(t1c=0, t2c=0)
        self.assertNotIn("trap", text)
        self.assertRegex(text, r"(?m)^er\s+MOV\.I\s+dbomb, w1$")

    def test_after_a_win_the_start_of_a_round_writes_nothing(self):
        # The fast path only reads.
        start, code, at = self.code()
        self.assertFalse([ln for ln in code[at["res"]:at["paper"]] if ln[8:].startswith("STP")])


@unittest.skipUnless(HAVE_CW, "needs cw")
class Assembly(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def write(self, text, name="w.red"):
        path = os.path.join(self.tmp, name)
        with open(path, "w") as fh:
            fh.write(text)
        return path

    def test_it_assembles_on_every_hill_within_100(self):
        path = self.write(lotsman.lotsman())
        for hill, params in HILLS.items():
            with self.subTest(hill=hill):
                r = run(["check", path, "--json"] + params[:-4] + ["-l", "100", "-d", params[-1]])
                got = json.loads(r.stdout)[0]
                self.assertTrue(got["ok"], got)
                self.assertLessEqual(got["length"], 100)

    def test_the_anti_imp_bomb_follows_the_core(self):
        # `cw list` prints a number past half the core as negative.
        path = self.write(lotsman.lotsman())
        for hill, step, core in (("s1", 2667, 8000), ("s2", 2731, 8192), ("prime", 5461, 8191)):
            with self.subTest(hill=hill):
                listing = run(["list", path] + HILLS[hill]).stdout
                shown = step if step <= core // 2 else step - core
                self.assertIn("DAT.F <%d," % shown, listing)

    def test_the_scanners_step_is_odd_on_every_core(self):
        path = self.write(lotsman.lotsman())
        for hill in HILLS:
            with self.subTest(hill=hill):
                step = int(re.search(r"(?m)^DAT\.F #(-?\d+), #\1$", run(["list", path] + HILLS[hill]).stdout).group(1))
                self.assertEqual(step % 2, 1)

    def test_every_forced_strategy_assembles(self):
        for n in range(2):
            path = self.write(lotsman.lotsman(force=n), "f%d.red" % n)
            r = run(["check", path, "--json"])
            self.assertTrue(json.loads(r.stdout)[0]["ok"], r.stdout)


@unittest.skipUnless(HAVE_CW, "needs cw")
class Strategies(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.sitter = os.path.join(self.tmp, "sitter.red")
        with open(self.sitter, "w") as fh:
            fh.write(SITTER)

    def pair(self, n, other, rounds=20):
        path = os.path.join(self.tmp, "f%d.red" % n)
        with open(path, "w") as fh:
            fh.write(lotsman.lotsman(force=n))
        r = run(["pair", path, other, "--rounds", str(rounds), "--json"])
        return json.loads(r.stdout)["result"]

    def test_the_scanner_kills_a_warrior_that_only_sits(self):
        r = self.pair(1, self.sitter)
        self.assertEqual(r["w1"], 20, r)

    def test_the_paper_beats_a_dwarf(self):
        r = self.pair(0, os.path.join(TESTDATA, "dwarf.red"))
        self.assertGreater(r["w1"], r["w2"])

    def versus(self, opponent, seeds=4):
        """Points a match, with traps and without, against one opponent's
        text, on season two's rules (512 rounds), mean over the seeds."""
        files = []
        for name, kw in (("Traps", {}), ("Plain", {"t1c": 0, "t2c": 0})):
            path = os.path.join(self.tmp, name + ".red")
            with open(path, "w") as fh:
                fh.write(lotsman.lotsman(name=name, **kw))
            files.append(path)
        opp = os.path.join(self.tmp, "opp.red")
        with open(opp, "w") as fh:
            # As at season two's seeding: without the assert on a core of 8000.
            fh.write(opponent.replace(";assert CORESIZE == 8000\n", ""))
        r = run(["versus"] + files + ["--against", opp, "--seeds", str(seeds), "--salt", "1",
                                      "--rounds", "512", "--json"] + HILLS["s2"])
        pts = {}
        for m in json.loads(r.stdout)["matches"]:
            x = m["result"]
            pts.setdefault(m["a"], []).append(3 * x["w1"] + x["ties"])
        return [sum(pts[i]) / len(pts[i]) for i in range(len(files))]

    def test_the_traps_send_postovoy_to_its_scanner(self):
        import postovoy
        traps, plain = self.versus(postovoy.postovoy())
        self.assertGreater(traps, plain + 300)

    def test_the_trust_trap_works_on_a_brain_that_checks_its_trust(self):
        # Постовой with its trust checked before one is taken: the choice
        # alone would send it back to paper at once, the trust keeps it on
        # its scanner.
        import postovoy
        text = postovoy.postovoy()
        old = "sloss   SUB.AB  #1, tru\n        JMN.B   keep, tru\n        MOV.AB  #0, sel\n"
        self.assertIn(old, text)
        fixed = text.replace(old, "sloss   JMZ.B   sl0, tru\n        DJN.B   keep, tru\n"
                                  "sl0     MOV.AB  #0, sel\n")
        traps, plain = self.versus(fixed)
        self.assertGreater(traps, plain + 300)


@unittest.skipUnless(HAVE_CW, "needs cw")
class Brain(unittest.TestCase):
    """Test builds: each strategy, against a warrior that only sits, ends its
    rounds in a set series: L dies at once, l dies late, T survives to a tie,
    W wins fast, w wins late, s is a stray: it spoils a cell the brain stores
    from and jumps to that write, as a process of ours might after the
    opponent overwrote our code, and then dies; "WLL" wins its first round,
    loses the next two and so on. The two series end their rounds in
    different ways, so `cw trace` shows which strategy the brain chose."""

    ENDS = {"L": "L", "l": "l", "T": "T", "W": "W", "w": "w", "s": "L"}

    def chosen(self, arms, rounds, **kw):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        me, sitter = os.path.join(tmp, "me.red"), os.path.join(tmp, "sitter.red")
        with open(me, "w") as fh:
            fh.write(lotsman.lotsman(testarms=arms, **kw))
        with open(sitter, "w") as fh:
            fh.write(SITTER)
        r = run(["trace", me, sitter, "--rounds", str(rounds), "-l", "200"])
        self.assertEqual(r.returncode, 0, r.stderr)
        out = []
        for rd in json.loads(r.stdout)["rounds"]:
            if rd.get("winner") is None:
                kind = "T"
            else:
                late = rd["end_cycle"] >= lotsman.TEST_SLOW
                kind = ("w" if late else "W") if rd["winner"] == 0 else ("l" if late else "L")
            out.append(next(i for i, series in enumerate(arms)
                            if kind in {self.ENDS[k] for k in series}))
        return out

    def check(self, arms, rounds=40, **kw):
        self.assertFalse({self.ENDS[k] for k in arms[0]} & {self.ENDS[k] for k in arms[1]})
        res = {i: [{"L": 0, "l": 0, "T": 2, "W": 1, "w": 1, "s": 0}[k] for k in series]
               for i, series in enumerate(arms)}
        self.assertEqual(self.chosen(arms, rounds, **kw), lotsman.brain_model(res, rounds, **kw))

    def test_a_failed_try_multiplies_the_threshold_by_2_to_the_grow(self):
        self.check(["T", "L"], 70, grow=2)

    def test_paper_ties_and_the_scanner_loses(self):
        # Tries after 9, 18 and 36 ties, and the run counted across them.
        self.check(["T", "L"], 80)

    def test_paper_ties_and_the_scanner_wins_one_round_in_three(self):
        self.check(["T", "WLL"], 80)

    def test_a_winning_scanner_keeps_at_most_tmax_trust(self):
        # 12 wins in a row leave trust 9, so 9 losses end the try.
        self.check(["T", "W" * 12 + "L" * 12], 50)

    def test_paper_ties_and_loses_by_turns(self):
        # Never 9 ties in a row: never a try.
        self.check(["Tl", "W"], 40)

    def test_a_stray_in_a_p_space_write_finds_it_erased(self):
        self.check(["T", "Ws"], 60)

    def test_paper_wins_from_the_start(self):
        self.check(["W", "L"])

    def test_paper_loses_late_from_the_start(self):
        self.check(["l", "W"])


if __name__ == "__main__":
    unittest.main()
