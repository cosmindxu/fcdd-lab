#!/usr/bin/env python3
"""Case 04 — D9 cross-check + final seal.

Joins the two answer sets:
  - referee answers (the MODEL, twin_referee.py)
  - engine answers (the Z80's own, seal_corpus.py partial file)

For each position:
  - model + engine AGREE        -> sealed answer = the model's (both recorded)
  - engine self-inconsistent    -> excluded (C16), reported
  - engine unjudgeable          -> sealed answer = the model's (the model
                                   needs no engine agreement to decide)
  - model unjudgeable           -> excluded, reported
  - model vs engine DISAGREE    -> EXCLUDED from scoring, written to the
                                   bug-inventory file (engine-bug report,
                                   a deliverable of the study)

Outputs: ledger/sealed/answers.json (+ sha256), ledger/sealed/
bug_inventory.json, statistics on stdout.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)


def load_jsonl(path):
    out = {}
    if not os.path.isfile(path):
        return out
    for line in open(path):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            out[r["fen"]] = r
        except Exception:
            pass
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--referee", required=True)
    ap.add_argument("--engine", required=True)
    args = ap.parse_args(argv)

    ref = load_jsonl(args.referee)
    eng = load_jsonl(args.engine)
    print("referee answers: %d   engine answers: %d"
          % (len(ref), len(eng)))

    sealed, bugs, excluded = [], [], []
    n_agree = n_eng_only = n_ref_only = 0
    for fen, r in ref.items():
        e = eng.get(fen)
        if r.get("kind") == "unj":
            excluded.append({"fen": fen, "why": "referee-unjudgeable"})
            continue
        # threefold-repetition draws are history-dependent: the FEN-only
        # submission interface cannot decide them. Their STATUS is not
        # scored (legal set still is). Recorded in the seal.
        rep = bool(r.get("repDraw"))
        if e is None:
            n_ref_only += 1
            sealed.append({"fen": fen, "legal": r["legal"],
                           "status": None if rep else r["status"],
                           "ply": r.get("ply"), "phase": r.get("phase"),
                           "agree": "referee-only", "repDraw": rep})
            continue
        if e.get("kind") != "ok":
            sealed.append({"fen": fen, "legal": r["legal"],
                           "status": None if rep else r["status"],
                           "ply": r.get("ply"), "phase": r.get("phase"),
                           "agree": "engine-unjudgeable", "repDraw": rep})
            continue
        if e["legal"] == r["legal"] and e["status"] == r["status"]:
            n_agree += 1
            sealed.append({"fen": fen, "legal": r["legal"],
                           "status": None if rep else r["status"],
                           "ply": r.get("ply"), "phase": r.get("phase"),
                           "agree": True, "repDraw": rep})
        else:
            bugs.append({"fen": fen, "ply": r.get("ply"),
                         "phase": r.get("phase"),
                         "modelLegal": r["legal"], "modelStatus": r["status"],
                         "engineLegal": e["legal"],
                         "engineStatus": e["status"]})
    for fen, e in eng.items():
        if fen not in ref:
            n_eng_only += 1
            excluded.append({"fen": fen, "why": "no-referee-answer"})

    # policy answers: the ENGINE's own level-1 chosen moves (D12 — the
    # primary outcome's ground truth), from seal_corpus phase 2
    policy = []
    ppath = os.path.join(LAB, "ledger", "sealing_partial.jsonl.policy")
    if os.path.isfile(ppath):
        policy = [json.loads(l) for l in open(ppath) if l.strip()]
    outdir = os.path.join(LAB, "ledger", "sealed")
    os.makedirs(outdir, exist_ok=True)
    out = {"rules": sealed, "policy": policy, "bugs": len(bugs)}
    path = os.path.join(outdir, "answers.json")
    with open(path, "w") as f:
        json.dump(out, f)
    with open(os.path.join(outdir, "bug_inventory.json"), "w") as f:
        json.dump({"count": len(bugs), "items": bugs}, f, indent=1)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    with open(os.path.join(outdir, "seal.sha256"), "w") as f:
        f.write("%s  answers.json\n" % h)

    print("sealed=%d (agree=%d, ref-only=%d, eng-unjudgeable=%d)  "
          "policy=%d  bug-inventory=%d  excluded=%d"
          % (len(sealed), n_agree, n_ref_only,
             sum(1 for s in sealed if s["agree"] == "engine-unjudgeable"),
             len(policy), len(bugs), len(excluded)))
    print("sha256=%s" % h)


if __name__ == "__main__":
    main()
