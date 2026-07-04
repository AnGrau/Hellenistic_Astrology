from datetime import timedelta
from pathlib import Path

from . import aspects, dignities, ephemeris, geocoding, houses, lots, lunation, sect, zodiacal_releasing
from .observation import Observation, PointPosition
from .timezone import BirthData, resolve_utc

DEFAULT_EPHE_PATH = str(Path(__file__).resolve().parents[3] / "data" / "ephe")

# Horizon de calcul de la libération zodiacale (jusqu'à quel âge afficher les
# chapitres) : limite pratique arbitraire, pas une contrainte de la technique
# elle-même (voir core.zodiacal_releasing). 365,25 jours/an (plutôt que
# `datetime.replace(year=...)`) pour éviter un 29 février qui n'existe pas
# dans l'année cible.
ZODIACAL_RELEASING_HORIZON_YEARS = 100


def build_observation(birth: BirthData, ephe_path: str = DEFAULT_EPHE_PATH) -> Observation:
    utc_dt = resolve_utc(birth)
    jd_ut = ephemeris.julian_day_utc(utc_dt)
    latitude, longitude = geocoding.resolve_coordinates(birth)

    ephemeris.set_ephemeris_path(ephe_path)
    flags = ephemeris.compute_flags(ephe_path)

    ascendant_lon, midheaven_lon = ephemeris.ascendant_midheaven(jd_ut, latitude, longitude)
    raw_planets = ephemeris.planet_positions(jd_ut, flags)

    sun_lon = raw_planets["Soleil"].longitude
    moon_lon = raw_planets["Lune"].longitude
    sun_house = houses.whole_sign_house(sun_lon, ascendant_lon)
    diurnal = sect.is_diurnal(sun_house)

    def make_point(
        name: str,
        longitude: float,
        retrograde: bool | None = None,
        essential_dignity: str | None = None,
        triplicity_dignity: str | None = None,
        bound_dignity: str | None = None,
        decan_dignity: str | None = None,
        sect_role: str | None = None,
        speed: float | None = None,
    ) -> PointPosition:
        sign = houses.sign_name(longitude)
        house = houses.whole_sign_house(longitude, ascendant_lon)
        return PointPosition(
            name=name,
            sign=sign,
            degree_in_sign=houses.degree_in_sign(longitude),
            house=house,
            # Réutilise dignities.SIGN_TRIPLICITY comme table sign -> élément
            # (déjà utilisée pour la triplicité) : universel, contrairement
            # aux dignités ci-dessous qui ne concernent que les planètes.
            element=dignities.SIGN_TRIPLICITY[sign],
            modality=houses.MODALITY_BY_SIGN[sign],
            house_quality=houses.house_quality(house),
            retrograde=retrograde,
            essential_dignity=essential_dignity,
            triplicity_dignity=triplicity_dignity,
            bound_dignity=bound_dignity,
            decan_dignity=decan_dignity,
            sect_role=sect_role,
            speed=speed,
        )

    ascendant = make_point("Ascendant", ascendant_lon)
    midheaven = make_point("Milieu du Ciel", midheaven_lon)
    planets = [
        make_point(
            name,
            raw.longitude,
            retrograde=raw.retrograde,
            essential_dignity=dignities.essential_dignity(name, houses.sign_name(raw.longitude)),
            triplicity_dignity=dignities.triplicity_dignity(name, houses.sign_name(raw.longitude)),
            bound_dignity=dignities.bound_dignity(
                name, houses.sign_name(raw.longitude), houses.degree_in_sign(raw.longitude)
            ),
            decan_dignity=dignities.decan_dignity(
                name, houses.sign_name(raw.longitude), houses.degree_in_sign(raw.longitude)
            ),
            sect_role=sect.sect_role(name, diurnal),
            speed=raw.speed,
        )
        for name, raw in raw_planets.items()
    ]

    fortune_lon = lots.part_of_fortune(ascendant_lon, sun_lon, moon_lon, diurnal)
    spirit_lon = lots.part_of_spirit(ascendant_lon, sun_lon, moon_lon, diurnal)
    part_of_fortune = make_point("Part de Fortune", fortune_lon)
    part_of_spirit = make_point("Part de l'Esprit", spirit_lon)

    venus_lon = raw_planets["Vénus"].longitude
    eros_lon = lots.part_of_eros(ascendant_lon, venus_lon, spirit_lon, diurnal)
    part_of_eros = make_point("Part d'Éros", eros_lon)

    raw_north_node = ephemeris.north_node(jd_ut, flags)
    north_node = make_point(
        "Nœud Nord", raw_north_node.longitude, retrograde=raw_north_node.retrograde
    )
    south_node = make_point(
        "Nœud Sud", (raw_north_node.longitude + 180) % 360, retrograde=raw_north_node.retrograde
    )

    all_points = [
        ascendant,
        *planets,
        north_node,
        south_node,
        midheaven,
        part_of_fortune,
        part_of_spirit,
        part_of_eros,
    ]
    clusters = aspects.build_clusters(all_points)
    cluster_aspects = aspects.compute_cluster_aspects(clusters, all_points)

    positions_by_planet = {p.name: p.sign for p in planets}
    mutual_receptions = dignities.mutual_receptions_by_domicile(positions_by_planet)

    solar_proximity = dignities.solar_proximity(
        sun_lon,
        {name: raw.longitude for name, raw in raw_planets.items() if name not in {"Soleil", "Lune"}},
    )

    lunation_phase = lunation.lunation_phase(sun_lon, moon_lon)

    zr_horizon = utc_dt + timedelta(days=365.25 * ZODIACAL_RELEASING_HORIZON_YEARS)
    zodiacal_releasing_fortune = zodiacal_releasing.releasing_chapters(
        part_of_fortune.sign, utc_dt, zr_horizon
    )
    zodiacal_releasing_spirit = zodiacal_releasing.releasing_chapters(
        part_of_spirit.sign, utc_dt, zr_horizon
    )

    return Observation(
        name=birth.name,
        sect="diurne" if diurnal else "nocturne",
        ascendant=ascendant,
        midheaven=midheaven,
        planets=planets,
        part_of_fortune=part_of_fortune,
        part_of_spirit=part_of_spirit,
        part_of_eros=part_of_eros,
        north_node=north_node,
        south_node=south_node,
        rulerships=dignities.traditional_rulerships(ascendant_lon),
        mutual_receptions=mutual_receptions,
        all_points=all_points,
        clusters=clusters,
        cluster_aspects=cluster_aspects,
        zodiacal_releasing_fortune=zodiacal_releasing_fortune,
        zodiacal_releasing_spirit=zodiacal_releasing_spirit,
        solar_proximity=solar_proximity,
        lunation_phase=lunation_phase,
    )
