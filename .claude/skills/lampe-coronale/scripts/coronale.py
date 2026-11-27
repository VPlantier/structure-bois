#!/usr/bin/env python3
"""Modèle paramétrique de la lampe « coronale ».

Sous-commandes :
  extract  <fichier.html|svg> [-o params.json]   lit le SVG et en déduit les paramètres
  check    <params.json>                          vérifie les contraintes, calcule la tige optimale
  svg      <params.json> [-o defs.svg]            produit les <path>/<circle> du plan de coupe
  apply    <params.json> <fichier.html> [-o out]  réécrit les pièces dans le fichier HTML/SVG
  obj      <params.json> [-o lampe.obj]           produit un modèle 3D (mm) + lampe.mtl + bois.png

Toutes les longueurs des paramètres sont en unités SVG (0,1 mm), comme le fichier source.
Bibliothèque standard uniquement (Python 3.8+).
"""
import argparse
import json
import math
import os
import re
import shutil
import sys

SQ3 = math.sqrt(3.0)


# ---------------------------------------------------------------- utilitaires
def u(theta_deg):
    """Vecteur radial unitaire, repère SVG (y vers le bas)."""
    t = math.radians(theta_deg)
    return (math.cos(t), math.sin(t))


def t_(theta_deg):
    """Direction tangentielle d'un montant placé à theta (vers theta+90°)."""
    return u(theta_deg + 90)


def pt(rho, tau, theta):
    """Point de coordonnées (radiale rho, tangentielle tau) autour du rayon theta."""
    a, b = u(theta), t_(theta)
    return (rho * a[0] + tau * b[0], rho * a[1] + tau * b[1])


def add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def mul(p, k):
    return (p[0] * k, p[1] * k)


def norm(p):
    return math.hypot(p[0], p[1])


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def f(x):
    """Format numérique du fichier source (3 décimales, sans zéros inutiles)."""
    s = "%.3f" % x
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- paramètres
DEFAULTS = {
    "hexagone_rayon": 200,           # rayon circonscrit de l'hexagone central
    "tranche_cote_court": 350,       # côté radial court d'une tranche
    "montant_epaisseur": 200,        # épaisseur radiale du montant
    "montant_largeur": 300,          # largeur tangentielle du montant
    "support_marge": 50,             # marge du support autour des montants
    "support_retrait": 40,           # le côté extérieur du 1er cadre s'arrête à marge+largeur+marge-retrait
    "support_poignee_debut": 0.2546, # longueur poignée 1 de la cubique / corde
    "support_poignee_fin": 0.2654,   # longueur poignée 2 de la cubique / corde
    "support_douille_rayon": 300,
    "trouSD_rayon": 65,
    "trouR_rayon": 175,
    "reuleaux_debord": 5,            # cercle inscrit du Reuleaux - rayon supportDouille
    "tige_rayon": 45,
    "tige_distance": "auto",         # distance centre lampe -> axe de la tige ; cote dérivée : "auto" = optimum
                                     # (un nombre = valeur imposée explicitement par l'utilisateur)
    "epaisseur": 200,                # épaisseur de toutes les plaques
    "montant_hauteur": 1800,
    "z_support": 0,
    "z_montant": 200,
    "z_support_douille": 200,
    "z_reuleaux": 400,
    "z_couronne": 800,
    "z_tige": 400,
    "tige_longueur": 600,
    # Joint de colle époxy entre tranches voisines (1 mm) : le groupe #secteurCouronne (tranche + montant
    # collé sur sa face) porte translate(-8.66,-5), soit colle_epaisseur le long de la bissectrice. Seul le
    # 1er SVG l'utilise ; les plans de débit utilisent #trancheCouronne / #montant sans translate.
    "colle_epaisseur": 10,
    # Option électrique : "oui" = douille + tige filetée + ampoule dans le 3D, "non" = rien
    "electrique": "non",
    "douille_rayon": 140,            # douille E14 minimale Ø 28 mm (doit passer l'hexagone)
    "z_douille_bas": None,           # None = z_reuleaux (fond de trouR = dessus du supportDouille)
    "z_douille_haut": None,          # None = dessus de la couronne (la douille traverse l'hexagone)
    "tige_filetee_rayon": 50,        # tige filetée Ø 10 mm, dans trouSD Ø 13 mm (adaptateur bois)
    "z_tige_filetee_bas": None,      # None = z_support_douille
    "z_tige_filetee_haut": None,     # None = z_douille_bas + 200 (vissée 20 mm dans la douille)
    "ampoule_rayon": 225,            # ampoule inventée : globe Ø 45 mm sur culot E14
}


def electrique(p):
    """Complète les paramètres électriques laissés à None."""
    e = {}
    e["douille_rayon"] = p["douille_rayon"]
    e["z_douille_bas"] = p["z_douille_bas"] if p.get("z_douille_bas") is not None else p["z_reuleaux"]
    e["z_douille_haut"] = p["z_douille_haut"] if p.get("z_douille_haut") is not None else p["z_couronne"] + p["epaisseur"]
    e["tige_filetee_rayon"] = p["tige_filetee_rayon"]
    e["z_tige_filetee_bas"] = (p["z_tige_filetee_bas"] if p.get("z_tige_filetee_bas") is not None
                               else p["z_support_douille"])
    e["z_tige_filetee_haut"] = (p["z_tige_filetee_haut"] if p.get("z_tige_filetee_haut") is not None
                                else e["z_douille_bas"] + 200)
    e["ampoule_rayon"] = p["ampoule_rayon"]
    return e


def load_params(path):
    with open(path, encoding="utf-8") as fh:
        p = json.load(fh)
    q = dict(DEFAULTS)
    q.update({k: v for k, v in p.items() if not k.startswith("_")})
    return q


def derived(p):
    d = {}
    d["r1"] = p["hexagone_rayon"] + p["tranche_cote_court"]
    d["r2"] = d["r1"] + p["montant_epaisseur"]
    d["tranche_cote_long"] = d["r2"] - p["hexagone_rayon"]
    d["tranche_face_montant"] = (2 * d["r2"] - d["r1"]) / SQ3  # côté perpendiculaire au côté court
    d["reuleaux_largeur"] = (p["support_douille_rayon"] + p["reuleaux_debord"]) / (1 - 1 / SQ3)
    d["reuleaux_rayon_sommet"] = d["reuleaux_largeur"] / SQ3
    g = p.get("colle_epaisseur", 0) or 0
    d["hexagone_apotheme"] = p["hexagone_rayon"] * SQ3 / 2 + g   # hexagone vide après translation
    return d


