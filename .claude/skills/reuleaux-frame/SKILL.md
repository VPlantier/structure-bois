---
name: reuleaux-frame
description: Trouve le triangle de Reuleaux d'identifiant #reuleaux dans un fichier SVG, l'analyse (centre, largeur, orientation) et ajoute dans <defs> trois groupes triangle1, triangle2, triangle3 contenant les triangles équilatéraux circonscrits optimaux (minimum de distance de Hausdorff), éventuellement agrandis d'une marge en px demandée à l'utilisateur, chacun défini pointe en haut puis placé par translate() rotate(), prêts à être instanciés par <use>. Utilise cette skill dès qu'un SVG contient un triangle de Reuleaux à encadrer, circonscrire ou approcher par des triangles ou un polygone (ennéagone), même si l'utilisateur ne cite pas l'algorithme, parle de « cadre », de « triangles tangents », de « Reuleaux triangle framing » ou demande seulement de « préparer les triangles dans les defs ».
---

# Encadrer un triangle de Reuleaux dans un SVG

Le script `scripts/frame_reuleaux.py` fait tout le travail. Il est déterministe, utilise uniquement la bibliothèque standard de Python 3.8+ et conserve le fichier d'origine octet pour octet, à l'insertion près. Utilise-le plutôt que de recalculer à la main : l'analyse d'un chemin SVG (arcs, Béziers, transformations, `<use>`) est facile à rater, et l'utilisateur attend une géométrie exacte, pas dessinée à l'œil.

## Résultat attendu

Le script ajoute dans `<defs>` un bloc délimité par des commentaires `reuleaux-frame:begin` et `reuleaux-frame:end`. Il crée le `<defs>` s'il n'existe pas. Le bloc contient :

```xml
<g id="triangle1" transform="[transform de #reuleaux] translate(cx cy) rotate(θ1)" data-rotation-deg="…" data-offset-deg="…" data-side="…" data-reuleaux-width="…">
  <polygon points="0,-R' -s'/2,R'/2 s'/2,R'/2" fill="none" stroke="black"/>   <!-- pointe en haut, marge incluse -->
</g>
… triangle2, triangle3
```

Ce que l'utilisateur doit savoir sur ce bloc :

- **Rien n'est dessiné.** Les groupes restent dans `<defs>` et l'utilisateur les place lui-même avec `<use href="#triangle1"/>`.
- **Les polygones portent `fill="none" stroke="black"`.** Ces attributs sont écrits sur le polygone lui-même, donc un `<use>` ne peut pas les changer par héritage. Pour un autre style, il faut passer par une règle CSS ou modifier le bloc.
- **La marge écarte chaque côté de la courbe.** Avec une marge de 5, chaque côté est à 5 unités de la courbe au lieu de la toucher. Les unités sont les unités utilisateur (px) du repère où l'on place les `<use>`. Le triangle reste équilatéral et de même centre : son rayon circonscrit augmente de 2·marge et son côté de 2√3·marge. Si #reuleaux porte une échelle, par exemple `scale(1.3)`, le script la compense pour que la marge reste bien de 5 px à l'écran.
- **Le préfixe de transformation est le `transform` de #reuleaux, recopié tel quel.** Le triangle hérite ainsi de la même transformation que le Reuleaux. Un `<use href="#triangleN">` placé exactement là où l'on placerait `<use href="#reuleaux">`, avec le même `transform` sur le `<use>`, encadre donc l'objet exactement, que #reuleaux soit dans `<defs>` ou dessiné directement. Si #reuleaux est dessiné dans un groupe transformé, le `<use>` doit aller dans ce même groupe, ou bien utilise `--frame global` (voir plus bas).
- **Relancer le script remplace le bloc précédent.** Il est idempotent.

## Procédure

1. Repère le fichier SVG. Si l'utilisateur donne un autre identifiant que `reuleaux`, passe `--id`.
2. **Demande la marge d'agrandissement si l'utilisateur ne l'a pas indiquée**, avant de lancer quoi que ce soit. Pose une seule question, par exemple : « Quelle marge veux-tu entre la courbe et les triangles, en px ? 0 donne des côtés exactement tangents. » Ne choisis pas de valeur à sa place : le script exige `--margin` justement pour que cette décision vienne de l'utilisateur. Si la marge est donnée dans une autre unité (mm, % de la largeur…), convertis-la en unités utilisateur et indique la conversion.
3. Lance le script :
   ```bash
   python3 <chemin-de-la-skill>/scripts/frame_reuleaux.py entree.svg -o sortie.svg --margin 5 --json rapport.json
   ```
   Options utiles :
   - `--prefix cadre` : produit `cadre1..3`. Le script refuse d'écraser des identifiants `triangle1..3` existants qui n'ont pas été créés par lui.
   - `--frame global` : exprime aussi les transformations des groupes ancêtres, pour un `<use>` placé à la racine du SVG.
   - `--angle 20` : impose une autre rotation relative a, par exemple la configuration de référence ±20°.
   - `--tol` et `--force` : règlent la tolérance de reconnaissance de la forme.
   - `--in-place` : réécrit le fichier d'entrée au lieu de produire `-o`.
