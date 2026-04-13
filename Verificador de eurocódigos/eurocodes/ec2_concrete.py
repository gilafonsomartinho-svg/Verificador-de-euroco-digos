"""Verification of rectangular reinforced-concrete sections to EN 1992-1-1.

Covers ULS bending — with or without an applied axial force — using the
rectangular stress block (§3.1.7). Strain compatibility is solved by
bisection on the neutral-axis depth `x`.

Sign convention throughout: **compression positive** (both forces and
stresses). Internal units are N, mm, MPa; the public API takes / returns
kN and kN·m because that's what every structural drawing prints.

Out of scope here: flanged (T) sections, circular sections, biaxial
bending, torsion, SLS and second-order effects. The rectangular case
covers most beams, slab strips and column bases encountered in practice.
"""

from dataclasses import dataclass

from .materials import Concrete, ReinforcementSteel


# --------------------------------------------------------------------------- #
# Data class                                                                  #
# --------------------------------------------------------------------------- #

@dataclass
class RCSection:
    b: float            # width [mm]
    h: float            # total height [mm]
    d: float            # effective depth to tension steel [mm]
    As: float           # tension reinforcement area [mm²]
    d_prime: float = 40.0   # depth to compression steel centroid [mm]
    As_comp: float = 0.0    # compression reinforcement area [mm²]
    concrete: Concrete = None
    steel: ReinforcementSteel = None


# --------------------------------------------------------------------------- #
# Internal helpers                                                            #
# --------------------------------------------------------------------------- #

def _steel_stress(strain: float, steel: ReinforcementSteel) -> float:
    """Bilinear elastic / perfectly-plastic σ(ε) for reinforcement."""
    sigma = steel.Es * strain
    return max(-steel.fyd, min(steel.fyd, sigma))


def _section_forces(sec: RCSection, x: float) -> tuple[float, float]:
    """Return (N_Rd, M_Rd) for a trial neutral-axis depth `x` [mm].

    Forces in N, moments in N·mm, taken about the mid-height of the section.
    The strain distribution is linear with εcu3 at the top compression fibre.
    Once λ·x would exceed h the compression block is capped at the full
    section — equivalent to saying "there's no more concrete to compress".
    """
    c = sec.concrete
    eps_cu = c.epsilon_cu3

    # linear strain field, anchor = εcu at y=0 (top fibre)
    eps_top = eps_cu * (x - sec.d_prime) / x
    eps_bot = eps_cu * (x - sec.d) / x

    sigma_top = _steel_stress(eps_top, sec.steel)
    sigma_bot = _steel_stress(eps_bot, sec.steel)

    # concrete rectangular block, stress = η·fcd over a depth of λ·x
    block_depth = min(c.lambda_ * x, sec.h)
    Fc = c.eta * c.fcd * sec.b * block_depth
    Fs_top = sec.As_comp * sigma_top
    Fs_bot = sec.As * sigma_bot

    N = Fc + Fs_top + Fs_bot

    # lever arms measured from mid-height (compression +)
    z_c = sec.h / 2 - block_depth / 2
    z_top = sec.h / 2 - sec.d_prime
    z_bot = sec.h / 2 - sec.d

    M = Fc * z_c + Fs_top * z_top + Fs_bot * z_bot
    return N, M


def _find_neutral_axis(sec: RCSection, N_target: float) -> float:
    """Bisect on x so that N_Rd(x) = N_target [N].

    N_Rd(x) is monotonically non-decreasing in x (more compressed concrete,
    steel stresses drifting from tension to compression), so bisection is
    safe as long as the target is within the bracket.
    """
    lo, hi = 1e-3, 5 * sec.h
    f_lo = _section_forces(sec, lo)[0] - N_target
    f_hi = _section_forces(sec, hi)[0] - N_target

    if f_lo > 0:
        raise ValueError(
            "Required axial force is below the section's tensile capacity "
            "(N_Ed too negative)."
        )
    if f_hi < 0:
        raise ValueError(
            "Required axial force exceeds the section's compressive capacity."
        )

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = _section_forces(sec, mid)[0] - N_target
        if abs(f_mid) < 1.0:    # 1 N is plenty
            return mid
        if f_mid < 0:
            lo = mid
        else:
            hi = mid
    return mid


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #

def resistance(sec: RCSection, N_Ed: float = 0.0) -> dict:
    """Compute the bending resistance M_Rd [kN·m] under an axial force N_Ed [kN].

    Also returns the neutral-axis depth, the ductility check (x/d ≤ limit)
    and minimum / maximum reinforcement checks from §9.2.1.1.
    """
    N_Ed_N = N_Ed * 1e3     # kN → N
    x = _find_neutral_axis(sec, N_Ed_N)
    _, M_Rd_Nmm = _section_forces(sec, x)
    M_Rd = M_Rd_Nmm / 1e6   # N·mm → kN·m

    # ductility — EC2 §5.5(4), without moment redistribution
    x_over_d_limit = 0.45 if sec.concrete.fck <= 50 else 0.35
    ductile = (x / sec.d) <= x_over_d_limit

    # min/max longitudinal reinforcement for beams — §9.2.1.1
    fctm = sec.concrete.fctm
    fyk = sec.steel.fyk
    As_min = max(0.26 * fctm * sec.b * sec.d / fyk, 0.0013 * sec.b * sec.d)
    As_max = 0.04 * sec.b * sec.h

    return {
        "x": x,
        "x_over_d": x / sec.d,
        "x_over_d_limit": x_over_d_limit,
        "ductile": ductile,
        "M_Rd_kNm": M_Rd,
        "N_Ed_kN": N_Ed,
        "As_min_mm2": As_min,
        "As_max_mm2": As_max,
        "As_ok": As_min <= sec.As <= As_max,
    }


def verify(sec: RCSection, M_Ed: float, N_Ed: float = 0.0) -> dict:
    """Top-level ULS check: compares M_Ed [kN·m] against M_Rd.

    A section "passes" when M_Ed ≤ M_Rd, the section is ductile
    (x/d below the limit) and the reinforcement area is within the
    code's min / max bounds.
    """
    res = resistance(sec, N_Ed=N_Ed)
    res["M_Ed_kNm"] = M_Ed
    res["utilization"] = (
        M_Ed / res["M_Rd_kNm"] if res["M_Rd_kNm"] > 0 else float("inf")
    )
    res["passes"] = (
        res["utilization"] <= 1.0
        and res["ductile"]
        and res["As_ok"]
    )
    return res