# ---------------------------------------------------------------- joint de colle
def colle_translation(p):
    """Translation de la tranche de base (180°-240°) : colle_epaisseur le long de sa bissectrice (210°).
    Elle l'écarte de colle/2 de chacun de ses deux rayons (g·sin 30° = g/2) : deux tranches voisines sont
    donc séparées de colle_epaisseur, et le côté d'hexagone recule de g (l'hexagone reste régulier)."""
    g = p.get("colle_epaisseur", 0) or 0
    return mul(u(210), g)


COLLE_COMMENT_RE = r"<!--[^>]*joint de colle de\s*(" + r"[0-9]+(?:[.,][0-9]+)?" + r")\s*mm[^>]*-->"


def colle_comment(p):
    """Commentaire HTML écrit par apply avant #secteurCouronne : rend lisible l'épaisseur du joint."""
    g = p.get("colle_epaisseur", 0) or 0
    return ("<!-- tranche + montant collé sur sa face ; translate = joint de colle de %s mm le long de la "
            "bissectrice (1er SVG seulement) ; écrit par coronale.py apply -->" % f(g / 10).replace(".", ","))


def translate_attr(p):
    t = colle_translation(p)
    return "translate(%s,%s)" % (f(t[0]), f(t[1]))


def placed(P, p, k=0):
    """Points de la pièce de base, translatés (joint de colle) puis tournés de 60°·k, comme dans le 1er SVG."""
    t = colle_translation(p)
    return [rot(add(q, t), 60 * k) for q in P]


def colle_points(p, theta=180):
    """Joint de colle sur le rayon theta : du sommet de l'hexagone jusqu'au bout du côté long (r2),
    entre le côté long d'une tranche et le côté court de la voisine prolongé par son montant."""
    g = p.get("colle_epaisseur", 0) or 0
    d = derived(p)
    s = g * SQ3 / 2                      # recul radial des côtés radiaux translatés
    a, b = p["hexagone_rayon"] + s, d["r2"] + s
    return [pt(a, -g / 2, theta), pt(b, -g / 2, theta), pt(b, g / 2, theta), pt(a, g / 2, theta)]


# ---------------------------------------------------------------- géométrie 2D
def tranche_points(p):
    """Tranche de base : entre les rayons 180° (côté court) et 240° (côté long)."""
    d = derived(p)
    Rh, r1, r2 = p["hexagone_rayon"], d["r1"], d["r2"]
    return [(-Rh, 0.0), (-r1, 0.0), (-r1, -d["tranche_face_montant"]),
            mul(u(240), r2), mul(u(240), Rh)]


def tranche_d(p):
    P = tranche_points(p)
    s = "M %s %s" % (f(P[0][0]), f(P[0][1]))
    for a, b in zip(P, P[1:]):
        v = sub(b, a)
        s += " l %s %s" % (f(v[0]), f(v[1]))
    return s + " z"


def montant_points(p, theta=180):
    d = derived(p)
    r1, r2, w = d["r1"], d["r2"], p["montant_largeur"]
    return [pt(r1, 0, theta), pt(r2, 0, theta), pt(r2, w, theta), pt(r1, w, theta)]


def montant_d(p):
    d = derived(p)
    e, w = p["montant_epaisseur"], p["montant_largeur"]
    return "M %s 0 l %s 0 l 0 %s l %s 0 z" % (f(-d["r1"]), f(-e), f(-w), f(e))


def support_geom(p):
    """Points clés du support (cadres autour des montants à 180° et 240°).

    Chaque cadre entoure son montant tel qu'il est posé dans le 1er SVG, joint de colle compris : le montant à
    180° porte la translation t du secteur de base, celui à 240° la même tournée de 60°. Dans le repère local
    (radial, tangentiel) de chaque montant, les deux décalages valent (g·√3/2, g/2) : les cadres reculent de
    g·√3/2 vers l'extérieur et glissent de g/2 vers les angles croissants. Le support n'est pas translaté en
    bloc (les deux cadres ne bougent pas dans la même direction) : son contour est recalculé, courbes comprises."""
    d = derived(p)
    r1, r2 = d["r1"], d["r2"]
    m, w, rt = p["support_marge"], p["montant_largeur"], p["support_retrait"]
    cg = p.get("colle_epaisseur", 0) or 0
    s, h = cg * SQ3 / 2, cg / 2              # décalage radial / tangentiel du montant (joint de colle)
    ri, ro = r1 + s - m, r2 + s + m
    lo, hi = h - m, h + w + m                # bornes tangentielles du cadre
    g = {}
    g["S"] = pt(ri, lo, 180)                 # coin intérieur du cadre 1
    g["A0"] = pt(ro, lo, 180)
    g["A"] = pt(ro, hi - rt, 180)            # début de la cubique
    g["B"] = pt(ro, lo, 240)                 # coin extérieur du cadre 2
    chord = norm(sub(g["B"], g["A"]))
    g["C1"] = add(g["A"], mul(t_(180), p["support_poignee_debut"] * chord))
    g["C2"] = sub(g["B"], mul(t_(240), p["support_poignee_fin"] * chord))
    g["B1"] = pt(ro, hi, 240)
    g["B2"] = pt(ri, hi, 240)
    g["Q0"] = pt(ri, lo, 240)                # début de la quadratique
    g["QC"] = mul(u(210), ri / math.cos(math.radians(30)))  # intersection des côtés intérieurs
    return g


def support_marges(p, sg):
    """Marges réelles des cadres du support autour des montants placés comme dans le 1er SVG (joint compris).
    Cadre 1 : montant k=0 (180°) ; cadre 2 : montant k=1 (240°), côté extérieur limité par B/B1."""
    M1 = placed(montant_points(p, 180), p, 0)
    M2 = placed(montant_points(p, 180), p, 1)

    def loc(q, theta):                       # coordonnées (radiale, tangentielle) autour de theta
        return (q[0] * u(theta)[0] + q[1] * u(theta)[1], q[0] * t_(theta)[0] + q[1] * t_(theta)[1])

    m1 = [loc(q, 180) for q in M1]
    m2 = [loc(q, 240) for q in M2]
    S, A0, B, B1 = loc(sg["S"], 180), loc(sg["A0"], 180), loc(sg["B"], 240), loc(sg["B1"], 240)
    return {
        "cadre1_interieure": min(q[0] for q in m1) - S[0],
        "cadre1_exterieure": A0[0] - max(q[0] for q in m1),
        "cadre1_cote_bas": min(q[1] for q in m1) - S[1],
        "cadre2_interieure": min(q[0] for q in m2) - loc(sg["Q0"], 240)[0],
        "cadre2_exterieure": B[0] - max(q[0] for q in m2),
        "cadre2_cote_bas": min(q[1] for q in m2) - B[1],
        "cadre2_cote_haut": B1[1] - max(q[1] for q in m2),
    }


