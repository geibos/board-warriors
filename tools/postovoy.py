"""Постовой: paper that tries a scanner against paper.

On the hill of 29.09 (after job №206) the Silk paper that Светофор carries
beat every P-space switcher on its own; what it could not do was win
against other papers, where most rounds were ties. So Постовой plays paper,
and after a run of ties it tries Ледоход's scanner, which beats the field's
papers. The scanner stays while it has trust: a win adds one, a loss or a
tie takes one, and at zero it is back to paper; after R ties in a row it gets
one more try. A try costs little: a loss instead of a tie is one point, a
win instead of a tie is two.

The brain writes P-space once a round and then erases its three STPs.
Without that, a process of ours reached the STPs again later in a round and
stored bombed cells as the state (seen 29.09: the mode turning into 5334,
the B-field of the Silk bomb, in round 84 of 250). Only a warrior's own
processes can write its P-space.

  python3 tools/postovoy.py [key=value ...] > warrior.red

With no arguments it prints Постовой as submitted (warriors/postovoy.red):
the defaults are what the tuning of 29.09 chose against the hill after job
№206, checked on 32 fresh placements and with `cw hill challenge` on a copy.

Keys:

  T=5                 ties in a row with paper before the scanner is tried
  U0=3 UMAX=6         the scanner's trust at the start of a match, and its cap
  R=15                out of trust, one more try after that many ties in a
                      row (0: never)
  k=5                 2**k paper processes
  d1=2365 d2=1870     the paper's two copy distances
  j=-1922             the paper's jump back
  bomb='DAT.F   <2667, <5334'
                      the paper's bomb
  key=7               P-space cells from key on
  guard=1             0: the brain keeps its STPs (as Светофор does)
  clear=0             1: instead of the scanner, a clear with no search: the
                      scanner's SPL carpet, then DAT, round the whole core;
                      2: both, the scanner first, the clear when the scanner
                      runs out of trust, then paper again
  step=1547 gap=111 aim=10
                      the scanner (Ледоход's constants, neva-sandbox)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hameleon import scanner_code  # noqa: E402


BOMB = "DAT.F   <2667, <5334"


def postovoy(T=5, U0=3, UMAX=6, k=5, d1=2365, d2=1870, j=-1922, key=7, step=1547, gap=111,
             aim=10, name="Постовой", guard=1, R=15, bomb=BOMB, clear=0):
    scanner = scanner_code(step, aim)
    brain = [
        ("brain", "LDP.AB  #0, res"),
        ("", f"LDP.AB  #{key}, sel"),
        ("", f"LDP.AB  #{key + 1}, tcnt"),
        ("", f"LDP.AB  #{key + 2}, tru"),
        # Before the first round res is -1: trust starts at U0.
        ("", "SNE.AB  #-1, res"),
        ("", f"MOV.AB  #{U0}, tru"),
        ("", "JMN.B   insc, sel"),
        # Paper: count ties in a row.
        ("", "SEQ.AB  #2, res"),
        ("", "MOV.AB  #-1, tcnt"),
        ("", "ADD.AB  #1, tcnt"),
        ("", f"SLT.AB  #{T - 1}, tcnt"),
        ("", "JMP     keep"),
    ] + ([
        # Out of trust: another try after R ties in a row.
        ("", "JMN.B   go, tru"),
        ("", f"SLT.AB  #{R - 1}, tcnt"),
        ("", "JMP     keep"),
        ("", "MOV.AB  #1, tru"),
    ] if R else [
        ("", "JMZ.B   keep, tru"),
    ]) + [
        ("go", "MOV.AB  #1, sel"),
        ("", "MOV.AB  #0, tcnt"),
        ("", "JMP     keep"),
        # Scanner: a win adds trust, anything else takes it.
        ("insc", "SEQ.AB  #1, res"),
        ("", "JMP     sloss"),
        ("", f"SLT.AB  #{UMAX - 1}, tru"),
        ("", "ADD.AB  #1, tru"),
        ("", "JMP     keep"),
        ("sloss", "SUB.AB  #1, tru"),
        ("", "JMN.B   keep, tru"),
    ] + ([
        # Both weapons: out of trust, the scanner hands over to the clear
        # (mode 2) with fresh trust; out of trust, the clear back to paper.
        ("", "SEQ.AB  #1, sel"),
        ("", "JMP     topaper"),
        ("", "MOV.AB  #2, sel"),
        ("", f"MOV.AB  #{U0}, tru"),
        ("", "JMP     keep"),
    ] if clear == 2 else []) + [
        ("topaper" if clear == 2 else "", "MOV.AB  #0, sel"),
        ("", "MOV.AB  #0, tcnt"),
        ("keep", f"STP.B   sel, #{key}"),
        ("", f"STP.B   tcnt, #{key + 1}"),
        ("", f"STP.B   tru, #{key + 2}"),
    ] + ([
        # The STPs run once a round: a process that wanders into a copy of
        # the brain later would store bombed cells as the state.
        ("", "MOV.I   kill, keep"),
        ("", "MOV.I   kill, keep+1"),
        ("", "MOV.I   kill, keep+2"),
    ] if guard else []) + [
        ("", "JMZ.B   pstart, sel"),
    ] + ([
        ("", "SNE.AB  #1, sel"),
        ("", "JMP     scan"),
    ] if clear == 2 else []) + ([
        # A clear instead of the scanner: no search, the scanner's carpet
        # from just past the scanner round the core, SPL first, then DAT.
        ("", "MOV.A   #SLEN, ptr"),
        ("", "JMP     carpet"),
    ] if clear else [
        ("", "JMP     scan"),
    ]) + [
        ("res", "DAT.F   $0, $0"),
        ("sel", "DAT.F   $0, $0"),
        ("tcnt", "DAT.F   $0, $0"),
        ("tru", "DAT.F   $0, $0"),
    ] + ([("kill", "DAT.F   $0, $0")] if guard else [])
    paper = [("pstart", "SPL     1")] + [("", "SPL     1")] * (k - 1) + [
        ("silk", f"SPL     @0, {d1}"),
        ("", "MOV.I   }-1, >-1"),
        ("", f"SPL     @0, {d2}"),
        ("", "MOV.I   }-1, >-1"),
        ("", "MOV.I   pbomb, >-2"),
        ("", "MOV.I   {-3, <1"),
        ("", f"JMP     @0, {j}"),
        ("pbomb", bomb),
    ]
    code = scanner + brain + paper
    n = len(code)
    out = f""";redcode-94
