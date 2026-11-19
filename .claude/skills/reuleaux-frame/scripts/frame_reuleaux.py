#!/usr/bin/env python3
"""
frame_reuleaux.py — Encadre un triangle de Reuleaux (#reuleaux) d'un SVG par les trois
triangles équilatéraux circonscrits optimaux (distance de Hausdorff), ajoutés dans <defs>
sous forme de groupes <g id="triangle1|2|3" transform="... translate(cx cy) rotate(θ)">.

Dépendances : bibliothèque standard Python 3.8+ uniquement.

Usage :
  python3 frame_reuleaux.py entree.svg -o sortie.svg --margin 5 [--id reuleaux] [--prefix triangle]
         [--frame local|global] [--angle 20.78] [--tol 1e-3] [--force] [--json rapport.json]
"""
import argparse, json, math, re, sys
import xml.etree.ElementTree as ET

XLINK_NS = "http://www.w3.org/1999/xlink"
SQ3 = math.sqrt(3.0)
MARK_BEGIN = "<!-- reuleaux-frame:begin"
MARK_END = "<!-- reuleaux-frame:end -->"


class FrameError(Exception):
    pass


# --------------------------------------------------------------------------- matrices affines
# Une matrice est le 6-uplet SVG (a, b, c, d, e, f) : x' = a x + c y + e ; y' = b x + d y + f
IDENT = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mul(m, n):
    """m ∘ n (on applique n puis m) — même convention que la concaténation SVG « m n »."""
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a*A + c*B, b*A + d*B, a*C + c*D, b*C + d*D, a*E + c*F + e, b*E + d*F + f)


def apply(m, p):
    a, b, c, d, e, f = m
    return (a*p[0] + c*p[1] + e, b*p[0] + d*p[1] + f)


_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_NUM_RE = re.compile(_NUM)


def parse_transform(s):
    if not s:
        return IDENT
    m = IDENT
    for name, args in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", s):
        v = [float(x) for x in _NUM_RE.findall(args)]
        if name == "matrix" and len(v) == 6:
            t = tuple(v)
        elif name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0)
        elif name == "scale":
            sx = v[0]; sy = v[1] if len(v) > 1 else v[0]
            t = (sx, 0, 0, sy, 0, 0)
        elif name == "rotate":
            r = math.radians(v[0]); co, si = math.cos(r), math.sin(r)
            t = (co, si, -si, co, 0, 0)
            if len(v) >= 3:
                cx, cy = v[1], v[2]
                t = mul((1, 0, 0, 1, cx, cy), mul(t, (1, 0, 0, 1, -cx, -cy)))
        elif name == "skewX":
            t = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif name == "skewY":
            t = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else:
            raise FrameError(f"transformation SVG non reconnue : {name}({args})")
        m = mul(m, t)
    return m


# --------------------------------------------------------------------------- lecture de chemins
class _Scanner:
    def __init__(self, d):
        self.s, self.i = d, 0

    def skip(self):
        while self.i < len(self.s) and self.s[self.i] in " \t\r\n,":
            self.i += 1

    def done(self):
        self.skip()
        return self.i >= len(self.s)

    def peek_cmd(self):
        self.skip()
        if self.i < len(self.s) and self.s[self.i].isalpha() and self.s[self.i] not in "eE":
            return self.s[self.i]
        return None

    def cmd(self):
        c = self.peek_cmd(); self.i += 1
        return c

    def num(self):
        self.skip()
        m = _NUM_RE.match(self.s, self.i)
        if not m:
            raise FrameError(f"nombre attendu dans le chemin à la position {self.i}")
        self.i = m.end()
        return float(m.group())

    def flag(self):
        self.skip()
        ch = self.s[self.i] if self.i < len(self.s) else ""
        if ch not in ("0", "1"):
            raise FrameError("drapeau d'arc invalide dans le chemin")
        self.i += 1
        return ch == "1"