def support_d(p):
    g = support_geom(p)
    seq = [("M", g["S"]), ("l", g["A0"]), ("l", g["A"])]
    s = "M %s %s" % (f(g["S"][0]), f(g["S"][1]))
    cur = g["S"]
    for pnt in (g["A0"], g["A"]):
        v = sub(pnt, cur)
        s += " l %s %s" % (f(v[0]), f(v[1]))
        cur = pnt
    c1, c2, b = sub(g["C1"], cur), sub(g["C2"], cur), sub(g["B"], cur)
    s += " c %s %s %s %s %s %s" % tuple(map(f, (c1[0], c1[1], c2[0], c2[1], b[0], b[1])))
    cur = g["B"]
    for pnt in (g["B1"], g["B2"], g["Q0"]):
        v = sub(pnt, cur)
        s += " l %s %s" % (f(v[0]), f(v[1]))
        cur = pnt
    qc, e = sub(g["QC"], cur), sub(g["S"], cur)
    s += " q %s %s %s %s z" % tuple(map(f, (qc[0], qc[1], e[0], e[1])))
    return s


def bez3(a, b, c, d_, n):
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt**3 * a[0] + 3 * mt * mt * t * b[0] + 3 * mt * t * t * c[0] + t**3 * d_[0],
                    mt**3 * a[1] + 3 * mt * mt * t * b[1] + 3 * mt * t * t * c[1] + t**3 * d_[1]))
    return out


def bez2(a, b, c, n):
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt * mt * a[0] + 2 * mt * t * b[0] + t * t * c[0],
                    mt * mt * a[1] + 2 * mt * t * b[1] + t * t * c[1]))
    return out


def support_points(p, n=24):
    g = support_geom(p)
    P = [g["S"], g["A0"], g["A"]]
    P += bez3(g["A"], g["C1"], g["C2"], g["B"], n)
    P += [g["B1"], g["B2"], g["Q0"]]
    P += bez2(g["Q0"], g["QC"], g["S"], n)[:-1]
    return P


def reuleaux_d(p):
    d = derived(p)
    W, R = d["reuleaux_largeur"], d["reuleaux_rayon_sommet"]
    return ("M 0 %s a %s %s 0 0 1 %s %s a %s %s 0 0 1 %s 0 a %s %s 0 0 1 %s %s z"
            % (f(-R), f(W), f(W), f(W / 2), f(W * SQ3 / 2), f(W), f(W), f(-W),
               f(W), f(W), f(W / 2), f(-W * SQ3 / 2)))


def reuleaux_points(p, n=40):
    d = derived(p)
    W, R = d["reuleaux_largeur"], d["reuleaux_rayon_sommet"]
    V = [mul(u(270 + 120 * k), R) for k in range(3)]   # sommets (haut, bas-droit, bas-gauche)
    P = []
    for k in range(3):
        a, b = V[k], V[(k + 1) % 3]
        c = V[(k + 2) % 3]                             # centre de l'arc = sommet opposé
        a0 = math.atan2(a[1] - c[1], a[0] - c[0])
        a1 = math.atan2(b[1] - c[1], b[0] - c[0])
        while a1 < a0:
            a1 += 2 * math.pi
        for i in range(n):
            t = a0 + (a1 - a0) * i / n
            P.append((c[0] + W * math.cos(t), c[1] + W * math.sin(t)))
    return P


