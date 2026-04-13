"""Regression tests for the EC3 verification routines.

Reference values are from standard European profile tables (IPE 300,
HEB 200 in S235) combined with the formulas in EN 1993-1-1 §6.2.
"""

import math

from eurocodes import ec3_steel
from eurocodes.materials import STEEL_GRADES
from eurocodes.sections import HEB_PROFILES, IPE_PROFILES


S235 = STEEL_GRADES["S235"]
S355 = STEEL_GRADES["S355"]


# --------------------------------------------------------------------------- #
# Classification                                                              #
# --------------------------------------------------------------------------- #

def test_ipe300_s235_is_class_1_in_pure_bending():
    """IPE 300 in S235, pure bending: both flange and web are Class 1."""
    cls = ec3_steel.classify(IPE_PROFILES["IPE 300"], S235, N_Ed=0)
    assert cls["flange_class"] == 1
    assert cls["web_class"] == 1
    assert cls["section_class"] == 1


def test_heb200_s235_is_class_1_in_pure_bending():
    cls = ec3_steel.classify(HEB_PROFILES["HEB 200"], S235, N_Ed=0)
    assert cls["section_class"] == 1


# --------------------------------------------------------------------------- #
# Cross-section resistances                                                   #
# --------------------------------------------------------------------------- #

def test_ipe300_s235_basic_resistances():
    """
    Hand values for IPE 300, S235 (γM0 = 1.0):
      N_pl,Rd = A · fy        = 53.81 cm² · 23.5 kN/cm² ≈ 1264 kN
      M_pl,y  = Wpl,y · fy    = 628.4 cm³ · 23.5 kN/cm² ≈ 1476.7 kN·cm ≈ 147.7 kN·m
      V_pl,Rd = Av · fy/√3    ≈ 25.68 cm² · 13.57 kN/cm² ≈ 348.4 kN
    """
    sec = IPE_PROFILES["IPE 300"]
    res = ec3_steel.cross_section_resistances(sec, S235, section_class=1)

    assert math.isclose(res["N_pl_Rd"], 1264.5, rel_tol=0.01)
    assert math.isclose(res["M_y_Rd"], 147.7, rel_tol=0.01)
    assert math.isclose(res["V_pl_Rd"], 348.4, rel_tol=0.02)


# --------------------------------------------------------------------------- #
# Top-level verification                                                      #
# --------------------------------------------------------------------------- #

def test_ipe300_passes_under_moderate_bending():
    forces = ec3_steel.Forces(N_Ed=0, My_Ed=120, Vz_Ed=50)
    res = ec3_steel.verify(IPE_PROFILES["IPE 300"], S235, forces)
    assert res["passes"]
    assert res["max_utilization"] < 1.0


def test_ipe300_fails_when_moment_exceeds_mrd():
    forces = ec3_steel.Forces(N_Ed=0, My_Ed=200, Vz_Ed=0)
    res = ec3_steel.verify(IPE_PROFILES["IPE 300"], S235, forces)
    assert not res["passes"]
    assert res["utilization_M"] > 1.0


def test_large_axial_reduces_bending_capacity():
    """N close to half the plastic capacity should bite into M_N,y,Rd."""
    sec = IPE_PROFILES["IPE 300"]
    base = ec3_steel.verify(sec, S235,
                            ec3_steel.Forces(N_Ed=0, My_Ed=100, Vz_Ed=0))
    with_N = ec3_steel.verify(sec, S235,
                              ec3_steel.Forces(N_Ed=600, My_Ed=100, Vz_Ed=0))
    assert with_N["M_y_N_Rd"] < base["M_y_N_Rd"]


def test_shear_above_half_vpl_reduces_mrd():
    sec = IPE_PROFILES["IPE 300"]
    low_v = ec3_steel.verify(sec, S235,
                             ec3_steel.Forces(N_Ed=0, My_Ed=100, Vz_Ed=100))
    high_v = ec3_steel.verify(sec, S235,
                              ec3_steel.Forces(N_Ed=0, My_Ed=100, Vz_Ed=300))
    assert high_v["M_y_Rd_after_V"] < low_v["M_y_Rd_after_V"]


def test_higher_grade_gives_higher_resistances():
    sec = IPE_PROFILES["IPE 300"]
    r235 = ec3_steel.cross_section_resistances(sec, S235, section_class=1)
    r355 = ec3_steel.cross_section_resistances(sec, S355, section_class=1)
    assert r355["N_pl_Rd"] > r235["N_pl_Rd"]
    assert r355["M_y_Rd"] > r235["M_y_Rd"]
