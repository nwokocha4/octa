# Proposal Review — "Reconstruct heterogeneous mobility from incomplete phase-separation measurements"

**Reviewed against:** TB-Science task-proposal rubric (`rubrics/task-proposal.md`, 7 criteria)
**Category claimed:** Science / Applied Mathematics
**Verdict:** **Accept** — with four substantive fixes that would move it to Strong Accept.

---

## 0. Re-statement

The agent receives a synthetic dataset from a binary-mixture Cahn–Hilliard (CH) simulation: an initial
concentration field, sparse noisy concentration measurements at several early times, a measurement-noise
covariance, domain geometry, boundary conditions, and a declared finite-dimensional parameterization of a
spatially varying, positive mobility field. It must infer the mobility field, produce withheld-time
predictions of phase separation, and report three diagnostics. A separate verifier re-simulates the
submitted mobility and grades against withheld observations, with a tolerance anchored to the supplied
noise covariance.

---

## 1. Criterion-by-criterion

### Verifiable — **Accept**
**For:** Outputs are concrete and typed (`.npz` arrays, `.json` scalars). The verifier's job is
well-defined: re-simulate M, compare against withheld truth, recompute diagnostics. Binary PASS/FAIL
maps cleanly onto Harbor's reward file. The three named diagnostics (weighted misfit, mass drift, energy
balance) are *scientific* checks, not formatting checks — that is the right instinct, and it is exactly
what `functional_verification` and `graded_instances_discriminate` want.
**Against:** "Independently simulate the submitted mobility" means the verifier container runs a PDE
solver. That is a reproducibility risk (floating-point sensitivity of a 4th-order PDE solve, pinned
versions, machine differences) *and* a threshold-calibration risk (if the threshold is tight, solver
noise flips the grade). It also conflicts with "reported numbers cannot substitute for independently
verified fields" only partially: if the verifier recomputes the diagnostics, the agent's reported
diagnostics are decorative unless compared within a stated tolerance.
**Judgement:** Accept.

### Well-specified — **Uncertain** *(the weakest criterion)*
**For:** The proposal names the gating metrics and explicitly refuses to publish thresholds, which is
exactly what the rubric asks. The structure — supplied data → declared representation → named outputs →
named diagnostics — is right.
**Against — and these are concrete:**
- **The generative model is not declared.** There is no prior over the mobility field (is it
  log-normal? a truncated Gaussian field with a stated spatial covariance? smooth? how smooth?). If the
  data-generating prior is not given, the *correct* reconstruction is not defined and the agent must
  invent a regularizer. Different defensible regularizers give materially different mobilities — this is
  the "two defensible conventions" failure the rubric names explicitly.
- **The observation model is under-specified.** Correlated noise with a supplied covariance is good, but
  the proposal doesn't say whether the covariance is per-time or pooled across times, whether the
  weighting is Σ⁻¹ (full) or diagonal (ignoring off-diagonals), whether the misfit is per-time
  χ²-summed or max, or normalized by dof. A factor-of-N ambiguity here flips the pass/fail.
- **`weighted_observation_misfit`, `relative_mass_drift`, `energy_balance_residual` have no
  definitions.** Relative to what baseline? Signed or absolute? What functional f(c) and κ? What
  spatial/temporal norm? "Diagnostic definitions will be specified with the input artifacts" is a
  deferral; the rubric judges the proposal, and the *instruction* must be executable.
- **The governing equation is never written down.** ∇·(M∇μ) vs M∇²μ, μ = f'(c) − κ∇²c, no-flux BCs,
  the exact double-well form and its coefficients, nondimensional vs physical units, 2D vs 3D, grid size.
- **"A declared finite-dimensional representation of positive mobility"** — how many degrees of freedom?
  This number *is* the difficulty dial (see §3) and it is unspecified.
**Judgement:** Uncertain — fixable, but currently a reviewer would flag it.