def circle_points(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def tige_centres(p, dist=None):
    dist = p["tige_distance"] if dist is None else dist
    return [rot((0.0, -dist), 120 * k) for k in range(3)]


# ---------------------------------------------------------------- contrôles
def seg_dist(q, a, b):
    ab, aq = sub(b, a), sub(q, a)
    L2 = ab[0] ** 2 + ab[1] ** 2
    t = max(0.0, min(1.0, (aq[0] * ab[0] + aq[1] * ab[1]) / L2)) if L2 else 0.0
    return norm(sub(q, add(a, mul(ab, t))))


def poly_dist(q, P):
    return min(seg_dist(q, P[i], P[(i + 1) % len(P)]) for i in range(len(P)))


def inside(q, P):
    c = False
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        if (a[1] > q[1]) != (b[1] > q[1]):
            x = a[0] + (q[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > q[0]:
                c = not c
    return c


def tige_clearances(p, dist):
    q = (0.0, -dist)
    tr = placed(tranche_points(p), p, 1)            # tranche (translatée) qui reçoit la tige à 270°
    rl = reuleaux_points(p, 400)
    rt = p["tige_rayon"]
    d_tr = poly_dist(q, tr) if inside(q, tr) else -poly_dist(q, tr)
    d_rl = poly_dist(q, rl) if inside(q, rl) else -poly_dist(q, rl)
    d_hole = dist - p["trouR_rayon"]
    return {"tranche": d_tr - rt, "reuleaux_bord": d_rl - rt, "trouR": d_hole - rt}


def tige_optimum(p):
    lo = p["trouR_rayon"]
    hi = derived(p)["reuleaux_rayon_sommet"]
    score = lambda r: min(tige_clearances(p, r).values())
    for _ in range(80):  # recherche dorée (fonction unimodale sur l'axe)
        a = lo + (hi - lo) * 0.381966
        b = lo + (hi - lo) * 0.618034
        if score(a) < score(b):
            lo = a
        else:
            hi = b
    r = (lo + hi) / 2
    return r, score(r)


def resolve(p):
    p = dict(p)
    if p.get("tige_distance") in (None, "auto"):
        p["tige_distance"] = round(tige_optimum(p)[0], 1)
    return p


def check(p):
    p = resolve(p)
    d = derived(p)
    rep = {"derives": {k: round(v, 3) for k, v in d.items()}, "verifications": [], "alertes": []}
    ok = rep["verifications"].append
    warn = rep["alertes"].append
    if p["montant_largeur"] > d["tranche_face_montant"] + 1e-6:
        warn("Le montant (%s) est plus large que la face de la tranche qui le reçoit (%.3f)."
             % (p["montant_largeur"], d["tranche_face_montant"]))
    else:
        ok("Montant collé sur la face de tranche : %.1f ≤ %.3f" % (p["montant_largeur"], d["tranche_face_montant"]))
    ok("Côté long = côté court + épaisseur montant : %.3f = %.3f + %.3f"
       % (d["tranche_cote_long"], p["tranche_cote_court"], p["montant_epaisseur"]))
    insc = d["reuleaux_largeur"] * (1 - 1 / SQ3)
    ok("Cercle inscrit du Reuleaux %.3f = supportDouille %.3f + débord %.3f"
       % (insc, p["support_douille_rayon"], p["reuleaux_debord"]))
    if p["trouR_rayon"] >= p["support_douille_rayon"]:
        warn("trouR plus grand que supportDouille.")
    if p["trouSD_rayon"] >= p["trouR_rayon"]:
        warn("trouSD n'est pas plus petit que trouR.")
    el = electrique(p)
    rep["electrique"] = {k: round(v, 3) for k, v in el.items()}
    rep["electrique"]["option"] = p.get("electrique", "non")
    if p["trouSD_rayon"] < el["tige_filetee_rayon"]:
        warn("trouSD (%s) trop petit pour la tige filetée (rayon %s)." % (p["trouSD_rayon"], el["tige_filetee_rayon"]))
    else:
        ok("Tige filetée Ø%.1f mm dans trouSD Ø%.1f mm" % (el["tige_filetee_rayon"] / 5, p["trouSD_rayon"] / 5))
    if el["douille_rayon"] > p["trouR_rayon"]:
        warn("La douille (rayon %s) ne rentre pas dans trouR (%s)." % (el["douille_rayon"], p["trouR_rayon"]))
    apo = d["hexagone_apotheme"]
    g = p.get("colle_epaisseur", 0) or 0
    t = colle_translation(p)
    rep["colle"] = {"epaisseur": g, "translate_tranche_base": translate_attr(p),
                    "apotheme_hexagone": round(apo, 3)}
    if g:
        ok("Joint de colle %.1f mm : tranches et montants translatés de (%.3f, %.3f), hexagone d'apothème %.1f"
           % (g / 10, t[0], t[1], apo))
    # Marges réelles du support autour des montants posés (joint compris) : doivent valoir support_marge
    sg = support_geom(p)
    marges = support_marges(p, sg)
    rep["support_marges_reelles"] = {k: round(v, 3) for k, v in marges.items()}
    if max(abs(v - p["support_marge"]) for v in marges.values()) > 0.01:
        warn("Les cadres du support ne sont pas à la marge %s des montants posés : %s"
             % (p["support_marge"], rep["support_marges_reelles"]))
    else:
        ok("Support : cadres à %.1f mm des montants posés (joint de colle compris)" % (p["support_marge"] / 10))
    if el["z_douille_haut"] > p["z_couronne"]:
        if el["douille_rayon"] > apo:
            warn("La douille (rayon %.1f) ne passe pas dans l'hexagone (apothème %.1f)." % (el["douille_rayon"], apo))
        else:
            ok("Douille Ø%.1f mm dans l'hexagone (cercle inscrit Ø%.2f mm)" % (el["douille_rayon"] / 5, apo / 5))
    if el["ampoule_rayon"] >= derived(p)["r1"]:
        warn("L'ampoule touche les montants.")
    cl = tige_clearances(p, p["tige_distance"])
    ropt, sopt = tige_optimum(p)
    rep["tige"] = {"distance": p["tige_distance"],
                   "jeu_mini_par_bord": {k: round(v, 2) for k, v in cl.items()},
                   "distance_optimale": round(ropt, 2), "jeu_mini_optimal": round(sopt, 2)}
    if min(cl.values()) <= 0:
        warn("La tige déborde (jeu ≤ 0) : %s" % cl)
    if abs(ropt - p["tige_distance"]) > 0.5:
        warn("tige_distance imposée (%.1f) ≠ optimum (%.1f) : mettre \"auto\" sauf choix explicite de l'utilisateur."
             % (p["tige_distance"], ropt))
    if p["tige_distance"] - p["tige_rayon"] < apo:
        warn("La tige mord sur l'hexagone central.")
    g = support_geom(p)
    if p["support_retrait"] < 0 or p["support_retrait"] > p["montant_largeur"] + 2 * p["support_marge"]:
        warn("support_retrait hors du cadre.")
    sp = support_points(p)
    if poly_area(sp) <= 0:
        warn("Le contour du support s'auto-intersecte ou est inversé.")
    return rep


def poly_area(P):
    """Aire signée ; positive = sens des aiguilles d'une montre à l'écran (y vers le bas)."""
    return 0.5 * sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1]
                     for i in range(len(P)))


# ---------------------------------------------------------------- extraction
NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def parse_path(d):
    """Renvoie la liste (commande absolue, points absolus) d'un chemin SVG simple."""
    toks = re.findall(r"[MmLlHhVvCcQqAaZz]|" + NUM, d)
    out, i, cur, start, cmd = [], 0, (0.0, 0.0), (0.0, 0.0), None
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                out.append(("Z", []))
                cur = start
                continue
        rel = cmd.islower()
        C = cmd.upper()
        n = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4, "A": 7}[C]
        v = [float(x) for x in toks[i:i + n]]
        i += n
        if C == "H":
            pts = [(v[0] + (cur[0] if rel else 0), cur[1])]
        elif C == "V":
            pts = [(cur[0], v[0] + (cur[1] if rel else 0))]
        elif C == "A":
            e = (v[5] + (cur[0] if rel else 0), v[6] + (cur[1] if rel else 0))
            out.append(("A", [tuple(v[:5]), e]))
            cur = e
            continue
        else:
            pts = [(v[k] + (cur[0] if rel else 0), v[k + 1] + (cur[1] if rel else 0))
                   for k in range(0, n, 2)]
        out.append((C, pts))
        cur = pts[-1]
        if C == "M":
            start = cur
            cmd = "l" if rel else "L"
    return out


def use_translate(tr):
    """Translation lue dans un attribut transform (« translate(x,y) »)."""
    m = re.search(r"translate\(\s*(" + NUM + r")[\s,]+(" + NUM + r")\s*\)", tr or "")
    return (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)


def attr(src, el_id, name):
    m = re.search(r'<[^>]*\bid="%s"[^>]*>' % re.escape(el_id), src)
    if not m:
        raise SystemExit("ERREUR : élément #%s introuvable" % el_id)
    a = re.search(r'\b%s="([^"]*)"' % name, m.group(0))
    if not a:
        raise SystemExit("ERREUR : #%s sans attribut %s" % (el_id, name))
    return a.group(1)


