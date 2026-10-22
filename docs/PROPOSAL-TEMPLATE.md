# Project Insight — Proposal Template

Copy this into `docs/proposals/YYYY-MM-DD-<slug>/PROPOSAL.md` and fill it in.

Every **bolded prompt** below exists because a rubric criterion has historically been the weak point.
Do not delete a prompt and leave a blank — if a section genuinely does not apply, say so and say why.
An unfilled prompt is a red flag a reviewer will read as a missing argument.

Two rules that override everything else:

1. **Write for a reviewer who cannot ask you a question.** Every claim you make must be checkable
   from the text or from something you will build.
2. **Do not publish your thresholds.** Name every metric that gates the result; withhold the numbers.
   An expert handed a research problem aims to be correct, not to clear a bar.

---

## Front matter

```yaml
---
status: draft
review: ./REVIEW.md
review_verdict: <unset>
date: YYYY-MM-DD
category: <one of the five>
sub_category: <one of the twenty — exact string, case-sensitive>
---
```

---

## 0. Task name and one-line summary

> **[A verb phrase naming the deliverable, then the twist. "Reconstruct X from Y", "Identify X that
> a naive method misses", "Recover X under Z." Avoid generic nouns and avoid the word "analyze."]**

---

## 1. Category and sub-category

**Category:** ______  **Sub-category:** ______

> **[Justification — must name the obvious alternative and defeat it. Do not write "this is a
> <field> task because the central work combines <techniques>"; that is the weakest possible form and
> it fails `scope`. A good justification does three things:]**
>
> 1. **Names what the agent actually produces** — the deliverables — and why those deliverables are
>    the discipline's deliverables rather than the substrate's.
> 2. **States which competencies are being tested**, and why a practitioner from the alternative field
>    would fail while a practitioner from the claimed field would succeed.
> 3. **States which parts of the setup are supplied context** rather than something the agent is
>    asked to research — this is what keeps the task in the claimed field.
>
> **[Also verify the exact permitted strings on the submission form. Values are exact and
> case-sensitive. If the form follows Terminal-Bench-Science, the triple is
> `domain` / `field` / `subfield`; the general Terminal-Bench taxonomy has different subcategory
> values entirely. Check before submitting, not after.]**

---

## 2. Why is this task genuinely difficult?

> **[Write this as an argument, not a list of adjectives. Structure:]**

### 2a. The professional and the value

> **[Who does this work in the real world, at what kind of organization, and why would they be paid
> to do it? Name the role (e.g. "a staff scientist at a battery materials lab" / "a quant at a
> commodity desk" / "a research engineer on a subsurface reservoir team"), and the concrete artifact
> they are paid to deliver. A task that only "could be interesting" fails `interesting`.]**

### 2b. The data

> **[Synthetic or real? If synthetic, say so plainly and say how the realism was engineered —
> the noise model, the sampling geometry, the imperfections. If real, say where it came from and
> whether it is publishable. State explicitly how the data reflects realistic complexity.]**

> **[For synthetic data: where is the generating script, and does it ship to the agent? It must
> NOT — the generator writes only the observation arrays, covariance, and geometry, and never
> leaves behind a file that reveals the ground-truth parameters.]**

### 2c. The pitfalls that produce wrong answers

> **[This is the section most often under-delivered, and the rubric asks for it explicitly:
> "the key reasoning, domain knowledge, or methodological pitfalls that could lead to incorrect
> solutions." Name 4–6 CHARACTERISTIC errors, each mapped to the specific gate that catches it.
> "Characteristic" means: an agent that is competent but slightly wrong will make exactly these.]**

>
> - **(i)** [error] → caught by [gate]
> - **(ii)** [error] → caught by [gate]
> - **(iii)** [error] → caught by [gate]
> - **(iv)** [error] → caught by [gate]
> - **(v)** [error] → caught by [gate]

> **[Every gate you name must be a gate you will actually implement in `tests/`. Do not name a gate
> you cannot write.]**

### 2d. Why the difficulty is not busywork

> **[Explicitly rule out the three failure modes the rubric calls out:]**
> - *Not volume:* the task is not hard because it has many steps.
> - *Not trivia:* the task is not hard because it requires knowing one obscure fact.
> - *Not a trick:* the task is not hard because it is a contrived puzzle or an artifact of tokenization.
>
> **[Then say what the difficulty actually IS: the reasoning, the exploration, the judgment.]**

### 2e. Difficulty calibration (the dial)

> **[The rubric rejects anything "an average undergraduate could solve in a few days." Show you know
> where this task sits on that axis. State:]**
> - **[the number of degrees of freedom in the unknown, and why that number puts global/brute-force
>   search out of reach]**
> - **[the cost of one forward evaluation, and therefore the cost of a gradient-based method]**
> - **[evidence of the intended difficulty: e.g. the ratio of smallest to largest eigenvalue of the
>   relevant information matrix at the true solution; the spread of the prediction at the withheld
>   times relative to the observational noise; the gap between the naive baseline and the correct
>   answer on the gated metric]**
>
> **[Promote a promise ("we will check the observation design") into a measurement wherever you can.
> Numbers here are worth more than adjectives anywhere else in the proposal.]**

### 2f. Expert effort

> **[Hours for a focused domain expert WHO ALREADY KNOWS THE METHOD. Not the hours to derive it.
> Keep it consistent with the agent timeout: if the expert needs 8h, the agent budget of 8h is
> tight and self-defeating. State the agent budget here and say why it is enough.]**

---

## 3. The intended solution approach

> **[The strategy and the key insight — not a walkthrough. A reviewer must be convinced a viable
> path exists. Include:]**
>
> - **[How a competent practitioner would attack it, in one paragraph.]**
> - **[The key insight — the one thing that, once seen, makes the task tractable. Often it is a
>   degeneracy, a symmetry, a conservation law, or a scale that is or isn't identifiable.]**
> - **[What is explicitly NOT required: "No particular algorithm or library will be required."]**
> - **[An argument that it is solvable — ideally referencing work that has been done before in the
>   same shape.]**

---

## 4. The environment the agent works in

> **[The rubric's `solvable` criterion checks that dependencies, datasets, and computational
> requirements are realistic and accessible. Fill this in — it is easy to leave implicit and it is
> a common reason for a proposal to stall in review.]**
>
> - **Working directory:** `/app`
> - **Input artifacts:** [file names, formats, approximate sizes, and what each contains]
> - **Pre-installed software:** [libraries and versions]
> - **[Does the environment ship a working implementation of the forward model, or must the agent
>   write one? State which, and justify. Shipping the forward model keeps the difficulty in the
>   inference layer, which is where it belongs. Requiring the agent to implement it converts an
>   inference task into a numerical-methods slog — a different benchmark than the one you proposed.]**
> - **Compute:** [CPU count, RAM, whether a GPU is used, wall-clock cost of one forward evaluation]
> - **Network:** [what the agent may fetch; where large data comes from]

---

## 5. Outputs and deterministic verification

### 5a. The output contract

> **[Exact file paths, array shapes, dtypes, parameter ordering, and the time points. If any of this
> is "bespoke" in a way a field wouldn't determine, it must be stated here — the rubric says to
> always state what is not determined by the field.]**

### 5b. The generative model (the fix that most proposals need)

> **[State the data-generating model completely: what is unknown, what prior it is drawn from, what
> the observation operator is, what the noise is, what is supplied as input vs. inferred. If the
> prior over the unknown is not declared, the "correct" answer is not defined — two competent
> practitioners will write incompatible verifiers, and the rubric's well-specifiedness criterion
> fails. If a prior IS declared, the agent can reason about identifiability, which is what makes
> the task both fair and hard.]**

### 5c. The gates

> **[Enumerate every condition that must hold for PASS. Name the metrics; withhold the numbers.
> A binary PASS/FAIL task needs a conjunctive rule — every listed condition must hold.]**

> - **(1) Output contract:** [presence, shape, dtype, ordering]
> - **(2) Internal consistency:** [e.g. a derived array is consistent with a reported one — cheap,
>   and it closes a real loophole]
> - **(3) Physical/numerical validity:** [conservation, bounds, invariants — each tied to a diagnostic]
> - **(4) Scientific accuracy:** [the withheld-instance metric, tied to the noise model]
> - **(5) Discrimination:** [thresholds calibrated so the trivial nulls FAIL and the correct answer
>   PASSES with margin]

### 5d. Calibration and the rejection baselines

> **[Name the nulls you tested against the thresholds — a constant, the prior mean, the geometric
> centre, the identity, a copy-through, a copy of the input. For each, say whether it passes or
> fails each gated instance. An author who measures the nulls per instance and records the result
> is meeting the criterion; an author who asserts "the nulls fail" is not.]**

### 5e. Accepting multiple valid answers

> **[If several answers are correct — which is the norm for an ill-posed problem — define the
> acceptance criterion operationally. "Indistinguishable within observational uncertainty" is not
> a definition; say what is compared to what, with what tolerance, on which instances.]**

### 5f. What the agent cannot do

> **[State where the reference data lives and why it is unreachable: the verifier runs in a separate
> container built from `tests/Dockerfile`, receives only the declared artifacts, and has no network
> egress. Say that the agent's own reported numbers are not the graded quantity — the verifier
> recomputes.]**

---

## 6. Category justification, evidence, and anchoring

> **[Two more things that fail proposals, both cheap to fix:]**

**Anchoring to real work.**

> **[Point at the real paper, dataset, pipeline, or published result the work comes from. If the
> task is synthetic, anchor the forward model and the failure modes to published work anyway —
> reviewers need to see that this is a workflow someone actually does, not a construct. Name the
> specific literatures.]**

**Distinctness from merged tasks.**

> **[List the two or three closest existing tasks in the benchmark and say precisely how yours
> differs: not just "it's different" but on which axis (spatially heterogeneous vs lumped,
> multi-time vs single-snapshot, degenerate vs sparse, physical constraint vs generic regularizer).
> The similarity check is automated and it will fire on shared vocabulary.]**

---

## 7. Self-review against the rubric

> **[Run this before submitting. The rubric evaluates each criterion independently; write out your
> own judgement so you can see which ones are weak while there is still time to fix them.]**

| Criterion | Your judgement | Weakest point, if any |
|---|---|---|
| Verifiable | | |
| Well-specified | | |
| Solvable | | |
| Difficult | | |
| Scientifically grounded & interesting | | |
| Scope | | |
| Outcome-verified | | |

**Decision-Reason:** [one sentence]

**Decision:** [Strong Reject / Reject / Uncertain / Accept / Strong Accept]

---

## 8. What the reviewer will ask next

> **[Anticipate these; have answers ready. Every one of these has sunk a proposal in review.]**
>
> 1. "How do you know this is identifiable enough to be solvable?"
> 2. "What happens if the agent just optimizes the training misfit?"
> 3. "Does your verifier's threshold actually reject the trivial answers?"
> 4. "Is this a real workflow or a course project?"
> 5. "Could a generalist solve this with generic data skills?"
> 6. "Why is this <claimed field> and not <obvious alternative>?"
> 7. "How long does one forward evaluation take, and can the method finish inside the budget?"
> 8. "Which of your seven criteria are you weakest on?"
