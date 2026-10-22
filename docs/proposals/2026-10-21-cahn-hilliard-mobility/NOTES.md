# Internal notes — Cahn–Hilliard mobility reconstruction

**Not part of the submission.** Working notes for the author: what still has to be decided, what has to
be measured before the proposal can be submitted, and the reasoning behind decisions that are not
visible in `PROPOSAL.md`.

---

## 1. Open `[PILOT-n]` items

These are the eight quantities the proposal marks as undetermined. Each needs a measurement, not an
opinion, before the proposal is submittable.

| ID | What it is | Where it comes from | Target / acceptance criterion |
|---|---|---|---|
| `PILOT-1` | Wall-clock cost of one forward evaluation (declared grid, through the prediction times) | Timed run of the reference solver on the target hardware | Must make a 9-D global search (≥10⁴ evals) exceed the 8 h agent budget, while a gradient method (≈10²–10³ evals for a finite-difference Jacobian over 9 parameters × tens of iterations) fits comfortably |
| `PILOT-2` | Ratio λ_min/λ_max of the Gauss–Newton information matrix for `θ` at the truth | J = ∂F/∂θ at `θ*`, from the observation operator | Small enough that an unregularized ML fit is measurably worse at prediction than a prior-regularized one; not so small that the prior dominates and the reconstruction is prior-driven rather than data-driven |
| `PILOT-3` | Posterior predictive spread at the withheld times, relative to the observational noise | Posterior draw or Laplace approximation at `θ*` | The spread must exceed the observational noise by a clear factor — otherwise the withheld-time gate cannot discriminate and the whole task collapses to fitting |
| `PILOT-4` | Margin between the constant-mobility baseline and the correct reconstruction on the G5 metric | Run both | Must be comfortably positive; this is the number that decides whether the task has teeth |
| `PILOT-5` | CPU count and RAM for `[environment]` | Measured peak memory of the solver and the inverse problem | Comfortably above measured usage, so the task never fails for environment reasons |
| `PILOT-6` | The admissible mobility range factor (as a multiple of `M₀`) | Chosen from the prior: `M ∈ [M₀ e^{-3σ_θ}, M₀ e^{+3σ_θ}]` covers ~99.7% of the prior support | Should exclude only physically absurd values, so the gate rejects sign-defective fields without constraining legitimate reconstructions |
| `PILOT-7` | Required separation factor: how far the constant-mobility baseline must fall below the G5 threshold | Design choice, validated by `PILOT-4` | A calibration is rejected if the null fails by less than this factor |
| `PILOT-8` | Required margin factor: how far the oracle must clear the G5 threshold | Design choice | Rejected if the oracle clears by less than this factor — that would mean the gate is tight enough to be fragile |

**The pilot is a go/no-go, not a tuning exercise.** If `PILOT-2`, `PILOT-3` and `PILOT-4` cannot be
satisfied simultaneously for some (grid, noise level, sensor density) combination, the design changes —
not the thresholds. The thresholds are set *from* the measured separation.

---

## 2. Pilot study plan

### P0 — Reference solver (`authoring/provenance/solver/`)

A pseudo-spectral solver on the declared square domain with homogeneous no-flux boundaries. A
sine-transform (or DCT-based) basis satisfies Neumann conditions exactly and gives spectral accuracy,
which is what makes the diagnostics meaningful.

Verify, before anything else:

- [ ] Mass conservation to machine precision over a long run.
- [ ] The free-energy dissipation identity `dF/dt = −∫M|∇μ|²` holds to the solver's convergence order.
- [ ] The **wrong** flux form `M∇²μ` (non-conservative) violates mass conservation at O(1) and the
      energy identity at O(1) — i.e. it is caught by G6 and G7, not just at solver-tolerance size.
      This is the task's signature trap; it must be measured, not assumed.
- [ ] The wrong free energy (`κ` perturbed) changes the coarsening rate enough to move the withheld-time
      prediction by more than the G5 threshold.
- [ ] Time-step and grid convergence: the field at the prediction times is converged to well inside the
      solver tolerance that G4 will use.

### P1 — Physical regime

Choose domain extent `L`, grid `N`, `κ`, `M₀`, and the observation/prediction times so that:

- [ ] At the first observation time the sample is in the early spinodal-decomposition regime — visible
      structure, not a fully coarsened state. A fully coarsened field has lost the sensitivity to `M`.
- [ ] At the last prediction time the pattern has genuinely evolved, so a wrong `M` produces a visibly
      wrong field. **The constant-mobility baseline failing G5 is the test of this.** If constant `M`
      passes, the prediction window is wrong: either too early (no divergence yet) or so late that the
      final morphology is set by the free energy and insensitive to `M`.
