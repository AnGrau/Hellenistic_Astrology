# CLAUDE.md

Ce fichier donne à Claude Code le contexte du projet. Le lire entièrement avant toute action.

## Objectif du projet

Outiller la production d'analyses de thèmes natals en astrologie hellénistique (signes entiers), pour remplacer progressivement la saisie manuelle des données Astro-Seek/Astro.com et la génération manuelle du document Word par un pipeline reproductible :

1. calcul des positions et facteurs du thème (idéalement via une éphéméride locale, sans dépendre d'une capture d'écran),
2. dérivation automatique des données de la phase d'observation (maisons en signes entiers, secte, dignités essentielles, aspects ptoléméens par signe, Lots grecs, libération zodiacale),
3. génération du document `.docx` final selon la structure déjà validée sur les thèmes d'Anthony et de Liam.

Le dépôt sera versionné sur GitHub.

## Réglages astrologiques (non négociables, à appliquer systématiquement)

- Système de maisons : signes entiers (Whole Sign).
- Zodiaque tropical.
- Aspects ptoléméens uniquement (conjonction, sextile, carré, trigone, opposition), considérés par signe plutôt que par degré d'orbe — plus l'écart en degré est faible, plus l'aspect est actif.
- Aspects hors-signe ignorés, sauf si la planète la plus rapide applique à moins de 3° à la planète la plus lente. Cette proximité se mesure sur l'écart réel en longitude écliptique (les deux planètes doivent être proches de la frontière commune entre leurs signes adjacents), pas sur une coïncidence de degré-dans-signe : Mercure à 11°57' Sagittaire et Vénus à 11°51' Scorpion ont des degrés-dans-signe presque identiques mais restent à ~30° d'écart réel, car aucun des deux n'est proche de la frontière Scorpion/Sagittaire (cas vérifié sur le thème d'Anthony — la règle ne s'active pas).
- Solaire (retour solaire) : lieu de naissance, Soleil non précessé.
- Secte de la carte déterminée par la position du Soleil au-dessus ou au-dessous de l'horizon ; la Part de Fortune et la Part de l'Esprit changent de formule selon secte diurne/nocturne (piège fréquent à tester explicitement).
- Rôle de secte par planète : règle symétrique retenue pour le luminaire « en désaccord » avec la secte de la carte — toujours « Hors secte (jour) » ou « Hors secte (nuit) », jamais « Neutre » (un des deux thèmes de référence contenait une asymétrie sur ce point, corrigée après validation explicite).

## Méthode de rédaction en trois phases (à respecter dans tout générateur de texte ou de document)

1. **Observation** : relevé factuel des positions, secte, dignités essentielles, rétrogradations, planètes sous les rayons, aspects par signe — sans interprétation.
2. **Rédaction** : fiche technique descriptive (répartition élémentaire et modale, angularité, Ascendant et son maître, luminaires, dignités et réceptions, nœuds et Parts, structure du thème).
3. **Interprétation** : synthèse destinée au client (orientation générale, Ascendant et son maître, luminaires, structure du thème, nuances de secte/dignité, synthèse finale), avec section optionnelle sur les repères temporels actuels (libération zodiacale) si les dates le permettent.

## Style des textes générés

