(* Case 04 — P3 extraction spike: minimal chess core in Rocq.
   Board as a list of (square, color, piece); movegen for KNIGHTS and KINGS
   only (pseudo-legal; pins/checks excluded — this is a TOOLCHAIN gate, not
   an engine-conformance gate). Validated against python-chess pseudo-legal
   moves restricted to kings and knights (see PILOT.md amendment to P3).

   Squares are Z (0x88 indices: rank*16+file, valid iff <128 and file<8);
   Z remaps to i64 under ExtrRustUncheckedArith. *)

From Stdlib Require Import List ZArith Bool.
Import ListNotations.
Open Scope Z_scope.

From TypedExtraction.Plugin Require Import Loader.
From TypedExtraction.Plugin Require Import ExtrRustBasic.
From TypedExtraction.Plugin Require Import ExtrRustUncheckedArith.

Definition sq := Z.

Inductive color := White | Black.
Inductive piece := Knight | King.

(* A Record, NOT a nested product: the extractor erases right-associative
   products (sq * color * piece) = (sq * (color * piece)) inconsistently
   between functions, which made lookup order-dependent (see PILOT.md,
   2026-08-24). Records extract to structs with named fields. *)
Record At := mkAt { at_sq : sq; at_color : color; at_piece : piece }.

Definition color_eqb (a b : color) : bool :=
  match a, b with
  | White, White => true
  | Black, Black => true
  | _, _ => false
  end.

Definition validSq (s : sq) : bool :=
  (0 <=? s)%Z && (s <? 128)%Z && (Z.modulo s 16 <? 8)%Z.

Fixpoint lookup (s : sq) (b : list At) : option (color * piece) :=
  match b with
  | nil => None
  | a :: rest => if (s =? at_sq a)%Z then Some (at_color a, at_piece a)
                 else lookup s rest
  end.

Definition knight_offsets : list (Z * Z) :=
  [(1,2);(2,1);(2,-1);(1,-2);(-1,-2);(-2,-1);(-2,1);(-1,2)].

Definition king_offsets : list (Z * Z) :=
  [(1,0);(1,1);(0,1);(-1,1);(-1,0);(-1,-1);(0,-1);(1,-1)].

(* one piece's pseudo-legal moves to empty or enemy-occupied squares *)
Fixpoint moves_for (s : sq) (offs : list (Z * Z)) (b : list At)
                   (col : color) : list (sq * sq) :=
  match offs with
  | nil => nil
  | (df, dr) :: rest =>
      let t := (s + 16 * df + dr)%Z in
      let keep :=
        validSq t &&
        match lookup t b with
        | Some (c, _) => negb (color_eqb c col)
        | None => true
        end in
      if keep then (s, t) :: moves_for s rest b col
      else moves_for s rest b col
  end.

Fixpoint genMoves' (full : list At) (b : list At) (col : color) : list (sq * sq) :=
  match b with
  | nil => nil
  | a :: rest =>
      let own := genMoves' full rest col in
      if color_eqb (at_color a) col
      then match at_piece a with
           | Knight => moves_for (at_sq a) knight_offsets full col ++ own
           | King   => moves_for (at_sq a) king_offsets full col ++ own
           end
      else own
  end.

Definition genMoves (b : list At) (col : color) : list (sq * sq) :=
  genMoves' b b col.

Definition spikeGen := genMoves.

Redirect "spike.rs" Rust Extract spikeGen.
