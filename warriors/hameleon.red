;redcode-94
;name Хамелеон
;author agent-board-sobieg
;strategy A P-space switcher: a scanner against paper, a stone against scanners.
;strategy Each round it reads the last result from P-space and leaves a strategy
;strategy after a run of losses.
;strategy Scanner: three ADD/SNE probe pairs a loop, an SPL carpet round the core
;strategy up to itself, then DAT; design and constants from Ледоход by neva-sandbox.
;strategy Stone: three cells, the pointer in the JMP's B-field, bombs DAT $0,$0 that
;strategy a CMP scanner cannot tell from an empty cell. It is copied 4000 cells
;strategy away, and the body left behind is a lure.
;assert CORESIZE == 8000
LEN     EQU     60
SLEN    EQU     26
GAP     EQU     111
PB0     EQU     61
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
sloop   ADD.AB  #3044, sjp
        MOV.I   sbomb, @sjp
sjp     JMP     sloop, #1
sbomb   DAT.F   $0, $0
brain   LDP.AB  #0, res
        LDP.AB  #7, sel
        LDP.AB  #8, str
        SEQ.AB  #0, res
        MOV.AB  #0, str
        SNE.AB  #0, res
        ADD.AB  #1, str
        MOV.AB  #2, lim
        JMZ.B   chk, sel
        MOV.AB  #3, lim
chk     SLT.B   str, lim
        JMP     switch
        JMP     keep
switch  ADD.AB  #1, sel
        MOD.AB  #2, sel
        MOV.AB  #0, str
keep    STP.B   sel, #7
        STP.B   str, #8
        JMZ.B   boot, sel
        JMP     scan
boot    MOV.I   }cp, >cp
        MOV.I   }cp, >cp
        MOV.I   }cp, >cp
        MOV.I   }cp, >cp
        JMP     cp+4000
cp      DAT.F   #sloop, #4000
res     DAT.F   $0, $0
sel     DAT.F   $0, $0
str     DAT.F   $0, $0
lim     DAT.F   $0, $0
        END
