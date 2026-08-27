#!/usr/bin/env python3
"""Saturation probe — the admission gate of method/SUBJECT_SELECTION.md §3.

For each candidate subject, ask the model to resolve a genuinely underdetermined
point WITH NO SPECIFICATION GIVEN, k times. If the runs agree, the resolution is
in the weights: no contract can be shown to narrow what priors already narrowed,
and the subject is DISQUALIFIED.

DIRECTION OF EVIDENCE (stated because it bounds every conclusion here): a small
model can only DISQUALIFY. Agreement at this tier is strong evidence of
saturation. Disagreement does NOT clear a candidate — a larger pinned model may
hold the resolution this one lacks. Re-probe survivors at the study's pinned tier.
"""
import json, subprocess, sys, collections, os
from concurrent.futures import ThreadPoolExecutor

MODEL = os.environ.get("PROBE_MODEL", "claude-haiku-4-5-20251001")
K = int(os.environ.get("PROBE_K", "5"))

CANDIDATES = {
    "chess (incumbent)": [
        ("ep-in-repetition-key",
         "In chess threefold repetition, are two positions considered the SAME when they "
         "differ only in an en passant square that could not legally be captured anyway? "
         "Reply with exactly one word: SAME or DIFFERENT."),
        ("same-colour-bishops",
         "In chess, King+Bishop vs King+Bishop with both bishops on the same colour squares: "
         "is this an immediate automatic draw by insufficient material under FIDE? "
         "Reply with exactly one word: YES or NO."),
    ],
    "HTTP caching (RFC 9111)": [
        ("expires-vs-maxage",
         "Per RFC 9111, when a response carries BOTH an Expires header and "
         "Cache-Control: max-age, which one determines freshness? "
         "Reply with exactly one word: EXPIRES or MAXAGE."),
        ("heuristic-on-404",
         "Per RFC 9111, may a cache apply heuristic freshness to a 404 response that has no "
         "explicit freshness information? Reply with exactly one word: YES or NO."),
    ],
    "pax/tar archive format": [
        ("pax-vs-gnu-longname",
         "In a tar archive where BOTH a pax extended header and a GNU long-name header supply "
         "a path for the same entry, which path should an extractor use? "
         "Reply with exactly one word: PAX or GNU."),
        ("pax-size-vs-ustar",
         "In a tar entry with a pax extended header 'size' record AND a ustar size field that "
         "disagree, which size wins? Reply with exactly one word: PAX or USTAR."),
    ],
    "ISO 8601 / calendar arithmetic": [
        ("month-end-add",
         "Adding a duration of exactly one month (P1M) to 2026-01-31: what is the resulting "
         "date? Reply with exactly one date in YYYY-MM-DD form and nothing else."),
        ("duration-order",
         "When adding P1M1D to a date, is the month component applied before the day component? "
         "Reply with exactly one word: MONTH-FIRST or DAY-FIRST."),
    ],
    "financial day-count (money path)": [
        ("30-360-end-rule",
         "Under the 30/360 US (Bond Basis) day-count convention, when the start date is the "
         "31st of a month, is the start day changed to 30 before computing days? "
         "Reply with exactly one word: YES or NO."),
        ("act-365-leap",
         "Under ACT/365 Fixed, when an accrual period spans 29 February, is the denominator "
         "still 365? Reply with exactly one word: YES or NO."),
    ],
}


def ask(prompt):
    r = subprocess.run(["claude", "-p", prompt, "--model", MODEL],
                       capture_output=True, text=True, timeout=180)
    return " ".join(r.stdout.strip().split())[:60] if r.returncode == 0 else None


def main():
    rows = []
    jobs = [(s_, q_, p_) for s_, qs_ in CANDIDATES.items() for q_, p_ in qs_]
    for subject, qid, prompt in jobs:
        if True:
            with ThreadPoolExecutor(max_workers=K) as ex:
                answers = [a for a in ex.map(lambda _: ask(prompt), range(K)) if a]
            if not answers:
                rows.append((subject, qid, 0, 0.0, "NO RESPONSE"))
                continue
            c = collections.Counter(a.upper() for a in answers)
            top, n = c.most_common(1)[0]
            rows.append((subject, qid, len(c), n / len(answers), top))
            print(f"  {subject:<32} {qid:<22} {n}/{len(answers)} agree -> {top[:34]}", flush=True)

    print("\n=== SATURATION PROBE ===")
    print(f"model {MODEL}, k={K}. Agreement = share of runs giving the modal answer,")
    print("with NO specification supplied.\n")
    print(f"{'candidate subject':<34}{'agreement':>11}   verdict")
    print("-" * 72)
    by_subj = collections.defaultdict(list)
    for s, q, dis, agree, top in rows:
        by_subj[s].append(agree)
    out = {}
    for s, aa in by_subj.items():
        m = sum(aa) / len(aa)
        verdict = ("DISQUALIFIED — resolution is in the weights" if m >= 0.9 else
                   "screened out — largely saturated" if m >= 0.7 else
                   "SURVIVES this screen (not cleared — see header)")
        out[s] = {"mean_agreement": round(m, 2), "verdict": verdict}
        print(f"{s:<34}{m:>10.0%}   {verdict}")
    dst = os.path.join(os.path.dirname(__file__), "probe_result.json")
    json.dump({"model": MODEL, "k": K, "per_question": rows, "per_subject": out},
              open(dst, "w"), indent=1)
    print(f"\nwritten: {dst}")


if __name__ == "__main__":
    main()
