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
- Docker : prévu (en vue d'une exposition future en service), à ajouter à partir du jalon où un point d'entrée exécutable existe réellement — pas dans le module de calcul seul.

## État d'avancement

- **Jalon 1 (terminé)** : cœur de calcul (`src/hellenistic_astrology/core/`) — positions planétaires, maisons en signes entiers, secte, Part de Fortune/Esprit, résolution de fuseau horaire. Validé par `tests/test_regression_anthony.py` et `tests/test_regression_liam.py` (écarts sous 0,5' d'arc par rapport aux thèmes de référence).
- **Jalon 2 (terminé)** :
  - 2a — `core/dignities.py` (dignités essentielles domicile/exaltation/exil/chute/pérégrin, au niveau du signe ; table des maîtrises traditionnelles) et `core/sect.py` étendu avec le rôle de secte par planète.
  - 2b — `docgen/builder.py` génère la Phase 1 (Observation) en `.docx` via python-docx (tableaux positions + maîtrises), à partir de l'objet `Observation` uniquement. `scripts/generate_docx.py` permet une génération manuelle vers `output/` (gitignored). Phases 2 et 3 (rédaction, interprétation) restent hors périmètre de docgen : ce sont des tâches de génération de texte, pas de mise en forme de données.
  - Validé par `tests/test_dignities.py`, `tests/test_sect.py`, `tests/test_docgen.py` en plus des tests de régression.
- **Jalon 3 (terminé)** : `core/aspects.py` — regroupement des points en amas par signe, aspect ptoléméen par signe entre chaque paire d'amas, règle des 3° hors-signe basée sur la proximité écliptique réelle. Les 31 relations d'amas des deux thèmes (10 pour Anthony, 21 pour Liam) ont été vérifiées à la main contre le texte "Aspects par signe relevés" des documents de référence. Validé par `tests/test_aspects.py` et les tests de régression étendus.
  - **Limite connue** : aucun des deux thèmes de référence ne déclenche la règle des 3° (les deux documents confirment explicitement qu'elle ne s'active pas) — le cas positif n'est couvert que par un test synthétique, sans validation sur données réelles. À surveiller si un futur thème la déclenche.
  - Rendu textuel des aspects (puces façon "X et Y conjoints en...", commentaires interprétatifs) volontairement hors périmètre : c'est une tâche de rédaction, pas de calcul ni de mise en forme mécanique — docgen n'a pas été touché par ce jalon.
- **Jalons suivants** : dignités essentielles plus fines (bornes/triplicité si besoin), libération zodiacale, rendu textuel des aspects, puis Skill Claude (`skills/hellenistic-astrology/SKILL.md`), MCP uniquement si un besoin réel émerge.

## Cas de test de référence (vérité terrain)

Deux thèmes ont déjà été analysés manuellement et validés : ils servent de fixtures de non-régression pour tout calcul automatisé.

- **Anthony** — 20 novembre 1970, 23h10 (CET), Paris 14e, France (48°49'59" N, 2°19'36" E). Thème nocturne. Part de Fortune attendue : Scorpion 20°08'. Ascendant Lion, MC Taureau.
- **Liam** — 19 octobre 2005, 15h50 (CEST), Vitry-sur-Seine, France (48°47' N, 2°24' E). Thème diurne. Part de Fortune attendue : Lion 27°60' (= 28°00', notation normalisée puisque 60' = 1°, confirmé par l'utilisateur). Ascendant Verseau, MC Sagittaire.

Tout module de calcul (positions, maisons, secte, dignités, Lots, aspects) doit être testé contre ces deux thèmes avant d'être considéré fiable.

**Ces données de naissance ne sont jamais poussées sur GitHub** : `/References` (les `.docx` sources), `/tests/fixtures` (les valeurs transcrites en JSON) et `/output` (les `.docx` générés par `scripts/generate_docx.py`) sont dans `.gitignore`. Le code des tests (`tests/test_regression_*.py`, `tests/test_timezone.py`, `tests/test_dignities.py`, `tests/test_sect.py`, `tests/test_docgen.py`, `tests/test_aspects.py`) reste versionné ; seules les données personnelles qu'il consomme ou produit restent locales.

## Ce que Claude Code ne doit pas faire sans validation explicite

- Ne pas modifier les réglages astrologiques listés ci-dessus (ce sont des choix méthodologiques assumés par l'utilisateur, pas des paramètres à optimiser).
- Ne pas remplacer les livres de référence ni en ajouter d'autres sans demande explicite.
- Ne pas publier ou committer de données personnelles de tiers (dates de naissance, lieux) au-delà des deux cas de test ci-dessus, qui ont déjà été partagés volontairement par l'utilisateur — et même pour ces deux cas, ne jamais retirer `/References`, `/tests/fixtures` ou `/output` du `.gitignore` sans demande explicite.
- Ne pas choisir seul les jalons suivants (rendu textuel des aspects, libération zodiacale, Skill, MCP) sans validation explicite, même si la trajectoire générale est déjà actée ci-dessus.