def extract(src):
    p = dict(DEFAULTS)
    tr = [s[1][-1] for s in parse_path(attr(src, "trancheCouronne", "d")) if s[0] != "Z"]
    p["hexagone_rayon"] = round(norm(tr[0]), 3)
    r1 = norm(tr[1])
    r2 = norm(tr[3])
    p["tranche_cote_court"] = round(r1 - norm(tr[0]), 3)
    mo = [s[1][-1] for s in parse_path(attr(src, "montant", "d")) if s[0] != "Z"]
    xs, ys = [q[0] for q in mo], [q[1] for q in mo]
    p["montant_epaisseur"] = round(max(xs) - min(xs), 3)
    p["montant_largeur"] = round(max(ys) - min(ys), 3)
    notes = []
    if abs((r2 - r1) - p["montant_epaisseur"]) > 0.01:
        notes.append("Incohérence : côté long - côté court (%.3f) ≠ épaisseur du montant (%.3f)"
                     % (r2 - r1, p["montant_epaisseur"]))
    # Joint de colle : un seul translate, sur le groupe #secteurCouronne (tranche + montant) des <defs>,
    # que seul le 1er SVG utilise (6 rotations). Les plans de débit utilisent #trancheCouronne / #montant.
    for el in ("trancheCouronne", "montant"):
        if re.search(r'<path[^>]*\bid="%s"[^>]*\btransform=' % el, src):
            notes.append("#%s porte un transform : il décale aussi les plans de débit ; le joint de colle se met "
                         "sur #secteurCouronne (apply le corrige)" % el)
    m = re.search(r'<g[^>]*\bid="secteurCouronne"[^>]*>', src)
    if not m:
        notes.append("Groupe #secteurCouronne introuvable : joint de colle supposé nul")
    tm = re.search(r'\btransform="([^"]*)"', m.group(0)) if m else None
    t0 = use_translate(tm.group(1) if tm else "")
    g = norm(t0)
    p["colle_epaisseur"] = round(g, 3)
    if g > 1e-9:
        ang = math.degrees(math.atan2(t0[1], t0[0])) % 360
        if abs(ang - 210) > 0.05:
            good = colle_translation(p)
            notes.append("translate(%s,%s) n'est pas sur la bissectrice de la tranche (%.2f° au lieu de 210°) : "
                         "l'hexagone central n'est plus régulier et les joints ne sont pas parallèles. "
                         "Pour un joint de %.2f mm : translate(%s,%s)"
                         % (f(t0[0]), f(t0[1]), ang, g / 10, f(good[0]), f(good[1])))
    # Support : ses cadres entourent les montants posés (joint de colle compris), voir support_geom.
    # S = (r1 + s - m, h - m)@180 et A = (r2 + s + m, h + w + m - retrait)@180, avec s = g√3/2, h = g/2.
    s_, h_ = g * SQ3 / 2, g / 2
    sp = parse_path(attr(src, "support", "d"))
    S = sp[0][1][0]
    m_rad = r1 + s_ - abs(S[0])              # marge radiale (côté intérieur du cadre 1)
    m_tan = S[1] + h_                        # marge tangentielle (côté bas du cadre 1)
    p["support_marge"] = round(m_rad, 3)
    if abs(m_rad - m_tan) > 0.5:
        if g > 1e-9 and abs((r1 - abs(S[0])) - S[1]) < 0.5:
            p["support_marge"] = round(r1 - abs(S[0]), 3)
            notes.append("#support est encore dessiné sans le joint de colle (cadres autour des montants non "
                         "translatés) : marge relue %.1f ; apply le déforme pour suivre les montants"
                         % p["support_marge"])
        else:
            notes.append("#support : marge radiale (%.1f) ≠ marge tangentielle (%.1f)" % (m_rad, m_tan))
    m_ = p["support_marge"]
    A = sp[2][1][0]
    hi = p["montant_largeur"] + m_ + (h_ if abs(m_rad - m_tan) <= 0.5 else 0)
    p["support_retrait"] = round(hi + A[1], 3)
    c1, c2, B = sp[3][1]
    chord = norm(sub(B, A))
    p["support_poignee_debut"] = round(norm(sub(c1, A)) / chord, 6)
    p["support_poignee_fin"] = round(norm(sub(B, c2)) / chord, 6)
    cy = float(attr(src, "tige", "cy"))
    cx = float(attr(src, "tige", "cx"))
    # La distance des tiges est une cote dérivée (optimum des jeux) : extract rend "auto" et signale l'écart
    # éventuel du fichier, que apply corrige. Une valeur imposée se met à la main dans params.json.
    p["_tige_distance_fichier"] = round(math.hypot(cx, cy), 3)
    p["tige_distance"] = "auto"
    p["tige_rayon"] = float(attr(src, "tige", "r"))
    p["support_douille_rayon"] = float(attr(src, "supportDouille", "r"))
    p["trouSD_rayon"] = float(attr(src, "trouSD", "r"))
    p["trouR_rayon"] = float(attr(src, "trouR", "r"))
    rl = parse_path(attr(src, "reuleaux", "d"))
    W = rl[1][1][0][0]
    p["reuleaux_debord"] = round(W * (1 - 1 / SQ3) - p["support_douille_rayon"], 3)
    # Commentaire du joint de colle (la valeur en mm n'apparaît pas dans le translate) : doit concorder
    cm = re.search(COLLE_COMMENT_RE, src)
    if cm and abs(float(cm.group(1).replace(",", ".")) * 10 - g) > 0.05:
        notes.append("Le commentaire annonce un joint de colle de %s mm mais le translate de #secteurCouronne "
                     "vaut %.2f mm (apply réécrit le commentaire d'après colle_epaisseur)" % (cm.group(1), g / 10))
    ropt = round(tige_optimum(p)[0], 1)
    if abs(p["_tige_distance_fichier"] - ropt) > 0.5:
        notes.append("Tiges à %.1f mm dans le fichier, optimum %.2f mm : apply les replace à l'optimum "
                     "(tige_distance \"auto\")" % (p["_tige_distance_fichier"] / 10, ropt / 10))
    # Vérifie que la régénération redonne bien les chemins du fichier
    for el, fn in (("trancheCouronne", tranche_d), ("montant", montant_d), ("support", support_d),
                   ("reuleaux", reuleaux_d)):
        a = [q for s in parse_path(attr(src, el, "d")) for q in s[1] if isinstance(q[0], float)]
        b = [q for s in parse_path(fn(p)) for q in s[1] if isinstance(q[0], float)]
        err = max((norm(sub(x, y)) for x, y in zip(a, b)), default=0) if len(a) == len(b) else float("inf")
        if err > 1.0:
            notes.append("#%s ne suit pas exactement le modèle (écart max %.2f unités = %.2f mm)"
                         % (el, err, err / 10))
    p["_notes"] = notes
    return p


# ---------------------------------------------------------------- écriture SVG
def svg_defs(p):
    p = resolve(p)
    return {
        "trancheCouronne": tranche_d(p),
        "montant": montant_d(p),
        "support": support_d(p),
        "reuleaux": reuleaux_d(p),
    }


