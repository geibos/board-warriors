"""Светофор with a quickscan and a sentinel: an experiment, measured on
2026-09-29 and not used (experiments/README.md has the numbers).

A copy of tools/svetofor.py as of that day, with three keys more; it is not
kept in step with the tool. With none of them it prints Светофор's code, the
only differences being two labels, `found` in the scanner and `disp` before the
dispatch.

  python3 experiments/svx.py [key=value ...] > warrior.red

  qk=0        quickscan pairs between the brain and the dispatch: each pair
              compares two cells (SEQ.I) and, on a difference, puts the cell
              in the scanner's ptr; 2*qk probes spread over the core
  qburst=0    1: on a find, four DAT bombs from the cell on, then the round
              goes on with the brain's choice; 0: the round becomes the
              scanner's carpet from the find
  watch=0     1: the stone's loop checks the cell after it (SEQ.I against an
              empty one); changed, it launches the paper from the body

Other keys as in tools/svetofor.py.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from hameleon import scanner_code, stone_code  # noqa: E402

NAMES = {"p": "paper", "s": "scanner", "k": "stone"}
# What to play against each of Позитив's modes (0 paper, 1 scanner, 2 stone):
# the stone against its scanner, paper against its stone. Against its paper
# the scanner that ought to win lost 3:22 (28.09, a round-by-round count), so
# the default is paper: ties, which keep it in paper until its credit is gone
# and it moves to the scanner.
ANSWER = {1: "k", 2: "p"}


def streak(ties, after):
    """Losses in a row into str (res: 0 lost, 1 won, 2 tie, CORESIZE-1 before
    the first round); with ties, a tie counts as a loss."""
    if ties:
        return [
            ("", "SNE.AB  #1, res"),
            ("", "MOV.AB  #0, str"),
            ("", "SLT.AB  #3, res"),
            ("", "SNE.AB  #1, res"),
            ("", f"JMP     {after}"),
            ("", "ADD.AB  #1, str"),
        ]
    return [
        ("", "SEQ.AB  #0, res"),
        ("", "MOV.AB  #0, str"),
        ("", "SNE.AB  #0, res"),
        ("", "ADD.AB  #1, str"),
    ]


def model_code(order, F):
    """Позитив's brain, kept in mdl (mode), crd (credit), run, in terms of our
    result: our win is its loss. mdl = 3: given up. Falls through to `gen` (the
    plain switcher) or jumps to mplay (placed after the dispatch)."""
    return [
        # Before the first round nothing has happened: play the answer to its
        # paper.
        ("mupd", "SLT.B   res, #3"),
        ("", "JMP     mplay"),
        ("", "SNE.AB  #3, mdl"),
        ("", "JMP     gen"),
        ("", "JMZ.B   mpap, mdl"),
        # Its scanner and stone count its losses in a row: four leave the
        # scanner for the stone, two leave the stone for paper.
        ("", "SNE.AB  #1, res"),
        ("", "ADD.AB  #1, run"),
        ("", "SEQ.AB  #1, res"),
        ("", "MOV.AB  #0, run"),
        ("", "SEQ.AB  #1, mdl"),
        ("", "JMP     mst"),
        ("", "SLT.AB  #3, run"),
        ("", "JMP     mdone"),
        ("mtost", "MOV.AB  #2, mdl"),
        ("mrst", "MOV.AB  #0, run"),
        ("", "JMP     mdone"),
        ("mst", "SLT.AB  #1, run"),
        ("", "JMP     mdone"),
        ("", "MOV.AB  #0, mdl"),
        ("", "JMP     mrst"),
        # Its paper: its loss (our win) sends it to the stone, its win (our
        # loss) gives it credit 2, a tie spends credit or, with none left,
        # sends it to the scanner (whose credit is then 0, as it is already).
        ("mpap", "SNE.AB  #1, res"),
        ("", "JMP     mtost"),
        ("", "JMZ.B   mwin, res"),
        ("", "JMZ.B   mtosc, crd"),
        ("", "SUB.AB  #1, crd"),
        ("", "JMP     mdone"),
        ("mtosc", "MOV.AB  #1, mdl"),
        ("", "JMP     mrst"),
        ("mwin", "MOV.AB  #2, crd"),
        # F losses in a row (ties do not count, ties=0): this is not Позитив,
        # or its own P-space has broken; give the model up.
        # The plain switcher then leaves the strategy at once (str >= T).
        ("mdone", f"SLT.AB  #{F - 1}, str"),
        ("", "JMP     mplay"),
        ("", "MOV.AB  #3, mdl"),
    ]


def mplay_code(order, vp):
    """sel = what to play against Позитив's mode mdl: vp against its paper,
    the stone against its scanner, paper against its stone."""
    idx = {c: i for i, c in enumerate(order)}
    want = {0: idx[vp], 1: idx[ANSWER[1]], 2: idx[ANSWER[2]]}
    if want[0] == want[2]:
        return [
            ("mplay", f"MOV.AB  #{want[0]}, sel"),
            ("", "SNE.AB  #1, mdl"),
            ("", f"MOV.AB  #{want[1]}, sel"),
            ("", "JMP     keep"),
        ]
    return [
        ("mplay", f"MOV.AB  #{want[0]}, sel"),
        ("", "SNE.AB  #1, mdl"),
        ("", f"MOV.AB  #{want[1]}, sel"),
        ("", "SNE.AB  #2, mdl"),
        ("", f"MOV.AB  #{want[2]}, sel"),
        ("", "JMP     keep"),
    ]


def svetofor(order="pks", tp=3, ts=4, tk=3, ties=1, model=0, T=3, F=4, vp="p", paper="silk",
             pspl=5, pstep=3620, pbstep=3044, ps1=2365, ps2=1870, pj=-1922, step=1547, gap=111,
             aim=10, sstep=3364, soff=1, doff=5000, key=7, qk=0, watch=0, qburst=0, name="Светофор"):
    assert sorted(order) == ["k", "p", "s"], "order is a permutation of p, s, k"
    entry = {"p": "pstart", "s": "scan", "k": "boot"}
    e0, e1, e2 = (entry[c] for c in order)
    scanner = scanner_code(step, aim)
    scanner[9] = ("found", scanner[9][1])
    stone = stone_code(sstep, soff)
    if watch:
        # The stone checks a cell next to it every round of its loop; changed
        # (its hunter is bombing near it), it launches the paper from the body.
        stone = [
            ("sloop", f"ADD.AB  #{sstep}, sjp"),
            ("", "MOV.I   sbomb, @sjp"),
            ("", "SEQ.I   sent, sbomb"),
            ("", f"JMP     pstart-{doff}"),
            ("sjp", f"JMP     sloop, #{soff}"),
            ("sbomb", "DAT.F   $0, $0"),
            ("sent", "DAT.F   $0, $0"),
        ]
    procs = [("pstart", "SPL     1")] + [("", "SPL     1")] * (pspl - 1)
    if paper == "silk":
        paper_code = procs + [
            ("silk", f"SPL     @0, {ps1}"),
            ("", "MOV.I   }-1, >-1"),
            ("", f"SPL     @0, {ps2}"),
            ("", "MOV.I   }-1, >-1"),
            ("", "MOV.I   pbomb, >-2"),
            ("", "MOV.I   {-3, <1"),
            ("", f"JMP     @0, {pj}"),
            ("pbomb", "DAT.F   <2667, <5334"),
        ]
    else:
        paper_code = procs + [
            ("paper", f"SPL     @0, {pstep}"),
            ("", "MOV.I   }paper, >paper"),
            ("", f"MOV.I   pbomb, >{pbstep}"),
            ("", "JMP     paper"),
            ("pbomb", "DAT.F   <2667, <5334"),
        ]
    brain = [
        ("brain", "LDP.AB  #0, res"),
        ("", f"LDP.AB  #{key}, sel"),
        ("", f"LDP.AB  #{key + 1}, str"),
    ]
    if model:
        brain += [
            ("", f"LDP.AB  #{key + 2}, mdl"),
            ("", f"LDP.AB  #{key + 3}, crd"),
            ("", f"LDP.AB  #{key + 4}, run"),
        ]
        brain += streak(ties, "mupd") + model_code(order, F)
        # One limit for every strategy.
        brain += [
            ("gen", f"SLT.AB  #{T - 1}, str"),
            ("", "JMP     keep"),
        ]
    else:
        limit = {"p": tp, "s": ts, "k": tk}
        t0, t1, t2 = (limit[c] for c in order)
        brain += streak(ties, "limits") + [
            ("limits", f"MOV.AB  #{t0}, lim"),
            ("", "JMZ.B   chk, sel"),
            ("", f"MOV.AB  #{t1}, lim"),
            ("", "SEQ.AB  #1, sel"),
            ("", f"MOV.AB  #{t2}, lim"),
            ("chk", "SLT.B   str, lim"),
            ("", "JMP     switch"),
            ("", "JMP     keep"),
        ]
    brain += [
        ("switch", "ADD.AB  #1, sel"),
        ("", "MOD.AB  #3, sel"),
        ("", "MOV.AB  #0, str"),
        ("keep", f"STP.B   sel, #{key}"),
        ("", f"STP.B   str, #{key + 1}"),
    ]
    if model:
        brain += [
            ("", f"STP.B   mdl, #{key + 2}"),
            ("", f"STP.B   crd, #{key + 3}"),
            ("", f"STP.B   run, #{key + 4}"),
        ]
    if qk:
        S = 7800 // (2 * qk)
        for k in range(qk):
            x = 100 + 2 * k * S + S // 2
            brain += [("", f"SEQ.I   ptr+{x}, ptr+{x + S}"), ("", f"MOV.AB  #{x}, ptr")]
        if qburst:
            # A find: four DAT bombs from the probed cell on, then the round
            # goes on with what the brain chose; ptr is put back for the scanner.
            brain += [
                ("", "SNE.AB  #PB0, ptr"),
                ("", "JMP     disp"),
                ("", "MOV.I   db, >ptr"),
                ("", "MOV.I   db, >ptr"),
                ("", "MOV.I   db, >ptr"),
                ("", "MOV.I   db, >ptr"),
                ("", "MOV.AB  #PB0, ptr"),
            ]
        else:
            brain += [
                ("", "SNE.AB  #PB0, ptr"),
                ("", "JMP     disp"),
                ("", "MOV.BA  ptr, ptr"),
                ("", f"ADD.A   #{S}, ptr"),
                ("", "JMP     found"),
            ]
    brain += [
        ("disp", f"JMZ.B   {e0}, sel"),
        ("", "SEQ.AB  #1, sel"),
        ("", f"JMP     {e2}"),
        ("", f"JMP     {e1}"),
    ]
    if model:
        brain += mplay_code(order, vp)
    brain += [
        # The stone is copied doff cells away and runs there.
        ("boot", "MOV.I   }cp, >cp"),
        ("", f"DJN.B   boot, #{len(stone)}"),
        ("", f"JMP     cp+{doff}"),
        ("cp", f"DAT.F   #sloop, #{doff}"),
        ("res", "DAT.F   $0, $0"),
        ("sel", "DAT.F   $0, $0"),
        ("str", "DAT.F   $0, $0"),
    ]
    brain += [("mdl", "DAT.F   $0, $0"), ("crd", "DAT.F   $0, $0"), ("run", "DAT.F   $0, $0")] if model \
        else [("lim", "DAT.F   $0, $0")]
    # Paper goes last: its copy loop copies on past its own five cells, and a
    # process that strays into a copy of the brain runs its STPs over garbage
    # (seen 28.09: P-space turning into bomb fields by round 3).
    code = scanner + stone + brain + paper_code
    n = len(code)
    seq = " → ".join(NAMES[c] for c in order)
    how = (f"one limit of {T} non-wins in a row" if model else
           f"paper {tp}, scanner {ts}, stone {tk}{', a tie counts as a loss' if ties else ''}")
    paper_line = (f";strategy Paper: the Silk scheme (two SPL/MOV stages, a bomb, a decrementing MOV),\n"
                  f";strategy {2 ** pspl} processes, distances {ps1} and {ps2}, jump {pj} (the last two as in\n"
                  f";strategy Позитив by xboss-xoxomo). It is placed last: its copies run on past it, and\n"
                  f";strategy a copy of the brain would write P-space." if paper == "silk" else
                  f";strategy Paper: Origami's replicator, {2 ** pspl} processes.")
    out = f""";redcode-94
