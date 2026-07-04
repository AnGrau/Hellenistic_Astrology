from dataclasses import dataclass
from datetime import datetime, timedelta

from .dignities import DOMICILES, opposite_sign
from .houses import SIGNS, index_of_sign

# Années fixes de la libération zodiacale (Vettius Valens, Anthologiae),
# vérifiées par recoupement de 3 sources indépendantes et cohérentes entre
# elles : transcription du podcast de Chris Brennan (épisode 192, citant
# directement Valens), calculateur Augurine, synthèse kerykeion. Capricorne
# (27 ans) diffère volontairement d'Aquarius (30 ans) bien que les deux
# soient domicile de Saturne — particularité documentée de la technique,
# pas une erreur de recopie (aucune fixture Anthony/Liam ne couvre ce calcul,
# voir CLAUDE.md).
ZODIACAL_RELEASING_YEARS: dict[str, int] = {
    "Bélier": 15,
    "Taureau": 8,
    "Gémeaux": 20,
    "Cancer": 25,
    "Lion": 19,
    "Vierge": 20,
    "Balance": 8,
    "Scorpion": 15,
    "Sagittaire": 12,
    "Capricorne": 27,
    "Verseau": 30,
    "Poissons": 12,
}

SIGN_RULERS: dict[str, str] = {sign: planet for planet, signs in DOMICILES.items() for sign in signs}

# La technique utilise une année "égyptienne" de 360 jours (12 mois de 30
# jours) et non l'année solaire de 365,25 jours — confirmé explicitement par
# Chris Brennan (même transcription que ci-dessus) : les dates réelles
# calculées "dérivent" donc légèrement par rapport au calendrier solaire au
# fil des décennies, c'est un effet attendu de la technique, pas un bug.
# Chaque niveau divise l'unité du niveau parent par 12 (année → mois → "jour"
# de 2,5 jours → "heure" de 5 heures), d'où la structure auto-similaire.
DAYS_PER_YEAR = 360.0
DAYS_PER_LEVEL: tuple[float, ...] = (
    DAYS_PER_YEAR,
    DAYS_PER_YEAR / 12,
    DAYS_PER_YEAR / 144,
    DAYS_PER_YEAR / 1728,
)

MAX_LEVEL = 4


@dataclass(frozen=True)
class ReleasingPeriod:
    level: int  # 1 (périodes générales) à 4
    sign: str
    ruler: str
    start: datetime
    end: datetime
    # True si cette période est celle qui a immédiatement suivi un
    # relâchement du lien (voir `level_periods`) : le signe attendu par la
    # simple continuation du cycle a été remplacé par le signe opposé au
    # signe de départ. False dans tous les autres cas, y compris pour les
    # occurrences ultérieures normales de ce même signe opposé.
    bond_loosed: bool = False


def _next_sign(sign: str) -> str:
    return SIGNS[(index_of_sign(sign) + 1) % 12]


def angular_signs_from(sign: str) -> set[str]:
    """Les 4 signes angulaires (1er/4e/7e/10e) comptés depuis `sign` — toujours
    le même groupe de modalité (cardinal/fixe/mutable) que `sign`."""
    i = index_of_sign(sign)
    return {SIGNS[(i + offset) % 12] for offset in (0, 3, 6, 9)}


def is_peak_period(period: ReleasingPeriod, fortune_sign: str) -> bool:
    """Période culminante ("peak period") : son signe est angulaire (1er,
    4e, 7e ou 10e) par rapport au signe de la Part de Fortune — toujours la
    Fortune, y compris quand la séquence de périodes suit la Part de
    l'Esprit. Confirmé par une source primaire (Chris Brennan, transcription
    du podcast épisode 192) : « you also wanna identify the other three
    signs that are angular to that sign [the Lot of Fortune] » et « when you
    start from the Lot of Spirit and you count around the zodiac until it
    comes to one of these four signs that are angular from the Lot of
    Fortune... it will coincide with what we call a peak period ». S'applique
    à tous les niveaux (L1 à L4) : la même règle, juste appliquée au signe de
    chaque période individuellement — Brennan confirme L1 explicitement, le
    calculateur Augurine confirme aussi L2.
    """
    return period.sign in angular_signs_from(fortune_sign)


