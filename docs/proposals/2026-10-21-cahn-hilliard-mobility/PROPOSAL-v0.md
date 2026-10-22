---
status: draft
review: ./REVIEW.md
review_verdict: Accept
date: 2026-10-21
category: Science
sub_category: Applied Mathematics
---

# v0 — Reconstruct heterogeneous mobility from incomplete phase-separation measurements

> **Superseded by `PROPOSAL.md` (v1).** Retained for history: this is the original author wording,
> verbatim. The v1 revision applies FIX 1–FIX 8 from `REVIEW.md`. Two substantive changes in v1 are
> worth flagging here: (a) the model is **plain Cahn–Hilliard with variable mobility**, not
> "advective Cahn–Hilliard" — an ACH model needs a velocity field `u(x)` that this task never
> specifies, so the original phrasing was under-specified; (b) the free energy is stated explicitly
> and the divergence form of the flux is made load-bearing, because the diagnostic that catches the
> wrong flux form is the task's best trap.

A computational mathematician or materials-modeling researcher must infer spatially varying transport
properties of a binary mixture governed by an advective Cahn–Hilliard model. The agent receives a
synthetic dataset consisting of an initial concentration field, sparse concentration measurements from
several early times, measurement-noise covariance, domain geometry, boundary conditions, and a declared
finite-dimensional representation of positive mobility. The measurements will be generated from a
conservative simulation and independently cross-checked. Correlated noise and uneven sensor coverage
represent realistic limitations of imaging-based transport inference.

The challenge is to distinguish mobility variations supported by the observations from weakly
identifiable variations that merely fit noise. A good training fit can coexist with incorrect transport
properties and incorrect later predictions. The agent must assess this ambiguity, obtain a stable
reconstruction, and predict phase separation at withheld times. This work requires specialist judgment
in nonlinear inverse problems, conservative fourth-order PDE modeling, and uncertainty propagation. The
difficulty comes from resolving competing reconstructions and validating their physical consequences,
rather than enlarging the grid or performing repetitive calculations.

## Intended approach and expert effort

A viable strategy is to examine how changes in mobility affect the measured concentration, identify
poorly constrained directions, and obtain a reconstruction that balances observational agreement with the
supplied admissibility constraints. The key insight is that mobility coefficients should not be treated as
equally recoverable: the reconstruction must preserve information supported by the measurements without
converting noise into transport heterogeneity. Sensitivity-based optimization, adjoint methods, or other
suitable inference methods may be used. No particular algorithm or library will be required.

A senior practitioner familiar with nonlinear PDE inverse problems is expected to require approximately 8
focused hours for data inspection, reconstruction, debugging, and validation. Before finalizing the
benchmark, the observation design will be checked to ensure that the required predictions and identifiable
mobility features are recoverable.

## Outputs and deterministic verification

The agent works in /app and produces /app/output/reconstruction.npz, containing mobility_coefficients,
mobility_grid, and predicted_concentration, plus /app/output/diagnostics.json, containing
weighted_observation_misfit, relative_mass_drift, and energy_balance_residual. Shapes, parameter
ordering, prediction times, and diagnostic definitions will be specified with the input artifacts.

A separate verifier will independently simulate the submitted mobility, recompute all diagnostics, and
evaluate predictions against withheld concentration observations and independently generated reference
fields. The acceptable observational misfit will be tied to the supplied noise covariance; numerical
allowances will bracket independently established solver and discretization errors. Bounds will be checked
against alternative correct reconstructions and rejection baselines, including constant mobility, ignored
noise correlations, and noise-overfitting solutions.

Multiple mobility reconstructions will be accepted when they are indistinguishable within
observational uncertainty, provided they satisfy the declared physical constraints and prediction
requirements. Exact agreement with unidentifiable generating coefficients will not be required. Binary
PASS requires all output-contract and scientific conditions to hold. Private references remain outside
the agent environment, and reported numbers cannot substitute for independently verified fields.

## Category justification

This is a Science task in Applied Mathematics because the central work combines nonlinear coefficient
inference, identifiability analysis, uncertainty-aware reconstruction, and numerical validation of a
conservation-law PDE. It requires iterative terminal work to inspect data, run simulations, diagnose
errors, and assess competing reconstructions.
