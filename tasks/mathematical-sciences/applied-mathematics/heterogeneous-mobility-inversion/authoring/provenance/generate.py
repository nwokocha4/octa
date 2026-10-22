"""Generate the synthetic dataset for the heterogeneous-mobility inversion task.

This script is AUTHOR-SIDE material.  It lives in ``authoring/provenance/`` and is never mounted
into a container, so neither the agent nor the verifier can see it.  It is the sole producer of
the ground truth:

* it draws the true mobility coefficients ``theta*`` from the supplied prior and writes them to
  ``tests/truth/theta_true.json``;
* it runs the reference forward model to produce the true trajectory;
* it applies the observation operator (point-spread blur + sparse, uneven sensor mask) and adds
  the correlated, heteroscedastic measurement noise;
* it writes the agent-visible input files and the verifier-only withheld observations.

Everything it writes is reproducible from the single seed below.

Run from the task root:

    python authoring/provenance/generate.py
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import scipy.linalg
import scipy.sparse

HERE = os.path.dirname(os.path.abspath(__file__))
TASK_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_DIR = os.path.join(TASK_ROOT, "environment", "data")
TRUTH_DIR = os.path.join(TASK_ROOT, "tests", "truth")
sys.path.insert(0, os.path.join(DATA_DIR, "mobility_solver"))

import solver as S  # noqa: E402

# ---------------------------------------------------------------------------
# task configuration -- every number the benchmark depends on lives here
# ---------------------------------------------------------------------------
SEED = 20261021

N = 48                     # grid cells per side
                           # Resolution note: with kappa = 0.125 the interface width is
                           # w = sqrt(2 kappa) = 0.5 against dx = 0.4167, i.e. w/dx = 1.2.
                           # The interface is only a few cells wide, so the coarsening rate is
                           # not quantitatively converged -- and it does not need to be.  Every
                           # comparison the verifier makes (G4/G5) re-simulates with this same
                           # solver, so discretisation error cancels; the physics must be stable,
                           # mobility-sensitive, and plausible, which the design screen verifies.
L = 20.0                   # domain extent
KAPPA = 0.125              # gradient-energy coefficient
M0 = 1.0                   # pre-exponential mobility
FCOEFFS = np.array([0.0, 0.0, 0.25, -0.5, 0.25])   # f(c) = c^2 (1-c)^2 / 4
SIGMA_THETA = 0.22         # prior standard deviation per mobility coefficient
                           # RMS-normalised basis: std(log M / M0) ~ SIGMA_THETA*sqrt(K) ~ 0.66
K_COEFF = 9                # number of mobility coefficients

TIMES_OBS = np.array([2.0, 6.0, 10.0, 14.0])
TIMES_PRED = np.array([17.0, 20.0, 23.0])

SENSOR_GRID = 18           # sensor lattice resolution (SENSOR_GRID x SENSOR_GRID positions)
SENSOR_KEEP = 0.62         # fraction of sensor positions actually observed (unevenly)
BLUR_SIGMA = 1.0           # PSF width in grid cells
NOISE_CORR_LEN = 1.6       # spatial correlation length of the measurement noise, in grid cells
NOISE_FLOOR = 0.00100      # noise floor (absolute)
NOISE_SHOT = 0.00004       # heteroscedastic: var = floor^2 + shot * max(1-y, 0)
NOISE_SCALE = 1.0          # overall noise multiplier

# ---------------------------------------------------------------------------
# basis: orthonormal Neumann (cosine) modes on [0, L]^2
# ---------------------------------------------------------------------------
MODES = [(0, 0), (0, 1), (1, 0), (0, 2), (1, 1), (2, 0), (1, 2), (2, 1), (2, 2)]


def build_basis(n=N, l=L, modes=MODES):
    """Orthonormal cosine modes, shape (K, N, N).

    RMS normalisation: each mode is scaled by sqrt(area) so that its spatial average of
    phi^2 is 1 rather than 1/area.  The mobility field is M = M0 exp(sum_k theta_k phi_k),
    so with this normalisation sigma_theta directly controls the log-mobility amplitude:
    std(eta) over the domain is about sigma_theta * sqrt(K).
    """
    area = l * l
    x = (np.arange(n) + 0.5) * l / n
    basis = []
    for (m, k) in modes:
        cx = 1.0 / np.sqrt(l) if m == 0 else np.sqrt(2.0 / l)
        cy = 1.0 / np.sqrt(l) if k == 0 else np.sqrt(2.0 / l)
        basis.append(cx * cy * np.sqrt(area) * np.cos(m * np.pi * x / l)[:, None]
                     * np.cos(k * np.pi * x / l)[None, :])
    return np.array(basis)


# ---------------------------------------------------------------------------
# initial condition
# ---------------------------------------------------------------------------
def make_initial_condition(rng, basis, amplitude=0.12):
    """Smooth random perturbation of the mean composition, band-limited to the unstable band.

    The fastest-growing wavelength for f(c) = c^2 (1-c)^2 / 4 at kappa = 0.125 is
    2*pi / q* with q*^2 = 0.25 / (2 kappa) = 1, i.e. wavelength 6.28 on a domain of
    L = 20, which is Neumann lattice mode m ~ 2L/lambda = 6.4.  The seed is placed there.
    """
    n = basis.shape[1]
    l = L
    x = (np.arange(n) + 0.5) * l / n
    seed_modes = [(0, 0), (6, 0), (0, 6), (6, 6), (7, 0), (0, 7), (5, 5), (7, 7),
                  (4, 6), (6, 4)]
    amps = rng.normal(size=len(seed_modes))
    c = np.full((n, n), 0.5)
    for (m, k), a in zip(seed_modes, amps):
        cx = 1.0 / np.sqrt(l) if m == 0 else np.sqrt(2.0 / l)
        cy = 1.0 / np.sqrt(l) if k == 0 else np.sqrt(2.0 / l)
        c = (c + a * cx * cy * np.cos(m * np.pi * x / l)[:, None]
             * np.cos(k * np.pi * x / l)[None, :])
    dev = float(np.max(np.abs(c - 0.5)))
    if dev > 0:
        c = 0.5 + (c - 0.5) * (amplitude / dev)
    return np.clip(c, 0.05, 0.95)


# ---------------------------------------------------------------------------
# observation operator: point-spread blur at sparse, unevenly distributed sensor positions
# ---------------------------------------------------------------------------
def build_operator(n=N, l=L, sensor_grid=SENSOR_GRID, keep=SENSOR_KEEP,
                   blur_sigma=BLUR_SIGMA, rng=None):
    """Return (G, positions) where G maps a field (N*N,) to sensor readings (n_sensors,)."""
    rng = rng or np.random.default_rng(SEED)
    cell = l / n
    # sensor lattice positions (cell indices, fractional)
    lat = (np.arange(sensor_grid) + 0.5) * n / sensor_grid
    ii, jj = np.meshgrid(lat, lat, indexing="ij")
    ii = ii.ravel()
    jj = jj.ravel()
    total = ii.size

    # uneven coverage: a smooth density gradient plus a low-coverage "shadow" region
    u = ii / n
    v = jj / n
    weight = 0.35 + 0.65 * (0.5 + 0.5 * np.cos(2 * np.pi * (u + 0.6 * v)))
    shadow = np.exp(-(((u - 0.22) ** 2 + (v - 0.78) ** 2) / (2 * 0.14 ** 2)))
    weight = weight * (1.0 - 0.85 * shadow)
    prob = weight / weight.sum()
    n_keep = int(round(keep * total))
    chosen = rng.choice(total, size=n_keep, replace=False, p=prob)
    chosen.sort()
    si = ii[chosen]
    sj = jj[chosen]

    # Gaussian PSF weights over a 7x7 stencil of cells
    rad = 3
    offs = np.arange(-rad, rad + 1)
    d2 = offs[:, None] ** 2 + offs[None, :] ** 2
    kern = np.exp(-d2 / (2.0 * blur_sigma ** 2))
    kern /= kern.sum()

    rows, cols, vals = [], [], []
    for r, (ci, cj) in enumerate(zip(si, sj)):
        for a in range(-rad, rad + 1):
            for b in range(-rad, rad + 1):
                ii2 = int(round(ci)) + a
                jj2 = int(round(cj)) + b
                if 0 <= ii2 < n and 0 <= jj2 < n:
                    rows.append(r)
                    cols.append(ii2 * n + jj2)
                    vals.append(kern[a + rad, b + rad])
    G = scipy.sparse.csr_matrix((vals, (rows, cols)), shape=(si.size, n * n))
    positions = np.stack([si, sj], axis=1)
    return G, positions


# ---------------------------------------------------------------------------
# correlated, heteroscedastic measurement noise
# ---------------------------------------------------------------------------
def build_noise_covariance(n_sensors, positions, y):
    """Return (Sigma_chol, marginal_variances) for eps ~ N(0, Sigma), Sigma = L L^T.

    Sigma = D^(1/2) R D^(1/2), where

      * D holds the marginal variances: a noise floor plus a heteroscedastic shot-noise term
        that is larger where the measured signal is smaller, and
      * R is a unit-diagonal Gaussian-kernel correlation matrix over the sensor lattice, standing
        for detector cross-talk between neighbouring sensor pixels.

    Writing it this way makes diag(Sigma) exactly D, so the marginal variances the agent is told
    about are the true ones, and the correlation structure is exactly R.  Samples are drawn as
    eps = L z with z ~ N(0, I), which makes them consistent with the shipped Sigma by
    construction rather than by argument.
    """
    n = N
    lattice = positions / (n / SENSOR_GRID)
    d2 = ((lattice[:, None, 0] - lattice[None, :, 0]) ** 2
          + (lattice[:, None, 1] - lattice[None, :, 1]) ** 2)
    R = np.exp(-d2 / (2.0 * NOISE_CORR_LEN ** 2))

    var = (NOISE_FLOOR ** 2 + NOISE_SHOT * np.maximum(1.0 - y, 1e-3)) * (NOISE_SCALE ** 2)
    D = np.diag(var)
    SqrtD = np.diag(np.sqrt(var))
    Sigma = SqrtD @ R @ SqrtD
    Sigma = 0.5 * (Sigma + Sigma.T) + 1e-12 * np.eye(n_sensors)
    L = np.linalg.cholesky(Sigma)
    return L, var


def apply_cholesky_inverse(L, v):
    """Return Sigma^{-1} v given Sigma = L L^T."""
    return scipy.linalg.solve_triangular(L.T, scipy.linalg.solve_triangular(L, v, lower=True))


# ---------------------------------------------------------------------------
# main generation
# ---------------------------------------------------------------------------
def main():
    t_start = time.time()
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(TRUTH_DIR, exist_ok=True)
    rng = np.random.default_rng(SEED)

    basis = build_basis()
    model = S.CHModel(N, L, KAPPA, FCOEFFS, M0=M0)
    # The mobility bound for the time step.  Larger M_MAX admits higher-contrast mobility
    # fields (which the design screen needs) at the price of a smaller step; the solver
    # derives its own stable step from the submitted mobility, so the task stays solvable.
    M_MAX = 2.0
    dt = model.stable_dt(max_mobility=M_MAX)

    # --- ground truth ------------------------------------------------------
    # The truth is drawn on a *subset* of the declared mobility modes at full prior strength,
    # while the agent always sees the full 9-mode basis and the same prior.  The drawn subset is
    # chosen below by measuring (fast, noiseless pilot simulations) which instantiation separates
    # best from the constant-mobility null.  Nothing about the draw leaks: the prior, the basis,
    # and the covariance are identical in every instantiation, and the truth is never
    # agent-visible.
    c0 = make_initial_condition(rng, basis)

    def _draw_on(modes, state):
        r = np.random.default_rng(state)
        th = np.zeros((K_COEFF,))
        th[np.asarray(modes)] = r.normal(0.0, SIGMA_THETA, size=len(modes))
        return th

    design_log = []
    design_fail = {"contrast": 0, "diverge": 0, "scored": 0}
    # The design screen simulates through the whole window, which is expensive (~25k steps per
    # draw, ~19 s).  7 blocks x 12 trials is ~25 min.  Two screens are not needed: the single
    # screen simulates (truth, null); the wrong-flux-form check happens once, against the winner.
    def _design_score(th):
        # Fast pilot: noiseless predictions of (truth, null) at the withheld times.
        M = model.mobility(th, basis)
        eta = np.log(np.asarray(M) / M0)
        design_log.append((float(eta.std()), float(np.max(M))))
        if not (0.5 <= eta.std() <= 1.1 and np.max(M) <= M_MAX and np.min(M) >= 0.05):
            design_fail["contrast"] += 1
            return None
        # Simulating once through the whole window raises on instability anywhere inside it,
        # so a passing draw is stable everywhere it matters.
        try:
            ref_traj = model.simulate_from(c0, th, basis, TIMES_PRED, dt=dt)
            null_traj = model.simulate_from(c0, np.zeros_like(th), basis, TIMES_PRED, dt=dt)
        except FloatingPointError:
            design_fail["diverge"] += 1
            return None
        design_fail["scored"] += 1
        ref, null = ref_traj, null_traj
        num = float(sum(float(np.sum((a - b) ** 2)) for a, b in zip(null, ref)))
        den = max(float(sum(float(np.sum(a * a)) for a in ref)), 1e-300)
        # separation of the truth from the constant null, in relative L2 at the withheld times
        return (num / den) ** 0.5

    CANDIDATE_BLOCKS = [
        list(range(0, 9)),   # all nine modes
        [0, 2, 3],           # x-modes
        [0, 1, 4],           # y-modes
        [0, 5, 6],           # diagonal modes
        [0, 7, 8],           # cross and square modes
        [1, 2, 3, 4],        # the full gradient-bearing set without the constant
        [0, 1, 2],           # the constant plus the two first harmonics
    ]
    best, best_score, best_th = None, -1.0, None
    print(f"[gen] design screen: amplitude now {c0.max()-c0.min():.4f} peak-to-peak")
    # Draw amplitudes from the declared prior: each coefficient is theta ~ N(0, sigma^2), and
    # full blocks carry several modes, so a block of b drawn modes has std ~ sigma*sqrt(b).
    # The design screen keeps the draws that land in the contrast window, so no rescaling.
    for bi, block in enumerate(CANDIDATE_BLOCKS):
        for trial in range(12):
            rng_b = np.random.default_rng(SEED + 1000 * (bi + 1) + trial)
            th = np.zeros((K_COEFF,))
            th[np.asarray(block)] = rng_b.normal(0.0, SIGMA_THETA, size=len(block))
            score = _design_score(th)
            if score is not None and score > best_score:
                best, best_score, best_th = block, score, th
    if best_th is None:
        import statistics as _st
        stds = sorted(x[0] for x in design_log)
        maxs = sorted(x[1] for x in design_log)
        print(f"[gen] design screen failed: {len(design_log)} draws, "
              f"eta.std median={_st.median(stds):.3f} max={max(stds):.3f}, "
              f"M.max median={_st.median(maxs):.3f} min={min(maxs):.3f}, "
              f"contrast-rejected={design_fail['contrast']} diverged={design_fail['diverge']} "
              f"scored={design_fail['scored']}")
        raise RuntimeError("no candidate mobility survived the design screen")
    theta_true, best_block = best_th, best
    M_true = model.mobility(theta_true, basis)
    eta = np.log(np.asarray(M_true) / M0)
    print(f"[gen] design screen: block={best_block} rel-L2(null vs truth)={best_score:.4f}")
    print(f"[gen] mobility: std(eta) over domain = {eta.std():.3f}  "
          f"M in [{np.min(M_true):.3f}, {np.max(M_true):.3f}]")

    # --- true trajectory ----------------------------------------------------
    all_times = np.concatenate([TIMES_OBS, TIMES_PRED])
    fields, energy = model.simulate_from(c0, theta_true, basis, all_times, dt=dt,
                                          track_energy=True)
    print("[gen] accepted on the design-screened draw")
    obs_fields = fields[: len(TIMES_OBS)]
    pred_fields = fields[len(TIMES_OBS):]

    mass0 = S.total_mass(c0, model.dx)
    mass_drift = max(abs(S.total_mass(f, model.dx) - mass0) / abs(mass0) for f in fields)

    print(f"[gen] dt={dt:.4e}  steps to t={all_times[-1]}: {all_times[-1]/dt:.0f}")
    print(f"[gen] energy balance residual (correct flux form): "
          f"{energy['energy_balance_residual']:.3e}")
    print(f"[gen] mass drift (relative): {mass_drift:.3e}")
    for tt, f in zip(all_times, fields):
        print(f"[gen]   t={tt:6.2f}  range=[{f.min():.4f}, {f.max():.4f}]  "
              f"std={f.std():.5f}")

    # --- observation operator ----------------------------------------------
    G, positions = build_operator(rng=np.random.default_rng(SEED + 1))
    n_sensors = G.shape[0]
    print(f"[gen] sensors: {n_sensors}")

    def observe(field):
        return G @ field.ravel()

    y_obs = np.stack([observe(f) for f in obs_fields])           # (n_times, n_sensors)
    L_chol, diag = build_noise_covariance(n_sensors, positions, y_obs[0])

    # Samples are eps = L z with z ~ N(0, I), so they have exactly the covariance that is
    # shipped to the agent.
    rng_noise = np.random.default_rng(SEED + 2)
    eps_obs = (L_chol @ rng_noise.normal(size=(n_sensors, y_obs.shape[0]))).T
    y_noisy = y_obs + eps_obs

    # --- withheld observations at the prediction times ----------------------
    y_pred_clean = np.stack([observe(f) for f in pred_fields])
    rng_pred = np.random.default_rng(SEED + 3)
    eps_pred = (L_chol @ rng_pred.normal(size=(n_sensors, y_pred_clean.shape[0]))).T
    y_pred_noisy = y_pred_clean + eps_pred

    # --- write agent-visible files ------------------------------------------
    np.savez_compressed(
        os.path.join(DATA_DIR, "initial_condition.npz"),
        c0=c0,
        dx=model.dx,
        L=L,
        kappa=KAPPA,
        f_coeffs=FCOEFFS,
        mean_composition=0.5,
        times_obs=TIMES_OBS,
        times_pred=TIMES_PRED,
    )
    np.savez_compressed(
        os.path.join(DATA_DIR, "basis.npz"),
        phi=basis,
        M0=M0,
        mode_indices=np.array(MODES),
    )
    np.savez_compressed(
        os.path.join(DATA_DIR, "observations.npz"),
        y=y_noisy,
        times_obs=TIMES_OBS,
        sigma_chol=L_chol,
        noise_variance_diagonal=diag,
        noise_floor=NOISE_FLOOR,
        noise_shot=NOISE_SHOT,
        sensor_positions=positions,
        sensor_grid=SENSOR_GRID,
        blur_sigma=BLUR_SIGMA,
        noise_correlation_length=NOISE_CORR_LEN,
    )
    scipy.sparse.save_npz(os.path.join(DATA_DIR, "observation_operator.npz"), G)
    with open(os.path.join(DATA_DIR, "prior.json"), "w") as fh:
        json.dump({
            "mean": [0.0] * K_COEFF,
            "covariance": np.eye(K_COEFF).tolist(),
            "sigma_theta": SIGMA_THETA,
            "description": "theta ~ N(0, sigma_theta^2 I), coefficients ordered as the basis "
                           "array in basis.npz",
        }, fh, indent=2)

    # --- write verifier-only truth ------------------------------------------
    np.savez_compressed(
        os.path.join(TRUTH_DIR, "withheld_observations.npz"),
        y_withheld=y_pred_noisy,
        times_pred=TIMES_PRED,
        noise_variance_diagonal=diag,
    )
    with open(os.path.join(HERE, "theta_true.json"), "w") as fh:
        json.dump({
            "theta_true": theta_true.tolist(),
            "basis_modes": MODES,
            "seed": SEED,
            "sigma_theta": SIGMA_THETA,
        }, fh, indent=2)
    np.savez_compressed(
        os.path.join(HERE, "true_trajectory.npz"),
        times=all_times,
        fields=np.stack(fields),
    )

    # the truth must never be present in the verifier image
    stale = os.path.join(TRUTH_DIR, "theta_true.json")
    if os.path.exists(stale):
        os.remove(stale)

    # --- verifier-side copies (separate container, own build context) --------
    tests_data = os.path.join(TRUTH_DIR, "..", "data")
    tests_data = os.path.abspath(tests_data)
    tests_solver = os.path.abspath(os.path.join(TRUTH_DIR, "..", "solver"))
    os.makedirs(tests_data, exist_ok=True)
    os.makedirs(tests_solver, exist_ok=True)
    import shutil
    for name in ("initial_condition.npz", "basis.npz", "observations.npz",
                 "observation_operator.npz", "prior.json"):
        shutil.copy2(os.path.join(DATA_DIR, name), os.path.join(tests_data, name))
    shutil.copy2(os.path.join(DATA_DIR, "mobility_solver", "solver.py"),
                 os.path.join(tests_solver, "solver.py"))

    # --- manifest -----------------------------------------------------------
    manifest = {
        "seed": SEED,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "grid": {"N": N, "L": L, "dx": model.dx},
        "model": {"kappa": KAPPA, "M0": M0, "f_coeffs": FCOEFFS.tolist(),
                  "dt": dt, "scheme": "explicit RK2, conservative face-flux finite volume"},
        "mobility": {"K": K_COEFF, "sigma_theta": SIGMA_THETA, "modes": MODES},
        "times": {"obs": TIMES_OBS.tolist(), "pred": TIMES_PRED.tolist()},
        "observation": {"sensor_grid": SENSOR_GRID, "n_sensors": int(n_sensors),
                        "blur_sigma": BLUR_SIGMA, "noise_floor": NOISE_FLOOR,
                        "noise_shot": NOISE_SHOT,
                        "noise_correlation_length": NOISE_CORR_LEN},
        "diagnostics": {
            "mass_drift_relative": float(mass_drift),
            "energy_balance_residual": float(energy["energy_balance_residual"]),
            "free_energy_change": float(energy["free_energy_change"]),
            "dissipation": float(energy["dissipation"]),
        },
    }
    with open(os.path.join(HERE, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"[gen] wrote data to {DATA_DIR}")
    print(f"[gen] wrote truth to {TRUTH_DIR}")
    print(f"[gen] elapsed {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