def _arc_points(p0, rx, ry, phi, fa, fs, p1, step_deg):
    """Conversion arc SVG (extrémités) -> centre, puis échantillonnage (spéc. SVG, annexe F.6.5)."""
    if rx == 0 or ry == 0 or p0 == p1:
        return [p1]
    rx, ry = abs(rx), abs(ry)
    ph = math.radians(phi); co, si = math.cos(ph), math.sin(ph)
    dx, dy = (p0[0]-p1[0])/2, (p0[1]-p1[1])/2
    x1, y1 = co*dx + si*dy, -si*dx + co*dy
    lam = x1*x1/(rx*rx) + y1*y1/(ry*ry)
    if lam > 1:
        s = math.sqrt(lam); rx *= s; ry *= s
    num = rx*rx*ry*ry - rx*rx*y1*y1 - ry*ry*x1*x1
    den = rx*rx*y1*y1 + ry*ry*x1*x1
    k = math.sqrt(max(0.0, num/den)) * (-1 if fa == fs else 1)
    cxp, cyp = k*rx*y1/ry, -k*ry*x1/rx
    cx = co*cxp - si*cyp + (p0[0]+p1[0])/2
    cy = si*cxp + co*cyp + (p0[1]+p1[1])/2

    def ang(ux, uy, vx, vy):
        return math.atan2(ux*vy - uy*vx, ux*vx + uy*vy)

    t1 = ang(1, 0, (x1-cxp)/rx, (y1-cyp)/ry)
    dt = ang((x1-cxp)/rx, (y1-cyp)/ry, (-x1-cxp)/rx, (-y1-cyp)/ry)
    if not fs and dt > 0:
        dt -= 2*math.pi
    if fs and dt < 0:
        dt += 2*math.pi
    n = max(2, int(abs(math.degrees(dt))/step_deg) + 1)
    out = []
    for j in range(1, n+1):
        t = t1 + dt*j/n
        x, y = rx*math.cos(t), ry*math.sin(t)
        out.append((co*x - si*y + cx, si*x + co*y + cy))
    out[-1] = p1
    return out


def _bez(pts, n=96):
    out = []
    for j in range(1, n+1):
        t = j/n
        q = list(pts)
        while len(q) > 1:
            q = [((1-t)*q[i][0] + t*q[i+1][0], (1-t)*q[i][1] + t*q[i+1][1]) for i in range(len(q)-1)]
        out.append(q[0])
    return out


def _line(p0, p1, n=16):
    return [(p0[0]+(p1[0]-p0[0])*j/n, p0[1]+(p1[1]-p0[1])*j/n) for j in range(1, n+1)]


def sample_path(d, step_deg=0.1):
    sc = _Scanner(d); pts = []; cur = (0.0, 0.0); start = cur
    last_c = last_q = None; cmd = None
    while not sc.done():
        c = sc.peek_cmd()
        if c:
            cmd = sc.cmd()
        elif cmd is None:
            raise FrameError("chemin SVG mal formé")
        rel = cmd.islower(); C = cmd.upper()

        def P():
            x, y = sc.num(), sc.num()
            return (cur[0]+x, cur[1]+y) if rel else (x, y)

        if C == "M":
            cur = P(); start = cur; pts.append(cur)
            cmd = "l" if rel else "L"; last_c = last_q = None
            continue
        if C == "Z":
            pts += _line(cur, start); cur = start; last_c = last_q = None
            continue
        if C == "L":
            p = P(); pts += _line(cur, p); cur = p; last_c = last_q = None
        elif C == "H":
            x = sc.num(); p = (cur[0]+x if rel else x, cur[1])
            pts += _line(cur, p); cur = p; last_c = last_q = None
        elif C == "V":
            y = sc.num(); p = (cur[0], cur[1]+y if rel else y)
            pts += _line(cur, p); cur = p; last_c = last_q = None
        elif C == "C":
            c1, c2, p = P(), P(), P()
            pts += _bez([cur, c1, c2, p]); last_c = c2; last_q = None; cur = p
        elif C == "S":
            c1 = (2*cur[0]-last_c[0], 2*cur[1]-last_c[1]) if last_c else cur
            c2, p = P(), P()
            pts += _bez([cur, c1, c2, p]); last_c = c2; last_q = None; cur = p
        elif C == "Q":
            q1, p = P(), P()
            pts += _bez([cur, q1, p]); last_q = q1; last_c = None; cur = p
        elif C == "T":
            q1 = (2*cur[0]-last_q[0], 2*cur[1]-last_q[1]) if last_q else cur
            p = P()
            pts += _bez([cur, q1, p]); last_q = q1; last_c = None; cur = p
        elif C == "A":
            rx, ry, phi = sc.num(), sc.num(), sc.num()
            fa, fs = sc.flag(), sc.flag()
            p = P()
            pts += _arc_points(cur, rx, ry, phi, fa, fs, p, step_deg); cur = p; last_c = last_q = None
        else:
            raise FrameError(f"commande de chemin non gérée : {cmd}")
    return pts


