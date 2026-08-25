include!("../extracted.rs");

fn sq_from(file: usize, rank: usize) -> i64 {
    (rank * 16 + file) as i64
}

fn main() {
    let prog = Program::new();
    let mut board: &Corelib_Init_Datatypes_list<Spike_piece_at> =
        prog.alloc(Corelib_Init_Datatypes_list::nil(PhantomData));
    let n_c = prog.alloc(Spike_color::White(PhantomData));
    let n_p = prog.alloc(Spike_piece::Knight(PhantomData));
    let at_n = ((sq_from(1, 2), n_c), n_p);
    board = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_n, board));
    let k_c = prog.alloc(Spike_color::White(PhantomData));
    let k_p = prog.alloc(Spike_piece::King(PhantomData));
    let at_k = ((sq_from(0, 0), k_c), k_p);
    board = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_k, board));
    let bk_c = prog.alloc(Spike_color::Black(PhantomData));
    let bk_p = prog.alloc(Spike_piece::King(PhantomData));
    let at_bk = ((sq_from(7, 0), bk_c), bk_p);
    board = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_bk, board));
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
