---
name: lampe-coronale
description: Structure 3D, vocabulaire et règles de proportion de la lampe de bureau en bois « coronale » décrite par lampeCoronale.html (plans de coupe SVG en 0,1 mm : #support, #montant, #supportDouille, #trouSD, #reuleaux, #trouR, #tige, #trancheCouronne). Utilise cette skill dès qu'il est question de cette lampe ou de ce fichier, en particulier pour agrandir, réduire ou modifier les proportions d'une pièce (couronne, hexagone central, montants, support, triangle de Reuleaux, tiges, douille, joint de colle entre tranches) en propageant les contraintes aux autres pièces, pour générer un modèle 3D .obj texturé (structure 100 % bois ou complète avec ampoule et colle), pour vérifier qu'une modification reste fabricable, ou pour expliquer l'assemblage — même si l'utilisateur dit seulement « la lampe », « la couronne », « l'hélice », « les tranches », « la colle », « le translate » ou « le plan de coupe ».
---

# Lampe coronale

Lampe de bureau entièrement en bois. Le fichier `lampeCoronale.html` contient plusieurs SVG ;
**le premier est la coupe horizontale de tous les plans superposés**, les suivants sont des plans
de débit (couronne, support, Reuleaux). **Unité SVG : 0,1 mm** (300 = 30 mm). Repère SVG : x vers
la droite, y vers le bas, origine = axe vertical de la lampe. Les pièces sont définies une fois dans
`<defs>` puis répétées par `<use … transform="rotate(…)">` : conserve toujours cette réutilisation,
les rotations et les coordonnées relatives (`l`, `c`, `q`, `a`) dans les chemins.

## Vocabulaire

| Terme | Id SVG | Description |
|---|---|---|
| support | `#support` | 3 pièces au sol (rotations 0/120/240°), épaisseur 20 mm. Chacune encadre 2 montants voisins. |
| montant | `#montant` | 6 poteaux verticaux de 180 mm, section 20 (radial) × 30 (tangentiel) mm, posés sur le support. |
| supportDouille | `#supportDouille` | Disque suspendu sous le Reuleaux, épaisseur 20 mm. |
| trouSD | `#trouSD` | Petit trou central du supportDouille, Ø 13 mm : reçoit l'adaptateur bois de la tige filetée. |
| triangle de Reuleaux | `#reuleaux` | Plaque de 20 mm collée sur le supportDouille, sommet vers le haut du plan (−y). |
| trouR | `#trouR` | Grand trou central du Reuleaux, Ø 35 mm : logement de la douille. |
| tige filetée | — | Tige filetée Ø 10 mm (non bois) qui traverse trouSD (avec adaptateur bois) et fixe la douille. |
| douille | — | Douille E14 minimale (non bois, Ø 28 mm), posée dans trouR sur le supportDouille, traverse l'hexagone de la couronne. |
| ampoule | — | Ampoule E14 vissée sur la douille, au-dessus de la couronne, entourée par le haut des montants. |
| tige | `#tige` | 3 tiges cylindriques verticales (0/120/240°) qui suspendent Reuleaux + supportDouille à la couronne. |
| couronne | — | Anneau de 6 tranches autour d'un hexagone vide ; appelée « hélice » dans d'anciens textes. |
| tranche (de couronne) | `#trancheCouronne` | Une des 6 pièces de la couronne (rotations de 60°), épaisseur 20 mm. |
| hexagone central | — | Vide hexagonal au centre de la couronne, délimité par les petits côtés intérieurs des tranches. |
| joint de colle | — | Couche d'époxy de 1 mm entre deux tranches voisines (et entre un montant et la tranche voisine), figurée par l'unique `translate` du groupe `#secteurCouronne` (tranche + montant), utilisé par le 1er SVG seulement. |
| côté court / côté long | — | Les deux côtés radiaux d'une tranche : côté long = côté court + épaisseur du montant. |
| encadrement / cadre | — | Rectangle du support autour d'un montant, à la marge de 5 mm. |
| triangle1..3 | `#triangle1..3` | Triangles circonscrits au Reuleaux générés par la skill `reuleaux-frame` (aide au débit, pas une pièce). |

## Empilement vertical (z depuis le sol, mm)

| Pièce | z bas → haut | Notes |
|---|---|---|
| support | 0 → 20 | |
| montants | 20 → 200 | posés sur le support |
| supportDouille | 20 → 40 | suspendu (ne touche pas le support) |
| Reuleaux | 40 → 60 | collé sur le supportDouille |
| (vide) | 60 → 80 | tiges apparentes sur 20 mm |
| couronne | 80 → 100 | collée aux montants |
| tiges | 40 → 100 | 60 mm : traversent Reuleaux, vide et couronne |
| tige filetée | 20 → 60 (hypothèse) | traverse trouSD, vissée ~20 mm dans la douille |
| douille | 40 → 100 | du fond de trouR jusqu'au dessus de la couronne, à travers l'hexagone |
| ampoule | 100 → 155 | au-dessus de la couronne, dans la « couronne » des montants (jusqu'à 200) |

Les tiges traversent des trous de leur diamètre dans le Reuleaux et dans 3 des 6 tranches
(celles qui couvrent 270°, 30° et 150°). Ces trous ne sont pas dessinés dans le SVG (le cercle
`#tige` les représente). La hauteur de la couronne le long des montants (80 mm) découle de la
description ; si l'utilisateur la précise autrement, change `z_couronne` (et `tige_longueur` si le vide change).

**Douille et hexagone.** La douille E14 (Ø 28 mm) passe dans l'hexagone, dont le cercle inscrit mesure
Rh·√3 + 2 × colle (34,64 + 2 = 36,64 mm, le joint de colle élargit l'hexagone) ; une douille au diamètre de trouR (35 mm) n'y passerait pas. Réduire l'hexagone pour
agrandir la couronne par l'intérieur est donc limité par la douille : `check` alerte si Rh·√3/2 + colle < rayon de
la douille. trouSD (Ø 13 mm) est dimensionné pour l'adaptateur bois de la tige filetée Ø 10 mm.

## Joint de colle (translate du 1er SVG)

Un seul translate, dans `<defs>`, sur un groupe que seul le 1er SVG utilise :

```svg
<g id="secteurCouronne" transform="translate(-8.66,-5)">
	<use href="#trancheCouronne" />
	<use href="#montant" />
</g>
…
<use href="#secteurCouronne" />  <!-- puis transform="rotate(60)" … rotate(300) -->
```

La tranche de base est déplacée de `colle_epaisseur` (10 = 1 mm)
le long de sa bissectrice (210°), donc de 0,5 mm perpendiculairement à chacun de ses deux rayons. C'est la seule
translation qui laisse un joint de 1 mm entre voisines **et** garde l'hexagone central régulier : chaque côté
d'hexagone recule de 1 mm (apothème 17,32 → 18,32 mm) et les joints pointent vers les sommets sans les atteindre.
Un `translate(-10,10)` (ou toute direction autre que 210°) déforme l'hexagone : `extract` le signale et donne la bonne valeur.
Le montant suit la tranche sur la face 2→3 de laquelle il est collé (même translation) ; le joint se prolonge donc
de l'hexagone jusqu'à r2, entre le côté long d'une tranche et [côté court de la voisine + montant].

- **Ne jamais mettre le translate sur `#trancheCouronne` ou `#montant` eux-mêmes** : les plans de débit (SVG 2 à 4)
  les utilisent directement et doivent rester dessinés comme sans joint. Le support n'est pas translaté (marges
  effectives 4,1/5,9 mm en radial et 4,5/5,5 mm en tangentiel au lieu de 5 mm, rapportées par `check`).
- Les tiges ne bougent pas : leur trou dans la tranche est décalé de 1 mm par rapport à la tranche (jeux recalculés
  par `check` avec les tranches translatées).

## Géométrie et proportions

Le détail des formules est dans `references/geometrie.md` ; lis-le avant toute modification de proportions.
L'essentiel :

- **Tranche** : bornée par deux rayons à 60° d'écart (côté court Rh→r1, côté long Rh→r2), par un côté de
  l'hexagone central (rayon circonscrit Rh) et par deux côtés extérieurs perpendiculaires à chaque rayon.
  r1 = Rh + côté court, **r2 = r1 + épaisseur radiale du montant** : c'est la contrainte « un côté = l'autre + 20 mm ».
  Le montant se loge dans l'encoche entre le bout du côté court d'une tranche et le côté long de la voisine.
- **Agrandir la couronne** : par l'extérieur (allonger le côté court ; le côté long suit) ou par l'intérieur
  (réduire l'hexagone, Rh). Les montants ne changent pas de section, ils se déplacent avec r1.
- **Support** : deux cadres (montant + 5 mm de marge) autour des montants à 180° et 240°, reliés à
  l'extérieur par une cubique et à l'intérieur par une quadratique, tangentes aux côtés des cadres (courbe
  lisse). Il se déforme automatiquement quand la couronne change.
- **Reuleaux** : son cercle inscrit dépasse le supportDouille de 0,5 mm (largeur = (R_SD + 5)/(1 − 1/√3)).
- **Tiges** : sur la bissectrice d'une tranche (270°, 30°, 150°), à la distance du centre qui maximise le
  plus petit jeu par rapport aux bords de la tranche, du Reuleaux et de trouR. Dans le fichier actuel la tige
  est à 28,0 mm alors que l'optimum calculé est 29,0 mm (28,5 mm sans le joint de colle) : signale-le si tu recalcules, sans le corriger d'office.

## Outil : `scripts/coronale.py`

Utilise le script plutôt que de recalculer à la main : la tranche, le support et le Reuleaux sont liés par
des contraintes faciles à casser, et l'utilisateur attend des cotes exactes. Bibliothèque standard Python.

```bash
S=<chemin-skill>/scripts/coronale.py
python $S extract lampeCoronale.html -o params.json   # paramètres lus dans le SVG (+ avertissements)
python $S check params.json                           # contraintes, jeux de la tige, optimum
python $S apply params.json lampeCoronale.html -o lampeCoronale-v2.html
python $S svg params.json                             # juste les <path>/<circle> régénérés
python $S obj params.json -o lampe.obj [--z-up] [--electrique oui|non]  # 3D en mm (+ lampe.mtl, bois.png)
```

Paramètres (unités SVG, 0,1 mm) : `hexagone_rayon`, `tranche_cote_court`, `montant_epaisseur`,
`montant_largeur`, `montant_hauteur`, `epaisseur`, `support_marge`, `support_retrait`,
`support_poignee_debut`/`_fin` (poignées de la cubique en fraction de la corde, gardées lors d'un agrandissement),
`support_douille_rayon`, `trouSD_rayon`, `trouR_rayon`, `reuleaux_debord`, `tige_rayon`,
`tige_distance` (nombre, ou `"auto"` pour l'optimum), les hauteurs `z_*`, `tige_longueur`, et les éléments
électriques `electrique` (`"oui"`/`"non"`), `douille_rayon`, `z_douille_bas`/`_haut`, `tige_filetee_rayon`,
`z_tige_filetee_bas`/`_haut`, `ampoule_rayon` (hauteurs laissées à `null` : elles suivent le Reuleaux et la couronne),
et `colle_epaisseur` (joint entre tranches, 10 = 1 mm ; 0 = pas de joint). `apply` écrit le translate sur `#secteurCouronne`
et retire tout `transform` mis par erreur sur les chemins `#trancheCouronne` / `#montant`.

## Modifier les proportions

1. `extract` le fichier courant (ne pars pas des valeurs par défaut : l'utilisateur a pu retoucher le SVG).
   Transmets les avertissements : un écart signifie qu'une pièce ne suit plus le modèle.
2. Traduis la demande en paramètres. Les cotes de l'utilisateur sont en mm : multiplie par 10. Ne change que
   ce qui est demandé ; le reste suit par les contraintes. Si la demande contredit une contrainte (par ex.
   côté long imposé indépendamment du montant), explique le conflit et demande quoi privilégier.
3. Si le Reuleaux ou le supportDouille change, mets `tige_distance` à `"auto"` sauf instruction contraire.
4. `check` : aucune alerte bloquante (montant plus large que sa face, tige qui déborde, support auto-sécant).
5. `apply` vers un **nouveau fichier** sauf demande explicite d'écraser. Le script met à jour les defs, les
   cercles, les repères de perçage des tiges et le rectangle de débit de la couronne.
6. Préviens de ce qui reste manuel : l'imbrication des supports sur la planche (3ᵉ SVG, positions fixes),
   la position du Reuleaux dans le 2ᵉ SVG si sa taille augmente, la `viewBox` si les pièces débordent, et le
   bloc `reuleaux-frame` (relance la skill `reuleaux-frame` si le Reuleaux a changé).
7. Résume les cotes en mm avant/après (r1, r2, côtés de tranche, largeur du Reuleaux, distance des tiges, encombrement).

## Générer le modèle 3D

`obj` produit un fichier OBJ industriel (pas artistique) : un objet nommé par pièce (`support_1..3`,
`montant_1..6`, `supportDouille`, `reuleaux`, `trancheCouronne_1..6`, `tige_1..3`), prismes fermés et
orientés, trous inclus, unité mm, axe vertical Y par défaut (convention OBJ ; `--z-up` pour les outils de
CAO). La vue de dessus n'est pas en miroir par rapport au SVG. Tranches et montants sont placés comme dans le
1er SVG, joint de colle compris (vide de 1 mm entre tranches).

Avec `-o lampe.obj`, le script écrit aussi `lampe.mtl` et copie à côté la texture **versionnée**
`assets/bois.png` (128 px, chêne sur quartier : veines douces, pores en tirets, maillures claires ; raccordable, fil selon l'axe v ; une répétition = 60 mm). Ne la régénère pas : remplace
le fichier si on veut une autre essence. Deux matériaux seulement :

- `bois` (texture `bois.png`, coordonnées UV fournies : fil vertical pour montants et tiges, fil le long de la
  pièce pour les plaques) — **toutes** les pièces du modèle SVG et elles seules ;
- `gris_bleute` (Kd 0,80 0,84 0,90, sans texture) — **tous** les éléments ajoutés par la structure complète.

**Structure 100 % bois ou complète** (`--electrique non|oui`, défaut `non`). Si l'utilisateur ne l'a pas précisé,
demande-lui. `non` = uniquement les pièces du 1er SVG, en bois ; le joint reste vide. `oui` ajoute tous les éléments
ensemble, jamais séparément, en gris bleuté : les 6 couches de colle `colle_1..6` (1 × 55 × 20 mm, du sommet
de l'hexagone jusqu'à r2, à la hauteur de la couronne), `douille`, `tigeFiletee` et l'ampoule (`ampoule_culot` +
`ampoule_globe`). L'ampoule est une forme inventée : culot E14 apparent Ø 14 × 11 mm, puis globe sphérique Ø 45 mm
raccordé au col, sommet à 155 mm. Pour une modification de proportions, génère
l'OBJ à partir des paramètres modifiés. Indique les hypothèses de hauteur utilisées.
