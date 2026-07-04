"""Calcul astrologique pur : positions planétaires (Swiss Ephemeris via
`pyswisseph`), maisons en signes entiers, secte, dignités essentielles et
mineures, aspects ptoléméens par signe, Lots grecs, Nœuds, éclipses, phase
de lunaison et libération zodiacale.

`chart.build_observation` est le point d'entrée qui orchestre tous ces
calculs et renvoie un objet `Observation` (défini dans `observation.py`) —
la seule donnée que consomment `docgen` et `interpretation`. Aucun module
de ce paquet ne connaît la notion de document ou de mise en forme.
"""
