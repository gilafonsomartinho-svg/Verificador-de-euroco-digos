"""Verification of rolled I/H steel sections to EN 1993-1-1.

What's covered:
  • Section classification (Class 1-4) per §5.5 and Table 5.2, with the
    web parameter α driven by the applied axial force.
  • Cross-section resistances N_pl,Rd, M_y,Rd, V_pl,Rd (§6.2.1–6.2.6).
  • Combined N+M interaction for doubly symmetric I/H sections (§6.2.9.1).
  • Shear-bending interaction via reduced web yield (§6.2.10).

What's **not** covered in this version:
  • Member buckling and lateral-torsional buckling — those need the
    member length plus lateral-restraint data, which the app doesn't
    collect yet. They live behind a future `member.py`.
  • Class 4 effective sections per EN 1993-1-5. For now a Class 4
    section falls back to elastic properties and the UI warns the user.
  • Bending about the weak axis (M_z) and biaxial bending.

Inputs to the public API use kN / kN·m; internal maths is in N, mm, MPa
so the formulas read like the code book.
"""

from dataclasses import dataclass

from .materials import StructuralSteel
from .sections import ISection


# --------------------------------------------------------------------------- #
# Applied forces                                                              #
# --------------------------------------------------------------------------- #

@dataclass
class Forces:
    N_Ed: float = 0.0       # axial force, compression positive [kN]
    My_Ed: float = 0.0      # bending about the strong (y-y) axis [kN·m]
    Vz_Ed: float = 0.0      # shear along z [kN]


# --------------------------------------------------------------------------- #
# Section classification                                                      #
# --------------------------------------------------------------------------- #

def _psi_web(sec: ISection, steel: StructuralSteel, N_Ed_N: float) -> float:
    """Stress ratio ψ = σ_bottom / σ_top at the web edges (Table 5.2).

    ψ = +1  → uniform compression
    ψ = −1  → pure bending

    We assume the extreme flexural fibre reaches fy and add the uniform
    axial stress. That's the worst-case reading an elastic distribution
    would give at the onset of yield.
    """
    if abs(N_Ed_N) < 1:
        return -1.0
    A_mm2 = sec.A * 100
    sigma_N = N_Ed_N / A_mm2
    sigma_M = steel.fy
    sigma_top = sigma_N + sigma_M
    sigma_bot = sigma_N - sigma_M
    if abs(sigma_top) < 1e-6:
        return -1.0
    return sigma_bot / sigma_top


def classify(sec: ISection, steel: StructuralSteel, N_Ed: float = 0.0) -> dict:
    """Classify the section per EN 1993-1-1 Table 5.2."""
    eps = steel.epsilon
    cf_tf = sec.c_over_tf()
    cw_tw = sec.c_over_tw()

    # --- flanges: outstand in compression ---------------------------------- #
    if cf_tf <= 9 * eps:
        flange_class = 1
    elif cf_tf <= 10 * eps:
        flange_class = 2
    elif cf_tf <= 14 * eps:
        flange_class = 3
    else:
        flange_class = 4

    # --- web: internal part in bending and/or compression ----------------- #
    #
    # For Class 1/2 the limit depends on α, the fraction of the web that
    # is in compression at the *plastic* neutral axis. We compute α from
    # the axial force balance on the web alone: setting Aw = cw·tw,
    #   (α − (1−α))·fy·Aw = N_Ed  →  α = ½·(1 + N_Ed/(fy·Aw))
    #
    # For Class 3 the limit depends on ψ (elastic stress ratio at the
    # edges of the web) — see `_psi_web` above.
    cw = sec.h - 2 * sec.tf - 2 * sec.r
    Aw = cw * sec.tw
    N_Ed_N = N_Ed * 1e3

    if abs(N_Ed_N) > 0:
        alpha = 0.5 * (1 + N_Ed_N / (steel.fy * Aw))
        alpha = max(0.0, min(1.0, alpha))
    else:
        alpha = 0.5    # pure bending

    if alpha > 0.5:
        c1_limit = 396 * eps / (13 * alpha - 1)
        c2_limit = 456 * eps / (13 * alpha - 1)
    else:
        c1_limit = 36 * eps / alpha if alpha > 0 else float("inf")
        c2_limit = 41.5 * eps / alpha if alpha > 0 else float("inf")

    psi = _psi_web(sec, steel, N_Ed_N)
    if psi >= -1:
        c3_limit = 42 * eps / (0.67 + 0.33 * psi)
    else:
        c3_limit = 62 * eps * (1 - psi) * (-psi) ** 0.5

    if cw_tw <= c1_limit:
        web_class = 1
    elif cw_tw <= c2_limit:
        web_class = 2
    elif cw_tw <= c3_limit:
        web_class = 3
    else:
        web_class = 4

    return {
        "flange_class": flange_class,
        "web_class": web_class,
        "section_class": max(flange_class, web_class),
        "alpha": alpha,
        "psi": psi,
        "c_over_tf": cf_tf,
        "c_over_tw": cw_tw,
        "epsilon": eps,
    }


# --------------------------------------------------------------------------- #
# Cross-section resistances                                                   #
# --------------------------------------------------------------------------- #

