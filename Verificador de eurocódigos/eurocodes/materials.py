"""Material grades from EN 1992-1-1 (concrete, rebar) and EN 1993-1-1 (steel).

All stresses are in MPa (= N/mm²), strains are dimensionless.
"""

from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# Concrete                                                                    #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Concrete:
    name: str
    fck: float      # characteristic cylinder strength [MPa]
    fctm: float     # mean axial tensile strength [MPa]
    Ecm: float      # secant modulus [GPa]

    # γc and αcc for persistent/transient situations (EN 1992-1-1 §3.1.6)
    gamma_c: float = 1.5
    alpha_cc: float = 1.0

    @property
    def fcd(self) -> float:
        return self.alpha_cc * self.fck / self.gamma_c

    @property
    def epsilon_cu3(self) -> float:
        # Ultimate concrete strain for the rectangular stress block (§3.1.7)
        if self.fck <= 50:
            return 3.5e-3
        return (2.6 + 35 * ((90 - self.fck) / 100) ** 4) * 1e-3

    @property
    def lambda_(self) -> float:
        # Effective height factor of the rectangular block
        if self.fck <= 50:
            return 0.80
        return 0.80 - (self.fck - 50) / 400

    @property
    def eta(self) -> float:
        # Effective strength factor of the rectangular block
        if self.fck <= 50:
            return 1.00
        return 1.00 - (self.fck - 50) / 200


CONCRETE_GRADES = {
    "C20/25": Concrete("C20/25", fck=20, fctm=2.2, Ecm=30),
    "C25/30": Concrete("C25/30", fck=25, fctm=2.6, Ecm=31),
    "C30/37": Concrete("C30/37", fck=30, fctm=2.9, Ecm=33),
    "C35/45": Concrete("C35/45", fck=35, fctm=3.2, Ecm=34),
    "C40/50": Concrete("C40/50", fck=40, fctm=3.5, Ecm=35),
    "C45/55": Concrete("C45/55", fck=45, fctm=3.8, Ecm=36),
    "C50/60": Concrete("C50/60", fck=50, fctm=4.1, Ecm=37),
}


# --------------------------------------------------------------------------- #
# Reinforcement                                                               #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ReinforcementSteel:
    name: str
    fyk: float              # characteristic yield [MPa]
    Es: float = 200_000     # elastic modulus [MPa]
    gamma_s: float = 1.15

    @property
    def fyd(self) -> float:
        return self.fyk / self.gamma_s

    @property
    def epsilon_yd(self) -> float:
        return self.fyd / self.Es


REBAR_GRADES = {
    "A400 NR":  ReinforcementSteel("A400 NR",  fyk=400),
    "A500 NR":  ReinforcementSteel("A500 NR",  fyk=500),  # most common in PT
    "B500B":    ReinforcementSteel("B500B",    fyk=500),
}


# --------------------------------------------------------------------------- #
# Structural steel                                                            #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class StructuralSteel:
    name: str
    fy: float           # yield strength for t ≤ 40 mm [MPa]
    fu: float           # ultimate strength [MPa]
    E: float = 210_000  # MPa
    gamma_M0: float = 1.0

    @property
    def epsilon(self) -> float:
        # ε = √(235 / fy) — shows up in every Class 1-4 slenderness limit
        return (235 / self.fy) ** 0.5


STEEL_GRADES = {
    "S235": StructuralSteel("S235", fy=235, fu=360),
    "S275": StructuralSteel("S275", fy=275, fu=430),
    "S355": StructuralSteel("S355", fy=355, fu=490),
    "S460": StructuralSteel("S460", fy=460, fu=540),
}