def level_periods(level: int, start_sign: str, start: datetime, duration: timedelta) -> list[ReleasingPeriod]:
    """Découpe `duration` à partir de `start` en périodes consécutives de
    signes de `level`, à partir de `start_sign`, tournant autant de fois que
    nécessaire autour du zodiaque (cas fréquent : la durée d'un signe au
    niveau parent dépasse presque toujours la somme d'un tour complet des 12
    signes à l'unité du niveau courant). La dernière période est tronquée
    pour s'arrêter exactement à `start + duration`.

    Relâchement du lien ("loosing of the bond", Vettius Valens via Chris
    Brennan) : si le cycle des 12 signes revient sur `start_sign` avant la
    fin de `duration`, la période suivante saute au signe **opposé** à
    `start_sign` plutôt que de le répéter, puis l'ordre zodiacal normal
    reprend à partir de là (`_next_sign`). Cette structure de "Reste à
    faire" attendait une source qui tranche : un tour complet des 12 signes
    totalise toujours ~17,4 ans à l'unité du niveau courant (211 "années" de
    la table `ZODIACAL_RELEASING_YEARS`, quel que soit le signe de départ),
    donc seuls les signes dont la durée propre dépasse ce seuil (Gémeaux,
    Cancer, Lion, Vierge, Capricorne, Verseau — maîtrisés par
    Mercure/Lune/Soleil/Saturne) peuvent effectivement boucler ; ceci émerge
    naturellement de la boucle ci-dessous, pas d'un seuil codé en dur.
    Vérifié contre plusieurs sources indépendantes et cohérentes entre elles
    (Mountain Astrologer, qui donne exactement l'exemple Capricorne -> ... ->
    Sagittaire -> [saut] Cancer ; The Astrology Podcast/lignée Brennan) et
    confirmé, à la date et au signe exacts, par les deux thèmes de référence
    pour la Part de Fortune (non documenté dans les `.docx`, mais recoupé par
    calcul direct) : Anthony (Capricorne L1 1997-07-01 -> 2024-02-10) boucle
    exactement le 2014-10-30 et saute vers le Cancer (opposé du Capricorne) ;
    Liam (Lion L1 2005-10-19 -> 2024-07-11) boucle exactement le 2023-02-17
    et saute vers le Verseau (opposé du Lion). Le blog aswinsubramanyan.com
    (déjà cité comme source pour la lignée Schmidt) indique à l'inverse un
    saut vers l'opposé du **dernier signe visité** — contredit par les deux
    sources ci-dessus et par les deux dates/signes vérifiés : traité comme
    une erreur de cette source, pas comme une variante légitime à arbitrer.
    S'applique récursivement à chaque niveau (L2 dans L1, L3 dans L2, L4
    dans L3), confirmé par les mêmes sources ("can also occur on L3 and
    L4") : automatique ici puisque `sub_periods`/`releasing_tree` appellent
    tous cette même fonction. Le drapeau `bond_loosed` n'autorise le saut
    qu'une seule fois par appel : après le saut, un second passage naturel
    par `start_sign` peut survenir bien avant qu'un tour complet (~17,4 ans)
    ne soit à nouveau écoulé depuis le saut (ce n'est pas une deuxième
    boucle, juste la suite normale de la séquence) — et aucun signe de la
    table n'est de toute façon assez long (max 30 ans) pour qu'un deuxième
    tour complet tienne après le premier saut.
    """
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"level doit être entre 1 et {MAX_LEVEL} : {level}")

    days_per_unit = DAYS_PER_LEVEL[level - 1]
    end = start + duration
    periods = []
    sign = start_sign
    cursor = start
    bond_loosed = False
    just_loosed = False
    while cursor < end:
        length = timedelta(days=ZODIACAL_RELEASING_YEARS[sign] * days_per_unit)
        period_end = min(cursor + length, end)
        periods.append(
            ReleasingPeriod(
                level=level,
                sign=sign,
                ruler=SIGN_RULERS[sign],
                start=cursor,
                end=period_end,
                bond_loosed=just_loosed,
            )
        )
        cursor = period_end
        just_loosed = False
        next_sign = _next_sign(sign)
        if next_sign == start_sign and not bond_loosed:
            next_sign = opposite_sign(start_sign)
            bond_loosed = True
            just_loosed = True
        sign = next_sign
    return periods


