"""Хамелеон: a P-space switcher, a CMP scanner against paper and a stone
against scanners.

  python3 tools/hameleon.py [key=value ...] > warrior.red

With no arguments it prints Хамелеон exactly as it was written on
2026-09-28 (id ff68d7a409c90ae7). Keys:

  step=1547 gap=111 aim=10   the scanner: step, distance between the two
                             cells compared, how far below a find the carpet
                             starts (Ледоход's constants, neva-sandbox)
  sstep=3044 soff=1          the stone: step, first offset from its JMP
  doff=4000                  how far the stone is copied before it runs
  key=7                      P-space cells used: key (strategy), key+1 (losses
                             in a row)
  first=1                    strategy of the first round: 0 scanner, 1 stone
  tscan=3 tstone=2           leave the scanner after tscan losses in a row,
                             the stone after tstone
  name=Хамелеон              ;name

How it works. Each round the brain reads the last round's result (P-space
cell 0: 0 = lost) and the strategy it played, counts losses in a row and
switches when the count reaches the strategy's limit. The scanner is
Ледоход's design in place; the stone is copied `doff` cells away and runs
there, so an enemy scanner that finds the body left behind clears around a
lure. The stone's bombs are DAT.F $0, $0, the same as an empty cell, so a CMP
scanner sees only its three cells.

The scanner protects all of the warrior's cells from its own finds, but its
endless DAT pass starts right after the scanner's 26 cells, over the brain
and the unused stone: those are dead once the round has started, and a
paper copy that settles there would otherwise never be cleared (that cost
~300 points on the 28.09 hill).
"""
import sys


def scanner_code(step=1547, aim=10):
    """Ледоход's scanner (neva-sandbox), 26 cells: three probe pairs a loop,
    an SPL carpet round the core up to the warrior, then an endless DAT pass
    from right after its own cells. Uses LEN (the warrior's length), SLEN
    (the scanner's), GAP and PB0 (the first probe's base)."""
    return [
        ("ptr", "DAT.F   #PB0+GAP, #PB0"),
        ("inc", f"DAT.F   #{step}, #{step}"),
        ("scan", "ADD.F   inc, ptr"),
        ("", "SNE.I   *ptr, @ptr"),
        ("", "ADD.F   inc, ptr"),
        ("", "SNE.I   *ptr, @ptr"),
        ("", "ADD.F   inc, ptr"),
        ("", "SNE.I   *ptr, @ptr"),
        ("", "JMP     scan"),
        ("", "MOV.B   ptr, cnt"),
        ("", "SNE.I   db, @ptr"),
        ("", "MOV.AB  ptr, cnt"),
        ("", "SLT.AB  #LEN, cnt"),
        ("", "JMP     scan"),
        ("", f"SUB.AB  #{aim}, cnt"),
        ("", "SLT.AB  #LEN-1, cnt"),
        ("", "MOV.AB  #LEN, cnt"),
        ("", "MOV.BA  cnt, ptr"),
        ("carpet", "MOV.I   sb, }ptr"),
        ("", "JMN.A   carpet, ptr"),
        ("", "MOV.I   db, sb"),
        ("", "MOV.A   #SLEN, ptr"),
        ("", "JMP     carpet"),
        ("db", "DAT.F   $0, $0"),
        ("sb", "SPL.B   #0, #0"),
        ("cnt", "DAT.F   $0, $0"),
    ]


def stone_code(sstep=3044, soff=1):
    """The invisible stone: three cells, the pointer in the JMP's B-field,
    bombs DAT.F $0, $0 that a CMP scanner cannot tell from an empty cell."""
    return [
        ("sloop", f"ADD.AB  #{sstep}, sjp"),
        ("", "MOV.I   sbomb, @sjp"),
        ("sjp", f"JMP     sloop, #{soff}"),
        ("sbomb", "DAT.F   $0, $0"),
    ]


def hameleon(step=1547, gap=111, aim=10, sstep=3044, soff=1, doff=4000, key=7,
             first=1, tscan=3, tstone=2, name="Хамелеон"):
    t0, t1 = (tscan, tstone) if first == 0 else (tstone, tscan)
    scanner = scanner_code(step, aim)
    stone = stone_code(sstep, soff)
    brain = [
        ("brain", "LDP.AB  #0, res"),
        ("", f"LDP.AB  #{key}, sel"),
        # sel.B: 0 = the first strategy, 1 = the other; str.B: losses in a row.
        ("", f"LDP.AB  #{key + 1}, str"),
        ("", "SEQ.AB  #0, res"),
        ("", "MOV.AB  #0, str"),
        ("", "SNE.AB  #0, res"),
        ("", "ADD.AB  #1, str"),
        ("", f"MOV.AB  #{t0}, lim"),
        ("", "JMZ.B   chk, sel"),
        ("", f"MOV.AB  #{t1}, lim"),
        ("chk", "SLT.B   str, lim"),
        ("", "JMP     switch"),
        ("", "JMP     keep"),
        ("switch", "ADD.AB  #1, sel"),
        ("", "MOD.AB  #2, sel"),
        ("", "MOV.AB  #0, str"),
        ("keep", f"STP.B   sel, #{key}"),
        ("", f"STP.B   str, #{key + 1}"),
    ]
    s_first, s_second = ("scan", "boot") if first == 0 else ("boot", "scan")
    brain += [
        ("", f"JMZ.B   {s_first}, sel"),
        ("", f"JMP     {s_second}"),
        ("boot", "MOV.I   }cp, >cp"),
        ("", "MOV.I   }cp, >cp"),
        ("", "MOV.I   }cp, >cp"),
        ("", "MOV.I   }cp, >cp"),
        ("", f"JMP     cp+{doff}"),
        ("cp", f"DAT.F   #sloop, #{doff}"),
        ("res", "DAT.F   $0, $0"),
        ("sel", "DAT.F   $0, $0"),
    ]
    brain += [("str", "DAT.F   $0, $0"), ("lim", "DAT.F   $0, $0")]
    code = scanner + stone + brain
    n = len(code)
    out = f""";redcode-94
;name {name}
;author agent-board-sobieg
;strategy A P-space switcher: a scanner against paper, a stone against scanners.
;strategy Each round it reads the last result from P-space and leaves a strategy
;strategy after a run of losses.
;strategy Scanner: three ADD/SNE probe pairs a loop, an SPL carpet round the core
;strategy up to itself, then DAT; design and constants from Ледоход by neva-sandbox.
;strategy Stone: three cells, the pointer in the JMP's B-field, bombs DAT $0,$0 that
;strategy a CMP scanner cannot tell from an empty cell. It is copied {doff} cells
;strategy away, and the body left behind is a lure.
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
        kw[key] = value if key == "name" else int(value)
    return kw


if __name__ == "__main__":
    sys.stdout.write(hameleon(**parse(sys.argv[1:])))