### Solvable — **Accept**
**For:** A forward model is well defined, a reference solution is constructible, and the inference
problem is a standard (if hard) regularized nonlinear inverse problem. Datasets are synthetic and
self-contained, so no dependency risk.
**Against:** The proposal does not state the **cost of one forward simulation**, which is the binding
constraint on solvability. A 4th-order PDE solve on a 256² grid costs ~seconds-to-minutes; on a
1024² grid it is minutes-to-hours. Gradient-based inversion needs O(K)–O(2K) solves per iteration over
tens of iterations. If K is large and the solve is slow, the task is *unsolvable in the 8-hour agent
budget*, not hard. The proposal also never states **whether the environment ships a solver** — that
decides whether the task is an inference problem or a numerical-methods implementation slog.
**Judgement:** Accept — conditional on the forward-solve cost and solver availability being pinned.

### Difficult — **Uncertain**
**For:** The core scientific idea is genuinely good and genuinely research-level: separating mobility
variations *supported by* observations from those that merely fit noise. This is real inverse-problem
science, not a dressed-up exercise. The multi-time structure (early observations → later predictions)
gives the task its discriminating power: an overfit reconstruction fits early data and diverges later.
**Against — the two ways this task fails:**
1. **Brute force erases the difficulty.** If the mobility has few degrees of freedom (K ≈ 3) and each
   forward solve is cheap, global optimization (differential evolution / multi-start) recovers the
   maximum-likelihood point estimate without any identifiability reasoning. The whole intellectual
   content evaporates. This is the single most likely way the task fails to be hard.
2. **The difficulty is only weakly coupled to the graded outputs.** The narrative is about identifiability
   and uncertainty, but the outputs are point estimates + three diagnostics + predictions. Nothing
   requires the agent to *reason about* identifiability — only to find an estimator that happens to
   predict well. With a declared prior and MAP estimation, the hard part becomes "implement a nonlinear
   Bayesian inverse problem with spatial priors and correlated-noise likelihood," which is still real work,
   but it should be named rather than implied.
**Judgement:** Uncertain — the idea is strong; the difficulty knob is unset.

### Scientifically Grounded & Interesting — **Accept**
**For:** Phase-field modeling of binary mixtures is a real research area; inferring transport properties
from in-situ imaging is a real job (materials informatics, catalysis, polymer blends, emulsion and
foam rheology, battery electrode microstructure). Correlated measurement noise and uneven sensor
coverage arising from imaging (PSF-blur correlation, illumination/occlusion) is a genuine realism, not
decoration. The work is not generic ETL — it requires judgment about regularization, identifiability,
and physical consistency.
**Against:** The rubric asks you to point to the real paper/pipeline. The proposal gestures at
"realistic limitations" without anchoring. A reviewer cannot tell whether this is a real workflow or a
nice synthetic construct.
**Judgement:** Accept.

### Scope — **Uncertain**
**For:** The *work* — nonlinear PDE coefficient inference, ill-posedness, identifiability, uncertainty —
is squarely applied mathematics. The rubric judges the work, and applied mathematics is a covered field.
**Against:** The *subject* is binary-mixture phase separation, which a Materials Science or Chemical
Engineering reviewer will recognize as their own turf. The current justification paragraph is one
sentence, generic, and does not defend against that reading. The rubric says: *an in-scope method
applied to an out-of-scope subject is still out of scope* — here the risk isn't the method, it's that
the task presents itself as a physical-materials problem. Also: **check the exact permitted sub-category
strings.** Under the general Terminal-Bench taxonomy, `Science` has subareas `Biology, Chemistry, Physics,
Earth, Robotics, Math, Linguistics` — "Applied Mathematics" is not a value there, and `Math` is
described as "formalized mathematics, theorem proving, and formal verification," which misdescribes this
task. Under the Terminal-Bench-Science taxonomy the correct triple is `domain = mathematical-sciences`,
`field = applied-mathematics`, `subfield = <free>` — and values are exact and case-sensitive.
**Judgement:** Uncertain — commit to Applied Mathematics and defend it adversarially, or move to
mathematical-sciences/applied-mathematics explicitly.

