<!-- MANAGED HEADER - do not edit above this line; run `python3 tools/task-readme/generate.py <task-dir>` to regenerate -->

# Heterogeneous mobility inversion from phase-separation imaging

Recover a spatially varying mobility field of a phase-separating binary mixture from a sparse,
correlated-noise record of its concentration field at four early times, and predict the sample's
separation at three later times that were not observed.

| | |
| --- | --- |
| Domain / Field | Mathematical Sciences / Applied Mathematics |
| Subfield | Inverse problems for PDE-constrained parameter estimation |
| Expert time | 5 hours |
| Agent budget | 8 h |
| Resources | 2 CPU, 4 GB RAM, no GPU |

## Difficulty

The data do not determine the answer. Nine mobility coefficients are estimated from four
snapshots of a partially observed, spatially heterogeneous, correlated-noise system, and the
sensitivity of the observation operator to those coefficients is strongly anisotropic: a few
directions are pinned by the observations and several are only weakly constrained. An
unregularised fit reproduces the training misfit while placing large, wrong structure in exactly
the weakly-constrained directions, and that structure shows up in the later times the experiment
never reached. Distinguishing "supported by the data" from "fits the noise" is the whole
difficulty, and it is a judgment call about identifiability rather than an implementation grind.

A second, sharper trap sits underneath. The forward model is a fourth-order conservation law
with a spatially varying coefficient, and the correct form of its flux is a *divergence*:
`dc/dt = div(M grad mu)`. Written the other way, `dc/dt = M lap(mu)`, the scheme is a perfectly
ordinary-looking diffusion equation that silently drops the `grad(M)` term. It is not wrong in an
obvious way -- it conserves nothing, and it changes the growth rate of the pattern everywhere.
The mass-drift and energy-balance diagnostics are what separate the two, and they are the reason
the environment ships a forward model with a documented, exact discrete energy identity rather
than leaving the agent to write one.

## Reference solution

`solution/infer.py` builds the observation operator from the supplied files, forms the
covariance-weighted misfit of the supplied observations under the supplied prior, and minimises
it with a gradient-based least-squares method (`scipy.optimize.least_squares`, finite-difference
Jacobian). The forward model is the supplied `mobility_solver` package; nothing about the
reconstruction is hard-coded. The result is the maximum-a-posteriori mobility field, from which
the solution simulates forward to the prediction times and reports the three diagnostics.

The key insight the solution relies on: the prior is part of the problem statement, and the
directions the data do not constrain should be shrunk toward it rather than left at whatever
value maximises the training misfit.

## Verification

The verifier runs in its own container with no network egress and receives only the two declared
artifacts. It re-simulates the submitted `mobility_coefficients` with its own pinned copy of the
forward model and grades six groups of conditions:

| Gate | What it checks |
| --- | --- |
| G1 | the output contract: files, shapes, dtypes, finiteness, diagnostic keys |
| G2 | `mobility_grid` is the expansion of `mobility_coefficients` under the supplied basis |
| G3 | the mobility field is positive and inside the admissible range |
| G4 | the submitted prediction is a genuine simulation of the submitted coefficients (compared against the verifier's independent re-simulation), conserves mass, satisfies the energy-balance bound, and the reported diagnostics match independent recomputation |
| G5 | **the primary scientific gate**: the covariance-weighted misfit of the verifier's re-simulation against the *withheld* observations at the prediction times |
| G6 | the verifier's re-simulation conserves mass |

G5 is the gate that carries the task. It never compares a submission to the coefficients that
generated the data; it compares the *predictions* of a submission to measurements the submission
never saw, under the supplied covariance. Two reconstructions that are predictively equivalent
therefore both pass, and a reconstruction that fits the observation times but predicts badly
fails.

The reference values the verifier grades against -- the withheld observations -- are produced by
`authoring/provenance/generate.py`, which draws the true coefficients from the supplied prior,
runs the reference forward model, and applies the observation operator and the noise model.
The oracle consumes that truth; it does not produce it. The tolerances were calibrated in
`authoring/evidence/sensitivity.py`, which measures the separation between the truth and each
rejection baseline (constant mobility, a scaled mobility, the maximum-likelihood fit) and
between the correct and incorrect flux forms.

## Data

Synthetic, generated by the reference forward model from a single seed recorded in
`authoring/provenance/manifest.json`. The realism is engineered rather than incidental: the
observation operator is a point-spread blur (finite optical resolution), the sensor mask has
uneven coverage density and a poorly-observed region, and the measurement noise is a correlated
field (detector cross-talk) plus a heteroscedastic component that is larger where the measured
signal is smaller. The covariance is supplied to the agent in factored form.
