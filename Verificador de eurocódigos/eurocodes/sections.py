"""Catalog of European rolled I/H profiles (IPE and HEB).

Geometric properties taken from the standard profile tables used across
European steel constructors' documentation (e.g. ArcelorMittal, Peiner,
Eurostandard). Units:

    h, b, tw, tf, r     [mm]
    A                   [cm²]
    Iy, Iz              [cm⁴]
    Wel_*, Wpl_*        [cm³]
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ISection:
    name: str
    h: float
    b: float
    tw: float
    tf: float
    r: float
    A: float
    Iy: float
    Wel_y: float
    Wpl_y: float
    Iz: float
    Wel_z: float
    Wpl_z: float

    # -- derived geometry ------------------------------------------------- #

    @property
    def hw(self) -> float:
        """Clear web height between flanges [mm]."""
        return self.h - 2 * self.tf

    @property
    def Av(self) -> float:
        """Shear area for vertical shear, EN 1993-1-1 §6.2.6(3)a) [cm²].

        Av = A − 2·b·tf + (tw + 2·r)·tf,  but not less than η·hw·tw (η = 1.20).
        """
        A_mm2 = self.A * 100
        Av_mm2 = A_mm2 - 2 * self.b * self.tf + (self.tw + 2 * self.r) * self.tf
        Av_min = 1.20 * self.hw * self.tw
        return max(Av_mm2, Av_min) / 100  # back to cm²

    # -- slenderness ratios used for classification ----------------------- #

    def c_over_tf(self) -> float:
        """Flange outstand c/tf (Table 5.2 — flange in compression)."""
        c = (self.b - self.tw - 2 * self.r) / 2
        return c / self.tf

    def c_over_tw(self) -> float:
        """Web c/tw (Table 5.2 — internal compression part)."""
        c = self.h - 2 * self.tf - 2 * self.r
        return c / self.tw


# --------------------------------------------------------------------------- #
# IPE (narrow-flange I beams)                                                 #
# --------------------------------------------------------------------------- #

IPE_PROFILES = {
    "IPE 100": ISection("IPE 100", h=100, b=55,  tw=4.1, tf=5.7,  r=7,
                        A=10.32, Iy=171,    Wel_y=34.2,  Wpl_y=39.41,
                        Iz=15.92, Wel_z=5.79, Wpl_z=9.146),
    "IPE 120": ISection("IPE 120", h=120, b=64,  tw=4.4, tf=6.3,  r=7,
                        A=13.21, Iy=317.8,  Wel_y=52.96, Wpl_y=60.73,
                        Iz=27.67, Wel_z=8.65, Wpl_z=13.58),
    "IPE 140": ISection("IPE 140", h=140, b=73,  tw=4.7, tf=6.9,  r=7,
                        A=16.43, Iy=541.2,  Wel_y=77.32, Wpl_y=88.34,
                        Iz=44.92, Wel_z=12.31, Wpl_z=19.25),
    "IPE 160": ISection("IPE 160", h=160, b=82,  tw=5.0, tf=7.4,  r=9,
                        A=20.09, Iy=869.3,  Wel_y=108.7, Wpl_y=123.9,
                        Iz=68.31, Wel_z=16.66, Wpl_z=26.10),
    "IPE 180": ISection("IPE 180", h=180, b=91,  tw=5.3, tf=8.0,  r=9,
                        A=23.95, Iy=1317,   Wel_y=146.3, Wpl_y=166.4,
                        Iz=100.9, Wel_z=22.16, Wpl_z=34.60),
    "IPE 200": ISection("IPE 200", h=200, b=100, tw=5.6, tf=8.5,  r=12,
                        A=28.48, Iy=1943,   Wel_y=194.3, Wpl_y=220.6,
                        Iz=142.4, Wel_z=28.47, Wpl_z=44.61),
    "IPE 220": ISection("IPE 220", h=220, b=110, tw=5.9, tf=9.2,  r=12,
                        A=33.37, Iy=2772,   Wel_y=252.0, Wpl_y=285.4,
                        Iz=204.9, Wel_z=37.25, Wpl_z=58.11),
    "IPE 240": ISection("IPE 240", h=240, b=120, tw=6.2, tf=9.8,  r=15,
                        A=39.12, Iy=3892,   Wel_y=324.3, Wpl_y=366.6,
                        Iz=283.6, Wel_z=47.27, Wpl_z=73.92),
    "IPE 270": ISection("IPE 270", h=270, b=135, tw=6.6, tf=10.2, r=15,
                        A=45.95, Iy=5790,   Wel_y=428.9, Wpl_y=484.0,
                        Iz=419.9, Wel_z=62.20, Wpl_z=96.95),
    "IPE 300": ISection("IPE 300", h=300, b=150, tw=7.1, tf=10.7, r=15,
                        A=53.81, Iy=8356,   Wel_y=557.1, Wpl_y=628.4,
                        Iz=603.8, Wel_z=80.50, Wpl_z=125.2),
    "IPE 330": ISection("IPE 330", h=330, b=160, tw=7.5, tf=11.5, r=18,
                        A=62.61, Iy=11770,  Wel_y=713.1, Wpl_y=804.3,
                        Iz=788.1, Wel_z=98.52, Wpl_z=153.7),
    "IPE 360": ISection("IPE 360", h=360, b=170, tw=8.0, tf=12.7, r=18,
                        A=72.73, Iy=16270,  Wel_y=903.6, Wpl_y=1019,
                        Iz=1043,  Wel_z=122.8, Wpl_z=191.1),
    "IPE 400": ISection("IPE 400", h=400, b=180, tw=8.6, tf=13.5, r=21,
                        A=84.46, Iy=23130,  Wel_y=1156,  Wpl_y=1307,
                        Iz=1318,  Wel_z=146.4, Wpl_z=229.0),
    "IPE 450": ISection("IPE 450", h=450, b=190, tw=9.4, tf=14.6, r=21,
                        A=98.82, Iy=33740,  Wel_y=1500,  Wpl_y=1702,
                        Iz=1676,  Wel_z=176.4, Wpl_z=276.4),
    "IPE 500": ISection("IPE 500", h=500, b=200, tw=10.2, tf=16.0, r=21,
                        A=115.5, Iy=48200,  Wel_y=1928,  Wpl_y=2194,
                        Iz=2142,  Wel_z=214.2, Wpl_z=335.9),
    "IPE 550": ISection("IPE 550", h=550, b=210, tw=11.1, tf=17.2, r=24,
                        A=134.4, Iy=67120,  Wel_y=2441,  Wpl_y=2787,
                        Iz=2668,  Wel_z=254.1, Wpl_z=400.5),
    "IPE 600": ISection("IPE 600", h=600, b=220, tw=12.0, tf=19.0, r=24,
                        A=156.0, Iy=92080,  Wel_y=3069,  Wpl_y=3512,
                        Iz=3387,  Wel_z=307.9, Wpl_z=485.6),
}


# --------------------------------------------------------------------------- #
# HEB (wide-flange H beams / columns)                                         #
# --------------------------------------------------------------------------- #

HEB_PROFILES = {
    "HEB 100": ISection("HEB 100", h=100, b=100, tw=6.0,  tf=10.0, r=12,
                        A=26.04, Iy=449.5,  Wel_y=89.91, Wpl_y=104.2,
                        Iz=167.3, Wel_z=33.45, Wpl_z=51.42),
    "HEB 120": ISection("HEB 120", h=120, b=120, tw=6.5,  tf=11.0, r=12,
                        A=34.01, Iy=864.4,  Wel_y=144.1, Wpl_y=165.2,
                        Iz=317.5, Wel_z=52.92, Wpl_z=80.97),
    "HEB 140": ISection("HEB 140", h=140, b=140, tw=7.0,  tf=12.0, r=12,
                        A=42.96, Iy=1509,   Wel_y=215.6, Wpl_y=245.4,
                        Iz=549.7, Wel_z=78.52, Wpl_z=119.8),
    "HEB 160": ISection("HEB 160", h=160, b=160, tw=8.0,  tf=13.0, r=15,
                        A=54.25, Iy=2492,   Wel_y=311.5, Wpl_y=354.0,
                        Iz=889.2, Wel_z=111.2, Wpl_z=170.0),
    "HEB 180": ISection("HEB 180", h=180, b=180, tw=8.5,  tf=14.0, r=15,
                        A=65.25, Iy=3831,   Wel_y=425.7, Wpl_y=481.4,
                        Iz=1363,  Wel_z=151.4, Wpl_z=231.0),
    "HEB 200": ISection("HEB 200", h=200, b=200, tw=9.0,  tf=15.0, r=18,
                        A=78.08, Iy=5696,   Wel_y=569.6, Wpl_y=642.5,
                        Iz=2003,  Wel_z=200.3, Wpl_z=305.8),
    "HEB 220": ISection("HEB 220", h=220, b=220, tw=9.5,  tf=16.0, r=18,
                        A=91.04, Iy=8091,   Wel_y=735.5, Wpl_y=827.0,
                        Iz=2843,  Wel_z=258.5, Wpl_z=393.9),
    "HEB 240": ISection("HEB 240", h=240, b=240, tw=10.0, tf=17.0, r=21,
                        A=106.0, Iy=11260,  Wel_y=938.3, Wpl_y=1053,
                        Iz=3923,  Wel_z=326.9, Wpl_z=498.4),
    "HEB 260": ISection("HEB 260", h=260, b=260, tw=10.0, tf=17.5, r=24,
                        A=118.4, Iy=14920,  Wel_y=1148,  Wpl_y=1283,
                        Iz=5135,  Wel_z=395.0, Wpl_z=602.2),
    "HEB 280": ISection("HEB 280", h=280, b=280, tw=10.5, tf=18.0, r=24,
                        A=131.4, Iy=19270,  Wel_y=1376,  Wpl_y=1534,
                        Iz=6595,  Wel_z=471.0, Wpl_z=717.6),
    "HEB 300": ISection("HEB 300", h=300, b=300, tw=11.0, tf=19.0, r=27,
                        A=149.1, Iy=25170,  Wel_y=1678,  Wpl_y=1869,
                        Iz=8563,  Wel_z=570.9, Wpl_z=870.1),
    "HEB 320": ISection("HEB 320", h=320, b=300, tw=11.5, tf=20.5, r=27,
                        A=161.3, Iy=30820,  Wel_y=1926,  Wpl_y=2149,
                        Iz=9239,  Wel_z=615.9, Wpl_z=939.1),
    "HEB 340": ISection("HEB 340", h=340, b=300, tw=12.0, tf=21.5, r=27,
                        A=170.9, Iy=36660,  Wel_y=2156,  Wpl_y=2408,
                        Iz=9690,  Wel_z=646.0, Wpl_z=985.7),
    "HEB 360": ISection("HEB 360", h=360, b=300, tw=12.5, tf=22.5, r=27,
                        A=180.6, Iy=43190,  Wel_y=2400,  Wpl_y=2683,
                        Iz=10140, Wel_z=676.1, Wpl_z=1032),
    "HEB 400": ISection("HEB 400", h=400, b=300, tw=13.5, tf=24.0, r=27,
                        A=197.8, Iy=57680,  Wel_y=2884,  Wpl_y=3232,
                        Iz=10820, Wel_z=721.3, Wpl_z=1104),
}