4. Lis le rapport JSON imprimé et vérifie trois choses :
   - `fit_relative_error` : l'écart relatif entre le tracé et un Reuleaux idéal. Il vaut environ 1e-7 pour des arcs exacts et environ 1e-5 pour des Béziers.
   - `checks.containment_violation` doit valoir environ 0 et `checks.tangency_gap` doit être proche de 0, ce qui signifie que les 9 côtés touchent bien le contour.
   - `checks.hausdorff_error` vaut environ 0,0166722 avec l'angle par défaut. Cette valeur concerne la configuration tangente : la marge s'y ajoute.
   - `checks.margin_error` doit être proche de 0 : chaque côté est alors bien à la marge demandée de la courbe.
5. Livre le SVG modifié, puis résume en quelques lignes : le centre, la largeur L, la direction d'un sommet, les trois rotations, la marge, les côtés avec et sans marge (`side_with_margin`, `side`), l'emplacement du bloc et un exemple de `<use>`. Transmets les `AVERTISSEMENT` éventuels sans les adoucir.
6. Si l'utilisateur veut voir le résultat, crée une copie de prévisualisation qui ajoute des `<use>`. Ne modifie pas le fichier livré pour cela, puisque la demande est de ne rien dessiner.

## En cas d'erreur (code de sortie 2, message `ERREUR : …`)

- **« n'est pas un triangle de Reuleaux à la tolérance… »** : montre l'écart mesuré. N'utilise `--force` que si l'utilisateur confirme qu'il s'agit d'un Reuleaux approché ou déformé exprès. Les triangles sont alors calculés pour le Reuleaux idéal le plus proche. Un Reuleaux étiré par un `scale(sx, sy)` non uniforme placé *sur l'élément* reste reconnu, car l'analyse se fait avant ce `transform`. En revanche, une déformation intégrée dans les coordonnées du chemin ne l'est pas.
- **Transformation qui n'est pas une similitude** (par exemple `scale(1.3 0.8)`) : la marge reste exacte à l'écran, mais en repère local les trois côtés reculent de quantités différentes, donc le polygone n'est plus centré sur l'origine du groupe. Le script le signale par un avertissement : transmets-le.
- **Éléments non gérés** : `<circle>`, `<ellipse>`, `<rect>`, les transformations CSS (`style="transform:…"`) et les coordonnées en pourcentage. Explique la limite et propose de convertir l'objet en `<path>`.
- **Identifiant déjà utilisé** : propose `--prefix`.

## Ce que fait l'algorithme (pour répondre aux questions)

1. **Échantillonnage.** Le contour de #reuleaux est échantillonné dans son repère local, c'est-à-dire avant son propre `transform`. Le script gère `path` (toutes les commandes, arcs convertis selon la spécification SVG), `polygon`, `polyline`, `g`, `symbol` et `use`, de façon récursive.
2. **Ajustement.** Le script prend le point le plus éloigné du centroïde, puis les plus éloignés dans les secteurs situés à 120° et 240° : ce sont les trois sommets. Il en déduit le centre c (moyenne des sommets), la largeur L (moyenne des côtés) et l'orientation β (moyenne circulaire modulo 120°). Il valide ensuite dans les deux sens : distance des échantillons au Reuleaux idéal, et couverture du contour idéal par les échantillons.
3. **Construction des triangles.** Pour les rotations relatives δ ∈ {−a, 0, +a}, le côté vaut s = L(2√3 − 2 cos δ) et le rayon circonscrit vaut R = s/√3. La rotation SVG est θ = β + 90° + δ, ramenée dans ]−60°, 60°]. Chaque triangle est centré exactement en c : c'est une conséquence de la symétrie d'ordre 3, et non une hypothèse.
   La marge m est ensuite appliquée côté par côté : le côté de normale locale n recule de m·‖A⁻ᵀn‖, où A est la partie linéaire de la transformation complète du groupe. Pour une échelle uniforme k, cela donne m/k sur chaque côté.
4. **Angle optimal.** Par défaut, a est l'optimum de Hausdorff, solution de 1/cos(a/2) − 1 = (1 − cos(30° − a))/cos(60° − a). On obtient a = 20,7810993° et une erreur E = 0,0166722·L, atteinte aux 9 sommets de l'ennéagone d'intersection.

Pour la démonstration, les autres critères (erreur moyenne, erreur radiale, aire excédentaire) et leurs optima respectifs, lis `references/geometry.md`. Ne le charge que si l'utilisateur pose une question mathématique ou demande un autre critère.
