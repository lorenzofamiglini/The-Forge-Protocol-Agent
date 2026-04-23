# Research Foundation

Forge Protocol is grounded in published cognitive-science and human-AI-interaction research. It is not a prompt pack or an aesthetic choice — it is an opinionated operationalisation of what the literature says actually preserves human skill when working with AI.

## The paper

A full write-up lives at [`docs/forge-protocol-paper.tex`](docs/forge-protocol-paper.tex) (roughly 25 pages). To compile locally:

```bash
# using tectonic (recommended — self-contained)
tectonic docs/forge-protocol-paper.tex

# or pdflatex
cd docs && pdflatex forge-protocol-paper.tex
```

A pre-compiled PDF is provided as a release asset when the repository cuts a release.

## Core theoretical pillars

The paper threads five bodies of research. Skim this table first, then dive into the paper for the derivations.

| Pillar | Primary sources | What Forge Protocol takes from it |
|---|---|---|
| **Generation effect** | Slamecka & Graf (1978); Bertsch et al. (2007) | Self-generated content is remembered and understood better than read content. Forge mode forbids the AI from generating the user's own reasoning. |
| **Desirable difficulties** | Bjork & Bjork (1994, 2011) | Productive struggle improves long-term retention. Mode-level friction is intentional, not accidental UX. |
| **Automation complacency** | Parasuraman & Manzey (2010) | Humans stop verifying AI output after roughly three interactions. The orchestrator's metacognitive checkpoints fire on that schedule. |
| **Bainbridge's ironies** | Bainbridge (1983) | Automating thinking while expecting humans to catch its errors creates a dependency that degrades the skill needed to catch the errors. Canaries measure the degradation. |
| **Deskilling programme** | Cabitza et al. (2024); Wharton/PNAS RCT (2024) | Four types of deskilling — cognitive, semiotic, social, moral. The Wharton RCT found a 17% decline in independent performance after a week of AI use. |

Beyond these, the paper addresses:

- **XAI halo effect** — clear, articulate AI explanations are believed more than they should be. Forge Protocol's "white-box paradox guard" and judicial/contrasting-reads protocol are direct responses.
- **Convergence & homogenisation** — AI-mediated work drifts toward a generic central tendency. The mode-specific forbidden behaviours exist to preserve the user's voice.

## The measurable claim

Most "AI literacy" tools are aspirational. Forge Protocol's central claim is different: **it tracks whether your independent skills are improving or drifting, and gives you the numbers.**

- Fixed canary prompts with stable IDs (`lib/canary.py::CANARY_QUESTIONS`)
- Unassisted responses scored by an independent Claude Sonnet auditor (`lib/auditor.py::score_canary`)
- Stored across weeks in `~/.forge-state/canary_history.json`
- Trend computation in `lib/canary.py::compute_trend` — last score, change vs. previous, mean of last 5, linear slope across attempts

This is the quantifiable piece that separates the protocol from a prompt pattern. If your slope is flat or negative, the framework is failing *you* and you should hear that honestly.

## Open research questions

Places where Forge Protocol is empirically thin — worthwhile projects for students, researchers, or contributors:

1. **Optimal checkpoint interval.** The defaults (Forge=5, Anvil=3, Crucible=4) are educated guesses. A within-subject study comparing intervals against engagement and learning retention would sharpen this.
2. **XAI halo effect under judicial protocol.** Does presenting charitable-and-uncharitable readings actually reduce overconfidence in Anvil critiques? Testable with a small user study.
3. **Self-judgment failure surface for LLMs.** Forge's validator trusts an LLM (or, with the auditor, a second LLM) to judge compliance with natural-language rules. Characterising where this breaks down — prompt types, rule shapes, model families — would be a contribution on its own.
4. **Deskilling recovery curve.** If a user has been heavily in Executor mode, how many Forge-mode sessions with active checkpoints are needed to restore independent performance on the canary set? Longitudinal canary history makes this measurable.
5. **Mode taxonomy gaps.** Is the Forge/Anvil/Crucible/Executor split exhaustive, or are there task types that don't fit cleanly (creative ideation, emotional-labour tasks, simulations)? Propose a fifth mode with evidence.

If you work on any of these, open an issue or PR and link the paper — we'll cite it.

## Cite

If you use Forge Protocol in teaching, research, or a product, a short citation is appreciated:

```
Famiglini, L. (2026). Forge Protocol: A Cognitive-Forcing Interaction Framework for Human-AI Collaboration.
https://github.com/lorenzofamiglini/The-Forge-Protocol-Agent
```