# --------------------------------------------------------------------------- géométrie d'un élément
def local(tag):
    return tag.split("}", 1)[-1]


def _f(v, default=0.0):
    if v is None or v.strip() == "":
        return default
    if v.strip().endswith("%"):
        raise FrameError(f"valeur en pourcentage non gérée : {v!r}")
    m = _NUM_RE.match(v.strip())
    if not m:
        raise FrameError(f"valeur numérique non gérée : {v!r}")
    return float(m.group())


SKIP_TAGS = ("title", "desc", "metadata", "text", "defs", "style", "script")


def element_points(el, by_id, depth=0):
    """Points du contour de l'élément dans SON repère local (sans son propre attribut transform)."""
    if depth > 20:
        raise FrameError("références <use> trop imbriquées (boucle ?)")
    t = local(el.tag)
    if t == "path":
        return sample_path(el.get("d", ""))
    if t in ("polygon", "polyline"):
        v = [float(x) for x in _NUM_RE.findall(el.get("points", ""))]
        P = list(zip(v[0::2], v[1::2]))
        out = [P[0]]
        for i in range(1, len(P)):
            out += _line(P[i-1], P[i])
        if t == "polygon":
            out += _line(P[-1], P[0])
        return out
    if t in ("g", "symbol"):
        out = []
        for ch in el:
            if local(ch.tag) in SKIP_TAGS:
                continue
            m = parse_transform(ch.get("transform"))
            out += [apply(m, p) for p in element_points(ch, by_id, depth+1)]
        return out
    if t == "use":
        href = el.get("href") or el.get(f"{{{XLINK_NS}}}href") or ""
        ref = by_id.get(href.lstrip("#"))
        if ref is None:
            raise FrameError(f"<use> : référence introuvable {href!r}")
        m = mul((1, 0, 0, 1, _f(el.get("x")), _f(el.get("y"))), parse_transform(ref.get("transform")))
        return [apply(m, p) for p in element_points(ref, by_id, depth+1)]
    raise FrameError(f"type d'élément non géré pour l'analyse : <{t}>")


# --------------------------------------------------------------------------- ajustement du Reuleaux
def centroid(P):
    A = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(P, P[1:] + P[:1]):
        cr = x0*y1 - x1*y0; A += cr; cx += (x0+x1)*cr; cy += (y0+y1)*cr
    if abs(A) < 1e-12:
        n = len(P)
        return (sum(p[0] for p in P)/n, sum(p[1] for p in P)/n)
    return (cx/(3*A), cy/(3*A))


def angdiff(a, b):
    return (a - b + math.pi) % (2*math.pi) - math.pi


def fit_reuleaux(P):
    """Centre c, largeur L et direction β d'un sommet (radians, repère SVG y vers le bas)."""
    c = centroid(P)
    for _ in range(3):
        ang = [math.atan2(p[1]-c[1], p[0]-c[0]) for p in P]
        rad = [math.hypot(p[0]-c[0], p[1]-c[1]) for p in P]
        i0 = max(range(len(P)), key=lambda i: rad[i])
        V = [P[i0]]
        for k in (1, 2):
            tgt = ang[i0] + k*2*math.pi/3
            cand = [i for i in range(len(P)) if abs(angdiff(ang[i], tgt)) < math.radians(40)]
            if not cand:
                raise FrameError("impossible de trouver trois sommets : la forme n'est pas un triangle de Reuleaux")
            V.append(P[max(cand, key=lambda i: rad[i])])
        c = (sum(v[0] for v in V)/3, sum(v[1] for v in V)/3)
    L = (math.dist(V[0], V[1]) + math.dist(V[1], V[2]) + math.dist(V[2], V[0]))/3
    # orientation : moyenne circulaire des directions des sommets modulo 120°
    s = sum(complex(math.cos(3*math.atan2(v[1]-c[1], v[0]-c[0])),
                    math.sin(3*math.atan2(v[1]-c[1], v[0]-c[0]))) for v in V)
    beta = math.atan2(s.imag, s.real)/3
    a0 = math.atan2(V[0][1]-c[1], V[0][0]-c[0])
    while angdiff(beta, a0) > math.pi/3:
        beta -= 2*math.pi/3
    while angdiff(beta, a0) < -math.pi/3:
        beta += 2*math.pi/3
    return c, L, beta


