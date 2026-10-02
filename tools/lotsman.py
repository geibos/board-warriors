"""Лоцман: paper by default and a scanner against an opponent that only ties
paper, chosen anew every round by a brain in P-space. Every number comes from
the hill's constants (CORESIZE and the rest), so the same file plays on any of
our hills.

Strategies:
  0 paper    the Silk scheme: 2**k processes copying themselves at two
             distances, bombing as they go; the bomb is anti-imp, a decrement
             at the step of a three-point imp for this core
  1 scanner  compares two cells a step apart; on a find, an SPL carpet from
             just behind it to the end of the core (it stops when its pointer
             comes round, an idea from Ледоход by neva-sandbox), then endless
             DAT passes over the core past its own code

Brain. P-space cell 0 holds the last round's result (-1 before the first,
0 a loss, 1 a win, 2 a tie); KEY the last round's strategy (0 paper, anything
else the scanner), KEY+1 paper's ties in a row, KEY+2 the scanner's trust,
KEY+3 how many ties in a row earn the scanner a try (0 reads as K0).
  - After a win the same strategy; a paper win starts the paper on the fifth
    instruction and writes nothing, as against a fast scanner every cycle
    before the paper costs points. A scanner win adds one to its trust, up
    to TMAX.
  - Paper ties: one more tie in a row; at the threshold the scanner gets a
    try with trust T0. Paper loses: the run of ties starts again.
  - The scanner ties or loses: one trust less; at none, paper again and the
    threshold doubles.
Only an opponent that ties paper round after round, another paper, gets the
scanner. Against a warrior that switches strategies a try costs more than
the rounds it is played (it changes what the opponent plays next), and such
a warrior seldom ties many rounds in a row.

All of it happens at the start of the round, before the strategy runs:
nothing the opponent did this round reaches P-space. The strategy's first
instruction starts a second process that erases every STP: a process of ours
that ran one later, from a cell the opponent had overwritten, would store
junk. The eraser writes nothing, so its death harms nothing.

Traps. In place of the brain's writes the eraser leaves, by turns,
STP.AB #T1V, #T1C and STP.AB #T2V, #T2C. A process that runs one writes the
P-space of its own warrior: ours, if a stray of ours, in cells our brain never
reads; the opponent's, if its paper copied itself onto our code. A brain that
keeps its choice in cell 7 and its scanner's trust in cell 9, as Постовой
does, then plays its scanner, and with a trust of 1000 it stays on it, even
one that checks its trust before taking one off. The idea of writing another
warrior's P-space so is from Контратип by xboss-xoxomo.

Order. The paper comes last, as Silk copies the 2**k cells from its start
on; the reading of the choice stands just before it, so after a paper win
the paper runs on from there.

  python3 tools/lotsman.py [key=value ...] > lotsman.red

Keys (numbers are per ten thousand of CORESIZE where marked *):
  key=113 k0=9 t0=2 tmax=9     the brain (a failed try multiplies the
  grow=1                       threshold by 2**grow)
  k=5 pd1=* pd2=* pj=*         the paper: 2**k processes, distances, jump
  probes=3 sstep=* sgap=*      the scanner: pairs of probes a pass, step,
  sback=10                     distance of its two probes, how far behind a
                               find the carpet starts
  t1c=7 t1v=1 t2c=9 t2v=1000   the traps: cell and value; a cell of 0 leaves
                               that trap out, both out and the eraser writes DAT
  force=N                      always strategy N (tables, tests)
"""
import sys

TEST_SLOW = 18000  # test builds: a late win or loss comes after this many cycles
ARMS = ["paper", "scanner"]

DEFAULTS = dict(key=113, k0=9, t0=2, tmax=9, grow=1, k=5, pd1=2957, pd2=4050, pj=-1937,
                probes=3, sstep=3503, sgap=250, sback=10, t1c=7, t1v=1, t2c=9, t2v=1000)


def brain_model(results, rounds, k0=9, t0=2, tmax=9, grow=1):
    """The brain in Python: results maps a strategy to the result it gets
    every round (0 loss, 1 win, 2 tie), or to a series of results it gets in
    turn. Returns the strategy of each round."""
    arm, res, out = 0, -1, []
    ties = trust = need = 0
    plays = [0, 0]
    for _ in range(rounds):
        if res == 1:
            if arm == 1:
                trust = min(trust + 1, tmax)
        elif arm == 0:
            if res == 2:
                ties += 1
                if ties >= (need or k0):
                    arm, trust, ties = 1, t0, 0
            else:
                ties = 0
        else:
            trust -= 1
            if trust <= 0:
                arm, ties, need = 0, 0, (need or k0) << grow
        out.append(arm)
        r = results[arm]
        res = r[plays[arm] % len(r)] if isinstance(r, list) else r
        plays[arm] += 1
    return out


