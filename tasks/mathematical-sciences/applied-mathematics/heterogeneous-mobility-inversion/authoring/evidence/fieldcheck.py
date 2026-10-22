"""Field-level separation study for the heterogeneous-mobility inversion task.

Author-side evidence.  Answers the question the covariance-weighted numbers cannot: how far apart
are the wrong-flux-form trajectory, the constant-mobility trajectory, and the truth, in units of
the field itself?  If the wrong flux form is only 1 per cent away in L2 while the observations are
10 per cent uncertain, G4's field-agreement gate cannot be set tighter than the noise floor, and
the physics diagnostics have to do their own work.

Run from the task root:

    python authoring/evidence/fieldcheck.py
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import scipy.sparse

HERE = os.path.dirname(os.path.abspath(__file__))
TASK_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(TASK_ROOT, "environment", "data")
sys.path.insert(0, os.path.join(DATA, "mobility_solver"))

import solver as S  # noqa: E402


class WrongModel(S.CHModel):
    """The non-conservative flux form: M * lap(mu)."""

    def rhs(self, c, M, out=None):
        lap = S.laplacian(self.chemical_potential(c), self.dx)
        if out is None:
            out = np.empty_like(c)
        out[...] = M * lap
        return out


def main():
    ic = np.load(os.path.join(DATA, "initial_condition.npz"))
    basis = np.load(os.path.join(DATA, "basis.npz"))
    model = S.CHModel(ic["c0"].shape[0], float(ic["L"]), float(ic["kappa"]),
                      ic["f_coeffs"], M0=float(basis["M0"]))
    t_obs, t_pred = ic["times_obs"], ic["times_pred"]
    th = np.array(json.load(open(os.path.join(
        TASK_ROOT, "authoring", "provenance", "theta_true.json")))["theta_true"])
    phi = basis["phi"]
    dt = model.stable_dt()
    wm = WrongModel(model.N, model.L, model.kappa, model.fcoeffs, M0=model.M0)
    M = model.mobility(th, phi)

    print(f"[fc] M in [{M.min():.3f}, {M.max():.3f}]  mean {M.mean():.3f}")

    ref_pred = model.simulate_from(ic["c0"], th, phi, t_pred, dt=dt)
    wrong_pred = wm.simulate_from(ic["c0"], th, phi, t_pred, dt=dt)
    null_pred = model.simulate_from(ic["c0"], np.zeros_like(th), phi, t_pred, dt=dt)

    print(f"[fc] {'gate':28s} {'t=18':>10s} {'t=22':>10s} {'t=26':>10s}")
    for label, fields in (("wrong-flux-form vs truth", wrong_pred),
                          ("constant-mobility vs truth", null_pred)):
        vals = []
        for f, r in zip(fields, ref_pred):
            num = float(np.linalg.norm(f - r))
            den = max(float(np.linalg.norm(r)), 1e-300)
            vals.append(num / den)
        print(f"[fc] {label:28s} {vals[0]:10.4f} {vals[1]:10.4f} {vals[2]:10.4f}")

    # the verifier's own G4 inputs: mass drift and the snapshot energy residual
    for label, fields in (("truth", ref_pred), ("wrong-flux-form", wrong_pred),
                          ("constant-mobility", null_pred)):
        masses = np.array([S.total_mass(f, model.dx) for f in fields])
        m0 = S.total_mass(ic["c0"], model.dx)
        drift = float(abs(masses[-1] - masses[0]) / abs(masses[0]))
        energies = [S.free_energy(f, model.fcoeffs, model.kappa, model.dx) for f in fields]
        dE = energies[-1] - energies[0]
        diss = []
        for f, Mm in zip(fields, [M, M, M][:1] * 3):
            mu = S.f_prime(f, model.fcoeffs) - model.kappa * S.laplacian(f, model.dx)
            gx = (mu[:, 1:] - mu[:, :-1]) / model.dx
            gy = (mu[1:, :] - mu[:-1, :]) / model.dx
            Mx = 0.5 * (M[:, :-1] + M[:, 1:])
            My = 0.5 * (M[:-1, :] + M[1:, :])
            diss.append(float((np.sum(Mx * gx * gx) + np.sum(My * gy * gy))
                               * model.dx * model.dx))
        diss = np.array(diss)
        dD = 0.0
        for k in range(len(t_pred) - 1):
            dD += 0.5 * (t_pred[k + 1] - t_pred[k]) * (diss[k] + diss[k + 1])
        denom = max(abs(dE), abs(dD), 1e-300)
        print(f"[fc] {label:28s} mass_drift={drift:.3e}  energy_residual={abs(dE+dD)/denom:.4f}")


if __name__ == "__main__":
    main()