def ideal_vertices(c, L, beta):
    r = L/SQ3
    return [(c[0] + r*math.cos(beta + k*2*math.pi/3), c[1] + r*math.sin(beta + k*2*math.pi/3)) for k in range(3)]


def _arcs(Vs):
    for k in range(3):
        C = Vs[k]; A, B = Vs[(k+1) % 3], Vs[(k+2) % 3]
        a1 = math.atan2(A[1]-C[1], A[0]-C[0])
        span = angdiff(math.atan2(B[1]-C[1], B[0]-C[0]), a1)
        yield C, A, B, a1, span


def dist_to_ideal(p, Vs, L):
    best = math.inf
    for C, A, B, a1, span in _arcs(Vs):
        u = angdiff(math.atan2(p[1]-C[1], p[0]-C[0]), a1)
        inside = (0 <= u <= span) if span > 0 else (span <= u <= 0)
        d = abs(math.hypot(p[0]-C[0], p[1]-C[1]) - L) if inside else min(math.dist(p, A), math.dist(p, B))
        best = min(best, d)
    return best


def ideal_boundary(Vs, L, n=60):
    out = []
    for C, A, B, a1, span in _arcs(Vs):
        out += [(C[0] + L*math.cos(a1+span*j/n), C[1] + L*math.sin(a1+span*j/n)) for j in range(n)]
    return out


def dist_to_polyline(q, P):
    """Distance de q à la ligne brisée des échantillons (contrôle que le contour est couvert)."""
    best = math.inf
    for A, B in zip(P, P[1:] + P[:1]):
        ex, ey = B[0]-A[0], B[1]-A[1]; l2 = ex*ex + ey*ey
        t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((q[0]-A[0])*ex + (q[1]-A[1])*ey)/l2))
        best = min(best, math.hypot(q[0]-A[0]-t*ex, q[1]-A[1]-t*ey))
    return best


# --------------------------------------------------------------------------- construction optimale
def optimal_offset_deg():
    """a* solution de 1/cos(a/2) − 1 = (1 − cos(30°−a)) / cos(60°−a) (égalisation arc / coin)."""
    d = math.radians
    f = lambda a: (1/math.cos(d(a)/2) - 1) - (1 - math.cos(d(30-a)))/math.cos(d(60-a))
    lo, hi = 10.0, 29.0
    for _ in range(200):
        mid = (lo+hi)/2
        if f(lo)*f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo+hi)/2


def triangle_specs(L, beta, a):
    if not 0 <= a <= 30:
        raise FrameError("--angle doit être compris entre 0 et 30°")
    specs = []
    for n, delta in enumerate((-a, 0.0, a), start=1):
        s = L*(2*SQ3 - 2*math.cos(math.radians(delta)))      # côté, valable pour |delta| ≤ 30°
        R = s/SQ3                                            # rayon circonscrit
        rho = math.degrees(beta) + 90.0 + delta              # rotation SVG du triangle « pointe en haut »
        rho = -((-rho + 60.0) % 120.0 - 60.0)                # symétrie d'ordre 3 : ramené dans ]-60°, 60°]
        specs.append(dict(n=n, offset_deg=delta, rotation_deg=rho, side=s, circumradius=R,
                          local_vertices=[(0.0, -R), (-s/2, R/2), (s/2, R/2)]))
    return specs


