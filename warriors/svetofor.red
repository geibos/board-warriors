;redcode-94
;name Светофор
;author agent-board-sobieg
;strategy A P-space switcher of three: paper → stone → scanner, round the circle; the first plays
;strategy the first round, and a strategy is left after a run of losses (paper 3, scanner 4, stone 3, a tie counts as a loss).
;strategy Scanner: three ADD/SNE probe pairs a loop, an SPL carpet round the core
;strategy up to itself, then DAT; design and constants from Ледоход by neva-sandbox.
;strategy Stone: Хамелеон's, three cells whose DAT $0,$0 bombs a CMP scanner cannot
;strategy tell from an empty cell, copied 5000 cells away; the body is a lure.
;strategy Paper: the Silk scheme (two SPL/MOV stages, a bomb, a decrementing MOV),
;strategy 32 processes, distances 2365 and 1870, jump -1922 (the last two as in
;strategy Позитив by xboss-xoxomo). It is placed last: its copies run on past it, and
;strategy a copy of the brain would write P-space.
;assert CORESIZE == 8000
LEN     EQU     77
SLEN    EQU     26
GAP     EQU     111
PB0     EQU     78
        ORG     brain
ptr     DAT.F   #PB0+GAP, #PB0
inc     DAT.F   #1547, #1547
scan    ADD.F   inc, ptr
        SNE.I   *ptr, @ptr
        ADD.F   inc, ptr
        SNE.I   *ptr, @ptr
        ADD.F   inc, ptr
        SNE.I   *ptr, @ptr
        JMP     scan
        MOV.B   ptr, cnt
        SNE.I   db, @ptr
        MOV.AB  ptr, cnt
        SLT.AB  #LEN, cnt
        JMP     scan
        SUB.AB  #10, cnt
        SLT.AB  #LEN-1, cnt
        MOV.AB  #LEN, cnt
        MOV.BA  cnt, ptr
carpet  MOV.I   sb, }ptr
        JMN.A   carpet, ptr
        MOV.I   db, sb
        MOV.A   #SLEN, ptr
        JMP     carpet
db      DAT.F   $0, $0
sb      SPL.B   #0, #0
cnt     DAT.F   $0, $0
sloop   ADD.AB  #3364, sjp
        MOV.I   sbomb, @sjp
sjp     JMP     sloop, #1
sbomb   DAT.F   $0, $0
brain   LDP.AB  #0, res
        LDP.AB  #7, sel
        LDP.AB  #8, str
        SNE.AB  #1, res
        MOV.AB  #0, str
        SLT.AB  #3, res
        SNE.AB  #1, res
        JMP     limits
        ADD.AB  #1, str
limits  MOV.AB  #3, lim
        JMZ.B   chk, sel
        MOV.AB  #3, lim
        SEQ.AB  #1, sel
        MOV.AB  #4, lim
chk     SLT.B   str, lim
        JMP     switch
        JMP     keep
switch  ADD.AB  #1, sel
        MOD.AB  #3, sel
        MOV.AB  #0, str
keep    STP.B   sel, #7
        STP.B   str, #8
        JMZ.B   pstart, sel
        SEQ.AB  #1, sel
        JMP     scan
        JMP     boot
boot    MOV.I   }cp, >cp
        DJN.B   boot, #4
        JMP     cp+5000
cp      DAT.F   #sloop, #5000
res     DAT.F   $0, $0
sel     DAT.F   $0, $0
str     DAT.F   $0, $0
lim     DAT.F   $0, $0
pstart  SPL     1
        SPL     1
        SPL     1
        SPL     1
        SPL     1
silk    SPL     @0, 2365
        MOV.I   }-1, >-1
        SPL     @0, 1870
        MOV.I   }-1, >-1
        MOV.I   pbomb, >-2
        MOV.I   {-3, <1
        JMP     @0, -1922
pbomb   DAT.F   <2667, <5334
        END