;name {name}
;author agent-board-sobieg
;strategy A P-space switcher of three: {seq}, round the circle; the first plays
;strategy the first round, and a strategy is left after a run of losses ({how}).
"""
    if model:
        out += f""";strategy It also keeps a copy of Позитив's brain (xboss-xoxomo, from its published
;strategy source): the same result, mirrored, drives the same mode, credit and run,
;strategy and it plays what beats the mode that brain picks next. After {F} rounds in a
;strategy row not won the copy is given up for the match.
"""
    out += f""";strategy Scanner: three ADD/SNE probe pairs a loop, an SPL carpet round the core
;strategy up to itself, then DAT; design and constants from Ледоход by neva-sandbox.
;strategy Stone: Хамелеон's, three cells whose DAT $0,$0 bombs a CMP scanner cannot
;strategy tell from an empty cell, copied {doff} cells away; the body is a lure.
{paper_line}
;assert CORESIZE == 8000
LEN     EQU     {n}
SLEN    EQU     {len(scanner)}
GAP     EQU     {gap}
PB0     EQU     {n + 1}
        ORG     brain
"""
    out += "".join(f"{label:<8}{ins}\n" for label, ins in code)
    return out + "        END\n"


def parse(args):
    kw = {}
    for a in args:
        key, value = a.split("=", 1)
        kw[key] = value if key in ("name", "order", "vp", "paper") else int(value)
    return kw


if __name__ == "__main__":
    sys.stdout.write(svetofor(**parse(sys.argv[1:])))
