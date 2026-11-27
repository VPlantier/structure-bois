# structure-bois

Plans et outils de conception d'objets en bois, pilotés par des skills Claude Code.

## Fichiers

| Fichier | Contenu |
|---|---|
| [lampecoronale.html](lampecoronale.html) | Plans SVG de la lampe « coronale » (coupe horizontale + plans de débit), unité 0,1 mm |
| `3d/` (non versionné) | Modèles 3D générés pour visualisation : `lampe-bois.obj` (100 % bois), `lampe-complete.obj` (+ colle, douille, ampoule), `.mtl`, `bois.png` |
## Table des matières des skills

Les skills sont dans [.claude/skills/](.claude/skills/) et sont chargées automatiquement par Claude Code dans ce dépôt.

| Skill | Rôle | Contenu |
|---|---|---|
| [lampe-coronale](.claude/skills/lampe-coronale/SKILL.md) | Vocabulaire, empilement 3D et règles de proportion de la lampe coronale ; modification des proportions avec propagation des contraintes ; export OBJ | [SKILL.md](.claude/skills/lampe-coronale/SKILL.md) · [références géométriques](.claude/skills/lampe-coronale/references/geometrie.md) · [scripts/coronale.py](.claude/skills/lampe-coronale/scripts/coronale.py) · [texture bois](.claude/skills/lampe-coronale/assets/bois.png) |
| [reuleaux-frame](.claude/skills/reuleaux-frame/SKILL.md) | Trouve le triangle de Reuleaux `#reuleaux` d'un SVG et ajoute dans `<defs>` les trois triangles équilatéraux circonscrits optimaux (Hausdorff), avec marge | [SKILL.md](.claude/skills/reuleaux-frame/SKILL.md) · [géométrie](.claude/skills/reuleaux-frame/references/geometry.md) · [scripts/frame_reuleaux.py](.claude/skills/reuleaux-frame/scripts/frame_reuleaux.py) |

### lampe-coronale en bref

```bash
S=.claude/skills/lampe-coronale/scripts/coronale.py
python $S extract lampecoronale.html -o params.json   # lit les paramètres du SVG
python $S check params.json                           # vérifie les contraintes
python $S apply params.json lampecoronale.html -o lampe-v2.html
python $S obj params.json -o lampe.obj --electrique non  # 3D 100 % bois (+ lampe.mtl, bois.png)
python $S obj params.json -o lampe.obj --electrique oui  # 3D complet : + colle, douille, ampoule (gris bleuté)
```

### Ajouter une skill

Créer `.claude/skills/<nom>/SKILL.md` (frontmatter `name` + `description`), puis ajouter une ligne à la table ci-dessus.
