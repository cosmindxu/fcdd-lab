include!("extracted.rs");
// Case 04 P3 spike — adapter, in the SAME module as the extracted code
// (include! at crate root: inner attributes legal, privacy moot, extracted
// file stays byte-identical to the extractor output = the hash-lock
// pattern the real Arm A runs will use).

fn sq_from(file: usize, rank: usize) -> i64 {
    (rank * 16 + file) as i64
}

fn sq_name(s: i64) -> String {
    format!("{}{}", (b'a' + (s % 16) as u8) as char, (s / 16 + 1))
}

fn run(fen: &str) -> Vec<String> {
    let board_part = fen.split_whitespace().next().unwrap();
    let prog = Program::new();

    let mut board: &Corelib_Init_Datatypes_list<&Spike_At> =
        prog.alloc(Corelib_Init_Datatypes_list::nil(std::marker::PhantomData));

    for (ri, rank) in board_part.split('/').enumerate() {
        let rank_idx = 7 - ri;
        let mut fi = 0usize;
        for ch in rank.chars() {
            if ch.is_ascii_digit() {
                fi += ch.to_digit(10).unwrap() as usize;
                continue;
            }
            let color_ref = prog.alloc(match ch {
                'K' | 'N' => Spike_color::White(std::marker::PhantomData),
                _ => Spike_color::Black(std::marker::PhantomData),
            });
            let piece_ref = prog.alloc(match ch {
                'N' | 'n' => Spike_piece::Knight(std::marker::PhantomData),
                _ => Spike_piece::King(std::marker::PhantomData),
            });
            let at = prog.alloc(Spike_At::mkAt(
                std::marker::PhantomData,
                sq_from(fi, rank_idx),
                color_ref,
                piece_ref,
            ));
            board = prog.alloc(Corelib_Init_Datatypes_list::cons(
                std::marker::PhantomData,
                at,
                board,
            ));
            fi += 1;
        }
    }

    let side = match fen.split_whitespace().nth(1).unwrap_or("w") {
        "w" => Spike_color::White(std::marker::PhantomData),
        _ => Spike_color::Black(std::marker::PhantomData),
    };
    let side_ref = prog.alloc(side);
    let moves = prog.spike_spikeGen()(board)(side_ref);

    let mut out: Vec<String> = Vec::new();
    let mut node = moves;
    loop {
        match node {
            Corelib_Init_Datatypes_list::cons(_, (f, t), rest) => {
                out.push(format!("{}{}", sq_name(*f), sq_name(*t)));
                node = rest;
            }
            Corelib_Init_Datatypes_list::nil(_) => break,
        }
    }
    out.sort();
    out
}

fn main() {
    let fen = std::env::args().nth(2).expect("usage: spike moves <FEN>");
    for m in run(&fen) {
        println!("{}", m);
    }
}
