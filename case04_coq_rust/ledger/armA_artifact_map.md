# Arm A artifact map — Rocq model -> extracted Rust -> theorems

Definitions: 161 (spec), generated fns: 150, theorems: 26

Generated Rust functions: 257 total (of which 107 `__curried` wrappers)

Definitions WITHOUT any generated code: ['COLBIT', 'EMPTY', 'GameState', 'History', 'Move', 'Position', 'SP_NONE', 'TYPEMASK', 'mvEqb', 'xorAux', 'xorB']

Generated names with NO spec definition (renamed/generated): none


## Layers


### byte/bit layer (17 definitions)

- `addB` — generated: curried, plain
- `andAux` — generated: curried, plain
- `andB` — generated: curried, plain  <— `T0a_onBoard_is_mask`, `T0b_type_is_mask`, `T0c_col_is_mask`, `T0d_file_is_mask`, `T0e_rank_is_mask`
- `bitn` — generated: curried, plain
- `negB` — generated: curried, plain
- `orAux` — generated: curried, plain
- `orB` — generated: curried, plain
- `parseCastling` — generated: curried, plain
- `pawnCapB` — generated: curried, plain
- `pawnCapW` — generated: curried, plain
- `pow2` — generated: curried, plain
- `rayGo` — generated: curried, plain
- `shieldMissing` — generated: curried, plain
- `slideGo` — generated: curried, plain
- `w8` — generated: curried, plain
- `xorAux` — generated: NOT EXTRACTED
- `xorB` — generated: NOT EXTRACTED  <— `T0f_mirrorIdx_is_xor`

### squares & pieces (38 definitions)

- `BB` — generated: plain
- `BK` — generated: plain
- `BLACK` — generated: plain
- `BN` — generated: plain
- `BP` — generated: plain
- `BQ` — generated: plain
- `BR` — generated: plain
- `COLBIT` — generated: NOT EXTRACTED  <— `T0c_col_is_mask`
- `EMPTY` — generated: NOT EXTRACTED
- `TYPEMASK` — generated: NOT EXTRACTED  <— `T0b_type_is_mask`
- `WB` — generated: plain
- `WHITE` — generated: plain  <— `T9b_no_rights_no_castle`, `T10a_ep_needs_target`
- `WK` — generated: plain
- `WN` — generated: plain
- `WP` — generated: plain
- `WQ` — generated: plain
- `WR` — generated: plain
- `anyHeavy` — generated: curried, plain
- `anyNonKing` — generated: curried, plain
- `bGet` — generated: curried, plain
- `bSet` — generated: curried, plain
- `centerDist` — generated: curried, plain
- `countPiece` — generated: curried, plain
- `emptyBoard` — generated: plain
- `fenOk` — generated: curried, plain
- `fileCount` — generated: curried, plain
- `findPiece` — generated: curried, plain
- `kingProx` — generated: curried, plain
- `mirrorIdx` — generated: curried, plain  <— `T0f_mirrorIdx_is_xor`
- `onBoard` — generated: curried, plain  <— `T0a_onBoard_is_mask`
- `other` — generated: curried, plain
- `passedPawns` — generated: curried, plain
- `pawnStruct` — generated: curried, plain
- `pcCol` — generated: curried, plain  <— `T0c_col_is_mask`
- `pcType` — generated: curried, plain  <— `T0b_type_is_mask`
- `sq64` — generated: curried, plain  <— `T0f_mirrorIdx_is_xor`
- `sqFile` — generated: curried, plain  <— `T0d_file_is_mask`
- `sqRank` — generated: curried, plain  <— `T0e_rank_is_mask`

### move encoding & dirs (19 definitions)

- `Move` — generated: NOT EXTRACTED
- `SP_DPUSH` — generated: plain
- `SP_EP` — generated: plain  <— `T10_ep_generated`, `T10a_ep_needs_target`
- `SP_NONE` — generated: NOT EXTRACTED
- `SP_OO` — generated: plain  <— `T9_castle_OO`, `T9b_no_rights_no_castle`
- `SP_OOO` — generated: plain  <— `T9a_castle_OOO`
- `bishopDirs` — generated: plain
- `kingDirs` — generated: plain
- `knightDirs` — generated: plain
- `moveChars` — generated: curried, plain
- `mvDst` — generated: curried, plain
- `mvEqb` — generated: NOT EXTRACTED
- `mvFlag` — generated: curried, plain
- `mvFrm` — generated: curried, plain  <— `T16c_pinned_piece_frozen`
- `mvPromo` — generated: curried, plain  <— `T11_promotions_count`
- `mvSpecial` — generated: curried, plain
- `pickBest` — generated: curried, plain
- `promoFlags` — generated: plain
- `rookDirs` — generated: plain

### attacks (8 definitions)

- `inCheckSide` — generated: curried, plain
- `isAttacked` — generated: curried, plain
- `pawnAt` — generated: curried, plain
- `posMc` — generated: curried, plain
- `scanHop` — generated: curried, plain
- `scanSlide` — generated: curried, plain
- `scanSquares` — generated: plain  <— `T0f_mirrorIdx_is_xor`
- `slideHit` — generated: curried, plain

### move generation (9 definitions)

- `addPromos` — generated: curried, plain
- `genCastling` — generated: curried, plain
- `genForSquare` — generated: curried, plain
- `genHops` — generated: curried, plain
- `genMoves` — generated: curried, plain  <— `T16a_pin_pseudo`
- `genPawnBlack` — generated: curried, plain
- `genPawnWhite` — generated: curried, plain
- `genRay` — generated: curried, plain
- `genSlides` — generated: curried, plain

### make/legality (5 definitions)

