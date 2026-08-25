#!/usr/bin/env python3
"""Case 04 — scorer. Runs a submission binary against the sealed oracle
answers (orchestrator-side only; the sealed file never enters a workspace).

    score_case04.py --binary /path/to/chess_clone [--out results.json]

Outputs per-run: rules-layer defect mass mu1 (position-level, primary),
move-level mass, policy mass mu2, status-only and legal-only divergences
(the misalignment taxonomy), completion statistics.
"""
import argparse
import json
import subprocess
import sys

TIMEOUT_LEGAL = 60
TIMEOUT_CHOOSE = 300
STATUSES = {"play", "white-mated", "black-mated", "stalemate",
            "draw", "flag-fall"}


def run_cmd(binary, cmd, fen, timeout):
    try:
        r = subprocess.run([binary, cmd, "--fen", fen],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except Exception as e:
        return None, "crash: %s" % e
    if r.returncode != 0:
        return None, "exit %d" % r.returncode
    return r.stdout, None


def parse_legal(out):
    moves = set()
    for line in out.splitlines():
        mv = line.strip().lower()
        if len(mv) in (4, 5):
            moves.add(mv)
    return moves


def score_rules(binary, answers):
    n, n_div, n_move_div = 0, 0, 0
    legal_div = status_div = timeout_cnt = parse_cnt = 0
    move_total = oracle_total = 0
    for a in answers:
        n += 1
        out, err = run_cmd(binary, "legal", a["fen"], TIMEOUT_LEGAL)
        if err:
            timeout_cnt += 1
            n_div += 1
            legal_div += 1
            n_move_div += 1
            move_total += 1
            oracle_total += len(a["legal"])
            continue
        got = parse_legal(out)
        oracle = set(a["legal"])
        move_total += len(got)
        oracle_total += len(oracle)
        if got != oracle:
            n_div += 1
            legal_div += 1
            n_move_div += 1
            extra = len(got - oracle) + len(oracle - got)
            move_total += extra
            oracle_total += extra
        if a.get("status") is None:      # history-dependent draw (repDraw)
            continue                    # status not scored on this position
        out, err = run_cmd(binary, "status", a["fen"], TIMEOUT_LEGAL)
        if err or out.strip() not in STATUSES:
            parse_cnt += 1
            if not err:
                n_div += 1
                status_div += 1
            continue
        if out.strip() != a["status"]:
            n_div += 1
            status_div += 1
    return {
        "n": n, "mu1": n_div / n if n else None,
        "moveMass": n_move_div / move_total if move_total else None,
        "legalDiv": legal_div, "statusDiv": status_div,
        "timeouts": timeout_cnt, "statusParseFail": parse_cnt,
        "moveMassSym": None}


def score_policy(binary, policy):
    n = agree = 0
    for p in policy:
        n += 1
        out, err = run_cmd(binary, "choose", p["fen"], TIMEOUT_CHOOSE)
        if not err:
            mv = out.strip().lower()
            if mv == p["move"]:
                agree += 1
    return {"n": n, "mu2": 1 - agree / n if n else None, "agree": agree}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--sealed", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    sealed = json.load(open(args.sealed))
    # D12: policy (choose agreement with the ENGINE) is the PRIMARY;
    # rules (vs the model referee) is the co-requisite gate.
    policy = score_policy(args.binary, sealed["policy"])
    rules = score_rules(args.binary, sealed["rules"])
    result = {"primary": {"mu2": policy["mu2"], "n": policy["n"],
                          "agree": policy["agree"]},
              "rules": rules}
    print(json.dumps(result, indent=1))
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