def set_attr(src, el_id, name, value):
    pat = re.compile(r'(<[^>]*\bid="%s"[^>]*\b%s=")[^"]*(")' % (re.escape(el_id), name))
    new, n = pat.subn(lambda m: m.group(1) + value + m.group(2), src, count=1)
    if not n:
        raise SystemExit("ERREUR : impossible de modifier %s de #%s" % (name, el_id))
    return new


def apply(p, src):
    p = resolve(p)
    for k, v in svg_defs(p).items():
        src = set_attr(src, k, "d", v)
    # joint de colle : un seul translate sur #secteurCouronne, jamais sur les chemins (plans de débit)
    for el in ("trancheCouronne", "montant"):
        src = re.sub(r'(<path[^>]*\bid="%s"[^>]*?)\s+transform="[^"]*"' % el, r"\1", src, count=1)
    if not re.search(r'<g[^>]*\bid="secteurCouronne"[^>]*\btransform=', src):
        raise SystemExit("ERREUR : groupe #secteurCouronne (avec transform) introuvable")
    src = set_attr(src, "secteurCouronne", "transform", translate_attr(p))
    # commentaire lisible du joint de colle, juste avant #secteurCouronne (la valeur en mm n'est pas dans le translate)
    com = colle_comment(p)
    src, n = re.subn(r'<!--[^>]*joint de colle[^>]*-->(\s*<g[^>]*\bid="secteurCouronne")',
                     lambda mm: com + mm.group(1), src, count=1)
    if not n:
        src = re.sub(r'(\n([ \t]*))(<g[^>]*\bid="secteurCouronne")',
                     lambda mm: mm.group(1) + com + mm.group(1) + mm.group(3), src, count=1)
    # 3e SVG : repères des montants sur le support, à leur position réelle (même translation que
    # #secteurCouronne, puis rotation de 60° pour le second). Recopie dérivée, jamais éditée à la main.
    m = re.search(r'(<g id="supportPlein">)(.*?)(</g>)', src, re.S)
    if m:
        body, n = m.group(2), [0]

        def montant_use(mm):
            k = n[0]
            n[0] += 1
            tr = translate_attr(p) if k == 0 else "rotate(60) " + translate_attr(p)
            return '<use href="#montant" fill="none" transform="%s" />' % tr

        body = re.sub(r'<use href="#montant"[^>]*/>', montant_use, body)
        src = src[:m.start(2)] + body + src[m.end(2):]
    src = set_attr(src, "tige", "cy", f(-p["tige_distance"]))
    src = set_attr(src, "tige", "cx", "0")
    src = set_attr(src, "tige", "r", f(p["tige_rayon"]))
    src = set_attr(src, "supportDouille", "r", f(p["support_douille_rayon"]))
    src = set_attr(src, "trouSD", "r", f(p["trouSD_rayon"]))
    src = set_attr(src, "trouR", "r", f(p["trouR_rayon"]))
    # repères de perçage des tiges (petits cercles r=3 à cy=-ancienne distance)
    src = re.sub(r'(<circle cx="0" cy=")-' + NUM + r'(" r="3")',
                 lambda m: m.group(1) + f(-p["tige_distance"]) + m.group(2), src)
    # plan de débit de la couronne : rectangle englobant de la tranche
    m = re.search(r'<g id="coupeCouronne">(.*?)</g>', src, re.S)
    if m:
        d = derived(p)
        P = tranche_points(p)
        bw = max(q[0] for q in P) - min(q[0] for q in P)
        bh = max(q[1] for q in P) - min(q[1] for q in P)
        g = m.group(1)
        rw = bw + 5  # le plan d'origine prend 0,5 mm de jeu en largeur (455 pour 450)
        g = re.sub(r'<use x="' + NUM + '" y="' + NUM + '"',
                   '<use x="%s" y="%s"' % (f(d["r1"]), f(bh)), g, count=1)
        g = re.sub(r'<rect width="' + NUM + '" height="' + NUM + '"',
                   '<rect width="%s" height="%s"' % (f(rw), f(bh)), g, count=1)
        g = re.sub(r'(<text[^>]*>)[^<]*(</text>)',
                   lambda mm: mm.group(1) + "%s x %s" % (f(rw), ("%.1f" % bh)) + mm.group(2), g, count=1)
        src = src[:m.start(1)] + g + src[m.end(1):]
    return src


