include!("../extracted.rs");

fn main() {
    let prog = Program::new();
    let wc = prog.alloc(Spike_color::White(PhantomData));
    let wp = prog.alloc(Spike_piece::King(PhantomData));
    let at_king = ((0i64, wc), wp);
    let wn = prog.alloc(Spike_piece::Knight(PhantomData));
    let at_knight = ((33i64, wc), wn);
    let bc = prog.alloc(Spike_color::Black(PhantomData));
    let bp = prog.alloc(Spike_piece::King(PhantomData));
    let at_bking = ((7i64, bc), bp);
    let nil = prog.alloc(Corelib_Init_Datatypes_list::nil(PhantomData));

    // spike's exact list order: front-to-back [k@7, K@0, N@33]
    let l1 = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_bking, nil));
    let l2 = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_king, l1));
    let board = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_knight, l2));

    let r0 = prog.spike_lookup(0, board);
    println!("lookup(0): {:?}", r0);
    let m = prog.spike_spikeGen()(board)(wc);
    let mut node = m;
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