- Ton bienveillant mais factuel, jamais péremptoire sur la vie de la personne (formulations du type « invite à », « suggère », « mérite d'être vérifié avec la personne concernée »).
- Aucune émoticône.
- Toute affirmation technique (dignité, aspect, secte) doit être vérifiable depuis les données d'observation de la phase 1 — pas d'interprétation qui devance les faits.
- Bibliographie systématique en fin de document, avec URLs vérifiées à la date de génération (voir ci-dessous).

## Références bibliographiques de travail

- Chris Brennan, *Hellenistic Astrology: The Study of Fate and Fortune* — https://theastrologypodcast.com/books/
- Demetra George, *Ancient Astrology in Theory and Practice: A Manual of Traditional Techniques, Volume I: Assessing Planetary Condition* (Rubedo Press, 2019) — https://rubedo.press/ancient-astrology
- Demetra George, *Ancient Astrology in Theory and Practice: A Manual of Traditional Techniques, Volume II: Delineating Planetary Meaning* (Rubedo Press, 2022) — https://rubedo.press/ancient-astrology-volume-two
- Demetra George, *Astrology for Yourself* et *Astrology and the Authentic Self* — https://demetra-george.com/books/

Ces URLs pointent vers les pages officielles (éditeur ou auteur/autrice). Si le projet les republie (README, docs), revérifier leur validité avant chaque publication plutôt que de les recopier sans contrôle.

## Environnement de travail

- Développement exclusivement sur PC (pas de mobile, pas de dépendance à un environnement cloud propriétaire).
- Langage principal : Python (`uv` pour l'environnement/dépendances), layout `src/hellenistic_astrology/`.
- Éphéméride : **pyswisseph** (Swiss Ephemeris). Licence AGPL-3.0 acceptée pour l'instant ; si un service web/API public est un jour lancé, budgéter la licence commerciale Swiss Ephemeris Professional avant la mise en ligne. Fichiers de données `.se1` téléchargés via `scripts/fetch_ephemeris.py` vers `data/ephe/` (gitignored, jamais committés) ; en leur absence, le calcul bascule automatiquement sur la théorie Moshier/Moseph (précision ~1 arcseconde, suffisante pour les tests).
- Fuseau horaire : résolution automatique lieu + heure locale via `zoneinfo`, fiable à partir de 1916 (introduction de l'heure d'été en France) ; avant cette date, un datetime UTC explicite est obligatoire (voir `core/timezone.py`).
- Génération du `.docx` : décision actée d'utiliser **python-docx** (pas de sous-processus Node) — le script Node/docx-js évoqué initialement n'a jamais existé dans ce dépôt.
- CLI : `hellenistic-astrology <fichier-birth-data.json>` (entry point `src/hellenistic_astrology/cli.py`, déclaré dans `pyproject.toml`), voir `README.md`.
- Géocodage (`core/geocoding.py`) : opt-in uniquement — `latitude`/`longitude` explicites sont toujours prioritaires et n'entraînent aucun appel réseau ; le champ `place` (texte libre) n'est résolu via Nominatim/OpenStreetMap que s'ils sont absents. Invariant à préserver : ne jamais géocoder silencieusement quand des coordonnées directes existent déjà.
- Docker : prévu (en vue d'une exposition future en service) ; le CLI ci-dessus lève le seul blocage technique, mais l'ajout reste une décision à prendre explicitement (voir Reste à faire).

## État d'avancement

- **Jalon 1 (terminé)** : cœur de calcul (`src/hellenistic_astrology/core/`) — positions planétaires, maisons en signes entiers, secte, Part de Fortune/Esprit, résolution de fuseau horaire. Validé par `tests/test_regression_anthony.py` et `tests/test_regression_liam.py` (écarts sous 0,5' d'arc par rapport aux thèmes de référence).
- **Jalon 2 (terminé)** :
  - 2a — `core/dignities.py` (dignités essentielles domicile/exaltation/exil/chute/pérégrin, au niveau du signe ; table des maîtrises traditionnelles) et `core/sect.py` étendu avec le rôle de secte par planète.
  - 2b — `docgen/builder.py` génère la Phase 1 (Observation) en `.docx` via python-docx (tableaux positions + maîtrises), à partir de l'objet `Observation` uniquement. `scripts/generate_docx.py` permet une génération manuelle vers `output/` (gitignored). Phases 2 et 3 (rédaction, interprétation) restent hors périmètre de docgen : ce sont des tâches de génération de texte, pas de mise en forme de données.
  - Validé par `tests/test_dignities.py`, `tests/test_sect.py`, `tests/test_docgen.py` en plus des tests de régression.
- **Jalon 3 (terminé)** : `core/aspects.py` — regroupement des points en amas par signe, aspect ptoléméen par signe entre chaque paire d'amas, règle des 3° hors-signe basée sur la proximité écliptique réelle. Les 31 relations d'amas des deux thèmes (10 pour Anthony, 21 pour Liam) ont été vérifiées à la main contre le texte "Aspects par signe relevés" des documents de référence. Validé par `tests/test_aspects.py` et les tests de régression étendus.
  - **Limite connue** : aucun des deux thèmes de référence ne déclenche la règle des 3° (les deux documents confirment explicitement qu'elle ne s'active pas) — le cas positif n'est couvert que par un test synthétique, sans validation sur données réelles. À surveiller si un futur thème la déclenche.
- **Jalon 4 (terminé)** : `docgen/builder.py` génère la section "Aspects par signe relevés" en puces factuelles — une puce de conjonction par amas (accord grammatical masculin/féminin selon les membres), puis une puce par paire d'amas pour chaque relation d'aspect, aversions incluses. Format volontairement plus simple et déterministe que la prose des deux documents de référence, qui divergeaient stylistiquement entre eux sur ce point. Commentaire interprétatif (significations de maîtrise, etc.) toujours hors périmètre de docgen.
- **Jalon 5 (terminé)** : CLI réel (`src/hellenistic_astrology/cli.py`, entry point `hellenistic-astrology` déclaré dans `pyproject.toml`) — prend en entrée un fichier JSON de données de naissance (schéma libre, name/latitude/longitude + local_date/local_time/tz_name ou utc_datetime) et génère le `.docx` vers `output/<nom-slugifié>.docx` par défaut. `main.py` (scaffold `uv` mort, jamais branché) a été supprimé. Testé de bout en bout avec un client synthétique en plus des deux fixtures. Usage documenté dans `README.md`.
- **Jalon 6 (terminé)** : géocodage opt-in (`core/geocoding.py`) — un champ `place` (texte libre) en alternative à `latitude`/`longitude` dans le JSON du CLI, résolu via l'API Nominatim/OpenStreetMap (dépendance réseau, envoie le lieu à ce service tiers). `latitude`/`longitude` restent toujours prioritaires si fournis : aucun appel réseau dans ce cas, comportement par défaut inchangé. Testé avec des appels réseau mockés (`tests/test_geocoding.py`) et vérifié une fois en conditions réelles.
- **Jalon 7 (terminé)** : désambiguïsation du géocodage — `geocode()` demande 5 résultats à Nominatim et refuse (avec la liste des candidats) si plusieurs **lieux réellement distincts** sont trouvés, plutôt que de deviner en prenant le premier. "Distincts" est déterminé par une distance approximative (< 5 km = même lieu) plutôt qu'un simple comptage brut : test manuel en conditions réelles, "Paris, France" et "Paris 14e, France" renvoient chacun plusieurs entrées OSM quasi-identiques (ville + département, ou plusieurs commerces du même quartier) qui auraient déclenché une fausse ambiguïté sans ce filtre. "Paris" seul (sans pays) reste correctement détecté comme ambigu (France vs Texas). Nouveau champ optionnel `country_code` (ISO 3166-1 alpha-2) transmis à Nominatim pour lever l'ambiguïté en amont. Validé par `tests/test_geocoding.py` (dont un test dédié à la non-régression sur les faux positifs de proximité) et un test manuel en conditions réelles.
- Voir la section **Reste à faire** ci-dessous pour la suite.

## Reste à faire

Roadmap explicite, dans l'ordre de priorité recommandé. Chaque jalon reste à valider avec l'utilisateur avant d'être attaqué (voir garde-fous ci-dessous) ; l'ordre ci-dessous est une recommandation, pas un engagement figé.

1. **Nœud Nord/Sud et Part d'Éros** — présents dans les deux documents de référence (tableau des positions et puces d'aspects) mais jamais calculés ; leur absence est actuellement une omission assumée, pas un choix définitif. Complète le tableau des positions et enrichit les amas/aspects.
2. **Réceptions mutuelles** — concept observé dans le texte de référence d'Anthony ("réception mutuelle par domicile entre Mars et Vénus") mais jamais implémenté ni discuté comme un item à part entière ; fait partie du relevé factuel de dignités de la Phase 1.
3. **Vérification automatique des URLs bibliographiques** (`scripts/check_bibliography.py`) — décidée lors de la phase de planification initiale (requête HTTP HEAD sur les 4 URLs avant génération) mais jamais implémentée.
4. **Dignités essentielles plus fines** (bornes égyptiennes, triplicités par secte, décans) — marqué "si besoin" dès l'origine, le moins prioritaire des calculs restants.
5. **Libération zodiacale** — technique de repères temporels citée dans l'objectif initial et dans la section optionnelle de la Phase 3.
6. **Phase 2 — Fiche technique** (répartition élémentaire/modale, angularité, Ascendant et son maître, luminaires, dignités et réceptions, nœuds et Parts, structure du thème) — mélange tableau (élémentaire/modale, déjà vu dans les références) et texte descriptif. Premier vrai changement de nature par rapport aux jalons précédents : ce n'est plus seulement de la mise en forme mécanique de données calculées.
7. **Phase 3 — Interprétation** (synthèse, nuances de secte/dignité, section optionnelle libération zodiacale) — rédaction pure destinée au client. À ce stade, `docgen` au sens actuel (mise en forme déterministe d'un objet `Observation`) atteint sa limite : c'est une tâche de génération de texte assistée, probablement un prompt structuré plutôt que du code Python déterministe — à repenser en phase de planification dédiée plutôt que de trancher seul.
8. **`docgen/CLAUDE.md` scopé** — évoqué à deux reprises sans être tranché ; le bon moment est l'attaque de l'item 6 ou 7, puisque c'est le changement de nature de tâche (texte vs données) qui justifierait un fichier séparé.
9. **Skill Claude** (`skills/hellenistic-astrology/SKILL.md`) — wrapper fin autour du CLI (jalon 5, terminé), idéalement après que les Phases 2/3 existent au moins partiellement.
10. **Docker** — prévu ; sa condition initiale (un point d'entrée réel) est désormais remplie par le CLI du jalon 5, donc plus aucun blocage technique, mais toujours pas engagé sans décision explicite.
11. **MCP** — uniquement si un besoin réel émerge d'un usage via Claude Desktop ou similaire ; non engagé.

## Cas de test de référence (vérité terrain)

Deux thèmes ont déjà été analysés manuellement et validés : ils servent de fixtures de non-régression pour tout calcul automatisé.

- **Anthony** — 20 novembre 1970, 23h10 (CET), Paris 14e, France (48°49'59" N, 2°19'36" E). Thème nocturne. Part de Fortune attendue : Scorpion 20°08'. Ascendant Lion, MC Taureau.
- **Liam** — 19 octobre 2005, 15h50 (CEST), Vitry-sur-Seine, France (48°47' N, 2°24' E). Thème diurne. Part de Fortune attendue : Lion 27°60' (= 28°00', notation normalisée puisque 60' = 1°, confirmé par l'utilisateur). Ascendant Verseau, MC Sagittaire.

Tout module de calcul (positions, maisons, secte, dignités, Lots, aspects) doit être testé contre ces deux thèmes avant d'être considéré fiable.

**Ces données de naissance ne sont jamais poussées sur GitHub** : `/References` (les `.docx` sources), `/tests/fixtures` (les valeurs transcrites en JSON) et `/output` (les `.docx` générés par `scripts/generate_docx.py` ou le CLI) sont dans `.gitignore`. Le code des tests (`tests/test_regression_*.py`, `tests/test_timezone.py`, `tests/test_dignities.py`, `tests/test_sect.py`, `tests/test_docgen.py`, `tests/test_aspects.py`, `tests/test_cli.py`, `tests/test_geocoding.py`) reste versionné ; seules les données personnelles qu'il consomme ou produit restent locales. Les tests de géocodage mockent l'appel réseau (`unittest.mock`) : aucun lieu réel n'est envoyé à Nominatim pendant `pytest`.

## Ce que Claude Code ne doit pas faire sans validation explicite

- Ne pas modifier les réglages astrologiques listés ci-dessus (ce sont des choix méthodologiques assumés par l'utilisateur, pas des paramètres à optimiser).
- Ne pas remplacer les livres de référence ni en ajouter d'autres sans demande explicite.
- Ne pas publier ou committer de données personnelles de tiers (dates de naissance, lieux) au-delà des deux cas de test ci-dessus, qui ont déjà été partagés volontairement par l'utilisateur — et même pour ces deux cas, ne jamais retirer `/References`, `/tests/fixtures` ou `/output` du `.gitignore` sans demande explicite.
- Ne pas choisir seul l'ordre ou le périmètre des items listés dans "Reste à faire" sans validation explicite — la priorisation proposée est une recommandation, pas un mandat. En particulier, ne pas décider seul de l'approche pour les Phases 2/3 (items 6/7) : ce sont des choix qui méritent leur propre discussion de planification.