# ---------------------------------------------------------------- 3D / OBJ
def triangulate(outer, holes=()):
    """Triangulation par oreilles avec trous (pont vers le contour). Renvoie des triangles d'indices
    dans la liste concaténée outer + holes."""
    pts = list(outer) + [q for h in holes for q in h]

    def area(idx):
        return 0.5 * sum(pts[idx[i]][0] * pts[idx[(i + 1) % len(idx)]][1]
                         - pts[idx[(i + 1) % len(idx)]][0] * pts[idx[i]][1] for i in range(len(idx)))

    ring = list(range(len(outer)))
    if area(ring) < 0:
        ring.reverse()
    off = len(outer)
    hrings = []
    for h in holes:
        hr = list(range(off, off + len(h)))
        off += len(h)
        if area(hr) > 0:
            hr.reverse()
        hrings.append(hr)
    hrings.sort(key=lambda hr: -max(pts[i][0] for i in hr))
    for hr in hrings:
        mi = max(hr, key=lambda i: pts[i][0])
        M = pts[mi]
        best, bx = None, float("inf")
        for k in range(len(ring)):
            a, b = pts[ring[k]], pts[ring[(k + 1) % len(ring)]]
            if (a[1] - M[1]) * (b[1] - M[1]) > 0 or a[1] == b[1]:
                continue
            x = a[0] + (M[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if M[0] <= x < bx:
                bx = x
                best = k if a[0] > b[0] else (k + 1) % len(ring)
        # choisit le sommet visible le plus proche en direction
        cand = best
        Pc = pts[ring[cand]]
        I = (bx, M[1])
        bestang = None
        for k, idx in enumerate(ring):
            q = pts[idx]
            if q[0] < M[0] or idx == ring[cand]:
                continue
            if in_tri(q, M, I, Pc):
                ang = abs(math.atan2(q[1] - M[1], q[0] - M[0]))
                if bestang is None or ang < bestang:
                    bestang, cand = ang, k
        hk = hr.index(mi)
        hseq = hr[hk:] + hr[:hk] + [mi]
        ring = ring[:cand + 1] + hseq + ring[cand:]
    tris = []
    idx = ring[:]
    guard = 0
    while len(idx) > 3 and guard < 100000:
        guard += 1
        n = len(idx)
        clipped = False
        for i in range(n):
            a, b, c = idx[i - 1], idx[i], idx[(i + 1) % n]
            A, B, C = pts[a], pts[b], pts[c]
            if cross(A, B, C) <= 1e-12:
                continue
            ok = True
            for j in idx:
                if j in (a, b, c):
                    continue
                Q = pts[j]
                if Q in (A, B, C):
                    continue
                if in_tri(Q, A, B, C):
                    ok = False
                    break
            if ok:
                tris.append((a, b, c))
                del idx[i]
                clipped = True
                break
        if not clipped:  # dégénéré : on force
            tris.append((idx[-1], idx[0], idx[1]))
            del idx[0]
    if len(idx) == 3:
        tris.append(tuple(idx))
    return pts, tris


def cross(A, B, C):
    return (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0])


def in_tri(Q, A, B, C):
    d1, d2, d3 = cross(A, B, Q), cross(B, C, Q), cross(C, A, Q)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


MAT_BOIS = "bois"                  # texture versionnée assets/bois.png (fil du bois = axe v de l'image)
MAT_AJOUT = "gris_bleute"          # tout ce qui n'est pas en bois : colle, douille, tige filetée, ampoule
TEXTURE_BOIS = "bois.png"
TEXTURE_TAILLE = 600               # une répétition de la texture (128 px) couvre 60 mm (unités SVG)


def mtl_text():
    return ("# Materiaux de la lampe coronale (coronale.py)\n"
            "newmtl %s\nKa 1 1 1\nKd 1 1 1\nKs 0.05 0.05 0.05\nNs 20\nd 1\nillum 2\nmap_Kd %s\n\n"
            "newmtl %s\nKa 0.80 0.84 0.90\nKd 0.80 0.84 0.90\nKs 0.2 0.2 0.2\nNs 60\nd 1\nillum 2\n"
            % (MAT_BOIS, TEXTURE_BOIS, MAT_AJOUT))


class Obj:
    def __init__(self, zup=False):
        self.v, self.vt, self.lines, self.zup = [], [], [], zup

    def vert(self, x, y, z):
        """x, y : plan SVG (0,1 mm) ; z : hauteur (0,1 mm). Sortie en mm."""
        X, Y, Z = x / 10, -y / 10, z / 10      # vue de dessus non miroir
        self.v.append((X, Y, Z) if self.zup else (X, Z, -Y))
        return len(self.v)

    def tex(self, a, b):
        self.vt.append((a / TEXTURE_TAILLE, b / TEXTURE_TAILLE))
        return len(self.vt)

    def face(self, vs, ts=None):
        self.lines.append("f " + " ".join("%d/%d" % (v, t) if ts else "%d" % v
                                          for v, t in zip(vs, ts or vs)))

    def prism(self, name, outer, holes, z0, h, mat=MAT_AJOUT, fil=None):
        """Prisme droit. fil = None (pas d'UV), ("plat", angle) : plaque dont le fil suit la direction
        angle (°) du plan, ou ("debout", 0) : pièce dont le fil est vertical (montants, tiges)."""
        self.lines.append("o %s" % name)
        self.lines.append("usemtl %s" % mat)
        pts, tris = triangulate(outer, holes)
        bot = [self.vert(q[0], q[1], z0) for q in pts]
        top = [self.vert(q[0], q[1], z0 + h) for q in pts]
        tt = None
        if fil:
            qq = [rot(q, -fil[1]) for q in pts]          # le fil devient l'axe x -> axe v de la texture
            tt = [self.tex(q[1], q[0]) for q in qq]
        for a, b, c in tris:   # tris : sens horaire à l'écran = anti-horaire vu de dessus (y inversé)
            self.face([top[a], top[b], top[c]], tt and [tt[a], tt[b], tt[c]])
            self.face([bot[c], bot[b], bot[a]], tt and [tt[c], tt[b], tt[a]])
        rings = [list(range(len(outer)))]
        off = len(outer)
        for hh in holes:
            rings.append(list(range(off, off + len(hh))))
            off += len(hh)
        for r_i, r in enumerate(rings):
            ring_pts = [pts[i] for i in r]
            outward_cw = poly_area(ring_pts) > 0          # horaire écran
            want_cw = (r_i == 0)
            seq = r if outward_cw == want_cw else r[::-1]
            s = 0.0
            for k in range(len(seq)):
                i, j = seq[k], seq[(k + 1) % len(seq)]
                ts = None
                if fil:
                    s2 = s + norm(sub(pts[j], pts[i]))
                    if fil[0] == "debout":   # fil vertical : v = hauteur
                        ts = [self.tex(s, z0), self.tex(s2, z0), self.tex(s2, z0 + h), self.tex(s, z0 + h)]
                    else:                    # fil horizontal le long du chant : v = abscisse
                        ts = [self.tex(z0, s), self.tex(z0, s2), self.tex(z0 + h, s2), self.tex(z0 + h, s)]
                    s = s2
                self.face([bot[i], bot[j], top[j], top[i]], ts)

    def revolve(self, name, profile, seg, mat=MAT_AJOUT):
        """Solide de révolution autour de l'axe de la lampe. profile = [(r, z), ...] du bas vers le haut,
        commençant et finissant sur l'axe (r = 0)."""
        self.lines.append("o %s" % name)
        self.lines.append("usemtl %s" % mat)
        rings = []
        for r, z in profile:
            if r == 0:
                rings.append([self.vert(0, 0, z)] * seg)
            else:
                rings.append([self.vert(r * math.cos(2 * math.pi * k / seg),
                                        r * math.sin(2 * math.pi * k / seg), z) for k in range(seg)])
        for a, b in zip(rings, rings[1:]):
            for k in range(seg):
                k2 = (k + 1) % seg
                q = [a[k], a[k2], b[k2], b[k]]
                q = [v for n, v in enumerate(q) if v not in q[:n]]
                if len(q) >= 3:
                    self.lines.append("f " + " ".join(map(str, q)))

    def text(self, header, mtllib=None):
        out = [header] + (["mtllib %s" % mtllib] if mtllib else [])
        out += ["v %.4f %.4f %.4f" % q for q in self.v]
        out += ["vt %.5f %.5f" % q for q in self.vt]
        # les faces sont construites dans le repère écran (y vers le bas) : on inverse
        # l'ordre pour obtenir des normales sortantes dans le repère 3D direct
        out += [" ".join(["f"] + l.split()[:0:-1]) if l.startswith("f ") else l for l in self.lines]
        return "\n".join(out) + "\n"


def build_obj(p, zup=False, seg=48, electro=None, mtllib=None):
    """Structure bois seule (electro False) : uniquement les pièces du 1er SVG, matériau bois texturé.
    Structure complète (electro True) : + joints de colle, douille, tige filetée, ampoule (gris bleuté)."""
    p = resolve(p)
    if electro is None:
        electro = str(p.get("electrique", "non")).lower() == "oui"
    o = Obj(zup)
    ep = p["epaisseur"]
    B = MAT_BOIS
    for k in range(3):
        o.prism("support_%d" % (k + 1), [rot(q, 120 * k) for q in support_points(p)], [],
                p["z_support"], ep, B, ("plat", 210 + 120 * k))
    for k in range(6):
        o.prism("montant_%d" % (k + 1), placed(montant_points(p), p, k), [],
                p["z_montant"], p["montant_hauteur"], B, ("debout", 0))
    o.prism("supportDouille", circle_points(0, 0, p["support_douille_rayon"], seg * 2),
            [circle_points(0, 0, p["trouSD_rayon"], seg)], p["z_support_douille"], ep, B, ("plat", 270))
    tc = tige_centres(p)
    rholes = [circle_points(0, 0, p["trouR_rayon"], seg)] + \
             [circle_points(c[0], c[1], p["tige_rayon"], seg) for c in tc]
    o.prism("reuleaux", reuleaux_points(p), rholes, p["z_reuleaux"], ep, B, ("plat", 270))
    base = tranche_points(p)
    for k in range(6):
        P = placed(base, p, k)
        holes = [circle_points(c[0], c[1], p["tige_rayon"], seg) for c in tc if inside(c, P)]
        o.prism("trancheCouronne_%d" % (k + 1), P, holes, p["z_couronne"], ep, B, ("plat", 240 + 60 * k))
    for k, c in enumerate(tc):
        o.prism("tige_%d" % (k + 1), circle_points(c[0], c[1], p["tige_rayon"], seg), [],
                p["z_tige"], p["tige_longueur"], B, ("debout", 0))
    if electro:
        el = electrique(p)
        if p.get("colle_epaisseur"):
            for k in range(6):   # joint sur chaque rayon 180° + 60°·k, à la hauteur de la couronne
                o.prism("colle_%d" % (k + 1), colle_points(p, 180 + 60 * k), [], p["z_couronne"], ep)
        o.prism("douille", circle_points(0, 0, el["douille_rayon"], seg * 2), [],
                el["z_douille_bas"], el["z_douille_haut"] - el["z_douille_bas"])
        o.prism("tigeFiletee", circle_points(0, 0, el["tige_filetee_rayon"], seg), [],
                el["z_tige_filetee_bas"], el["z_tige_filetee_haut"] - el["z_tige_filetee_bas"])
        # Ampoule inventée : culot E14 apparent (Ø 14, 11 mm) puis globe sphérique raccordé au col.
        z0, rc, Rg = el["z_douille_haut"], 70, el["ampoule_rayon"]
        o.revolve("ampoule_culot", [(0, z0), (rc, z0), (rc, z0 + 110), (0, z0 + 110)], seg)
        a0 = math.acos(rc / Rg)                 # angle (sous l'équateur) où le globe rejoint le col
        zc = z0 + 110 + Rg * math.sin(a0)
        prof = [(0, z0 + 110)]
        n = 24
        for i in range(n + 1):
            a = -a0 + (math.pi / 2 + a0) * i / n
            prof.append((Rg * math.cos(a) if i < n else 0, zc + Rg * math.sin(a)))
        o.revolve("ampoule_globe", prof, seg)
    hdr = "# Lampe coronale - unite : mm - axe vertical : %s - %s\n# genere par coronale.py" % (
        "Z" if zup else "Y", "structure complete" if electro else "structure 100 % bois")
    return o.text(hdr, mtllib)


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("extract"); a.add_argument("src"); a.add_argument("-o")
    a = sp.add_parser("check"); a.add_argument("params")
    a = sp.add_parser("svg"); a.add_argument("params"); a.add_argument("-o")
    a = sp.add_parser("apply"); a.add_argument("params"); a.add_argument("src"); a.add_argument("-o")
    a = sp.add_parser("obj"); a.add_argument("params"); a.add_argument("-o")
    a.add_argument("--z-up", action="store_true", help="axe vertical Z (défaut : Y, convention OBJ)")
    a.add_argument("--segments", type=int, default=48)
    a.add_argument("--electrique", choices=["oui", "non"],
                   help="oui = douille + tige filetée + ampoule ; non = bois seul (défaut : paramètre electrique)")
    args = ap.parse_args()
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass

    def out(text, path):
        if path:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            print("écrit :", path, file=sys.stderr)
        else:
            sys.stdout.write(text)

    if args.cmd == "extract":
        with open(args.src, encoding="utf-8") as fh:
            p = extract(fh.read())
        for n in p["_notes"]:
            print("AVERTISSEMENT :", n, file=sys.stderr)
        out(json.dumps(p, indent=2, ensure_ascii=False) + "\n", args.o)
    elif args.cmd == "check":
        print(json.dumps(check(load_params(args.params)), indent=2, ensure_ascii=False))
    elif args.cmd == "svg":
        p = resolve(load_params(args.params))
        dd = svg_defs(p)
        s = "\n".join('<path id="%s" d="%s" fill="none" stroke="black" />' % kv for kv in dd.items())
        s += '\n<circle id="tige" cx="0" cy="%s" r="%s" fill="none" stroke="black" />' % (
            f(-p["tige_distance"]), f(p["tige_rayon"]))
        for k, key in (("supportDouille", "support_douille_rayon"), ("trouSD", "trouSD_rayon"),
                       ("trouR", "trouR_rayon")):
            s += '\n<circle id="%s" cx="0" cy="0" r="%s" fill="none" stroke="black" />' % (k, f(p[key]))
        out(s + "\n", args.o)
    elif args.cmd == "apply":
        with open(args.src, encoding="utf-8") as fh:
            src = fh.read()
        out(apply(load_params(args.params), src), args.o or args.src)
    elif args.cmd == "obj":
        # lampe.obj -> lampe.mtl + bois.png (copie de la texture versionnée assets/bois.png) à côté
        stem = os.path.splitext(args.o)[0] if args.o else "lampe"
        mtl = os.path.basename(stem) + ".mtl"
        el = None if args.electrique is None else args.electrique == "oui"
        out(build_obj(load_params(args.params), args.z_up, args.segments, el, mtl), args.o)
        if args.o:
            dst = os.path.dirname(os.path.abspath(args.o))
            out(mtl_text(), os.path.join(dst, mtl))
            src_tex = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", TEXTURE_BOIS)
            shutil.copyfile(src_tex, os.path.join(dst, TEXTURE_BOIS))
            print("copié :", os.path.join(dst, TEXTURE_BOIS), file=sys.stderr)
        else:
            print("(sans -o : %s et %s non écrits)" % (mtl, TEXTURE_BOIS), file=sys.stderr)


if __name__ == "__main__":
    main()
