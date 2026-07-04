"""Calcul et mise en forme de thèmes natals en astrologie hellénistique
(signes entiers).

Trois sous-paquets, chacun responsable d'une nature de tâche distincte :

- `core` : calcul astrologique pur (positions, maisons, secte, dignités,
  aspects, Lots, libération zodiacale) — aucune notion de mise en forme.
- `docgen` : rendu déterministe de l'objet `Observation` (calculé par
  `core`) en document `.docx` (Phase 1 — Observation, Phase 2 — Fiche
  technique).
- `interpretation` : assemblage d'un brief factuel pour la rédaction
  assistée de la Phase 3 — Interprétation (pas de rendu déterministe,
  la rédaction elle-même reste une étape supervisée).

`cli.py` et `mcp_server.py` sont les deux points d'entrée qui orchestrent
ces sous-paquets (respectivement en ligne de commande et via le protocole
MCP). Voir `CLAUDE.md` à la racine du dépôt pour le contexte complet du
projet, les réglages astrologiques non négociables, et la roadmap.
"""