- [ ] The observation times and the prediction times are separated enough that an overfit reconstruction
      has diverged, but the total elapsed time is short enough that the reference field is still a
      well-resolved single-phase pattern rather than a late-time coarsened polycrystal.

### P2 — Observation design

- [ ] Sensor mask: uneven by construction — coverage density varying across the field plus one
      poorly-observed region. Fixed at build time, shipped in `observations.npz`.
- [ ] Blur kernel: fixed PSF, shipped exactly. The agent must be able to apply it without ambiguity.
- [ ] Noise: heteroscedastic component (variance model shipped as an explicit formula) plus the
      spatial correlation induced by the blur. `L` shipped so `Σ = L Lᵀ` is exact and the agent can
      compute `Σ⁻¹` without inverting a large matrix.
- [ ] Sweep the noise magnitude and sensor density; select the point that satisfies `PILOT-2` and
      `PILOT-3` simultaneously.

### P3 — Baselines and thresholds

- [ ] Run every baseline in §5e of the proposal against every gated instance **separately**, not
      against the suite as a whole. Record the per-instance results — the rubric explicitly credits an
      author who measures nulls per instance and penalizes one who only asserts they fail.
- [ ] Set the G5 threshold from the measured separation (`PILOT-7`, `PILOT-8`).
- [ ] Set the G6 and G4 tolerances from the solver convergence study, scaled to the declared grid and
      time step.

### P4 — Reproducibility

- [ ] Run the oracle **five times** in the target sandbox and confirm reward 1.0 every time.
      (Upstream guidance: "run the oracle solutions 5x to confirm all tasks work as expected.")
- [ ] Run the nop agent and confirm reward exactly 0.0.
- [ ] Confirm the verifier is deterministic: no RNG in the verifier path, or a pinned seed for any
      randomness in threshold estimation.
- [ ] Confirm no live network dependency at solve or verify time.

### P5 — Agent trials

- [ ] At least one trial with a strong agent, and the trajectory analysis attached to the PR.
- [ ] Read the trajectory specifically for: (a) did the agent identify the degeneracy, or did it fit and
      stop? (b) did it use the supplied covariance? (c) did it verify its own prediction before
      submitting? A task where the agent passes *despite* not engaging the intended reasoning needs a
      redesign of the gate, not a raise of the threshold.
- [ ] A cheat trial: a submission that daemons/forges the reward path must score 0.

---

## 3. Design decisions and their reasoning

Recorded so the reasoning survives contact with a reviewer.

**Plain Cahn–Hilliard, not advective.** v0 said "advective Cahn–Hilliard". An ACH model requires a
velocity field `u(x)`; v0 never specified one, so the model was under-specified. The described
diagnostics (mass drift, energy balance) are those of plain CH with variable mobility, so v1 drops the
word. If a second advective task is ever wanted, it needs its own `u` and its own proposal.

**The divergence form is load-bearing, not incidental.** For `∂c/∂t = ∇·(M∇μ)`, the free-energy
dissipation law `dF/dt = −∫M|∇μ|²` follows from integration by parts and holds for *spatially varying*
`M`. For the non-conservative `M∇²μ`, mass is not conserved and the identity fails at O(1). So one
diagnostic catches a whole family of errors — including, importantly, the physically common mistake of
writing a variable-coefficient diffusion as "diffusion coefficient times Laplacian."

**The solver ships with the environment.** If the agent implements the PDE itself, the benchmark
measures numerical-methods work, not inference. This is the single highest-leverage design decision.

**The solver's interface takes `θ`, not a grid.** It bakes in the declared parameterization, so agent
and verifier share the same forward model and there is no ambiguity about how `θ` becomes `M`. An agent
that fits a free grid is still fine — it projects onto the supplied orthonormal basis, and the graded
quantity is the projection.

**Grade the reconstruction, not the agent's numerics.** G5 is computed by the verifier's own
re-simulation of the submitted `mobility_coefficients`. The agent's `predicted_concentration` is checked
for contract and physical consistency only. An agent whose solver differs from the reference within the
stated tolerance should not be penalized for that — and this is what "reported numbers cannot substitute
for independently verified fields" means in practice.

**`mobility_grid` vs `mobility_coefficients` consistency gate (G2).** Cheap, and it closes a real
loophole: submitting a good grid with meaningless coefficients, or the reverse. Any submission is
graded through the coefficients, so an agent could otherwise game the grid.

**The prior is supplied, not invented.** Declaring the generative model is what makes the "regularize
rather than chase the likelihood" insight *available* rather than lucky. It also makes the answer
well-defined — the v0 hole.

