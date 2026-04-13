"""Regression tests for the EC2 verification routines.

Values come from worked examples in the Portuguese reference
"Estruturas de Betão Armado I" (IST lecture notes) and from hand
calculations using the rectangular stress block with λ=0.8, η=1.0.
"""

import math

import pytest

from eurocodes import ec2_concrete
from eurocodes.materials import CONCRETE_GRADES, REBAR_GRADES


def _section(**overrides):
    defaults = dict(
        b=300, h=500, d=450,
        As=1500, d_prime=40, As_comp=0,
        concrete=CONCRETE_GRADES["C25/30"],
        steel=REBAR_GRADES["A500 NR"],
    )
    defaults.update(overrides)
    return ec2_concrete.RCSection(**defaults)


def test_pure_bending_hand_calc():
    """Single layer of As = 1500 mm², C25/30, A500 — hand calc gives ≈ 250 kN·m."""
    sec = _section()
    res = ec2_concrete.resistance(sec, N_Ed=0.0)

    # fcd = 25/1.5 ≈ 16.67 MPa, fyd = 500/1.15 ≈ 434.78 MPa
    # x = As·fyd / (η·fcd·b·λ) ≈ 163 mm
    # z = d − λx/2 ≈ 385 mm
    # M_Rd ≈ 1500 · 434.78 · 385 / 1e6 ≈ 251 kN·m
    assert math.isclose(res["x"], 163, rel_tol=0.03)
    assert math.isclose(res["M_Rd_kNm"], 251, rel_tol=0.03)
    assert res["ductile"] is True
    assert res["As_ok"] is True


def test_verify_passes_just_under_capacity():
    sec = _section()
    res = ec2_concrete.verify(sec, M_Ed=240.0)
    assert res["passes"]
    assert res["utilization"] < 1.0


def test_verify_fails_above_capacity():
    sec = _section()
    res = ec2_concrete.verify(sec, M_Ed=300.0)
    assert not res["passes"]
    assert res["utilization"] > 1.0


def test_over_reinforced_fails_ductility():
    """Cram too much steel in — x/d shoots past 0.45."""
    sec = _section(As=4500)
    res = ec2_concrete.resistance(sec)
    assert res["x_over_d"] > 0.45
    assert res["ductile"] is False


def test_compression_axial_raises_m_rd_slightly():
    """Small compression moves the NA down and should lift M_Rd a bit."""
    sec = _section()
    m0 = ec2_concrete.resistance(sec, N_Ed=0.0)["M_Rd_kNm"]
    m1 = ec2_concrete.resistance(sec, N_Ed=200.0)["M_Rd_kNm"]
    assert m1 > m0


def test_below_minimum_reinforcement_flagged():
    sec = _section(As=100)
    res = ec2_concrete.resistance(sec)
    assert not res["As_ok"]


def test_excessive_axial_raises():
    sec = _section()
    with pytest.raises(ValueError):
        ec2_concrete.resistance(sec, N_Ed=1e6)  # absurd compression
