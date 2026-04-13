"""Eurocode Verifier — Streamlit UI.

Two tabs, two codes:
  • EC2 — rectangular reinforced-concrete section under bending (+ N)
  • EC3 — rolled I/H steel section under N + M_y + V_z

Run with:
    streamlit run app.py
"""

from math import pi

import streamlit as st

from eurocodes import ec2_concrete, ec3_steel
from eurocodes.materials import (
    CONCRETE_GRADES,
    REBAR_GRADES,
    STEEL_GRADES,
)
from eurocodes.sections import HEB_PROFILES, IPE_PROFILES


st.set_page_config(
    page_title="Eurocode Verifier",
    page_icon="🏗️",
    layout="wide",
)

st.title("Eurocode Verifier")
st.caption(
    "ULS checks of structural cross-sections to EN 1992-1-1 "
    "(reinforced concrete) and EN 1993-1-1 (structural steel)."
)

tab_ec2, tab_ec3 = st.tabs(
    ["🧱  EC2 — Reinforced Concrete", "🔩  EC3 — Steel"]
)


# =========================================================================== #
#  EC2  —  Rectangular reinforced-concrete section                            #
# =========================================================================== #

with tab_ec2:
    st.subheader("Rectangular RC section under bending (with optional axial)")

    col_geom, col_mat, col_loads = st.columns(3)

    with col_geom:
        st.markdown("**Geometry & reinforcement**")
        b = st.number_input("Width b [mm]", 100, 2000, 300, step=10)
        h = st.number_input("Height h [mm]", 100, 3000, 500, step=10)
        cover = st.number_input(
            "Distance from tension face to steel centroid [mm]",
            20, 200, 50,
        )
        d = h - cover
        st.caption(f"→ effective depth d = **{d} mm**")

        n_bars = st.number_input("Tension bars — count", 2, 20, 4)
        d_bar = st.number_input("Tension bars — Ø [mm]", 8, 40, 16)
        As = n_bars * pi * d_bar ** 2 / 4
        st.caption(f"→ As = **{As:.0f} mm²**")

        with st.expander("Compression reinforcement (optional)"):
            n_bars_c = st.number_input("Compression bars — count", 0, 20, 0)
            d_bar_c = st.number_input("Compression bars — Ø [mm]", 8, 40, 12)
            As_comp = n_bars_c * pi * d_bar_c ** 2 / 4
            d_prime = st.number_input("d' [mm]", 20, 200, 40)

    with col_mat:
        st.markdown("**Materials**")
        conc_name = st.selectbox(
            "Concrete class", list(CONCRETE_GRADES.keys()), index=2
        )
        rebar_name = st.selectbox(
            "Reinforcement grade", list(REBAR_GRADES.keys()), index=1
        )
        conc = CONCRETE_GRADES[conc_name]
        rebar = REBAR_GRADES[rebar_name]
        st.markdown("---")
        st.caption(f"f_cd = {conc.fcd:.2f} MPa")
        st.caption(f"f_yd = {rebar.fyd:.1f} MPa")
        st.caption(f"ε_cu3 = {conc.epsilon_cu3 * 1000:.2f} ‰")

    with col_loads:
        st.markdown("**Design forces (ULS)**")
        M_Ed = st.number_input("M_Ed [kN·m]", value=150.0, step=10.0)
        N_Ed = st.number_input(
            "N_Ed [kN] (compression positive)",
            value=0.0, step=10.0,
        )

    sec = ec2_concrete.RCSection(
        b=b, h=h, d=d,
        As=As,
        d_prime=d_prime,
        As_comp=As_comp,
        concrete=conc,
        steel=rebar,
    )

    if st.button("Run check", key="run_ec2", type="primary"):
        try:
            res = ec2_concrete.verify(sec, M_Ed=M_Ed, N_Ed=N_Ed)
        except ValueError as err:
            st.error(f"Could not solve the section: {err}")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("M_Rd", f"{res['M_Rd_kNm']:.1f} kN·m")
            c2.metric(
                "Utilization",
                f"{res['utilization'] * 100:.0f} %",
            )
            c3.metric(
                "x / d",
                f"{res['x_over_d']:.2f}",
                delta=f"limit {res['x_over_d_limit']:.2f}",
                delta_color="off",
            )

            if res["passes"]:
                st.success("Section verifies — all ULS checks passed.")
            else:
                issues = []
                if res["utilization"] > 1:
                    issues.append("M_Ed > M_Rd")
                if not res["ductile"]:
                    issues.append("x/d exceeds ductility limit")
                if not res["As_ok"]:
                    issues.append("As outside [As_min, As_max]")
                st.error("Section does **not** verify: " + "; ".join(issues))

            with st.expander("Details"):
                st.json({
                    "x [mm]":          round(res["x"], 1),
                    "M_Rd [kN·m]":     round(res["M_Rd_kNm"], 2),
                    "M_Ed [kN·m]":     round(M_Ed, 2),
                    "As provided [mm²]": round(As, 0),
                    "As_min [mm²]":    round(res["As_min_mm2"], 0),
                    "As_max [mm²]":    round(res["As_max_mm2"], 0),
                    "x/d":             round(res["x_over_d"], 3),
                    "ductile":         res["ductile"],
                    "As_ok":           res["As_ok"],
                })


