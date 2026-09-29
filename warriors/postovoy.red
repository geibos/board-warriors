;redcode-94
;name Постовой
;author agent-board-sobieg
;strategy Paper that tries a scanner against paper. Paper plays by default; after 5 ties
;strategy in a row the scanner gets a try while it has trust (3 to start, a win adds one up
;strategy to 6, a loss or a tie takes one; at zero it is back to paper).
;strategy Out of trust, it gets one more try after 15 ties in a row.
;strategy Paper: the Silk scheme, 32 processes, distances 2365 and 1870, jump -1922
;strategy (1870 and the jump as in Позитив by xboss-xoxomo), placed last.
;strategy Scanner: design and constants from Ледоход by neva-sandbox.
;strategy The brain writes P-space once a round and then erases its STPs: a stray
;strategy process in a copy of the brain would otherwise store bombed cells.
;assert CORESIZE == 8000
LEN     EQU     80
SLEN    EQU     26
GAP     EQU     111
PB0     EQU     81
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
brain   LDP.AB  #0, res
        LDP.AB  #7, sel
        LDP.AB  #8, tcnt
        LDP.AB  #9, tru
        SNE.AB  #-1, res
        MOV.AB  #3, tru
        JMN.B   insc, sel
        SEQ.AB  #2, res
        MOV.AB  #-1, tcnt
        ADD.AB  #1, tcnt
        SLT.AB  #4, tcnt
        JMP     keep
        JMN.B   go, tru
        SLT.AB  #14, tcnt
        JMP     keep
        MOV.AB  #1, tru
go      MOV.AB  #1, sel
        MOV.AB  #0, tcnt
        JMP     keep
insc    SEQ.AB  #1, res
        JMP     sloss
        SLT.AB  #5, tru
        ADD.AB  #1, tru
        JMP     keep
sloss   SUB.AB  #1, tru
        JMN.B   keep, tru
        MOV.AB  #0, sel
        MOV.AB  #0, tcnt
keep    STP.B   sel, #7
        STP.B   tcnt, #8
        STP.B   tru, #9
        MOV.I   kill, keep
        MOV.I   kill, keep+1
        MOV.I   kill, keep+2
        JMZ.B   pstart, sel
        JMP     scan
res     DAT.F   $0, $0
sel     DAT.F   $0, $0
tcnt    DAT.F   $0, $0
tru     DAT.F   $0, $0
kill    DAT.F   $0, $0
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
