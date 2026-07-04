# Table des termes égyptiens (Egyptian Terms / Bounds)

Source : table traditionnelle transmise par Vettius Valens (Anthologiae, Livre I) et reprise
par la plupart des auteurs hellénistiques et par Chris Brennan (*Hellenistic Astrology*,
annexe des tables de dignités). Chaque signe est divisé en cinq segments inégaux, chacun
attribué à l'une des cinq planètes non-luminaires (le Soleil et la Lune n'ont pas de termes).

Les degrés indiqués sont les bornes de fin de segment (borne de début = fin du segment
précédent, ou 0° pour le premier). Un total de 30° par signe.

## Table de référence

| Signe        | Segment 1        | Segment 2        | Segment 3        | Segment 4        | Segment 5        |
|--------------|------------------|------------------|------------------|------------------|------------------|
| Bélier       | Jupiter 0–6°     | Vénus 6–12°      | Mercure 12–20°   | Mars 20–25°      | Saturne 25–30°   |
| Taureau      | Vénus 0–8°       | Mercure 8–14°    | Jupiter 14–22°   | Saturne 22–27°   | Mars 27–30°      |
| Gémeaux      | Mercure 0–6°     | Jupiter 6–12°    | Vénus 12–17°     | Mars 17–24°      | Saturne 24–30°   |
| Cancer       | Mars 0–7°        | Vénus 7–13°      | Mercure 13–19°   | Jupiter 19–26°   | Saturne 26–30°   |
| Lion         | Jupiter 0–6°     | Vénus 6–11°      | Saturne 11–18°   | Mercure 18–24°   | Mars 24–30°      |
| Vierge       | Mercure 0–7°     | Vénus 7–13°      | Jupiter 13–18°   | Saturne 18–24°   | Mars 24–30°      |
| Balance      | Saturne 0–6°     | Mercure 6–14°    | Jupiter 14–21°   | Vénus 21–28°     | Mars 28–30°      |
| Scorpion     | Mars 0–7°        | Vénus 7–11°      | Mercure 11–19°   | Jupiter 19–24°   | Saturne 24–30°   |
| Sagittaire   | Jupiter 0–12°    | Vénus 12–17°     | Mercure 17–21°   | Saturne 21–26°   | Mars 26–30°      |
| Capricorne   | Mercure 0–7°     | Jupiter 7–14°    | Vénus 14–22°     | Saturne 22–26°   | Mars 26–30°      |
| Verseau      | Mercure 0–7°     | Vénus 7–13°      | Jupiter 13–20°   | Mars 20–25°      | Saturne 25–30°   |
| Poissons     | Vénus 0–12°      | Jupiter 12–16°   | Mercure 16–19°   | Mars 19–28°      | Saturne 28–30°   |

Vérification : chaque ligne totalise bien 30°.

## Structure de données Python (prête à l'emploi)

```python
# egyptian_terms.py
# Table des termes égyptiens : bornes supérieures (exclusives) de chaque segment, par signe.
# Signes indexés 0 (Bélier) à 11 (Poissons), cohérent avec une numérotation zodiacale standard.

EGYPTIAN_TERMS = {
    "Belier":      [(6, "Jupiter"), (12, "Venus"),   (20, "Mercure"), (25, "Mars"),    (30, "Saturne")],
    "Taureau":     [(8, "Venus"),   (14, "Mercure"),  (22, "Jupiter"), (27, "Saturne"), (30, "Mars")],
    "Gemeaux":     [(6, "Mercure"), (12, "Jupiter"),  (17, "Venus"),   (24, "Mars"),    (30, "Saturne")],
    "Cancer":      [(7, "Mars"),    (13, "Venus"),    (19, "Mercure"), (26, "Jupiter"), (30, "Saturne")],
    "Lion":        [(6, "Jupiter"), (11, "Venus"),    (18, "Saturne"), (24, "Mercure"), (30, "Mars")],
    "Vierge":      [(7, "Mercure"), (13, "Venus"),    (18, "Jupiter"), (24, "Saturne"), (30, "Mars")],
    "Balance":     [(6, "Saturne"), (14, "Mercure"),  (21, "Jupiter"), (28, "Venus"),   (30, "Mars")],
    "Scorpion":    [(7, "Mars"),    (11, "Venus"),    (19, "Mercure"), (24, "Jupiter"), (30, "Saturne")],
    "Sagittaire":  [(12, "Jupiter"),(17, "Venus"),    (21, "Mercure"), (26, "Saturne"), (30, "Mars")],
    "Capricorne":  [(7, "Mercure"), (14, "Jupiter"),  (22, "Venus"),   (26, "Saturne"), (30, "Mars")],
    "Verseau":     [(7, "Mercure"), (13, "Venus"),    (20, "Jupiter"), (25, "Mars"),    (30, "Saturne")],
    "Poissons":    [(12, "Venus"),  (16, "Jupiter"),  (19, "Mercure"), (28, "Mars"),    (30, "Saturne")],
}


def terme_egyptien(signe: str, degre: float) -> str:
    """Retourne le maître du terme égyptien pour un degré donné (0 <= degre < 30) dans un signe."""
    if not (0 <= degre < 30):
        raise ValueError("Le degré doit être compris entre 0 (inclus) et 30 (exclu).")
    for borne_sup, maitre in EGYPTIAN_TERMS[signe]:
        if degre < borne_sup:
            return maitre
    raise ValueError(f"Aucun terme trouvé pour {signe} {degre}° — vérifier la table.")
```

## Vérifications effectuées avant transcription

- Bélier (Jupiter 0–6°, Vénus 6–12°) et Verseau (Mercure 0–7°, Vénus 7–13°, Jupiter 13–20°,
  Mars 20–25°, Saturne 25–30°) confirmés par recoupement avec les délinéations de Vettius Valens.
- Balance confirmée degré par degré (Saturne 6°, Mercure 8°, Jupiter 7°, Vénus 7°, Mars 2°) :
  le segment de Mars en fin de Balance (28–30°) est le plus court de toute la table avec celui
  de Mercure en fin de Poissons (16–19°, 3°).
- Chaque ligne recalculée pour confirmer un total de 30°.

## Sources consultées pour la vérification

- Chris Brennan, *Hellenistic Astrology: The Study of Fate and Fortune* — page officielle de l'auteur : https://theastrologypodcast.com/books/
- Vettius Valens (délinéations citées), via Kira Ryberg, "The Power of the Bounds (Egyptian Terms)" : https://www.kiraryberg.com/blog/the-bounds
- Two Wander x Elysium Rituals, "What are the Bounds in Astrology?" (confirmation des degrés de la Balance) : https://www.twowander.com/blog/astrological-bounds
- Augurine, "Egyptian Bounds Calculator" (méthodologie et sources croisées : Valens, Dorothée, Héphaistion) : https://www.augurine.com/tools/egyptian-bounds-calculator