def apply_margin(specs, margin, frame_m):
    """Écarte chaque côté de `margin` unités, mesurées dans le repère où l'on place les <use>
    (celui obtenu après la transformation `frame_m`). En repère local, le côté de normale n
    recule de δ = margin·‖A⁻ᵀn‖, A étant la partie linéaire de frame_m ∘ rotate(θ).
    Échelle uniforme k : δ = margin/k pour les trois côtés, le triangle reste équilatéral."""
    out = []
    a0, b0, c0, d0 = frame_m[:4]
    for sp in specs:
        r = math.radians(sp["rotation_deg"]); co, si = math.cos(r), math.sin(r)
        a, b, c, d = a0*co + c0*si, b0*co + d0*si, -a0*si + c0*co, -b0*si + d0*co   # A = F·R
        det = a*d - b*c
        if abs(det) < 1e-15:
            raise FrameError("transformation dégénérée : impossible d'appliquer la marge")
        ia, ib, ic, id_ = d/det, -b/det, -c/det, a/det                               # A⁻¹
        rin = sp["side"]/(2*SQ3)
        normals = [(0.0, 1.0), (-SQ3/2, -0.5), (SQ3/2, -0.5)]   # base, côté gauche, côté droit
        lines, deltas = [], []
        for nx, ny in normals:
            tx, ty = ia*nx + ib*ny, ic*nx + id_*ny               # A⁻ᵀ n
            dl = margin*math.hypot(tx, ty)
            deltas.append(dl); lines.append((nx, ny, rin + dl))
        def cross(l1, l2):
            (a1, b1, c1), (a2, b2, c2) = l1, l2
            dt = a1*b2 - a2*b1
            return ((c1*b2 - c2*b1)/dt, (a1*c2 - a2*c1)/dt)
        verts = [cross(lines[1], lines[2]), cross(lines[0], lines[1]), cross(lines[2], lines[0])]
        sides = [math.dist(verts[i], verts[(i+1) % 3]) for i in range(3)]
        q = dict(sp)
        deltas = [deltas[1], deltas[0], deltas[2]]   # même ordre que les côtés sommet0→1, 1→2, 2→0
        q.update(margin=margin, margin_local=deltas, local_vertices=verts, side_with_margin=sum(sides)/3)
        out.append(q)
    return out


def margin_gaps(P, c, specs):
    """Distance minimale (repère local) entre le contour échantillonné et chaque côté."""
    res = []
    for sp in specs:
        r = math.radians(sp["rotation_deg"]); co, si = math.cos(r), math.sin(r)
        G = [(c[0] + co*x - si*y, c[1] + si*x + co*y) for x, y in sp["local_vertices"]]
        gaps = []
        for i in range(3):
            A, B = G[i], G[(i+1) % 3]
            ex, ey = B[0]-A[0], B[1]-A[1]; ln = math.hypot(ex, ey)
            nx, ny = ey/ln, -ex/ln
            if (c[0]-A[0])*nx + (c[1]-A[1])*ny > 0:
                nx, ny = -nx, -ny
            off = A[0]*nx + A[1]*ny
            gaps.append(min(off - (p[0]*nx + p[1]*ny) for p in P))
        res.append(gaps)
    return res


def check_and_measure(P, c, L, specs, Vs):
    """Contrôles dans le repère local : inclusion, tangence, erreur de Hausdorff de l'intersection."""
    lines = []; worst_out = 0.0; worst_gap = 0.0
    for sp in specs:
        r = math.radians(sp["rotation_deg"]); co, si = math.cos(r), math.sin(r)
        G = [(c[0] + co*x - si*y, c[1] + si*x + co*y) for x, y in sp["local_vertices"]]
        for i in range(3):
            A, B = G[i], G[(i+1) % 3]
            ex, ey = B[0]-A[0], B[1]-A[1]; ln = math.hypot(ex, ey)
            nx, ny = ey/ln, -ex/ln
            if (c[0]-A[0])*nx + (c[1]-A[1])*ny > 0:
                nx, ny = -nx, -ny                           # normale extérieure
            off = A[0]*nx + A[1]*ny
            vals = [off - (p[0]*nx + p[1]*ny) for p in P]   # ≥ 0 : point du bon côté
            worst_out = max(worst_out, -min(vals))
            worst_gap = max(worst_gap, max(0.0, min(vals)))
            lines.append((math.atan2(ny, nx), nx, ny, off))
    lines.sort()
    poly = []
    for i in range(len(lines)):
        _, a1, b1, c1 = lines[i]; _, a2, b2, c2 = lines[(i+1) % len(lines)]
        det = a1*b2 - a2*b1
        if abs(det) > 1e-14:
            poly.append(((c1*b2 - c2*b1)/det, (a1*c2 - a2*c1)/det))
    H = max(dist_to_ideal(p, Vs, L) for p in poly)
    return dict(containment_violation=worst_out/L, tangency_gap=worst_gap/L,
                hausdorff_error=H/L, intersection_vertices=len(poly))


