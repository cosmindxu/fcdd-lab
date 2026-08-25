// Skeleton: implements the CLI contract with NO chess logic. Replace the
// body of each command. See IFACE.md for the full contract.
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        eprintln!("usage: chess_clone <legal|status|choose> --fen <FEN>");
        std::process::exit(2);
    }
    let cmd = args[1].as_str();
    let fen = args
        .iter()
        .position(|a| a == "--fen")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    match cmd {
        "legal" => legal(fen),
        "status" => status(fen),
        "choose" => choose(fen),
        _ => {
            eprintln!("unknown command: {}", cmd);
            std::process::exit(2);
        }
    }
}

fn legal(_fen: &str) {
    // TODO: print every legal move, one per line, lowercase long algebraic.
    eprintln!("skeleton: legal not implemented");
    std::process::exit(1);
}

fn status(_fen: &str) {
    // TODO: print exactly one of play, white-mated, black-mated, stalemate,
    //       draw, flag-fall.
    eprintln!("skeleton: status not implemented");
    std::process::exit(1);
}

fn choose(_fen: &str) {
    // TODO: print the move the ENGINE plays at the frozen level.
    eprintln!("skeleton: choose not implemented");
    std::process::exit(1);
}