# =========================================================================== #
#  EC3  —  Rolled I / H section                                               #
# =========================================================================== #

with tab_ec3:
    st.subheader("Rolled I/H profile under N + M_y + V_z")

    col_sec, col_mat, col_loads = st.columns(3)

    with col_sec:
        st.markdown("**Section**")
        family = st.radio(
            "Family", ["IPE", "HEB"], horizontal=True, key="family"
        )
        catalog = IPE_PROFILES if family == "IPE" else HEB_PROFILES
        prof_name = st.selectbox("Profile", list(catalog.keys()))
        sec_steel = catalog[prof_name]
        st.caption(
            f"h = {sec_steel.h:g} mm · b = {sec_steel.b:g} mm · "
            f"tw = {sec_steel.tw:g} mm · tf = {sec_steel.tf:g} mm"
        )
        st.caption(
            f"A = {sec_steel.A:.1f} cm² · "
            f"W_pl,y = {sec_steel.Wpl_y:.0f} cm³ · "
            f"I_y = {sec_steel.Iy:.0f} cm⁴"
        )

    with col_mat:
        st.markdown("**Steel grade**")
        steel_name = st.selectbox(
            "Grade", list(STEEL_GRADES.keys()), index=2
        )
        steel = STEEL_GRADES[steel_name]
        st.caption(f"f_y = {steel.fy} MPa · f_u = {steel.fu} MPa")
        st.caption(f"ε = √(235/f_y) = {steel.epsilon:.3f}")

    with col_loads:
        st.markdown("**Design forces (ULS)**")
        N_Ed = st.number_input(
            "N_Ed [kN] (compression positive)",
            value=0.0, step=10.0, key="st_n",
        )
        My_Ed = st.number_input(
            "M_y,Ed [kN·m]", value=100.0, step=10.0, key="st_m",
        )
        Vz_Ed = st.number_input(
            "V_z,Ed [kN]", value=50.0, step=5.0, key="st_v",
        )

    if st.button("Run check", key="run_ec3", type="primary"):
        forces = ec3_steel.Forces(N_Ed=N_Ed, My_Ed=My_Ed, Vz_Ed=Vz_Ed)
        res = ec3_steel.verify(sec_steel, steel, forces)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Class", f"{res['section_class']}")
        c2.metric("N_pl,Rd", f"{res['N_pl_Rd']:.0f} kN")
        c3.metric("M_y,Rd", f"{res['M_y_Rd']:.1f} kN·m")
        c4.metric("V_pl,Rd", f"{res['V_pl_Rd']:.0f} kN")

        st.markdown("**Utilizations**")
        u1, u2, u3 = st.columns(3)
        u1.progress(
            min(res["utilization_N"], 1.0),
            text=f"N:  {res['utilization_N'] * 100:.0f} %",
        )
        u2.progress(
            min(res["utilization_M"], 1.0),
            text=f"M:  {res['utilization_M'] * 100:.0f} %",
        )
        u3.progress(
            min(res["utilization_V"], 1.0),
            text=f"V:  {res['utilization_V'] * 100:.0f} %",
        )

        if res["passes"]:
            st.success(
                f"Section verifies — peak utilization "
                f"{res['max_utilization'] * 100:.0f} %."
            )
        else:
            st.error(
                f"Section does **not** verify — peak utilization "
                f"{res['max_utilization'] * 100:.0f} %."
            )

        if res["section_class"] == 4:
            st.warning(
                "Class 4 cross-section: v1 falls back to elastic section "
                "properties. A proper EN 1993-1-5 effective-section "
                "calculation is not yet implemented."
            )

        with st.expander("Details"):
            st.json({
                "section_class":        res["section_class"],
                "α (web)":              round(res["classification"]["alpha"], 3),
                "ψ (web)":              round(res["classification"]["psi"], 3),
                "c/tf":                 round(res["classification"]["c_over_tf"], 2),
                "c/tw":                 round(res["classification"]["c_over_tw"], 2),
                "M_y,Rd after shear":   round(res["M_y_Rd_after_V"], 2),
                "M_y,N,Rd (with N)":    round(res["M_y_N_Rd"], 2),
                "ρ (shear factor)":     round(res["rho_shear"], 4),
            })


st.markdown("---")
st.caption(
    "References: EN 1992-1-1:2004 §3.1.7, §5.5, §6.1, §9.2.1.1 · "
    "EN 1993-1-1:2005 §5.5, §6.2.1-6.2.10. "
    "Member buckling, lateral-torsional buckling and Class 4 effective "
    "sections are out of scope for this release."
)
