# Géométrie détaillée de la lampe coronale

Unités : 0,1 mm (unités SVG). Repère SVG, y vers le bas ; un angle θ désigne la direction
u(θ) = (cos θ, sin θ), donc 270° pointe vers le haut du plan. Valeurs actuelles entre crochets.

## Notations

- Rh : rayon circonscrit de l'hexagone central [200]. Apothème = Rh·√3/2 [173,2].
- c : côté court d'une tranche [350] ; r1 = Rh + c [550].
- e : épaisseur radiale du montant [200] ; r2 = r1 + e [750] ; côté long = r2 − Rh [550].
- w : largeur tangentielle du montant [300].
- m : marge du support [50].

## Tranche de couronne (`#trancheCouronne`, pièce de base entre 180° et 240°)

Sommets dans l'ordre du chemin :

1. (−Rh, 0) : sommet de l'hexagone à 180°.
2. (−r1, 0) : fin du côté court, le long du rayon 180°.
3. (−r1, −(2·r2 − r1)/√3) : le côté 2→3 est perpendiculaire au rayon 180° (droite x = −r1) ; le point 3 est
   son intersection avec la droite perpendiculaire au rayon 240° à la distance r2. Longueur de cette face
   F = (2·r2 − r1)/√3 [548,483] : c'est la face sur laquelle le montant est collé, il faut w ≤ F.
4. r2·u(240) : fin du côté long [(−375, −649,519)]. Le côté 3→4 est perpendiculaire au rayon 240°.
5. Rh·u(240) : sommet de l'hexagone à 240°. Le côté 4→5 est radial (côté long), 5→1 est un côté de l'hexagone.

La tranche est convexe. Les 6 tranches sont les rotations de 60°·k. Le côté long de la tranche k et le côté
court de la tranche k+1 sont sur le même rayon : la tranche k+1 s'arrête à r1, la tranche k continue jusqu'à r2.
L'encoche ainsi formée (r1 → r2 radialement, du côté de la tranche k+1) reçoit le montant : il est collé à
la face 2→3 de la tranche k+1 et au côté long de la tranche k. D'où **côté long = côté court + e**.

Encombrement d'une tranche (débit) : largeur r1 − Rh/2 [450], hauteur r2·√3/2 [649,519]. Le plan de débit
utilise une largeur de 455 (0,5 mm de jeu).

## Montant (`#montant`)

Rectangle radial [r1, r2] × tangentiel [0, w] autour du rayon 180°, du côté des angles croissants (−y) :
`M −r1 0 l −e 0 l 0 −w l e 0 z`. Six rotations de 60°.

## Support (`#support`)

On repère un point par (ρ radial, τ tangentiel) autour d'un rayon θ : P = ρ·u(θ) + τ·u(θ+90°).
Cadre autour du montant à θ : ρ ∈ [r1 − m, r2 + m], τ ∈ [−m, w + m] (300 × 400 actuellement).
Une pièce de support relie les cadres à 180° (cadre 1) et 240° (cadre 2) ; trois pièces à 0/120/240°.

Contour (sens du chemin) :

1. S = (r1−m, −m)@180 [(−500, 50)] → (r2+m, −m)@180 : côté du cadre 1, complet.
2. → A = (r2+m, w+m−retrait)@180 : côté extérieur du cadre 1, raccourci de `retrait` [40].
3. Cubique A → B = (r2+m, −m)@240 (coin extérieur du cadre 2). Poignées tangentes aux côtés extérieurs :
   C1 = A + h1·u(270), C2 = B − h2·u(330). h1, h2 = fractions de la corde |AB| [0,2546 et 0,2654 de 505,2].
4. → (r2+m, w+m)@240 → (r1−m, w+m)@240 → Q0 = (r1−m, −m)@240 : trois côtés complets du cadre 2.
5. Quadratique Q0 → S, point de contrôle = intersection des côtés intérieurs des deux cadres
   = (r1−m)/cos 30° · u(210) [(−500, −288,7)]. Tangente aux deux côtés intérieurs.

Les raccords sont donc G1 (lisses) aux quatre extrémités des courbes. Quand r1 change, les cadres suivent
les montants et les courbes sont recalculées avec les mêmes fractions de poignées.

## supportDouille, Reuleaux, trous

- supportDouille : cercle de rayon R_SD [300] ; trouSD rayon [50].
- Reuleaux : sommet à 270° (vers −y). Largeur W = (R_SD + d)/(1 − 1/√3) avec d = débord [5] → W [721,638].
  Distance centre-sommet W/√3 [416,638]. Chaque arc a pour rayon W et pour centre le sommet opposé.
  Chemin : `M 0 −W/√3 a W W 0 0 1 W/2 W√3/2 a W W 0 0 1 −W 0 a W W 0 0 1 W/2 −W√3/2 z`.
- trouR : rayon [175], centré.

## Tiges

Centres à la distance D du centre, dans les directions 270°, 30°, 150° : la tige est sur la bissectrice
de la tranche qui la reçoit (à égale distance des deux coins de l'hexagone) et sur l'axe d'un sommet du
Reuleaux. Rayon [45].

Jeux (bord à bord, tige comprise) en fonction de D :

- tranche : distance au contour de la tranche tournée de 60° (le côté d'hexagone, apothème Rh·√3/2, est en
  général le plus proche) moins le rayon de la tige ;
- Reuleaux : distance aux arcs adjacents au sommet, W − √((W/2)² + (W/(2√3) + D)²), moins le rayon ;
- trouR : D − R_trouR − rayon.

Règle de conception : D maximise le minimum de ces jeux (`tige_distance: "auto"`). Actuellement D = 280
pour un optimum de 285,2 (jeu mini 60 contre 65,2). Pour que l'optimum soit atteignable, le Reuleaux doit
être orienté sommet vers la tige et assez grand pour que tige + trouR tiennent entre le centre et le sommet.

## Plans de débit (SVG 2 à 4)

- SVG 2 : deux tranches dans leur rectangle de débit (`#coupeCouronne`), le Reuleaux avec les repères de
  perçage des tiges (petits cercles r = 3).
- SVG 3 : imbrication de 3 supports avec leurs montants (`#supportPlein`) sur une planche de 140 × 140 mm ;
  positions et rotation (−131°) choisies à la main, à revoir si le support change.
- SVG 4 : Reuleaux et triangles circonscrits (`#triangle1..3`, skill `reuleaux-frame`).
