# Géométrie de l'encadrement optimal d'un triangle de Reuleaux

Toutes les longueurs sont exprimées en multiples de la largeur L. Les angles sont en degrés.

## Reuleaux et fonction de support

On place les sommets Vₖ à la distance r = L/√3 du centre, dans les directions β + 120°·k. Le Reuleaux est l'intersection des trois disques de rayon L centrés en Vₖ. Son aire vaut (π − √3)/2 · L².

La fonction de support h(φ) donne la distance du centre à la droite d'appui de normale φ. Soit d ∈ [0°, 60°] l'écart entre φ et la direction de sommet la plus proche :

- si d ≤ 30°, la droite passe par un sommet et h = L cos(d)/√3 ;
- sinon, elle est tangente à un arc et h = L(1 − cos(60° − d)/√3).

## Triangles circonscrits

**Un seul paramètre par triangle.** Un côté tangent avec le Reuleaux d'un seul côté est une droite d'appui. L'orientation fixe donc les trois côtés, et la position comme la taille ne sont pas libres.

**Centre imposé.** Le Reuleaux est invariant par rotation de 120°, donc les trois distances d'appui d'un même triangle sont égales. Le triangle est alors centré exactement au centre du Reuleaux.

**Taille.** On note δ la rotation relative, avec δ = 0 quand la pointe du triangle est dirigée vers un sommet. Le triangle touche alors les milieux des arcs. Le côté vaut :

- s(δ) = L(2√3 − 2 cos δ) pour |δ| ≤ 30° ;
- s = 2L cos(60° − |δ|) pour 30° ≤ |δ| ≤ 60°.

La période est de 120°.

## Optimum de Hausdorff

Le polygone d'intersection contient le Reuleaux. La distance de Hausdorff est donc le maximum, sur les sommets du polygone, de la distance au Reuleaux, car la distance à un convexe est une fonction convexe.

Pour la famille (−a, 0, a), deux erreurs s'opposent :

- les sommets situés sur les arcs ont une erreur E_arc = 1/cos(a/2) − 1, croissante en a ;
- les sommets situés sur l'axe d'un coin ont une erreur E_coin = (1 − cos(30° − a))/cos(60° − a), décroissante en a.

L'unique croisement donne a* = 20,781099296° et E* = 0,016672171. Les 9 sommets sont alors à égale distance du Reuleaux (équi-oscillation).

La recherche numérique globale confirme ce résultat : grille sur tous les triplets d'angles puis Nelder-Mead depuis plusieurs départs, tous convergents vers (−a*, 0, a*). L'optimalité globale est seulement observée, pas démontrée. Elle n'est démontrée qu'à l'intérieur de la famille symétrique.

## Autres critères (famille symétrique, optima numériques)

| Critère | a optimal | Hausdorff | Moyenne | Radiale | Aire excédentaire |
|---|---|---|---|---|---|
| Hausdorff | 20,781099 | **0,0166722** | 0,0053536 | 0,0171227 | 0,0166237 |
| Radiale (rayons issus du centre) | 20,700255 | 0,0169848 | 0,0053512 | **0,0169849** | 0,0166065 |
| Moyenne (le long du périmètre) | 20,586838 | 0,0174289 | **0,0053500** | 0,0174289 | 0,0165883 |
| Aire excédentaire (× L²) | 20,345793 | 0,0183946 | 0,0053556 | 0,0183946 | **0,0165725** |
| Référence ±20° | 20 | 0,0198321 | 0,0053836 | 0,0198321 | 0,0166054 |

Ces optima diffèrent parce que les critères ne mesurent pas la même chose :

- **Hausdorff** est un critère de pire cas : il égalise les erreurs des coins et des arcs.
- **La moyenne et l'aire** sont des intégrales qui pèsent peu les petites pointes de coin. Elles conduisent à un a plus petit.
- **L'erreur radiale** se mesure le long de rayons issus du centre, alors que les arcs sont centrés sur les sommets. Elle pénalise donc davantage les arcs.

Pour utiliser l'un de ces optima avec le script, passe `--angle <a>`.
