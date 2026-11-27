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

## Joint de colle (1er SVG uniquement)

g = colle_epaisseur [10]. La tranche de base et le montant collé sur sa face 2→3 sont translatés de
T = g·u(210) = (−g·√3/2, −g/2) [(−8,660 ; −5)] : un seul `translate(-8.66,-5)`, sur le groupe
`#secteurCouronne` (tranche + montant) que le 1er SVG répète par `rotate(60·k)`.

- Écart à chacun des deux rayons de la tranche : g·sin 30° = g/2 → joint de g entre tranches voisines.
- Composante le long de la bissectrice : g → chaque côté d'hexagone recule de g ; l'hexagone vide reste régulier,
  d'apothème Rh·√3/2 + g [183,2]. Les côtés radiaux translatés sont décalés radialement de g·√3/2 [8,66] : leurs
  extrémités intérieures (Rh + g√3/2 sur le rayon, ±g/2 en tangentiel) restent à g/√3 [5,77] du sommet de l'hexagone.
- Toute autre translation (par ex. (−10, 10)) n'est pas sur la bissectrice : joints non parallèles, hexagone irrégulier.
- Couche de colle (3D, structure complète) sur le rayon θ = 180° + 60°·k : ρ ∈ [Rh + g√3/2, r2 + g√3/2],
  τ ∈ [−g/2, g/2], z de la couronne. Elle touche le côté long de la tranche k−1 d'un côté, le côté court de la
  tranche k puis son montant de l'autre.
- Montant translaté avec sa tranche ; Reuleaux, supportDouille et tiges non translatés.
- Support **déformé** (pas translaté) : ses cadres suivent les montants posés, voir § Support. Le montant k=0
  (180°) porte t = g·u(210), le montant k=1 (240°) porte rot60(t) = g·u(270) ; dans le repère local de chacun,
  le décalage vaut (s, h) = (g√3/2, g/2) [(8,66 ; 5)].
- SVG 2 et 4 : aucun translate (tranches et montants dessinés comme sans joint). SVG 3 : le contour `#support`
  est la pièce réelle (déformée) et les repères `#montant` de `#supportPlein` portent la translation du joint
  (`translate(t)` et `rotate(60) translate(t)`, écrits par `apply`).

## Montant (`#montant`)

Rectangle radial [r1, r2] × tangentiel [0, w] autour du rayon 180°, du côté des angles croissants (−y) :
`M −r1 0 l −e 0 l 0 −w l e 0 z`. Six rotations de 60°.

## Support (`#support`)

On repère un point par (ρ radial, τ tangentiel) autour d'un rayon θ : P = ρ·u(θ) + τ·u(θ+90°).
Le cadre entoure le montant **posé** (joint de colle compris), décalé de (s, h) = (g√3/2, g/2) dans son repère
local (voir § Joint de colle ; s = h = 0 sans joint). On note ri = r1 + s − m [508,66], ro = r2 + s + m [808,66],
τ ∈ [h − m, h + w + m] [−45 → 355]. Cadre : 300 × 400.
Une pièce de support relie les cadres à 180° (cadre 1) et 240° (cadre 2) ; trois pièces à 0/120/240°.
Les deux cadres ont le même décalage local, mais pas la même direction dans le plan : la pièce n'est pas une
translation de la version sans joint, son contour (dont les courbes) est recalculé.

Contour (sens du chemin) :

1. S = (ri, h−m)@180 [(−508,66, 45)] → (ro, h−m)@180 : côté du cadre 1, complet.
2. → A = (ro, h+w+m−retrait)@180 : côté extérieur du cadre 1, raccourci de `retrait` [40].
3. Cubique A → B = (ro, h−m)@240 (coin extérieur du cadre 2). Poignées tangentes aux côtés extérieurs :
   C1 = A + h1·u(270), C2 = B − h2·u(330). h1, h2 = fractions de la corde |AB| [0,2545 et 0,2654 de 514,9].