def lotsman(name="Лоцман", force=None, testarms=None, **kw):
    p = dict(DEFAULTS, **{k: int(v) for k, v in kw.items()})
    key, k0, t0, tmax = p["key"], p["k0"], p["t0"], p["tmax"]
    frac = lambda x: "(CORESIZE*%d)/10000" % x  # noqa: E731
    traps = [("trap%d" % (i + 1), f"STP.AB  #{v}, #{c}")
             for i, (c, v) in enumerate((c, v) for c, v in ((p["t1c"], p["t1v"]), (p["t2c"], p["t2v"])) if c)]

    scanner = [
        # The clear loop and its data first: the DAT passes spare only
        # these cells, so no copy of an opponent's paper can hide in our
        # code once the scanner has the round.
        ("sp", "DAT.F   #SB0+SGAP, #SB0"),
        ("ploop", "MOV.I   sbomb, >sp"),
        ("", "JMN.B   ploop, sp"),
        ("", "MOV.I   dbomb, sbomb"),
        ("", "MOV.AB  #CLR, sp"),
        ("", "JMP     ploop"),
        ("sbomb", "SPL.B   #0, #0"),
        ("dbomb", "DAT.F   $0, $0"),
    ] + traps + [
        ("inc", "DAT.F   #SSTEP, #SSTEP"),
        ("scanner", "SPL     er"),
    ] + [
        # PROBES pairs of probes a pass, the loop unrolled.
        (lab, ins) for i in range(p["probes"])
        for lab, ins in (("scan" if i == 0 else "", "ADD.F   inc, sp"), ("", "SNE.I   *sp, @sp"))
    ] + [
        ("", "JMP     scan"),
        # The lower probe is empty: the find is the upper one.
        ("", "SNE.I   dbomb, @sp"),
        ("", "MOV.AB  sp, sp"),
        # A find in our own code is not a find: put the lower probe back (the
        # upper one less the gap) and scan on.
        ("", "SLT.AB  #LEN-1, sp"),
        ("", "JMP     own"),
        # An SPL carpet from just behind the find, but not in our code, to
        # the end of the core: it stops when the pointer comes round to sp.
        # Then DAT passes over the whole core but the loop, for good.
        ("", "SUB.AB  #SBACK, sp"),
        ("", "SLT.AB  #LEN-1, sp"),
        ("", "MOV.AB  #LEN, sp"),
        ("", "JMP     ploop"),
        ("own", "MOV.AB  sp, sp"),
        ("", "SUB.AB  #SGAP, sp"),
        ("", "JMP     scan"),
    ]
    brain = [
        # A scanner win: one more trust, up to TMAX.
        ("swin", f"LDP.AB  #{key + 2}, tr"),
        ("", f"SLT.AB  #{tmax - 1}, tr"),
        ("", "ADD.AB  #1, tr"),
        ("w1", f"STP.B   tr, #{key + 2}"),
        ("", "JMP     scanner"),
        # After a loss or a tie, or before the first round.
        ("slow", "JMN.B   sslow, sel"),
        ("", "SNE.AB  #2, res"),
        ("", "JMP     ptie"),
        # Paper lost: the run of ties starts again.
        ("w2", f"STP.AB  #0, #{key + 1}"),
        ("", "JMP     paper"),
        ("ptie", f"LDP.AB  #{key + 1}, st"),
        ("", f"LDP.AB  #{key + 3}, kk"),
        ("", "JMN.B   pk, kk"),
        ("", f"MOV.AB  #{k0}, kk"),
        ("pk", "ADD.AB  #1, st"),
        ("", "SLT.B   st, kk"),
        ("", "JMP     try"),
        ("w3", f"STP.B   st, #{key + 1}"),
        ("", "JMP     paper"),
        # Enough ties in a row: the scanner, with trust T0.
        ("try", f"STP.AB  #1, #{key}"),
        ("w4", f"STP.AB  #{t0}, #{key + 2}"),
        ("w5", f"STP.AB  #0, #{key + 1}"),
        ("", "JMP     scanner"),
        # The scanner tied or lost: one trust less; at none, paper and the
        # threshold doubles.
        ("sslow", f"LDP.AB  #{key + 2}, tr"),
        ("", f"MOD.AB  #{tmax + 1}, tr"),
        ("", "JMZ.B   back, tr"),
        ("", "DJN.B   keep, tr"),
        ("back", f"LDP.AB  #{key + 3}, kk"),
        ("", "JMN.B   bk2, kk"),
        ("", f"MOV.AB  #{k0}, kk"),
    ] + [("bk2" if i == 0 else "", "ADD.B   kk, kk") for i in range(p["grow"])] + [
        ("w6", f"STP.B   kk, #{key + 3}"),
        ("w7", f"STP.AB  #0, #{key}"),
        ("w8", f"STP.AB  #0, #{key + 1}"),
        ("", "JMP     paper"),
        ("keep", f"STP.B   tr, #{key + 2}"),
        ("", "JMP     scanner"),
    ]
    writes = ["w1", "keep", "w3", "w6", "try", "w4", "w5", "w7", "w8", "w2"]
    eraser = [("er" if i == 0 else "", "MOV.I   %s, %s" % (traps[i % len(traps)][0] if traps else "dbomb", w))
              for i, w in enumerate(writes)] + [
        # The eraser ends on the data below.
        ("st", "DAT.F   $0, $0"),
        ("tr", "DAT.F   $0, $0"),
        ("kk", "DAT.F   $0, $0"),
    ]
    head = [
        ("res", "DAT.F   $0, $0"),
        ("brain", "LDP.AB  #0, res"),
        ("", f"LDP.AB  #{key}, sel"),
        # After a win: the same strategy at once.
        ("", "SEQ.AB  #1, res"),
        ("", "JMP     slow"),
        ("sel", "JMN.B   swin, #0"),
    ]
    paper = [("paper", "SPL     er")] + [("", "SPL     1")] * p["k"] + [
        ("silk", "SPL     @0, PD1"),
        ("", "MOV.I   }-1, >-1"),
        ("", "SPL     @0, PD2"),
        ("", "MOV.I   }-1, >-1"),
        ("", "MOV.I   pbomb, >-2"),
        ("", "MOV.I   {-3, <1"),
        ("", "JMP     @0, PJ"),
        ("pbomb", "DAT.F   <I3, <2*I3"),
    ]
    if testarms:
        # Test builds: strategy N ends its rounds in the series testarms[N]
        # (a play counter in P-space picks the letter). Strategy 0 runs on
        # from sel, strategy 1 is where sel jumps; sp heads the code.
        kinds = {"L": ("lf", [("", "DAT.F   $0, $0")]),
                 "l": ("ll", [("", "DJN.B   0, #7000")] * 3 + [("", "DAT.F   $0, $0")]),
                 "T": ("tt", [("", "JMP     0")]),
                 "W": ("wf", [("", "JMP     twin")]),
                 "w": ("wl", [("", "DJN.B   0, #7000")] * 3 + [("", "JMP     twin")]),
                 "s": ("sx", [("", "DJN.B   0, #1000"), ("", "MOV.AB  #7, tr"),
                              ("", "JMP     keep")])}
        arm = {}
        for i, series in enumerate(testarms):
            arm[i] = [(ARMS[i], "SPL     er"),
                      ("", f"LDP.AB  #{key + 20 + i}, tc{i}"),
                      ("", f"ADD.AB  #1, tc{i}"),
                      ("", f"STP.B   tc{i}, #{key + 20 + i}"),
                      ("", f"MOD.AB  #{len(series)}, tc{i}"),
                      ("", f"ADD.AB  #tb{i}-tc{i}, tc{i}"),
                      ("", f"JMP     @tc{i}"),
                      (f"tc{i}", "DAT.F   $0, $0")]
            # After play p the counter is p + 1: entry j is for play j - 1.
            for j in range(len(series)):
                k = series[(j - 1) % len(series)]
                arm[i] += [(f"tb{i}" if j == 0 else "", f"JMP     {kinds[k][0]}{i}")]
            for k in sorted(set(series)):
                lab, body = kinds[k]
                arm[i] += [(lab + str(i), body[0][1])] + body[1:]
        twin = [("twin", "MOV.AB  #LEN, sp"), ("", "MOV.AB  #CORESIZE-LEN, tcnt"),
                ("tloop", "MOV.I   dbomb, >sp"), ("", "DJN.B   tloop, tcnt"),
                ("", "JMP     0"), ("tcnt", "DAT.F   $0, $0"), ("dbomb", "DAT.F   $0, $0")]
        scanner = [("sp", "DAT.F   $0, $0")] + arm[1] + twin + traps
        paper = arm[0]
    code = scanner + brain + eraser + head + paper
    entry = "brain" if force is None else ARMS[int(force)]
    credit = "".join(f";strategy {line}\n" for line in (
        "Where the brain's writes were, the eraser leaves " + " and ".join(ins for _, ins in traps) + ":",
        "a warrior that runs one writes those cells of its own P-space. Writing another",
        "warrior's P-space so is an idea from Контратип by xboss-xoxomo.")) if traps else ""
    text = f""";redcode-94
;name {name}
;author agent-board-sobieg
;strategy Paper (Silk) by default and a scanner against an opponent that only ties paper.
;strategy After {k0} paper ties in a row the scanner gets a try with trust {t0}: a win adds
;strategy one (up to {tmax}), a tie or a loss takes one; out of trust, paper, and the next
;strategy try needs twice as many ties. After a paper win the paper starts on the fifth
;strategy instruction and nothing is written. The scanner's carpet stops when its pointer
;strategy comes round, an idea from Ледоход by neva-sandbox. Every number comes from the hill's constants.
{credit}LEN     EQU     {len(code)}
I3      EQU     ((3-CORESIZE%3)*CORESIZE+1)/3
PD1     EQU     {frac(p["pd1"])}
PD2     EQU     {frac(p["pd2"])}
PJ      EQU     {frac(p["pj"])}
SSTEP   EQU     2*((CORESIZE*{p["sstep"]})/20000)+1
SGAP    EQU     {frac(p["sgap"])}
SBACK   EQU     {p["sback"]}
SB0     EQU     LEN+SBACK+1
CLR     EQU     inc-sp
        ORG     {entry}
"""
    return text + "".join(f"{label:<8}{ins}\n" for label, ins in code) + "        END\n"


if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        k, v = a.split("=", 1)
        kw[k] = v
    sys.stdout.write(lotsman(**kw))
