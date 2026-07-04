---
name: hellenistic-astrology-phase3
description: Rédige la Phase 3 — Interprétation d'un thème natal en astrologie hellénistique (signes entiers) à partir d'un brief factuel déjà généré (interpretation/brief.py, jalon 26) ou des données déjà calculées d'une Observation. Utiliser quand l'utilisateur colle ou joint un tel brief, demande de rédiger/interpréter un thème hellénistique, ou mentionne "brief de rédaction", "Phase 3" ou "Interprétation" dans ce contexte.
---

# Rédaction de Phase 3 — Interprétation (astrologie hellénistique)

Ce skill rédige la prose de la Phase 3 (Interprétation) d'un thème natal en
astrologie hellénistique (signes entiers), à partir d'un **brief factuel
déjà produit** — jamais à partir de calculs inventés ou de connaissances
astrologiques générales appliquées librement.

## Entrée attendue

Un brief au format produit par `interpretation/brief.py` (voir le projet
`hellenistic-astrology` — fonction `build_interpretation_brief`), collé
dans la conversation ou joint en pièce. Ce brief contient déjà :
- un rappel des règles de style à respecter (reprises ci-dessous) ;
- les faits de chaque sous-section, réutilisés tels quels depuis la Phase 1
  (Observation) et la Phase 2 (Fiche technique) déjà calculées et testées ;
- la bibliographie à inclure en fin de document.

**Si aucun brief n'est fourni** mais que l'environnement dispose d'un accès
fichiers/Bash au dépôt du projet (ex. Claude Code, Mistral Vibe en local) :
proposer de le générer d'abord via `uv run python scripts/generate_brief.py
<nom-fixture>` (ou l'équivalent pour un thème réel, en créant un JSON de
données de naissance — voir `README.md` du projet), puis reprendre la
rédaction à partir du brief obtenu. Ne jamais rédiger sans brief sous la
main : ce n'est pas le chemin principal de ce skill.

## Règle non négociable : traçabilité aux faits

**Chaque affirmation technique (signe, maison, dignité, aspect, secte,
réception, date de libération zodiacale...) doit être vérifiable depuis le
brief fourni.** N'invente aucun fait, ne recalcule rien de mémoire, et ne
mobilise pas de connaissances astrologiques générales pour compléter ce que
le brief ne dit pas. Si une information semble manquante pour une
conclusion qui paraîtrait naturelle, formule la conclusion en restant
alignée sur les seuls faits donnés, ou omets-la plutôt que de deviner.

## Ton et style

- Bienveillant mais factuel, jamais péremptoire sur la vie de la personne :
  utiliser des formulations du type « invite à », « suggère », « pourrait »,
  « mérite d'être vérifié avec la personne concernée ».
- Aucune émoticône.
- Ne pas qualifier subjectivement les difficultés techniques (pas de « juste
  hors de... », pas de jugement de valeur implicite) — rester descriptif
  même en interprétant.
- Terminer par la bibliographie fournie dans le brief, reproduite telle
  quelle (URLs incluses).

## Structure attendue (8 sous-sections réelles + bibliographie)

Dans cet ordre, avec ces titres :

1. **(intro, sans titre)** — un court paragraphe indiquant que cette section
   relie les observations entre elles pour une lecture d'ensemble, et
   qu'elle gagnera à être vérifiée et affinée avec la personne concernée.
2. **Orientation générale** — éléments des points directeurs (Ascendant/
   Soleil/Lune), répartition modale, angularité d'ensemble : une vue
   d'ensemble du "climat" du thème.
3. **L'Ascendant et son maître** — signe/maison de l'Ascendant, condition du
   maître traditionnel (dignité, maison, aspect avec le signe qu'il
   gouverne, conjonctions), ce que cela suggère pour l'affirmation de soi.
4. **Les luminaires** — Soleil et Lune : dignité, secte, combustion,
   conjonctions/aspects, phase de lunaison natale.
5. **La structure du thème** — les amas de signe et leurs aspects entre eux
   (figure géométrique si le thème s'y prête, ou lecture par pôles séparés
   sinon), réceptions mutuelles.
6. **Nuances de secte, de dignité (et de mouvement)** — rôles de secte par
   planète, dignités essentielles, rétrogradations, combustion : ce qui
   tempère ou renforce chaque facteur.
7. **Synthèse** — aucun fait nouveau : relier les points saillants des
   sous-sections précédentes en une conclusion brève et cohérente.
8. **Repères temporels actuels** — périodes de libération zodiacale
   actuellement actives (Fortune et Esprit), reprises telles que données
   dans le brief, avec la formule d'usage sur le caractère indicatif de ces
   techniques.
9. **Limites de cette analyse** — réglages appliqués, précision de l'heure
   de naissance, rappel que le document est une base de travail à discuter
   avec la personne concernée.

Utiliser des titres de niveau 2 (`##`) pour chaque sous-section nommée,
sous un titre de niveau 1 `# Phase 3 — Interprétation`.

## Ce que ce skill ne fait pas

- Il ne calcule rien lui-même (positions, aspects, dignités, libération
  zodiacale) : tout calcul vient du brief ou du pipeline Python du projet
  (`hellenistic_astrology.core`), jamais d'une estimation du modèle.
- Il ne remplace pas une relecture humaine : le texte produit reste un
  brouillon à vérifier, pas un livrable final.
