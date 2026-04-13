# Eurocode Verifier

A small Streamlit web app that performs **ultimate-limit-state (ULS) checks** on
structural cross-sections according to the Eurocodes:

- **EN 1992-1-1** — reinforced concrete
- **EN 1993-1-1** — structural steel

![screenshot](docs/screenshot.png)

## The problem it solves

When you're sizing a beam, a column or a slab, the code check itself is
rarely the hard part — the friction is in flipping back and forth between
the Eurocode clauses, the material tables and a pile of section
catalogs just to answer **"is this section OK for these forces?"**.

Commercial software does this, but it's expensive, opaque, and way
overkill for the moments when you just want a quick, honest sanity
check: reviewing a colleague's spreadsheet, teaching a class, scoping
an early-stage design, or double-checking a hand calculation before
the meeting starts.

This tool is the "quick sanity check" version of that workflow. You
pick a section, a material grade and the design forces; it tells you
whether the section passes the ULS checks, shows the governing
utilization, and exposes the intermediate numbers so you can trace
every result back to a clause in the code.

It is **not** a replacement for a stamped calculation report or for
engineering judgement.

## What it checks

### EC2 — Reinforced concrete
- Rectangular section with tension and (optional) compression reinforcement
- Bending alone, or bending combined with an axial force
- Rectangular concrete stress block (§3.1.7) solved by strain compatibility
  on the neutral axis depth
- Ductility check `x/d ≤ 0.45` (concrete up to C50/60) — §5.5
- Minimum and maximum longitudinal reinforcement — §9.2.1.1

### EC3 — Structural steel
- Rolled **IPE** and **HEB** profiles from a built-in catalog
- Section classification (Class 1-4) per Table 5.2, with the web limit
  driven by the actual axial force (parameter α)
- Cross-section resistances `N_pl,Rd`, `M_y,Rd`, `V_pl,Rd` (§6.2.1–6.2.6)
- M-N interaction for doubly symmetric I/H sections (§6.2.9.1)
- Shear-bending interaction via reduced web yield (§6.2.10)

### Explicitly out of scope (for now)
- Member buckling and lateral-torsional buckling — these need member
  length and lateral-restraint data the app doesn't collect yet
- Class 4 effective sections per EN 1993-1-5 (the app falls back to
  elastic properties and warns the user)
- Biaxial bending, second-order effects, fatigue, serviceability checks

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL, usually <http://localhost:8501>.

## Tests

```bash
pytest
```

The test suite validates the EC2 routines against a hand-calculated
rectangular beam example and the EC3 routines against the standard
IPE 300 / HEB 200 values from the European profile tables.

## Project layout

```
.
├── app.py                    # Streamlit UI
├── eurocodes/
│   ├── materials.py          # Concrete, rebar and structural-steel grades
│   ├── sections.py           # IPE / HEB catalog with geometric properties
│   ├── ec2_concrete.py       # EN 1992-1-1 verification
│   └── ec3_steel.py          # EN 1993-1-1 verification
├── tests/
│   ├── test_ec2.py
│   └── test_ec3.py
├── requirements.txt
└── README.md
```

## Units

User inputs are in **kN, kN·m, mm and MPa**, because that's what shows
up on every structural drawing. Internally everything runs in N and mm
so the formulas read like the code book.

## Disclaimer

Use this as a sanity-check helper, not as a structural calculation
report. The author takes no responsibility for decisions made on the
basis of its output — verify with your usual tools and your usual
engineering judgement.

## License

MIT.