### Outcome-verified — **Accept**
**For:** Grading is on outputs, not method. The proposal explicitly says no particular algorithm is
required and that multiple reconstructions are acceptable. Correct posture.
**Against:** "Multiple reconstructions will be accepted when they are indistinguishable within
observational uncertainty" is stated but **not operationalized**. "Indistinguishable" between two
*mobility fields* is not a defined quantity. The right operationalization is **predictive
equivalence**: two reconstructions are indistinguishable if their predictions at the withheld times agree
within the observational uncertainty. As written this is a well-specifiedness hole, because the verifier
must implement it.
**Judgement:** Accept — pending the operationalization above.

---

## 2. Final analysis

This is a good task idea with a real scientific spine. The multi-time design (fit early observations,
predict withheld later times) is the correct mechanism for discriminating overfit reconstructions, and
the three diagnostics are genuine physical checks rather than formatting checks — that is a
well-informed proposal, not a generic one.

It is not yet a Strong Accept because three of the seven criteria have unresolved holes, and two of them
are the kind of hole the rubric explicitly punishes. First, the generative model is not declared: with no
prior on the mobility field and no precise observation model, the "correct" answer is not defined and
two competent practitioners will write incompatible verifiers — a direct Well-specified failure.
Second, the difficulty is not pinned: the number of mobility degrees of freedom is unspecified, and at
low dimension the task collapses into global optimization with no identifiability reasoning. Third, the
category justification is one generic sentence that does not survive the obvious Materials Science
reading.

All three are fixable on the page, and none require changing the task's concept. The single most
important addition is the **prior + observation model + declared degrees of freedom**, because it
converts the proposal from "a plausible inverse problem" into "an inverse problem with a definable
answer" — which simultaneously fixes Well-specified, fixes Solvable, and restores the difficulty.

**Decision-Reason:** Strong inverse-problem concept and a well-designed multi-time discrimination
mechanism, but an undeclared generative model, an unset difficulty dial, and a thin category
justification keep it at Accept rather than Strong Accept.
**Decision:** Accept

---

## 3. Ranked fixes

### FIX 1 — Declare the generative model (fixes Well-specified *and* Solvable)
Add, as a single paragraph:

> The mobility is drawn from a prior distribution over a K-dimensional coefficient vector θ
> (K = ___), with M(x) = M₀ · exp(Σₖ θₖ φₖ(x)) over a fixed orthonormal basis {φₖ} supplied in the
> input artifact; θ is drawn from N(0, Σθ) with Σθ supplied. Observations are y = S(M(c₀;θ)) + ε,
> with ε ~ N(0, Σ_ε) and Σ_ε supplied per observation time, sampled at a specified set of sensor
> locations. All of M₀, the basis, the prior covariance, and the observation times and locations are
> supplied as inputs; none of them are to be inferred.

Why this matters: it defines the answer. It also makes the task *fair* — the agent can reason about
identifiability because it knows the family. And it makes the constant-mobility baseline a genuinely
informative rejection case rather than an arbitrary strawman.

### FIX 2 — Set the difficulty dial explicitly (fixes Difficult)
State K, the grid, and the forward-solve cost. K should be large enough that global optimization is out
of reach (K ≳ 8), so that sensitivity/adjoint-based methods are required — which is what your
"intended approach" paragraph already assumes. Also state the forward-solve wall time and the
environment's CPU/RAM. Add one sentence of identifiability *evidence*, e.g. the ratio of the smallest to
largest eigenvalue of the Fisher information at the true θ, and the posterior predictive spread at the
withheld times relative to the observational noise. That converts "we checked the observation design"
from a promise into a measurement.

### FIX 3 — Name the failure modes and map each to the gate that catches it (fixes the rubric's
"methodological pitfalls" requirement, which the proposal currently under-delivers)
The rubric explicitly asks: *"the key reasoning, domain knowledge, or methodological pitfalls that could
lead to incorrect solutions."* The proposal describes the challenge but never the concrete errors. Add a
short list — this is the highest-leverage paragraph in the whole proposal:

