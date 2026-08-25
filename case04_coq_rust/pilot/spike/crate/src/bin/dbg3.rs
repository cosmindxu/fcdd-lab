include!("../extracted.rs");

fn main() {
    let prog = Program::new();
    // manual construction, but FRESH allocs per piece (like the loop)
    let wck = prog.alloc(Spike_color::White(PhantomData));
    let wp = prog.alloc(Spike_piece::King(PhantomData));
    let at_king = ((0i64, wck), wp);
    let wcn = prog.alloc(Spike_color::White(PhantomData));
    let wn = prog.alloc(Spike_piece::Knight(PhantomData));
    let at_knight = ((33i64, wcn), wn);
    let bc = prog.alloc(Spike_color::Black(PhantomData));
    let bp = prog.alloc(Spike_piece::King(PhantomData));
    let at_bking = ((7i64, bc), bp);
    let nil: &Corelib_Init_Datatypes_list<Spike_piece_at> = prog.alloc(Corelib_Init_Datatypes_list::nil(PhantomData));
    let l1 = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_bking, nil));
    let l2 = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_king, l1));
    let board = prog.alloc(Corelib_Init_Datatypes_list::cons(PhantomData, at_knight, l2));
    let m = prog.spike_spikeGen()(board)(wck);
    let mut node = m;
    loop {
        match node {
            Corelib_Init_Datatypes_list::cons(_, (f, t), rest) => {
                println!("move: {}->{}", f, t); node = rest; }
            Corelib_Init_Datatypes_list::nil(_) => break,
        }
    }
}
