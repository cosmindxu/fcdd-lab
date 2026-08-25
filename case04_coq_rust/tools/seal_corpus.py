#!/usr/bin/env python3
"""Case 04 — P5: seal the hidden corpus (checkpointed, resumable).

Phase 1: double-probe every corpus entry (legal+status) against the live
oracle; entries that are not self-consistent or are unjudgeable are
EXCLUDED with statistics (C16 hygiene rule). Results append to a partial
JSONL as they land, so a crash resumes instead of restarting.

Phase 2: the policy subset — entries whose recorded status is 'play' and
whose target position has Black to move, in corpus order, first
--policy-n; each double-probed with `choose` at level 1, checkpointed the
same way.

Phase 3: write ledger/sealed/answers.json + exclusions.json + sha256.

Usage: seal_corpus.py <corpus.json> [--jobs 8] [--policy-n 2000]
                [--resume]   # skip entries already in the partial file
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from oracle_cli import probe_legal, probe_choose  # noqa: E402

PARTIAL = os.path.join(LAB, "ledger", "sealing_partial.jsonl")


def side_of(fen):
    return "b" if fen.split()[1] == "b" else "w"


def check_legal(e):
    try:
        a = probe_legal(e["fen"], e["path"], False)
        b = probe_legal(e["fen"], e["path"], False)
    except Exception as ex:   # unjudgeable must EXCLUDE, never crash the pool
        return ("unj", e, str(ex)[:200])
    if a is None or b is None or "error" in a or "error" in b:
        return ("unj", e, (a or b or {}).get("error", "?"))
    if a["legal"] != b["legal"] or a["status"] != b["status"]:
        return ("diff", e, None)
    return ("ok", e, {"legal": sorted(a["legal"]), "status": a["status"],
                      "genCount": a["genCount"]})


def check_choose(fen):
    try:
        a = probe_choose(fen, 1)
        b = probe_choose(fen, 1)
    except Exception:
        return None
    if a is None or b is None or "error" in a or "error" in b:
        return None
    if a["move"] != b["move"]:
        return None
    return a["move"]


def load_partial():
    done = {}
    if os.path.isfile(PARTIAL):
        for line in open(PARTIAL):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                done[r["fen"]] = r
            except Exception:
                pass
    return done


def append_partial(rec):
    with open(PARTIAL, "a") as f:
        f.write(json.dumps(rec) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--policy-n", type=int, default=2000)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args(argv)

    data = json.load(open(args.corpus))
    entries = data["entries"]
    done = load_partial() if args.resume else {}
    todo = [e for e in entries if e["targetFen"] not in done]
    print("entries: %d  todo: %d (resume=%s)"
          % (len(entries), len(todo), args.resume), flush=True)

    results = []
    if todo:
        with mp.Pool(args.jobs) as pool:
            for i, (kind, e, payload) in enumerate(
                    pool.imap_unordered(check_legal, todo)):
                rec = {"fen": e["targetFen"], "path": e["path"],
                       "ply": e["ply"], "phase": e["phase"], "kind": kind}
                if kind == "ok":
                    rec.update(payload)
                else:
                    rec["detail"] = str(payload)[:200]
                results.append(rec)
                append_partial(rec)
                if (i + 1) % 250 == 0:
                    print("  phase1: %d/%d processed" % (i + 1, len(todo)),
                          flush=True)
    print("phase 1 done: %d new results (+%d resumed)"
          % (len(results), len(done)), flush=True)

    all_recs = list(done.values()) + results
    answers = [r for r in all_recs if r["kind"] == "ok"]
    exclusions = [r for r in all_recs if r["kind"] != "ok"]
    print("phase 1: answers=%d  unjudgeable=%d  inconsistent=%d"
          % (len(answers),
             sum(1 for r in exclusions if r["kind"] == "unj"),
             sum(1 for r in exclusions if r["kind"] == "diff")), flush=True)

    # phase 2: policy subset
    policy_cand = [a for a in answers
                   if a["status"] == "play" and side_of(a["fen"]) == "b"]
    print("policy candidates: %d" % len(policy_cand), flush=True)
    chosen_done = set()
    if args.resume and os.path.isfile(PARTIAL + ".policy"):
        for line in open(PARTIAL + ".policy"):
            if line.strip():
                try:
                    chosen_done.add(json.loads(line)["fen"])
                except Exception:
                    pass
    todo_p = [a for a in policy_cand[:args.policy_n]
              if a["fen"] not in chosen_done]
    if todo_p:
        with mp.Pool(args.jobs) as pool:
            moves = pool.map(check_choose, [a["fen"] for a in todo_p])
        for a, mv in zip(todo_p, moves):
            if mv is not None:
                rec = {"fen": a["fen"], "path": a["path"], "move": mv}
                with open(PARTIAL + ".policy", "a") as f:
                    f.write(json.dumps(rec) + "\n")
    chosen = [json.loads(l) for l in open(PARTIAL + ".policy")]
    print("phase 2: policy answers=%d" % len(chosen), flush=True)

    outdir = os.path.join(LAB, "ledger", "sealed")
    os.makedirs(outdir, exist_ok=True)
    out = {"corpus": os.path.abspath(args.corpus),
           "rules": answers, "policy": chosen,
           "exclusions": {
               "unj": sum(1 for r in exclusions if r["kind"] == "unj"),
               "diff": sum(1 for r in exclusions if r["kind"] == "diff")},
           "exclusionItems": exclusions[:50]}
    path = os.path.join(outdir, "answers.json")
    with open(path, "w") as f:
        json.dump(out, f)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    with open(os.path.join(outdir, "seal.sha256"), "w") as f:
        f.write("%s  answers.json\n" % h)
    print("SEALED: %s  sha256=%s" % (path, h))


if __name__ == "__main__":
    main()
