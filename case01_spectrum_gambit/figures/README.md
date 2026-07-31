# Figures

## `fcdd_process` — the process encoded in the formal-contract-dev skill

Source: `fcdd_process.mmd` (Mermaid). Rendered: `fcdd_process.png` (1984×1120,
raster for slides) and `fcdd_process.svg` (vector, preferred for the article).

Drawn **from** `~/.claude/skills/formal-contract-dev/SKILL.md` — the method as
actually encoded and executed by Arm B in this case, not a stylised account.
Every box traces to a numbered step or law in that file.

### Draft caption

> **Figure 1 — Formal Contract-Driven Development as executed by Arm B.**
> The method is a lifecycle of four "beats" plus two interposed honesty
> stages. Phase ① is entirely offline and pure: Beat 1 formalises the safety
> properties as a *spec of record* in a kernel-checked prover, admitting no
> unproven obligations; Beat 2 produces a pure implementation ("twin") that
> must agree with the spec clause for clause, obtained either by transcription
> or by verified extraction; Beat 3 builds the conformance suite that ties the
> shipped twin to the proved facts — which *samples* agreement and is
> explicitly not a refinement proof. Phase ② admits the environment for the
> first time: the shell is the only impure layer, and it publishes a
> falsifiability tiering so that the strength of each claim matches what its
> evidence can actually refute, after which the system is replayed against
> real history including its motivating incident. Phase ③ is adversarial:
> independent reviewers with deliberately distinct lenses attempt to break the
> package, proving findings by execution; the system then ships and continues
> to be judged in operation. Dotted edges are repair loops — a finding is
> fixed at the layer that caused it, never by patching the test. The heavy
> edge is the closure that makes it a lifecycle rather than a pipeline: a real
> incident becomes a new theorem in Beat 1. The two side panels state the
> method's cross-cutting laws and, as importantly, its residuals: FCDD
> establishes coherence, never correctness of intent, and its bridge cannot
> detect a common-mode error in which one author's misconception is shared by
> spec and twin alike.

### Regenerating

The Mermaid CLI needs a browser; the bundled download fails in this VM, so
point it at the system Chrome and disable the sandbox:

```sh
echo '{"args":["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage"]}' > /tmp/pptr.json
PUPPETEER_EXECUTABLE_PATH=/opt/google/chrome/chrome \
  npx -y @mermaid-js/mermaid-cli -i fcdd_process.mmd -o fcdd_process.svg \
  -b transparent -p /tmp/pptr.json
```

### Known layout note

Phases render bottom-to-top (① lowest) because the lifecycle-closing edge
(OPERATE → Beat 1) outranks layout hints; invisible rank links were tried and
do not override it. The circled phase numbers carry the reading order. If the
article needs strict top-down flow, redraw in TikZ — the Mermaid source is the
specification of content, not the final typesetting.
