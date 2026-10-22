"""Difficulty calibration for the heterogeneous-mobility inversion task.

Author-side evidence.  This script measures exactly what the verifier measures, for a set of
candidate reconstructions, so that the thresholds in ``tests/test_state.py`` are calibrated against
measured separations rather than asserted:

* the covariance-weighted misfit of the withheld-time predictions -- the primary scientific gate;
* the snapshot-based mass drift and energy-balance residual the verifier recomputes;
* the wrong flux form, to confirm that the physics diagnostics discriminate;
* the conditioning of the observation operator's sensitivity to the mobility coefficients.

Candidate reconstructions: the truth, the constant-mobility null, a scaled mobility, and -- when
their output directories exist -- the MAP and maximum-likelihood reconstructions produced by
``solution/infer.py``.

Run from the task root:

    python authoring/evidence/sensitivity.py
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
DATA = os.path.join(TASK_ROOT, "environment", "data")
TRUTH = os.path.join(TASK_ROOT, "tests", "truth")
sys.path.insert(0, os.path.join(DATA, "mobility_solver"))

import solver as S  # noqa: E402

RUNS = {
    "map": "/tmp/oracle_runs/map",
    "ml": "/tmp/oracle_runs/ml",
}


def load():
    ic = np.load(os.path.join(DATA, "initial_condition.npz"))
    basis = np.load(os.path.join(DATA, "basis.npz"))
    obs = np.load(os.path.join(DATA, "observations.npz"))
    G = scipy.sparse.load_npz(os.path.join(DATA, "observation_operator.npz"))
    truth = np.load(os.path.join(TRUTH, "withheld_observations.npz"))
    with open(os.path.join(TASK_ROOT, "authoring", "provenance", "theta_true.json")) as fh:  # noqa: E501
        theta_true = np.array(json.load(fh)["theta_true"])
    model = S.CHModel(ic["c0"].shape[0], float(ic["L"]), float(ic["kappa"]),
                      ic["f_coeffs"], M0=float(basis["M0"]))
    return {
        "model": model, "c0": ic["c0"], "phi": basis["phi"], "L": obs["sigma_chol"],
        "y_obs": obs["y"], "t_obs": obs["times_obs"], "G": G,
        "t_pred": truth["times_pred"], "y_withheld": truth["y_withheld"],
        "dt": model.stable_dt(), "theta_true": theta_true,
    }


def chi2(L, residuals):
    z = scipy.linalg.solve_triangular(L, residuals.T, lower=True)
    return float(np.sum(z * z))


def snapshot_diagnostics(model, M, fields, t_pred):
    """The mass drift and energy-balance residual the verifier recomputes from the snapshots."""
    masses = np.array([S.total_mass(f, model.dx) for f in fields])
    mass_drift = float(abs(masses[-1] - masses[0]) / abs(masses[0]))
    energies = [S.free_energy(f, model.fcoeffs, model.kappa, model.dx) for f in fields]
    dissipations = []
    for f in fields:
        mu = S.f_prime(f, model.fcoeffs) - model.kappa * S.laplacian(f, model.dx)
        gx = (mu[:, 1:] - mu[:, :-1]) / model.dx
        gy = (mu[1:, :] - mu[:-1, :]) / model.dx
        Mx = 0.5 * (M[:, :-1] + M[:, 1:])
        My = 0.5 * (M[:-1, :] + M[1:, :])
        dissipations.append(float((np.sum(Mx * gx * gx) + np.sum(My * gy * gy))
                                  * model.dx * model.dx))
    dissipations = np.array(dissipations)
    dE = energies[-1] - energies[0]
    dD = 0.0
    for k in range(len(t_pred) - 1):
        dD += 0.5 * (t_pred[k + 1] - t_pred[k]) * (dissipations[k] + dissipations[k + 1])
    denom = max(abs(dE), abs(dD), 1e-300)
    return mass_drift, float(abs(dE + dD) / denom)


def main():
    d = load()
    model = d["model"]
    c0, phi, G, L = d["c0"], d["phi"], d["G"], d["L"]
    t_pred, y_withheld = d["t_pred"], d["y_withheld"]
    dt = d["dt"]
    dof = y_withheld.size
    print(f"[cal] sensors={G.shape[0]}  withheld points={y_withheld.size}  dof={dof}")
    print(f"[cal] dt={dt:.4e}")

    results = {"dof": int(dof), "candidates": {}}

    def evaluate(name, theta, note=""):
        t0 = time.time()
        M = model.mobility(theta, phi)
        fields = model.simulate_from(c0, theta, phi, t_pred, dt=dt)
        pred = np.stack([G @ f.ravel() for f in fields])
        c2 = chi2(L, y_withheld - pred)
        drift, resid = snapshot_diagnostics(model, M, fields, t_pred)
        results["candidates"][name] = {
            "theta": np.asarray(theta).tolist(),
            "chi2_total": c2,
            "chi2_per_dof": c2 / dof,
            "snapshot_mass_drift": drift,
            "snapshot_energy_residual": resid,
            "note": note,
        }
        print(f"[cal] {name:22s} chi2/dof={c2/dof:14.4g}   mass_drift={drift:.3e}   "
              f"energy_residual={resid:.3e}   ({time.time()-t0:.0f}s)")
        return results["candidates"][name]

    evaluate("truth", d["theta_true"], "the generating coefficients")
    evaluate("constant_mobility", np.zeros_like(d["theta_true"]),
             "the trivial null: theta = 0")
    evaluate("scaled_M", 0.8 * d["theta_true"],
             "M scaled by a constant: a time-rescaling of the truth")

    for label, path in RUNS.items():
        f = os.path.join(path, "theta.json")
        if os.path.exists(f):
            with open(f) as fh:
                theta = np.array(json.load(fh)["theta"])
            evaluate(label, theta, f"reconstruction from solution/infer.py ({label})")
        else:
            print(f"[cal] {label}: not available ({f} missing)")

    # --- the wrong flux form ------------------------------------------------
    class WrongModel(S.CHModel):
        def rhs(self, c, M, out=None):
            lap = S.laplacian(self.chemical_potential(c), self.dx)
            if out is None:
                out = np.empty_like(c)
            out[...] = M * lap
            return out

    wm = WrongModel(model.N, model.L, model.kappa, model.fcoeffs, M0=model.M0)
    M_true = model.mobility(d["theta_true"], phi)
    fields = wm.simulate_from(c0, d["theta_true"], phi, t_pred, dt=dt)
    pred = np.stack([G @ f.ravel() for f in fields])
    c2 = chi2(L, y_withheld - pred)
    drift, resid = snapshot_diagnostics(model, M_true, fields, t_pred)
    # distance of the wrong form's own prediction from the verifier's re-simulation:
    # this is what gate G4 compares.
    try:
        ref = model.simulate_from(c0, d["theta_true"], phi, t_pred, dt=dt)
        dif = [a - b for a, b in zip(fields, ref)]
        num = float(sum(float(np.sum(x * x)) for x in dif))
        den = float(sum(float(np.sum(x * x)) for x in ref))
        print(f"[cal] wrong-flux-form field vs truth field: relative L2 = {(num/den)**0.5:.4g}")
    except Exception as e:
        print(f"[cal] wrong-flux-form field comparison failed: {e}")
    results["wrong_flux_form"] = {
        "chi2_total": c2, "chi2_per_dof": c2 / dof,
        "snapshot_mass_drift": drift, "snapshot_energy_residual": resid,
        "note": "M * lap(mu) instead of div(M grad mu): non-conservative",
    }
    print(f"[cal] {'wrong_flux_form':22s} chi2/dof={c2/dof:14.4g}   mass_drift={drift:.3e}   "
          f"energy_residual={resid:.3e}")

    # --- conditioning of the sensitivity ------------------------------------
    base = np.stack([G @ f.ravel() for f in
                     model.simulate_from(c0, d["theta_true"], phi, d["t_obs"], dt=dt)])
    J = np.empty((base.size, d["theta_true"].size))
    h = 1e-4
    for k in range(d["theta_true"].size):
        tp = d["theta_true"].copy()
        tp[k] += h
        pert = np.stack([G @ f.ravel() for f in
                         model.simulate_from(c0, tp, phi, d["t_obs"], dt=dt)])
        J[:, k] = ((pert - base) / h).ravel()
    sv = np.linalg.svd(J, compute_uv=False)
    results["sensitivity"] = {
        "singular_values": sv.tolist(),
        "sv_ratio": float(sv[-1] / sv[0]),
    }
    print(f"[cal] sensitivity: max sv={sv[0]:.4g}  min sv={sv[-1]:.4g}  "
          f"ratio={sv[-1]/sv[0]:.4g}")

    with open(os.path.join(HERE, "calibration.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"[cal] wrote {os.path.join(HERE, 'calibration.json')}")


if __name__ == "__main__":
    main()
