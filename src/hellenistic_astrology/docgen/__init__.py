"""Rendu déterministe d'un objet `Observation` (calculé par `core`) en
document `.docx`, via `python-docx` — Phase 1 (Observation) et Phase 2
(Fiche technique) uniquement. `builder.build_observation_document` est le
point d'entrée ; `styles.py` centralise la mise en forme des tableaux.

Ne fait aucun calcul astrologique : toute donnée affichée provient déjà de
l'`Observation` fournie. La Phase 3 (Interprétation) est hors périmètre —
voir `interpretation/` pour la rédaction assistée qui la remplace.
"""