- `capSquare` — generated: curried, plain
- `clrCastleSq` — generated: curried, plain
- `genLegal` — generated: curried, plain  <— `T2_start_20_moves`, `T4a_mate_no_moves`, `T7b_fifty_has_moves`, `T9_castle_OO`, `T9a_castle_OOO`, `T9b_no_rights_no_castle`, `T10_ep_generated`, `T10a_ep_needs_target`, `T11_promotions_count`, `T16b_pin_legal`, `T16c_pinned_piece_frozen`
- `makeMove` — generated: curried, plain
- `moverInCheck` — generated: curried, plain

### terminal & draw (9 definitions)

- `GameState` — generated: NOT EXTRACTED
- `History` — generated: NOT EXTRACTED
- `countN` — generated: curried, plain  <— `T11_promotions_count`
- `countReps` — generated: curried, plain
- `emptyHist` — generated: plain
- `isInsufficient` — generated: curried, plain  <— `T6a_insufficient_holds`, `T7a_fifty_not_insufficient`
- `statusChars` — generated: curried, plain
- `statusOf` — generated: curried, plain  <— `T1_start_is_play`, `T4_mate`, `T5_stalemate`, `T6_insufficient`, `T7_fifty`
- `updateTerminal` — generated: curried, plain

### evaluation (16 definitions)

- `eval` — generated: curried, plain
- `evalWhite` — generated: curried, plain
- `gamePhase` — generated: curried, plain
- `kingPstSigned` — generated: curried, plain
- `materialTbl` — generated: plain
- `matingEval` — generated: curried, plain
- `pieceValSigned` — generated: curried, plain
- `pstBishop` — generated: plain
- `pstFor` — generated: curried, plain
- `pstKingEG` — generated: plain
- `pstKingMG` — generated: plain
- `pstKnight` — generated: plain
- `pstPawn` — generated: plain
- `pstQueen` — generated: plain
- `pstRook` — generated: plain
- `pstScore` — generated: curried, plain

### search & perft (2 definitions)

- `chooseMove` — generated: curried, plain
- `negamax` — generated: curried, plain

### FEN / CLI (10 definitions)

- `dropField` — generated: curried, plain
- `entry` — generated: curried, plain
- `fieldAt` — generated: curried, plain
- `isDigitC` — generated: curried, plain
- `nzeros` — generated: curried, plain
- `parseBoard` — generated: curried, plain
- `parseBoardAux` — generated: curried, plain
- `parseFen` — generated: curried, plain
- `pieceOfChar` — generated: curried, plain
- `takeField` — generated: curried, plain

## Theorems -> definitions (proofs are erased; the mapping shows what each constrains)

- `T0a_onBoard_is_mask`
  - `andB` (byte/bit layer)
  - `nseq` (other)
  - `onBoard` (squares & pieces)
- `T0b_type_is_mask`
  - `TYPEMASK` (squares & pieces)
  - `andB` (byte/bit layer)
  - `nseq` (other)
  - `pcType` (squares & pieces)
- `T0c_col_is_mask`
  - `COLBIT` (squares & pieces)
  - `andB` (byte/bit layer)
  - `nseq` (other)
  - `pcCol` (squares & pieces)
- `T0d_file_is_mask`
  - `andB` (byte/bit layer)
  - `nseq` (other)
  - `sqFile` (squares & pieces)
- `T0e_rank_is_mask`
  - `andB` (byte/bit layer)
  - `nseq` (other)
  - `sqRank` (squares & pieces)
- `T0f_mirrorIdx_is_xor`
  - `mirrorIdx` (squares & pieces)
  - `scanSquares` (attacks)
  - `sq64` (squares & pieces)
  - `xorB` (byte/bit layer)
- `T1_start_is_play`
  - `statusOf` (terminal & draw)
- `T2_start_20_moves`
  - `genLegal` (make/legality)
- `T3_start_perft1`
- `T4_mate`
  - `statusOf` (terminal & draw)
- `T4a_mate_no_moves`
  - `genLegal` (make/legality)
  - `isNil` (other)
- `T5_stalemate`
  - `statusOf` (terminal & draw)
- `T6_insufficient`
  - `statusOf` (terminal & draw)
- `T6a_insufficient_holds`
  - `isInsufficient` (terminal & draw)
  - `posBoard` (other)
- `T7_fifty`
  - `statusOf` (terminal & draw)
- `T7a_fifty_not_insufficient`
  - `isInsufficient` (terminal & draw)
  - `posBoard` (other)
- `T7b_fifty_has_moves`
  - `genLegal` (make/legality)
  - `isNil` (other)
- `T9_castle_OO`
  - `SP_OO` (move encoding & dirs)
  - `genLegal` (make/legality)
- `T9a_castle_OOO`
  - `SP_OOO` (move encoding & dirs)
  - `genLegal` (make/legality)
- `T9b_no_rights_no_castle`
  - `SP_OO` (move encoding & dirs)
  - `WHITE` (squares & pieces)
  - `genLegal` (make/legality)
  - `posBoard` (other)
- `T10_ep_generated`
  - `SP_EP` (move encoding & dirs)
  - `genLegal` (make/legality)
- `T10a_ep_needs_target`
  - `SP_EP` (move encoding & dirs)
  - `WHITE` (squares & pieces)
  - `genLegal` (make/legality)
  - `posBoard` (other)
- `T11_promotions_count`
  - `countN` (terminal & draw)
  - `genLegal` (make/legality)
  - `mvPromo` (move encoding & dirs)
- `T16a_pin_pseudo`
  - `genMoves` (move generation)
- `T16b_pin_legal`
  - `genLegal` (make/legality)
- `T16c_pinned_piece_frozen`
  - `genLegal` (make/legality)
  - `mvFrm` (move encoding & dirs)