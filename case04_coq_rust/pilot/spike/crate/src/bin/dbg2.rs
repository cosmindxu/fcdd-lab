include!("../extracted.rs");

fn sq_from(file: usize, rank: usize) -> i64 {
    (rank * 16 + file) as i64
}

fn main() {
    let fen = "8/8/8/8/8/1N6/8/K6k w - - 0 1";
    let board_part = fen.split_whitespace().next().unwrap();
    let prog = Program::new();
    let mut board: &Corelib_Init_Datatypes_list<&Spike_At> =
        prog.alloc(Corelib_Init_Datatypes_list::nil(PhantomData));
    for (ri, rank) in board_part.split('/').enumerate() {
        let rank_idx = 7 - ri;
        let mut fi = 0usize;
        for ch in rank.chars() {
            if ch.is_ascii_digit() {
                fi += ch.to_digit(10).unwrap() as usize;
                continue;
            }
            let color_ref = prog.alloc(match ch {
                'K' | 'N' => Spike_color::White(PhantomData),
                _ => Spike_color::Black(PhantomData),
            });
            let piece_ref = prog.alloc(match ch {
                'N' | 'n' => Spike_piece::Knight(PhantomData),
                _ => Spike_piece::King(PhantomData),
            });
            let at = prog.alloc(Spike_At::mkAt(
                PhantomData,
                sq_from(fi, rank_idx),
                color_ref,
                piece_ref,
            ));
            board = prog.alloc(Corelib_Init_Datatypes_list::cons(
                PhantomData,
                at,
                board,
            ));
            fi += 1;
        }
    }
    let side_ref = prog.alloc(Spike_color::White(PhantomData));
    let moves = prog.spike_spikeGen()(board)(side_ref);
    let mut node = moves;
    loop {
        match node {
            Corelib_Init_Datatypes_list::cons(_, (f, t), rest) => {
                println!("move: {}->{}", f, t);
                node = rest;
            }
            Corelib_Init_Datatypes_list::nil(_) => break,
        }
    }
}