> Wrong solutions are characteristic and each is caught by a different gate:
> (i) using the non-conservative form M∇²μ instead of ∇·(M∇μ) — breaks mass conservation, caught by
> relative_mass_drift; (ii) mis-specifying the free energy f(c) or the gradient penalty κ — wrong
> coarsening kinetics, caught by the energy-balance residual and by withheld-time predictions;
> (iii) treating the noise as white (diagonal weights) instead of using the supplied correlation —
> over-weights correlated measurements and yields an overfitted reconstruction, caught by withheld-time
> prediction error; (iv) submitting a constant mobility — the trivial end of the regularization
> spectrum, caught by withheld-time prediction error; (v) an unconstrained parameterization producing
> locally negative mobility, caught by the declared positivity bounds; (vi) an under-resolved
> discretization admitting grid-scale mobility structure that fits early data but not later — caught by
> the energy-balance residual and prediction error.

Note that (i) is a genuinely elegant trap and the proposal should say so explicitly — for non-constant
mobility the free-energy dissipation law dF/dt = −∫M|∇μ|² holds **only** in the conservative form, so
the energy residual doubles as a check that the agent used the right PDE. That is a real physics
insight and it is worth advertising.

### FIX 4 — Operationalize the acceptance criterion (fixes Well-specified / Outcome-verified)
Replace *"indistinguishable within observational uncertainty"* with the predictive-equivalence
definition, and enumerate the gates:

> PASS requires all of: (1) every declared artifact present with the specified shape, dtype, and
> parameter ordering; (2) the verifier's re-simulation of the submitted mobility reproduces the
> agent's predictions to within the declared solver tolerance; (3) withheld-time prediction error below
> a threshold calibrated so that the true-parameter reconstruction passes with margin and the
> constant-mobility, white-noise-weighting, and noise-overfitting baselines all fail; (4) the
> verifier's recomputed weighted observation misfit below a threshold derived from the supplied noise
> covariance at a stated confidence level; (5) relative mass drift and energy-balance residual within
> tolerances scaled to the declared grid and time step; (6) positivity of the submitted mobility field.

Also add the **consistency check**: the verifier should confirm that `mobility_grid` is the reconstruction
of `mobility_coefficients` under the declared parameterization. Cheap, and it closes a real loophole
(agent submits a good grid with garbage coefficients, or vice versa).

### FIX 5 — State the environment and what the agent is given (fixes Solvable, and the rubric's
"dependencies must be realistic and accessible")
Say plainly:
- whether the environment ships a working CH solver (recommended) or the agent must implement one
  (not recommended — it converts an inference task into a numerical-methods slog);
- the file names, formats, and sizes of the input artifacts;
- CPU/RAM and the wall-clock cost of one forward simulation.

My strong recommendation: **ship the solver.** If the agent must write a variable-coefficient,
mass-conserving 4th-order PDE solver from scratch, the scientific content gets buried under
implementation busywork and the task becomes an implementation benchmark, which is exactly what the
rubric warns against. If you ship it — even a correct but unparameterized one — the entire difficulty
sits in the inference layer, where you want it. The task should be hard because *the inverse problem is
hard*, not because *the PDE is annoying*.

### FIX 6 — Sharpen the category justification (fixes Scope)
Current text is one generic sentence. Replace with something that names the alternative reading and
defeats it:

> **Category: Mathematical Sciences / Field: Applied Mathematics.** The subject matter is a
> nonlinear, ill-posed coefficient-inference problem for a fourth-order conservation law: the
> deliverables are an admissible reconstruction, an identifiability assessment, and a predictive
> validation against held-out observations. Those are applied-mathematics deliverables. The physical
> system (binary-mixture phase separation) is the *substrate* that makes the inverse problem
> well-posed and interesting — it is supplied as context, not something the agent is asked to research.
> We place this in Applied Mathematics rather than Materials Science because the competencies being
> tested are regularization, sensitivity analysis, and identifiability, not phase-field theory or
> microstructure characterization; a solver who knows the forward model but not inverse-problem
> methodology would fail this task. Conversely, the physics is not decorative: the conservative form of
> the PDE is essential to the diagnostics, and the free-energy dissipation law is what makes the energy
> balance a meaningful check.