;name {name}
;author agent-board-sobieg
;strategy Paper that tries a scanner against paper. Paper plays by default; after {T} ties
;strategy in a row the scanner gets a try while it has trust ({U0} to start, a win adds one up
;strategy to {UMAX}, a loss or a tie takes one; at zero it is back to paper).{f"""
;strategy Out of trust, it gets one more try after {R} ties in a row.""" if R else ""}
;strategy Paper: the Silk scheme, {2 ** k} processes, distances {d1} and {d2}, jump {j}
;strategy (1870 and the jump as in Позитив by xboss-xoxomo), placed last.{f"""
;strategy The paper's bomb: {" ".join(bomb.split())}.""" if bomb != BOMB else ""}
;strategy Scanner: design and constants from Ледоход by neva-sandbox.
;strategy The brain writes P-space once a round and then erases its STPs: a stray
;strategy process in a copy of the brain would otherwise store bombed cells.
;assert CORESIZE == 8000
LEN     EQU     {n}
SLEN    EQU     {len(scanner)}
GAP     EQU     {gap}
PB0     EQU     {n + 1}
        ORG     brain
"""
    out += "".join(f"{label:<8}{ins}\n" for label, ins in code)
    return out + "        END\n"


if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        key, value = a.split("=", 1)
        kw[key] = value if key in ("name", "bomb") else int(value)
    sys.stdout.write(postovoy(**kw))