def cross_section_resistances(
    sec: ISection,
    steel: StructuralSteel,
    section_class: int,
) -> dict:
    """N_pl,Rd, M_y,Rd (class-dependent) and V_pl,Rd — all in kN / kN·m."""
    fy = steel.fy
    gM0 = steel.gamma_M0

    A_mm2 = sec.A * 100
    Av_mm2 = sec.Av * 100

    N_pl_Rd = A_mm2 * fy / gM0 / 1e3                # kN

    if section_class <= 2:
        Wy_mm3 = sec.Wpl_y * 1e3
    else:
        # Class 3 → elastic; Class 4 falls back to elastic here and the
        # top-level `verify` flags it. Full EN 1993-1-5 reduction is TODO.
        Wy_mm3 = sec.Wel_y * 1e3

    M_y_Rd = Wy_mm3 * fy / gM0 / 1e6                # kN·m
    V_pl_Rd = Av_mm2 * (fy / 3 ** 0.5) / gM0 / 1e3  # kN

    return {
        "N_pl_Rd": N_pl_Rd,
        "M_y_Rd": M_y_Rd,
        "V_pl_Rd": V_pl_Rd,
    }


# --------------------------------------------------------------------------- #
# Interaction: §6.2.9 (M-N) and §6.2.10 (M-V)                                 #
# --------------------------------------------------------------------------- #

def _m_n_interaction(
    sec: ISection,
    steel: StructuralSteel,
    M_y_Rd: float,
    N_pl_Rd: float,
    N_Ed: float,
) -> float:
    """Return M_N,y,Rd — the bending resistance reduced for axial force.

    Follows EN 1993-1-1 §6.2.9.1(5), eqs. (6.36) / (6.37), for doubly
    symmetric I/H sections bent about the strong axis.
    """
    if N_pl_Rd <= 0:
        return M_y_Rd

    n = abs(N_Ed) / N_pl_Rd
    A_mm2 = sec.A * 100
    a = (A_mm2 - 2 * sec.b * sec.tf) / A_mm2
    a = min(a, 0.5)

    # Small axial force — no reduction needed (eq 6.33)
    threshold_a = 0.25
    threshold_b = 0.5 * sec.hw * sec.tw * steel.fy / (N_pl_Rd * 1e3)
    if n <= threshold_a and n <= threshold_b:
        return M_y_Rd

    M_N = M_y_Rd * (1 - n) / (1 - 0.5 * a)
    return min(M_N, M_y_Rd)


# --------------------------------------------------------------------------- #
# Top-level verification                                                      #
# --------------------------------------------------------------------------- #

def verify(sec: ISection, steel: StructuralSteel, forces: Forces) -> dict:
    """Full cross-section ULS verification for combined N + M_y + V_z."""
    cls = classify(sec, steel, N_Ed=forces.N_Ed)
    section_class = cls["section_class"]
    res = cross_section_resistances(sec, steel, section_class)

    N_pl_Rd = res["N_pl_Rd"]
    M_y_Rd = res["M_y_Rd"]
    V_pl_Rd = res["V_pl_Rd"]

    # ---- shear utilization ------------------------------------------------ #
    V_ratio = abs(forces.Vz_Ed) / V_pl_Rd if V_pl_Rd > 0 else float("inf")

    # ---- shear-bending interaction, §6.2.10 ------------------------------- #
    # Below half the plastic shear capacity the reduction is waived; above
    # it we knock down the plastic modulus by (ρ·Aw²)/(4·tw).
    if V_ratio > 0.5 and section_class <= 2:
        rho = (2 * V_ratio - 1) ** 2
        Aw = sec.hw * sec.tw
        Wpl_y_mm3 = sec.Wpl_y * 1e3
        Wpl_y_red = Wpl_y_mm3 - rho * Aw ** 2 / (4 * sec.tw)
        Wpl_y_red = max(Wpl_y_red, sec.Wel_y * 1e3)     # never below elastic
        M_y_Rd_V = Wpl_y_red * steel.fy / steel.gamma_M0 / 1e6
    else:
        rho = 0.0
        M_y_Rd_V = M_y_Rd

    # ---- M-N interaction -------------------------------------------------- #
    M_y_N_Rd = _m_n_interaction(sec, steel, M_y_Rd_V, N_pl_Rd, forces.N_Ed)

    # ---- utilizations ----------------------------------------------------- #
    util_N = abs(forces.N_Ed) / N_pl_Rd if N_pl_Rd > 0 else float("inf")
    util_V = V_ratio
    util_M = abs(forces.My_Ed) / M_y_N_Rd if M_y_N_Rd > 0 else float("inf")

    max_util = max(util_N, util_V, util_M)
    return {
        "section_class": section_class,
        "classification": cls,
        "N_pl_Rd": N_pl_Rd,
        "V_pl_Rd": V_pl_Rd,
        "M_y_Rd": M_y_Rd,
        "M_y_Rd_after_V": M_y_Rd_V,
        "M_y_N_Rd": M_y_N_Rd,
        "rho_shear": rho,
        "utilization_N": util_N,
        "utilization_V": util_V,
        "utilization_M": util_M,
        "max_utilization": max_util,
        "passes": max_util <= 1.0,
    }
