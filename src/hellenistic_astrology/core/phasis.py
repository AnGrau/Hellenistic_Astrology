"""Phasis : proximité d'une station (la planète devient rétrograde ou
redevient directe) ou d'un lever/coucher héliaque (l'écart réel
Soleil-planète franchit le seuil de 15° déjà utilisé pour « sous les
rayons », jalon 20/44) autour de la date de naissance, fenêtre de 7 jours
(CLAUDE.md).

Dernière technique laissée de côté lors de la planification de la grille
de condition planétaire (jalon 44, `core.condition`). Contrairement au
reste de cette grille, qui ne fait que recombiner des positions déjà
calculées à un instant donné, le phasis exige une vraie recherche
numérique dans le temps : un balayage jour par jour de l'éphéméride
autour de la naissance (±SEARCH_WINDOW_DAYS), capacité qui n'existe nulle
part ailleurs dans `core/`. `pyswisseph` n'a aucune fonction de recherche
de station intégrée ; sa fonction de visibilité héliaque réelle
(`heliacal_ut`) est écartée comme trop complexe (modélisation
atmosphérique/géographique/observateur, limitée à 60S-60N) — même
philosophie de proxy simplifié que `core.eclipse`.

Le système classique complet distingue 4 événements héliaques (lever
héliaque, coucher cosmique, lever acronyque, coucher héliaque), mais au
moins une source situe le lever/coucher acronyque sur l'opposition (180°)
pour les planètes extérieures, pas sur le seuil de 15° — ce vocabulaire
est volontairement évité ici pour ne pas désigner un événement différent
de celui réellement calculé (recherche faite avant planification, jalon
45). Les étiquettes utilisées distinguent seulement le côté matin/soir
(étoile du matin : `aspects.is_west_of_sun`), en vocabulaire simple.

Reste purement informationnel : ne participe pas au classement à 6
niveaux de `core.condition` (décidé explicitement avec l'utilisateur
après recherche — ces phases sont décrites comme des « changements
fonctionnels » plutôt que des jugements favorable/défavorable, à la
différence de la dignité ou de la secte).

Aucune fixture Anthony/Liam ne documente cette technique (comme la
grille de condition planétaire en son temps) : tests synthétiques pour la
logique de détection, tests d'intégration de plausibilité seulement sur
les thèmes réels.

**Limitation documentée** : quand une station ET un franchissement
héliaque tombent tous deux dans la fenêtre de 7 jours — cas réel, pas
seulement théorique, pour Mercure (sa boucle rétrograde est centrée sur
la conjonction inférieure, qui est aussi le moment où elle franchit 15°,
écart minimal mesuré de 0 jour entre les deux types d'événement lors de
la validation de ce jalon) — seul le plus proche des deux est rapporté ;
l'autre existe mais n'est pas visible dans le résultat."""

from dataclasses import dataclass

from .aspects import angular_gap, is_west_of_sun
from .ephemeris import CLASSICAL_PLANETS, planet_positions

# Dupliqué depuis condition.UNDER_RAYS_ORB_DEGREES (même valeur, même
# raison de duplication déjà en place dans ce module frère : éviter un
# couplage core-à-core pour un seul float).
HELIACAL_THRESHOLD_DEGREES = 15.0

# Marge ~3x au-dessus du pire écart réel mesuré entre deux événements
# consécutifs (station ou héliaque, toutes planètes) pour Mars, la
# planète la plus lente concernée ici (~341 jours observés lors de la
# validation de ce jalon) — garantit qu'un événement est toujours trouvé
# quelle que soit la date de naissance.
SEARCH_WINDOW_DAYS = 500

# Fenêtre d'intensification (CLAUDE.md) : 7 jours autour de la naissance.
PHASIS_WINDOW_DAYS = 7

_NON_LUMINARY_PLANETS = [name for name in CLASSICAL_PLANETS if name not in ("Soleil", "Lune")]


@dataclass(frozen=True)
class PhasisEvent:
    planet: str
    event_type: str  # "Station directe" | "Station rétrograde" | "Lever héliaque du matin" | "Coucher héliaque du matin" | "Lever héliaque du soir" | "Coucher héliaque du soir"
    # Signé : négatif = avant la naissance, positif = après. Jour
    # d'attribution = le jour APRÈS le franchissement (convention fixe,
    # cohérente avec la granularité "jour" de la fenêtre de 7 jours
    # elle-même — voir `_find_crossings`).
    days_from_birth: int
    in_window: bool  # abs(days_from_birth) <= PHASIS_WINDOW_DAYS


@dataclass(frozen=True)
class _DailySample:
    day_offset: int
    speed: float
    gap_to_sun: float
    west_of_sun: bool


