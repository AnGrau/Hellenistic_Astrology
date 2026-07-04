---
name: hellenistic-astrology
description: Produit l'analyse complète d'un thème natal en astrologie hellénistique (signes entiers), de bout en bout — calcul, document Phase 1/2, brief de Phase 3, rédaction assistée avec relecture humaine, document final assemblé. Utiliser quand l'utilisateur demande de générer/produire un thème, une analyse ou un document complet à partir de données de naissance, pas seulement de rédiger une section isolée.
---

# Génération de bout en bout d'un thème hellénistique

Ce skill orchestre les quatre étapes du pipeline du projet
`hellenistic-astrology` à partir de données de naissance, en s'adaptant à
ce que l'environnement courant peut réellement exécuter, et **sans jamais
sauter la relecture humaine de la Phase 3** — c'est la seule étape que ce
skill ne doit jamais automatiser.

## Étape 0 : déterminer ce qui est exécutable ici

Avant de commencer, vérifier si l'environnement dispose d'un accès aux
outils MCP du projet (`compute_observation`, `generate_document`,
`generate_interpretation_brief`, `assemble_final_document` — serveur local
défini dans `.mcp.json`, disponible dans Claude Code, Claude Desktop
configuré, ou Mistral Vibe travaillant sur ce dépôt cloné).

- **Outils disponibles** : les appeler directement aux étapes 1, 2 et 4
  ci-dessous.
- **Outils indisponibles** (Claude Chat ou Mistral Le Chat sans logiciel
  local, ou tout environnement sans le serveur MCP connecté) : à chaque
  étape concernée, indiquer clairement à l'utilisateur la commande exacte à
  lancer lui-même (voir chaque étape) et lui demander de coller le
  résultat dans la conversation avant de continuer. Ne jamais deviner ou
  recalculer ce que ces commandes produiraient.

## Étape 1 : calculer le thème et générer le document Phase 1/2

- **Avec outils** : appeler `generate_document(birth_data)` (schéma
  `birth_data` : `name`, `latitude`/`longitude` ou `place`,
  `local_date`/`local_time`/`tz_name` ou `utc_datetime` — voir
  `README.md`). Renvoie le chemin du `.docx` écrit.
- **Sans outils** : demander à l'utilisateur de lancer
  `uv run hellenistic-astrology <fichier-naissance.json>` et de confirmer
  le chemin du `.docx` obtenu.

## Étape 2 : générer le brief de Phase 3

- **Avec outils** : appeler `generate_interpretation_brief(birth_data)`.
  Renvoie directement le texte du brief (pas besoin de le relire depuis un
  fichier).
- **Sans outils** : demander à l'utilisateur de lancer
  `uv run python scripts/generate_brief.py <nom>` (thèmes de test) ou la
  commande Python équivalente documentée dans `docs/HOWTO.md` pour un
  thème réel, puis de coller le contenu du brief obtenu.

## Étape 3 : rédiger la Phase 3, puis marquer une pause pour relecture

Rédiger la prose de Phase 3 à partir du brief obtenu, en suivant
**exactement** les règles du skill `hellenistic-astrology-phase3` (même
répertoire `.claude/skills/` — traçabilité stricte aux faits du brief, ton,
structure des 8 sous-sections). Ne pas dupliquer ces règles ici : les
relire dans ce skill si besoin d'un rappel.

**Arrêt obligatoire ici.** Présenter le brouillon rédigé et demander
explicitement à l'utilisateur de le relire, corriger ou approuver avant de
poursuivre vers l'étape 4. Ne jamais enchaîner automatiquement sur
l'assemblage sans cette confirmation, même si l'utilisateur n'a rien
demandé d'autre entre-temps — c'est la seule étape que ce skill ne doit
jamais sauter ni accélérer.

## Étape 4 : assembler le document final

Une fois, et seulement une fois, la Phase 3 approuvée par l'utilisateur :

- **Avec outils** : appeler `assemble_final_document(docx_path,
  markdown_path)` avec le `.docx` de l'étape 1 et le texte finalisé de
  l'étape 3 (l'écrire dans un fichier temporaire si nécessaire, ou
  transmettre le texte tel quel selon ce que l'outil accepte). Renvoie le
  chemin du document final (`<docx>_final.docx` par défaut).
- **Sans outils** : demander à l'utilisateur de sauvegarder le texte
  finalisé dans un fichier puis de lancer
  `uv run python scripts/assemble_document.py <docx> <markdown> [-o sortie]`.

## Ce que ce skill ne fait pas

- Il ne recalcule rien lui-même : toute donnée vient des outils MCP ou des
  commandes CLI du projet, jamais d'une estimation du modèle.
- Il ne remplace jamais la relecture humaine de la Phase 3 (étape 3) — ni
  en la sautant, ni en la résumant à une simple confirmation implicite.
- Il ne décide pas à la place de l'utilisateur quelle sortie (`.docx`
  seul, brief seul, document final) est souhaitée si la demande initiale
  est ambiguë : demander si besoin avant de lancer la première étape.
