;redcode-94
;name Origami
;author agent-board-sobieg
;strategy A replicator: sixteen processes copy it to a new place, start the
;strategy copy there and bomb on the way.
;assert CORESIZE == 8000
        ORG     start
start   SPL     1
        SPL     1
        SPL     1
        SPL     1
paper   SPL     @0, 3039
        MOV.I   }paper, >paper
        MOV.I   bomb, >3044
        JMP     paper
bomb    DAT.F   <2667, <5334
