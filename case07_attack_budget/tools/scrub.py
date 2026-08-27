#!/usr/bin/env python3
"""Build a scrubbed copy of the subject tree, and ASSERT the result.

Round 3 B1/B2: the manifest was prose. Its `docs/REVIEW_*.md` glob matched zero
files while 64 review documents sat in planning/, and the live account id
survived in 51 files. Nothing checked, because nothing ran. This runs.

Exit non-zero if any assertion fails: no cell is built from a tree that has not
passed.
"""
import os, re, shutil, subprocess, sys

SRC = "/media/sf_Projects/ikbr_tools"
DST = sys.argv[1] if len(sys.argv) > 1 else "/tmp/c07_scrubbed"

# whole trees/files removed — reason recorded per entry
REMOVE = {
    "gateway": "live-connection scripts",
    "packaging": "deployment credentials + account id",
    ".git": "full defect history — a rediscovery answer key",
    "planning": "64 review/audit/incident documents naming every unit (round 3 B1)",
    "docs": "architecture + review material, same reason",
    "env.sh": "evals the ib_creds vault",
    "CHANGELOG.md": "dated defect list",
    # round 3 follow-on, found by this script's own assertion: built packages are
    # an ARCHIVED COPY of everything above — removing source paths while a .deb
    # of those paths survives is no removal at all.
    "dist": "built .deb packages carrying the whole pre-scrub tree + account id",
    # found by the assertion: the tree ships its own reviewer tooling and a
    # backtest log. .opencode/ would hand a cell a prior adversarial-review agent
    # definition and a review-loop command — the study's own treatment, pre-cooked.
    ".opencode": "prior adversarial-reviewer agent + review-loop command",
    "BACKTEST_LOG.md": "dated defect/finding log",
}
ARCHIVE_EXT = {".deb", ".tar", ".gz", ".tgz", ".zip", ".whl", ".rpm"}
# secrets redacted in place, by PATTERN not by hand-listed file (round 3 B2)
REDACT = [
    (re.compile(rb"\b[UD]{1,2}\d{6,9}\b"), b"ACCT_REDACTED"),
]
TEXT_EXT = {".py", ".md", ".yaml", ".yml", ".txt", ".sh", ".json", ".cfg", ".ini", ".toml", ".service", ".cron"}


def main():
    if os.path.exists(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".venv"))
    removed = []
    for name, why in REMOVE.items():
        p = os.path.join(DST, name)
        if os.path.isdir(p):
            shutil.rmtree(p); removed.append((name + "/", why))
        elif os.path.exists(p):
            os.remove(p); removed.append((name, why))

    # any stray archive anywhere is a scrub bypass
    for root, _d, files in os.walk(DST):
        for f in files:
            if os.path.splitext(f)[1].lower() in ARCHIVE_EXT:
                os.remove(os.path.join(root, f)); removed.append((f, "archive — scrub bypass"))

    # Retained documentation that MENTIONS prior review findings: redact the lines,
    # keep the file. Deleting a project README changes what the system tells a
    # reviewer about itself; leaving "an adversarial-review tranche found three X"
    # hands over an answer. Line-level redaction is the honest middle.
    for root, _d, files in os.walk(DST):
        for f in files:
            if not f.endswith(".md"):
                continue
            p_ = os.path.join(root, f)
            lines = open(p_, errors="ignore").read().splitlines(True)
            keep = [("[line redacted — prior-review reference, case07 scrub]\n"
                     if re.search(r"adversarial.review", l, re.I) else l) for l in lines]
            if keep != lines:
                open(p_, "w").write("".join(keep)); removed.append((f + " (lines)", "prior-review references"))

    redacted = 0
    for root, _d, files in os.walk(DST):
        for f in files:
            p = os.path.join(root, f)
            if os.path.splitext(f)[1].lower() not in TEXT_EXT:
                continue
            try:
                b = open(p, "rb").read()
            except OSError:
                continue
            nb = b
            for pat, rep in REDACT:
                nb = pat.sub(rep, nb)
            if nb != b:
                open(p, "wb").write(nb); redacted += 1

    print("REMOVED"); [print(f"  {n:<16} {w}") for n, w in removed]
    print(f"REDACTED in {redacted} files\n")

    # --- assertions: the build fails rather than warns
    fails = []
    hits = subprocess.run(["grep", "-rlE", r"\b[UD]{1,2}[0-9]{6,9}\b", DST],
                          capture_output=True, text=True).stdout.strip()
    if hits:
        fails.append(f"account-id pattern survives in {len(hits.splitlines())} files")
    for forbidden in ("gateway", "planning", "docs", ".git", "env.sh"):
        if os.path.exists(os.path.join(DST, forbidden)):
            fails.append(f"{forbidden} still present")
    # the review corpus must be gone
    # in-code incident references (the R18 incident theorems, their tests) are part
    # of the SYSTEM and must stay — removing them would change the code under review.
    # They are answer-key-ish for the hardened stratum, and the widened rediscovery
    # rule (scrub_manifest §"Rediscovery") is what handles them. The assertion
    # therefore targets DOCUMENT-shaped review material only.
    rev = subprocess.run(["bash", "-c",
                          f"grep -rl -iE 'adversarial.review' {DST} --include='*.md' 2>/dev/null | wc -l"],
                         capture_output=True, text=True).stdout.strip()
    if rev != "0":
        fails.append(f"{rev} markdown files still carry adversarial-review material")
    if os.path.exists(os.path.expanduser("~/.config/ikbr_tools")):
        print("  NOTE: operator vault exists at ~/.config/ikbr_tools — cells must not see $HOME")

    if fails:
        print("ASSERTIONS FAILED:"); [print("  ✗ " + f) for f in fails]
        sys.exit(1)
    n = sum(len(fs) for _r, _d, fs in os.walk(DST))
    print(f"ASSERTIONS PASSED — scrubbed tree at {DST} ({n} files)")


if __name__ == "__main__":
    main()