# --------------------------------------------------------------------------- écriture SVG
def fmt(x):
    s = f"{x:.10f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def build_block(specs, prefix, frame_tf, ns_prefix, L, a, center, indent="  "):
    pfx = f"{ns_prefix}:" if ns_prefix else ""
    out = [f"{MARK_BEGIN} : généré par frame_reuleaux.py, ne pas éditer à la main. "
           f"L={fmt(L)}, rotations relatives (-a, 0, +a), a={fmt(a)} deg, marge={fmt(specs[0]['margin'])} -->"]
    for sp in specs:
        tf = (frame_tf + " " if frame_tf else "") + \
             f"translate({fmt(center[0])} {fmt(center[1])}) rotate({fmt(sp['rotation_deg'])})"
        pts = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in sp["local_vertices"])
        out.append(f'{indent}<{pfx}g id="{prefix}{sp["n"]}" transform="{tf}" '
                   f'data-rotation-deg="{fmt(sp["rotation_deg"])}" data-offset-deg="{fmt(sp["offset_deg"])}" '
                   f'data-side="{fmt(sp["side_with_margin"])}" data-side-tangent="{fmt(sp["side"])}" '
                   f'data-margin="{fmt(sp["margin"])}" data-reuleaux-width="{fmt(L)}">')
        out.append(f'{indent}{indent}<{pfx}polygon points="{pts}" fill="none" stroke="black"/>')
        out.append(f"{indent}</{pfx}g>")
    out.append(MARK_END)
    return "\n".join(out)


def insert_block(text, block, ns_prefix):
    if MARK_BEGIN in text:
        i = text.index(MARK_BEGIN); j = text.index(MARK_END, i) + len(MARK_END)
        return text[:i] + block + text[j:], "bloc précédent remplacé"
    q = (ns_prefix + ":") if ns_prefix else ""
    m = re.search(rf"<{re.escape(q)}defs\b[^>]*?(/?)>", text)
    if m:
        if m.group(1) == "/":
            opening = m.group(0)[:-2].rstrip() + ">"
            return text[:m.start()] + opening + "\n" + block + f"\n</{q}defs>" + text[m.end():], "ajouté dans le <defs/> existant"
        return text[:m.end()] + "\n" + block + "\n" + text[m.end():], "ajouté dans le <defs> existant"
    m = re.search(rf"<{re.escape(q)}svg\b[^>]*>", text)
    if not m:
        raise FrameError("élément racine <svg> introuvable")
    return text[:m.end()] + f"\n<{q}defs>\n" + block + f"\n</{q}defs>" + text[m.end():], "nouveau <defs> créé"