@dataclass(frozen=True)
class ReleasingChapter:
    """Un chapitre de niveau 1 et ses sous-périodes de niveau 2 — structure
    imbriquée prête pour un rendu tabulaire (docgen), qui évite d'avoir à
    regrouper la liste plate de `releasing_tree()` (laquelle place tous les
    L1 d'abord, puis tous les L2 groupés par parent, pas un ordre entrelacé)."""

    l1: ReleasingPeriod
    sub_periods: list[ReleasingPeriod]


def releasing_chapters(lot_sign: str, birth: datetime, horizon: datetime) -> list[ReleasingChapter]:
    """Chapitres de niveau 1 (de `birth` à `horizon`, tronqué en pratique
    comme `level_periods` niveau 1), chacun avec ses sous-périodes de niveau 2."""
    return [
        ReleasingChapter(l1=period, sub_periods=sub_periods(period))
        for period in level_periods(1, lot_sign, birth, horizon - birth)
    ]


def sub_periods(parent: ReleasingPeriod) -> list[ReleasingPeriod]:
    """Périodes du niveau directement inférieur, à l'intérieur de `parent`.

    Toujours démarrées sur le même signe que `parent` (règle explicite de
    Valens/Brennan : "the first level two within that level one will always
    be the same sign") et bornées exactement à la durée réelle de `parent`.
    """
    if parent.level >= MAX_LEVEL:
        raise ValueError(f"Pas de niveau au-delà de {MAX_LEVEL}.")
    return level_periods(parent.level + 1, parent.sign, parent.start, parent.end - parent.start)


def releasing_tree(
    lot_sign: str, birth: datetime, horizon: datetime, max_level: int = MAX_LEVEL
) -> list[ReleasingPeriod]:
    """Calcule récursivement les niveaux 1 à `max_level` de la libération
    zodiacale à partir du signe de la Part (Fortune ou Esprit), de `birth`
    jusqu'à `horizon`. Retourne une liste plate de toutes les périodes de
    tous les niveaux calculés (chaque période porte son propre `level`,
    `start`/`end` permettent de reconstituer la hiérarchie parent/enfant).

    Contrairement aux niveaux 2 à 4 (bornés exactement par la durée réelle de
    leur période parente), le niveau 1 est tronqué à `horizon` par simple
    commodité pratique (limite arbitraire de calcul) : passer un `horizon`
    largement au-delà de l'âge qui intéresse l'appelant pour obtenir des
    périodes de niveau 1 non tronquées en pratique.
    """
    if not 1 <= max_level <= MAX_LEVEL:
        raise ValueError(f"max_level doit être entre 1 et {MAX_LEVEL} : {max_level}")

    periods = level_periods(1, lot_sign, birth, horizon - birth)
    for level in range(2, max_level + 1):
        parents = [p for p in periods if p.level == level - 1]
        for parent in parents:
            periods.extend(sub_periods(parent))
    return periods


def active_period(periods: list[ReleasingPeriod], level: int, when: datetime) -> ReleasingPeriod | None:
    """Période de `level` active à la date `when`, ou None si `when` est hors
    de la plage couverte par `periods` (avant le début ou après l'horizon)."""
    for period in periods:
        if period.level == level and period.start <= when < period.end:
            return period
    return None