def _station_label(speed_before: float, speed_after: float) -> str | None:
    if speed_before >= 0 and speed_after < 0:
        return "Station rétrograde"
    if speed_before < 0 and speed_after >= 0:
        return "Station directe"
    return None


def _heliacal_label(gap_before: float, gap_after: float, west_of_sun_after: bool) -> str | None:
    """Table de vérité (direction du franchissement x côté matin/soir) :
    gap croissant (planète qui s'éloigne du Soleil, émerge de sous ses
    rayons) -> "Lever" ; gap décroissant (planète qui s'en approche,
    disparaît sous ses rayons) -> "Coucher". Combiné au côté déterminé par
    `aspects.is_west_of_sun` au jour du franchissement."""
    crosses_up = gap_before < HELIACAL_THRESHOLD_DEGREES <= gap_after
    crosses_down = gap_after < HELIACAL_THRESHOLD_DEGREES <= gap_before
    if not crosses_up and not crosses_down:
        return None
    direction = "Lever" if crosses_up else "Coucher"
    side = "matin" if west_of_sun_after else "soir"
    return f"{direction} héliaque du {side}"


def _find_crossings(samples: list[_DailySample]) -> list[tuple[int, str]]:
    """Logique pure de détection (aucun appel d'éphéméride) : parcourt une
    série triée par `day_offset` croissant et détecte chaque station et
    chaque franchissement du seuil héliaque, tagué avec le jour APRÈS le
    franchissement. Résolution d'un jour : suffisante ici, aucune planète
    concernée ne peut changer de vitesse ou d'écart au Soleil assez vite
    pour "sauter" par-dessus un franchissement entre deux échantillons
    consécutifs (vérifié empiriquement lors de la validation de ce jalon,
    Mercure étant la plus rapide des cinq)."""
    crossings: list[tuple[int, str]] = []
    for before, after in zip(samples, samples[1:]):
        station = _station_label(before.speed, after.speed)
        if station is not None:
            crossings.append((after.day_offset, station))
        heliacal = _heliacal_label(before.gap_to_sun, after.gap_to_sun, after.west_of_sun)
        if heliacal is not None:
            crossings.append((after.day_offset, heliacal))
    return crossings


def _nearest_event(planet: str, samples: list[_DailySample]) -> PhasisEvent | None:
    """Parmi tous les franchissements trouvés (stations et héliaques
    confondus), ne garde que celui de plus petit `abs(day_offset)`. En cas
    d'égalité exacte de distance, `min` renvoie le premier rencontré dans
    `crossings`, qui est construit en parcourant les jours par ordre
    chronologique croissant — un départage déterministe, documenté, mais
    arbitraire (voir le module docstring pour le cas réel où ceci peut se
    produire, Mercure)."""
    crossings = _find_crossings(samples)
    if not crossings:
        return None
    day_offset, event_type = min(crossings, key=lambda c: abs(c[0]))
    return PhasisEvent(
        planet=planet,
        event_type=event_type,
        days_from_birth=day_offset,
        in_window=abs(day_offset) <= PHASIS_WINDOW_DAYS,
    )


def compute_phasis_events(
    jd_ut: float, flags: int, search_window_days: int = SEARCH_WINDOW_DAYS
) -> list[PhasisEvent]:
    """Un `PhasisEvent` par planète non-luminaire (au plus), l'événement
    (station ou héliaque) le plus proche de la naissance par nombre de
    jours, dans l'ordre canonique de `ephemeris.CLASSICAL_PLANETS`.
    Absente de la liste si aucun franchissement n'est trouvé dans la
    fenêtre (ne devrait jamais arriver pour une planète réelle vu les
    périodes synodiques, mais géré proprement)."""
    samples_by_planet: dict[str, list[_DailySample]] = {name: [] for name in _NON_LUMINARY_PLANETS}
    for day_offset in range(-search_window_days, search_window_days + 1):
        positions = planet_positions(jd_ut + day_offset, flags)
        sun_longitude = positions["Soleil"].longitude
        for name in _NON_LUMINARY_PLANETS:
            raw = positions[name]
            samples_by_planet[name].append(
                _DailySample(
                    day_offset=day_offset,
                    speed=raw.speed,
                    gap_to_sun=angular_gap(raw.longitude, sun_longitude),
                    west_of_sun=is_west_of_sun(raw.longitude, sun_longitude),
                )
            )

    events = []
    for name in _NON_LUMINARY_PLANETS:
        event = _nearest_event(name, samples_by_planet[name])
        if event is not None:
            events.append(event)
    return events
