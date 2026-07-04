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
- Aspects hors-signe ignorés, sauf si la planète la plus rapide applique à moins de 3° à la planète la plus lente.
- Solaire (retour solaire) : lieu de naissance, Soleil non précessé.
- Secte de la carte déterminée par la position du Soleil au-dessus ou au-dessous de l'horizon ; la Part de Fortune et la Part de l'Esprit changent de formule selon secte diurne/nocturne (piège fréquent à tester explicitement).

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
- **Jalon 2 (à venir)** : génération du `.docx` en python-docx à partir de l'objet `Observation`.
- **Jalons suivants** : aspects par signe, dignités essentielles complètes, libération zodiacale, puis Skill Claude (`skills/hellenistic-astrology/SKILL.md`), MCP uniquement si un besoin réel émerge.

## Cas de test de référence (vérité terrain)

Deux thèmes ont déjà été analysés manuellement et validés : ils servent de fixtures de non-régression pour tout calcul automatisé.

- **Anthony** — 20 novembre 1970, 23h10 (CET), Paris 14e, France (48°49'59" N, 2°19'36" E). Thème nocturne. Part de Fortune attendue : Scorpion 20°08'. Ascendant Lion, MC Taureau.
- **Liam** — 19 octobre 2005, 15h50 (CEST), Vitry-sur-Seine, France (48°47' N, 2°24' E). Thème diurne. Part de Fortune attendue : Lion 27°60' (= 28°00', notation normalisée puisque 60' = 1°, confirmé par l'utilisateur). Ascendant Verseau, MC Sagittaire.

Tout module de calcul (positions, maisons, secte, dignités, Lots) doit être testé contre ces deux thèmes avant d'être considéré fiable.

**Ces données de naissance ne sont jamais poussées sur GitHub** : `/References` (les `.docx` sources) et `/tests/fixtures` (les valeurs transcrites en JSON) sont dans `.gitignore`. Le code des tests (`tests/test_regression_*.py`, `tests/test_timezone.py`) reste versionné ; seules les données personnelles qu'il consomme restent locales.

## Ce que Claude Code ne doit pas faire sans validation explicite

- Ne pas modifier les réglages astrologiques listés ci-dessus (ce sont des choix méthodologiques assumés par l'utilisateur, pas des paramètres à optimiser).
- Ne pas remplacer les livres de référence ni en ajouter d'autres sans demande explicite.
- Ne pas publier ou committer de données personnelles de tiers (dates de naissance, lieux) au-delà des deux cas de test ci-dessus, qui ont déjà été partagés volontairement par l'utilisateur — et même pour ces deux cas, ne jamais retirer `/References` et `/tests/fixtures` du `.gitignore` sans demande explicite.
- Ne pas choisir seul les jalons suivants (docgen, Skill, MCP) sans validation explicite, même si la trajectoire générale est déjà actée ci-dessus.