**Ground-truth provenance.** `θ*` and the withheld observations are produced by the generator and
written out at generation time; the oracle is a *consumer* of that truth, not its producer. That is the
"independent reference" outcome the rubric wants. The generator lives in `authoring/provenance/`,
which Harbor never mounts. The shared solver is shared *infrastructure*, not a shared step under test —
worth stating explicitly in the `## Verification` section of the task README, because the rubric calls
this distinction out.

**Binary reward.** Harbor's reward is 1 or 0. All gates are conjunctive. Nothing here needs partial
credit, and a partial-credit scheme would complicate the calibration without adding signal.

---

## 4. Open design questions

These need an answer before `instruction.md` can be written. Each one, if left implicit, is a
well-specifiedness hole.

1. **Basis definition.** The nine orthonormal basis functions must be shipped as an array
   (`basis.npz`) with an explicit enumeration order, so "the k-th coefficient" is unambiguous. Decide
   and document: which nine modes (a 3×3 low-frequency block of 2-D DCT modes including the constant),
   and the exact normalization on `[0, L]²`. Do not describe them in prose and hope the agent matches.
2. **Blur kernel.** Exact form (Gaussian PSF? a physical diffraction profile?), width, and whether it
   is applied in sensor space or field space. Ship the kernel itself.
3. **Noise variance model.** The heteroscedastic component needs an explicit formula in the instruction
   (e.g. `σ_j² = σ_floor² + a / max(y_j, ε)`), with `σ_floor`, `a`, `ε` supplied.
4. **`Σ_ε = L Lᵀ`.** Ship `L` and state the factorization, so `Σ⁻¹` is exactly recoverable.
5. **Sensor mask.** Fixed at build time; ship the mask array and the sensor coordinates. State whether
   the agent may interpolate onto a finer grid (it may — but then the blur/observation operator must be
   applied consistently, and the instruction should say which grid the *observation* is on).
6. **Which grid the prediction is on.** The declared grid (128²). State it explicitly, and state whether
   sub-grid interpolation is permitted for the prediction (it should not be — it would let the agent
   dodge the discretization comparison).
7. **Solver tolerance for G4.** The tolerance that brackets independently established discretization
   errors. Comes out of the P0 convergence study.
8. **Whether the agent may write its own solver.** Yes — but then G4's comparison tolerance must be
   stated in the instruction as a range of accepted discretization errors, so the agent is not
   surprised by a tight numerical comparison.
9. **Number of prediction times and their spacing.** Three, and their values from P1.
10. **Whether `predicted_concentration` is also required at observation times.** No — the withheld
    prediction is the point. But the agent may want to check its own fit; that is its business.

---

## 5. What has to be true for this task to be worth building

The load-bearing claims, in order of fragility:

1. **The withheld-time gate separates.** Constant `M` fails, MAP passes, and the gap is wide. If this
   fails, the task has no teeth. → `PILOT-4`, P3.
2. **An unregularized fit is worse than a regularized one.** This is the whole insight the task claims
   to test. If the unregularized fit also passes, the task reduces to "solve a nonlinear least-squares
   problem," which a frontier model does routinely. → `PILOT-2`, P3.
3. **Global search is out of budget.** Otherwise the task is a 9-D optimization that a strong optimizer
   may crack. → `PILOT-1`.
4. **The physics is not decorative.** The energy identity must actually discriminate at O(1). → P0.

Items 1 and 2 are the same pilot measurement seen from two sides: if the gate cannot separate the
constant baseline from the truth, and cannot separate the ML fit from the MAP fit, then the two design
axes that carry the task — the predictive gate and the prior — are both inert, and the task is a
curve-fit.

---

## 6. Repository plan

The task itself lives in a fork of `harbor-framework/terminal-bench-science`, not in this repo. This
repo holds the proposal and its review history.

```
terminal-bench-science/                       (fork)
└── tasks/mathematical-sciences/applied-mathematics/
    └── heterogeneous-mobility-inversion/
        ├── instruction.md
        ├── task.toml
        ├── README.md
        ├── environment/
        │   ├── Dockerfile
        │   └── data/                 # c0, observations, basis, prior
        ├── solution/
        │   ├── solve.sh
        │   └── infer.py
        ├── tests/
        │   ├── Dockerfile
        │   ├── test.sh
        │   ├── test_state.py
        │   └── truth/                # θ*, withheld observations
        └── authoring/
            ├── hint.md
            ├── provenance/            # generator, solver, manifests, checksums
            └── evidence/              # independent re-implementation, sensitivity studies
```
