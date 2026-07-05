# CLAUDE.md — docgen/

Rendu déterministe de l'objet `Observation` (calculé par `core/`) en
`.docx` via `python-docx`. Phase 1 (Observation) et Phase 2 (Fiche
technique) uniquement — la Phase 3 (Interprétation) est hors périmètre,
voir `interpretation/CLAUDE.md`.

## Frontière stricte

- Ce module ne calcule rien. Toute donnée affichée provient déjà de
  l'`Observation` fournie en argument — si un fait manque, il doit être
  ajouté côté `core/`, jamais recalculé ou approximé ici.
- Ce module ne fait pas d'interprétation. Le style reste factuel même dans
  les sous-sections « rédactionnelles » de Phase 2 (Ascendant/maître,
  Luminaires, Nœuds et Parts) : elles décrivent des relations vérifiables
  (conjonction, aspect, dignité), sans tirer de conclusion psychologique.
  Ça, c'est le travail de la rédaction assistée de Phase 3 (voir
  `interpretation/CLAUDE.md`).

## Structure du fichier

- `builder.py` : toutes les fonctions `add_*_table`/`add_*_section`, plus
  `build_observation_document` (le seul point d'entrée public — orchestre
  l'appel de toutes les sous-sections dans l'ordre du document final).
- `styles.py` : mise en forme des tableaux (en-têtes, largeurs, ombrage) —
  purement visuel, aucune logique astrologique. Contient aussi
  `add_table_of_contents` (champ Word `TOC`, construit via oxml bas niveau
  faute de support natif python-docx).
- `chart_image.py` (jalon 33) : rendu d'images (`Observation -> bytes` PNG,
  via `matplotlib`) — roue du thème, graphique élément/modalité, frise de
  libération zodiacale. Même frontière que le reste de `docgen` : aucun
  calcul de position propre, dessiné à la main plutôt qu'avec une
  bibliothèque de thèmes existante (`kerykeion`) pour ne jamais introduire
  un second moteur Swiss Ephemeris indépendant de `core/`. Un import tardif
  dans `render_elemental_modal_chart` (vers `builder._distribution_points`)
  évite un cycle `builder -> chart_image -> builder` — même pattern que
  `dignities.solar_proximity` (jalon 20). Les constantes radiales de la
  roue (rayons, pas d'étagement, décalage d'étiquette) forment un système
  couplé, pas des réglages indépendants : les revoir ensemble, jamais un
  seul isolément, sous peine de déplacer un chevauchement plutôt que de le
  résoudre (voir jalon 43 dans le `CLAUDE.md` racine pour l'exemple vécu).
  `scripts/render_wheel_debug.py` rend la roue seule (PNG) vers
  `output/wheel_debug/`, sans régénérer tout le `.docx` — pratique pour
  itérer visuellement sur ces constantes.

## Deux styles de rendu textuel, selon la nature de la sous-section

1. **Tables et puces factuelles** (Phase 1 entière, plus « Dignités et
   réceptions » en Phase 2) : un fait → une ligne/puce, format fixe, pas de
   phrase composée. Ex. `add_positions_table`, `add_aspects_section`.
2. **Phrases relationnelles** (le reste de Phase 2, depuis le jalon 19) :
   assemble plusieurs faits en une phrase française. Trois helpers
   réutilisables à connaître avant d'en écrire un nouveau :
   - `_conjunction_clause(point, observation)` — « conjoint(e) à X, Y »
     pour les co-résidents de signe.
   - `_rulership_aspect_clause(ruler, governed_sign)` — relation d'aspect
     entre le signe d'une planète et un signe qu'elle gouverne.
   - `_cluster_relations_clause(point, observation)` — énumère les
     relations d'aspect de l'amas d'un point vers tous les autres amas,
     groupées par type dans l'ordre canonique de `ASPECT_LABEL`.

   Avant d'écrire une nouvelle sous-section relationnelle : vérifier si un
   de ces trois helpers (ou une combinaison) suffit plutôt que d'en ajouter
   un nouveau.

## Simplifications assumées (norme, pas exception au cas par cas)

Les deux documents de référence (Anthony, Liam) divergent souvent l'un de
l'autre sur la forme exacte d'une phrase (ordre signe/maison, jonction
« et »/virgule, qualificatifs subjectifs comme « juste » ou « à la limite
de »). La règle constante appliquée dans tout ce module : choisir **un**
gabarit déterministe et le documenter (dans le jalon concerné, `CLAUDE.md`
racine), plutôt que de reproduire la variabilité de la prose humaine ou de
basculer entre plusieurs styles selon le thème. Ne jamais recopier un
qualificatif subjectif (« juste », « à la limite », un jugement de valeur
implicite) : rester descriptif.

Quand les deux documents divergent sur un point structurel plus important
qu'une formulation (ex. quels points inclure dans une répartition), c'est
un choix de fond, pas une simplification de style — voir le `CLAUDE.md`
racine, section garde-fous, avant de trancher seul.

## Tests

Pour toute nouvelle section : un test synthétique isolé (`PointPosition`/
`Observation` construits à la main, pas les fixtures Anthony/Liam) qui
couvre les branches de la fonction, puis un recoupement dans
`test_build_observation_document_structure` contre le texte réel des deux
documents de référence quand ils documentent la sous-section — mot pour
mot si le texte source le permet, en notant explicitement les écarts
assumés sinon. Voir `tests/test_docgen.py`.

## Historique détaillé

L'ordre d'ajout des sections (jalons 2b, 4, 18-25) et le détail de chaque
divergence/incohérence découverte sont dans le `CLAUDE.md` racine, section
État d'avancement — pas dupliqué ici pour éviter la dérive entre les deux
au fil des jalons futurs.
