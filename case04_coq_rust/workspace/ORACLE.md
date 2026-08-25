# The oracle CLI — your discovery instrument

`tools/oracle_cli.py` is your ONLY access to the reference Z80 chess
engine. Correctness is defined by a hidden formal model of the engine's
rules; the engine itself is not the referee (it is an imperfect 1980s
program with known bugs). But the engine's behaviour is how you LEARN
what to build: which rules it implements, and where it diverges from
FIDE. The scorer measures against the hidden model, so use probes to pin
down the engine's rule details — draw conditions, castling and en-passant
edge cases, anything your chess knowledge is not certain of — and do not
blindly copy quirks that look like bugs.

## Budget

Every probe counts against a hard per-run budget and the counter is
mechanical. Budget is a resource: think about what you need to learn
before you spend it. A refused probe (exit code 2) is final.

## Probes

    legal  --fen FEN [--path m1,m2,...]   [--auto]
    status --fen FEN [--path m1,m2,...]   [--auto]
    choose --fen FEN [--level N]

`--run-id` is set for you by the environment; do not change it.

### How positions are addressed

The engine's state is only observable after a move completes. A probe
therefore REPLAYS a path of UCI moves from a seed FEN (usually the start
position) and reports the position the path reaches:

    legal --fen "<start-fen>" --path e2e4,e7e5,g1f3

    {"layer":"legal","fen":"...","path":[...],"genCount":NN,
     "legal":["b8c6","b8a6",...], "status":"play",
     "gameState":0,"reachedFen":"..."}

`legal` returns the engine's own legal move set (lowercase long algebraic,
promotion letter included) for the side to move, plus the terminal status.
`--auto` makes the CLI search for a path from the start position for you —
it only finds shallow targets (a few plies); for anything else supply your
own path. An UNJUDGEABLE answer means the replay did not land on the
position you asked for; fix the path.

`status` is the same replay, same output.

### Chosen moves

`choose` injects a Black-to-move position directly (no path) and returns
the move the engine plays at the given level:

    choose --fen "<black-to-move-fen>" --level 1

    {"layer":"choose","fen":"...","level":1,"move":"b8c6",
     "gameState":"play","moveLogN":1}

Deterministic: the same position at the same level always yields the same
move. Terminal positions return no move and the terminal `gameState`.

## Provenance

Every observable is read from the engine's own RAM after a fixed, fully
deterministic frame schedule. If you want to know exactly what a number
means, ask the CLI and read the answer fields; the memory addresses and
their meanings are documented in the CLI source, which you may read.