Also confirm the exact strings the site's form expects. If it follows the Terminal-Bench-Science
taxonomy, use `mathematical-sciences` / `applied-mathematics`.

### FIX 7 — Anchor to the literature (fixes Scientifically Grounded)
Name the forward model and the failure modes in terms of actual published work: Cahn–Hilliard /
phase-field models of binary mixtures; the Onsager / hydrodynamic theory of phase separation;
nonlinear ill-posed inverse problems and Tikhonov-type regularization; Fisher-information and
identifiability analysis for parameter estimation; imaging-based inference of transport coefficients
from in-situ microscopy. A reviewer should be able to read the proposal and think "yes, this is what
someone in that field actually does."

### FIX 8 — Calibration and realism details to nail down
- **The absolute scale of M.** If M enters multiplicatively, M and αM are related by a time rescaling.
  Predictions at fixed absolute times break the degeneracy — but say this explicitly, because it is
  exactly the kind of thing that separates a real inverse-problem practitioner from a fitter, and it
  should be *load-bearing* in the design rather than an accident.
- **Noise covariance realism.** Build the correlation structure from an actual measurement model
  (optical point-spread blur, shot noise, illumination gradient) rather than an arbitrary kernel. It
  costs nothing and it directly satisfies "reflects realistic complexity."
- **Prediction window.** The withheld times must be late enough that an overfit reconstruction has
  visibly diverged, but not so late that the answer is dominated by the free-energy minimizer and
  grid effects (late-time CH coarsening becomes weakly sensitive to M). The constant-mobility baseline
  is the check that this window was chosen well — if constant M passes, the window is wrong.
- **Expert effort vs. agent budget.** 8 hours expert effort against an 8-hour agent budget is tight and
  a bit self-defeating. The rubric wants the estimate for someone who *already knows the method* —
  4–6 hours is the more defensible number for that, and it leaves the agent room to explore.

---

## 4. Distinctness check

The merge list contains a family of related inverse-problem tasks: `rbc-temperature-inference`
(Rayleigh–Bénard temperature inference — physical PDE parameter inference with constraints),
`traffic-flux-inversion`, `koopman-mfg-id`, `ode-law-discovery`, `certified-sparse-regression`,
`symbolic-regression`, `localized-sspd-solver`, `finite-free-stam`, `amr-poisson-optimize`.

The TF-IDF similarity check will fire on words like "inverse", "mobility", "PDE", "parameter
estimation". Be ready to say, in the PR, how this differs: it is a **spatially heterogeneous**
coefficient field (not a lumped parameter), **multi-time with a withheld-time predictive gate** (not a
single-snapshot fit), **degenerate/weakly-identified directions as the explicit difficulty** (not
sparsity), and **conservation-law physics as a verifiable constraint** (not a generic regularizer).

---

## 5. What is already strong — keep these

1. **The multi-time design.** Fit early observations, predict withheld later times. This is the single
   best design decision in the proposal: it makes "overfitting the noise" a *detectable* failure rather
   than a philosophical worry, and it means the grader measures something scientifically meaningful.
2. **Three physical diagnostics, not three format checks.** Mass drift and energy balance are exactly
   the right instruments for a conservation-law inverse problem. The energy-balance residual as a test of
   whether the agent used the conservative PDE form is elegant.
3. **Naming the rejection baselines** (constant mobility, ignored noise correlations, noise-overfitting).
   Calibrating thresholds against them is the correct way to satisfy `graded_instances_discriminate`.
4. **"No particular algorithm or library will be required."** Correct — the rubric forbids
   method-prescription, and the solver/adjoint choice should be free.
5. **Withholding the thresholds.** Correct per the rubric. Name the metrics; withhold the numbers.
6. **Refusing point-estimate grading.** Correct — "exact agreement with unidentifiable generating
   coefficients will not be required" is precisely the right stance for an ill-posed problem, and it
   should be stated as confidently as it is here.