4. → (ro, h+w+m)@240 → (ri, h+w+m)@240 → Q0 = (ri, h−m)@240 : trois côtés complets du cadre 2.
5. Quadratique Q0 → S, point de contrôle = intersection des côtés intérieurs des deux cadres
   = ri/cos 30° · u(210) [(−508,66, −293,7)]. Tangente aux deux côtés intérieurs.

Les raccords sont donc G1 (lisses) aux quatre extrémités des courbes. Quand r1 ou le joint de colle change, les
cadres suivent les montants et les courbes sont recalculées avec les mêmes fractions de poignées.
`extract` relit m et retrait en tenant compte de (s, h) ; s'il trouve un support dessiné sans joint alors que
`#secteurCouronne` en porte un, il le signale (apply le déforme). `check` rapporte les marges réelles
(`support_marges_reelles`) mesurées sur les montants posés.

## supportDouille, Reuleaux, trous

- supportDouille : cercle de rayon R_SD [300] ; trouSD rayon [50].
- Reuleaux : sommet à 270° (vers −y). Largeur W = (R_SD + d)/(1 − 1/√3) avec d = débord [5] → W [721,638].
  Distance centre-sommet W/√3 [416,638]. Chaque arc a pour rayon W et pour centre le sommet opposé.
  Chemin : `M 0 −W/√3 a W W 0 0 1 W/2 W√3/2 a W W 0 0 1 −W 0 a W W 0 0 1 W/2 −W√3/2 z`.
- trouR : rayon [175], centré.

## Douille, tige filetée, ampoule (hors bois, option électrique)

- trouSD Ø 13 mm [rayon 65] : logement de l'adaptateur bois de la tige filetée Ø 10 mm.
- Douille E14 minimale Ø 28 mm [rayon 140], du fond de trouR (dessus du supportDouille, z 40 mm) jusqu'au
  dessus de la couronne (z 100 mm), à travers l'hexagone. Condition : rayon douille ≤ Rh·√3/2 [173,2].
  trouR [rayon 175] est plus large que la douille.
- Tige filetée : de z 20 à 60 mm (hypothèse : vissée 20 mm dans la douille).
- Ampoule (forme inventée) : culot cylindrique Ø 14 mm de z 100 à 111 mm, puis globe sphérique de rayon
  [225] dont le bas rejoint le culot ; sommet à 155 mm, entouré par les montants (face intérieure à r1).

## Tiges

Centres à la distance D du centre, dans les directions 270°, 30°, 150° : la tige est sur la bissectrice
de la tranche qui la reçoit (à égale distance des deux coins de l'hexagone) et sur l'axe d'un sommet du
Reuleaux. Rayon [45].

Jeux (bord à bord, tige comprise) en fonction de D :

- tranche : distance au contour de la tranche tournée de 60° (le côté d'hexagone, apothème Rh·√3/2, est en
  général le plus proche) moins le rayon de la tige ;
- Reuleaux : distance aux arcs adjacents au sommet, W − √((W/2)² + (W/(2√3) + D)²), moins le rayon ;
- trouR : D − R_trouR − rayon.

Règle de conception : D maximise le minimum de ces jeux (`tige_distance: "auto"`) ; c'est une cote dérivée,
recalculée par `apply` dès qu'une pièce qui la borne change (joint de colle compris). Avec le joint de 1 mm,
D = 289,8 (285,2 sans joint), jeu mini 6,16 mm, à égalité entre la tranche et le Reuleaux. Pour que l'optimum soit atteignable, le Reuleaux doit
être orienté sommet vers la tige et assez grand pour que tige + trouR tiennent entre le centre et le sommet.

## Plans de débit (SVG 2 à 4)

- SVG 2 : deux tranches dans leur rectangle de débit (`#coupeCouronne`), le Reuleaux avec les repères de
  perçage des tiges (petits cercles r = 3).
- SVG 3 : imbrication de 3 supports avec leurs montants (`#supportPlein`) sur une planche de 140 × 140 mm ;
  positions et rotation (−131°) choisies à la main, à revoir si le support change.
- SVG 4 : Reuleaux et triangles circonscrits (`#triangle1..3`, skill `reuleaux-frame`).
