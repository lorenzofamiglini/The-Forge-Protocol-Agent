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

The paper threads several bodies of research. Skim this table, then dive into the paper for the derivations.

| Pillar | Primary sources | What Forge Protocol takes from it |
|---|---|---|
| **Generation effect** | Slamecka & Graf (1978); Bertsch et al. (2007) | Self-generated content is remembered and understood better than read content. Forge mode forbids the AI from generating the user's own reasoning. |
| **Desirable difficulties** | Bjork & Bjork (1994, 2011) | Productive struggle improves long-term retention. Mode-level friction is intentional, not accidental UX. |
| **Automation complacency** | Parasuraman & Manzey (2010) | Humans stop verifying AI output after roughly three interactions. The orchestrator's metacognitive checkpoints fire on that schedule. |
| **Bainbridge's ironies** | Bainbridge (1983) | Automating thinking while expecting humans to catch its errors creates a dependency that degrades the skill needed to catch the errors. Canaries measure the degradation. |
| **Deskilling programme** | Cabitza et al. (2017, 2024); Natali et al. (2025); Wharton/PNAS RCT (2024) | Four types of deskilling — cognitive, semiotic, social, moral. The Wharton RCT found a 17% decline in independent performance after a week of AI use. |

## The Cabitza lab contribution (central)

The four modes are not arbitrary. They map directly onto patterns validated in the human-AI collaboration research programme run by Federico Cabitza and colleagues at the University of Milano-Bicocca, with contributions from Lorenzo Famiglini (maintainer of this project) on explainability design.

| Forge mode | Protocol | Key paper | What it's designed to prevent |
|---|---|---|---|
| **Forge** | Judicial AI paradigm | Cabitza et al. 2025, *Judicial Protocols in Diagnostic AI* | Oracular consultation — single-verdict outputs collapse the decision space |
| **Anvil** | Hounds protocol (human-first) | Cabitza et al. 2023, *Rams, hounds and white boxes*, Artificial Intelligence in Medicine | Anchoring to AI output (Rams). Preserved independent judgment empirically across 12 radiologists + 44 ECG readers. |
| **Anvil** (max-rigor option) | Displacement protocol | Cabitza et al. 2025, *Five Degrees of Separation* | Reaches 87–89% accuracy across radiology, ECG, endoscopy — outperforms AI-first and human-first alone |
| **Crucible** | Frictional AI + Programmed Inefficiencies | Cabitza et al. 2024, *Frictional AI*; Cabitza et al. 2019 | Premature convergence; automatic reliance on plausible-sounding AI output |
| **Crucible** guard | Epistemic sclerosis | Natali, Marconi, Dias Duran, Miglioretti & Cabitza 2025 | Rigidification of knowledge processes when AI is blindly trusted |
| **Executor** | Rams protocol (AI-first) | Cabitza et al. 2023 | Acceptable ONLY for mechanical tasks; causes anchoring when judgment is at stake |
| All thinking modes | White-box paradox guard | Cabitza et al. 2024, *Never Tell Me the Odds* (xAI 2024 Best Paper) | XAI halo effect — articulate explanations increase uncritical acceptance |
| All thinking modes | OMA — Open, Multiple, Adjunct | Cabitza et al. 2022 | Outputs stay supportive and plural, never authoritative |

### Famiglini lab contributions (this project's maintainer)

Specific mechanisms drawn from Lorenzo Famiglini's co-authored work at Milano-Bicocca:

- **Pro-hoc explanations** (Famiglini et al. 2024, *Never tell me the odds*, Artificial Intelligence in Medicine, Vol. 150): explanations delivered AFTER the user commits — not before — prevent anchoring. Implemented as the "commit before consult" rule across all thinking modes.
- **Contrasting evidence via Class Activation Maps** (Famiglini et al., CD-MAKE 2022 *Color shadows*; Alternative CAM strategies, 2024): presenting evidence for BOTH positive and negative predictions forces active adjudication. Operationalised in Forge's judicial protocol and Anvil's contrasting-reads.
- **Evidence-based XAI design framework** (Famiglini et al., ResearchGate preprint 377964086): explanations are evaluated on understandability and clinical relevance, not just plausibility. The rating dimensions in Anvil (clarity, precision, structure, tone, persuasiveness, concision) apply the same evaluation-before-acceptance principle to writing.
- **Conformal prediction for clinical decision support** (Famiglini et al. 2025, ECG interpretation): uncertainty quantification forces clinicians to commit before consulting AI. Adapted here as the "state your confidence, then I'll challenge it" mechanic in Forge and Crucible.

Beyond these, the paper addresses:

- **XAI halo effect** — Cabitza et al. 2024's finding that articulate AI explanations are accepted MORE uncritically, not less. Every thinking-mode soul contains an explicit guard.
- **Convergence & homogenisation** — AI-mediated work drifts toward a generic central tendency (Doshi & Hauser 2024; Cabitza's *epistemic sclerosis*). The mode-specific forbidden behaviours and divergence-check metacognitive prompts are direct responses.

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