# --------------------------------------------------------------------------- programme principal
def run(src_text, margin, rid="reuleaux", prefix="triangle", frame="local", angle=None, tol=1e-3, force=False):
    if margin < 0:
        raise FrameError("la marge doit être positive ou nulle")
    root = ET.fromstring(src_text.encode("utf-8"))
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}
    parent = {ch: p for p in root.iter() for ch in p}
    target = by_id.get(rid)
    if target is None:
        raise FrameError(f"aucun élément d'identifiant #{rid}")
    if MARK_BEGIN not in src_text:
        for n in (1, 2, 3):
            if f"{prefix}{n}" in by_id:
                raise FrameError(f"l'identifiant #{prefix}{n} existe déjà ; choisissez un autre --prefix")

    P = element_points(target, by_id)
    if len(P) < 30:
        raise FrameError("géométrie trop pauvre pour être analysée")
    c, L, beta = fit_reuleaux(P)
    Vs = ideal_vertices(c, L, beta)
    dev = max(dist_to_ideal(p, Vs, L) for p in P) / L
    cov = max(dist_to_polyline(q, P) for q in ideal_boundary(Vs, L)) / L
    fit_err = max(dev, cov)
    if fit_err > tol and not force:
        raise FrameError(f"#{rid} n'est pas un triangle de Reuleaux à la tolérance {tol:g} "
                         f"(écart relatif mesuré {fit_err:.3g}). Utilisez --tol ou --force si c'est voulu.")

    a = optimal_offset_deg() if angle is None else float(angle)
    specs = triangle_specs(L, beta, a)
    checks = check_and_measure(P, c, L, specs, Vs)

    tfs = []
    if frame == "global":
        anc = []; e = parent.get(target)
        while e is not None and e is not root:
            if local(e.tag) in ("svg", "symbol", "pattern", "clipPath", "mask", "marker"):
                raise FrameError(f"--frame global : ancêtre <{local(e.tag)}> avec viewport propre non géré")
            if e.get("transform"):
                anc.append(e.get("transform").strip())
            e = parent.get(e)
        tfs += list(reversed(anc))
    if target.get("transform"):
        tfs.append(target.get("transform").strip())
    frame_tf = " ".join(tfs)

    m = re.match(r"\s*(?:<\?.*?\?>\s*|<!--.*?-->\s*|<!DOCTYPE[^>]*>\s*)*<(?:(\w+):)?svg\b", src_text, re.S)
    ns_prefix = (m.group(1) or "") if m else ""
    final = apply_margin(specs, margin, parse_transform(frame_tf))
    gaps = margin_gaps(P, c, final)
    checks["margin_error"] = max(abs(g - dl) for sp, gg in zip(final, gaps)
                                 for g, dl in zip(gg, sp["margin_local"])) / L
    block = build_block(final, prefix, frame_tf, ns_prefix, L, a, c)
    out_text, where = insert_block(src_text, block, ns_prefix)
    ET.fromstring(out_text.encode("utf-8"))   # le résultat doit rester un XML valide

    warnings = []
    if fit_err > 1e-5:
        warnings.append(f"forme approchée (écart relatif {fit_err:.2e}) : triangles calculés pour le Reuleaux idéal ajusté")
    if checks["containment_violation"] > 1e-6:
        warnings.append(f"le contour dépasse les triangles de {checks['containment_violation']:.2e} L au plus "
                        "(approximation du tracé d'origine)")
    if margin > 0 and len({round(d, 9) for sp in final for d in sp["margin_local"]}) > 1:
        warnings.append("le transform n'est pas une similitude : en repère local, les trois côtés reculent "
                        "de quantités différentes pour obtenir la même marge à l'écran ; le centre du "
                        "polygone n'est donc plus exactement à l'origine du groupe")
    report = dict(reuleaux_id=rid, element=local(target.tag), frame=frame,
                  frame_transform=frame_tf or None, center=c, width_L=L,
                  vertex_direction_deg=math.degrees(beta), fit_relative_error=fit_err,
                  offset_a_deg=a, margin=margin, defs=where, triangles=final, checks=checks,
                  warnings=warnings)
    return out_text, report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="fichier SVG d'entrée")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-o", "--output", help="fichier SVG de sortie")
    g.add_argument("--in-place", action="store_true", help="réécrit le fichier d'entrée")
    ap.add_argument("--margin", type=float, required=True,
                    help="marge entre la courbe et chaque côté, en unités utilisateur (px) du repère "
                         "où les <use> seront placés ; 0 = tangence exacte")
    ap.add_argument("--id", default="reuleaux", help="identifiant du Reuleaux (défaut : reuleaux)")
    ap.add_argument("--prefix", default="triangle", help="préfixe des groupes créés (défaut : triangle)")
    ap.add_argument("--frame", choices=["local", "global"], default="local",
                    help="local : repère du parent de #reuleaux (défaut) ; global : repère de la racine")
    ap.add_argument("--angle", type=float, default=None,
                    help="rotation relative a en degrés (défaut : optimum de Hausdorff 20.7810993°)")
    ap.add_argument("--tol", type=float, default=1e-3, help="écart relatif toléré à un Reuleaux exact")
    ap.add_argument("--force", action="store_true", help="continue même si la forme s'écarte d'un Reuleaux")
    ap.add_argument("--json", help="écrit aussi le rapport JSON dans ce fichier")
    args = ap.parse_args(argv)
    try:
        with open(args.input, encoding="utf-8") as fh:
            src = fh.read()
        out, rep = run(src, args.margin, args.id, args.prefix, args.frame, args.angle, args.tol, args.force)
    except (FrameError, ET.ParseError, OSError) as e:
        print(f"ERREUR : {e}", file=sys.stderr)
        return 2
    with open(args.input if args.in_place else args.output, "w", encoding="utf-8") as fh:
        fh.write(out)
    js = json.dumps(rep, indent=2, ensure_ascii=False)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            fh.write(js)
    print(js)
    for w in rep["warnings"]:
        print(f"AVERTISSEMENT : {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
