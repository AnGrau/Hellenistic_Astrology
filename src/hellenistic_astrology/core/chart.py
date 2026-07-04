from pathlib import Path

from . import aspects, dignities, ephemeris, houses, lots, sect
from .observation import Observation, PointPosition
from .timezone import BirthData, resolve_utc

DEFAULT_EPHE_PATH = str(Path(__file__).resolve().parents[3] / "data" / "ephe")


def build_observation(birth: BirthData, ephe_path: str = DEFAULT_EPHE_PATH) -> Observation:
    utc_dt = resolve_utc(birth)
    jd_ut = ephemeris.julian_day_utc(utc_dt)

    ephemeris.set_ephemeris_path(ephe_path)
    flags = ephemeris.compute_flags(ephe_path)

    ascendant_lon, midheaven_lon = ephemeris.ascendant_midheaven(
        jd_ut, birth.latitude, birth.longitude
    )
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
        sect_role: str | None = None,
        speed: float | None = None,
    ) -> PointPosition:
        return PointPosition(
            name=name,
            sign=houses.sign_name(longitude),
            degree_in_sign=houses.degree_in_sign(longitude),
            house=houses.whole_sign_house(longitude, ascendant_lon),
            retrograde=retrograde,
            essential_dignity=essential_dignity,
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
            sect_role=sect.sect_role(name, diurnal),
            speed=raw.speed,
        )
        for name, raw in raw_planets.items()
    ]

    fortune_lon = lots.part_of_fortune(ascendant_lon, sun_lon, moon_lon, diurnal)
    spirit_lon = lots.part_of_spirit(ascendant_lon, sun_lon, moon_lon, diurnal)
    part_of_fortune = make_point("Part de Fortune", fortune_lon)
    part_of_spirit = make_point("Part de l'Esprit", spirit_lon)

    all_points = [ascendant, *planets, midheaven, part_of_fortune, part_of_spirit]
    clusters = aspects.build_clusters(all_points)
    cluster_aspects = aspects.compute_cluster_aspects(clusters, all_points)

    return Observation(
        name=birth.name,
        sect="diurne" if diurnal else "nocturne",
        ascendant=ascendant,
        midheaven=midheaven,
        planets=planets,
        part_of_fortune=part_of_fortune,
        part_of_spirit=part_of_spirit,
        rulerships=dignities.traditional_rulerships(ascendant_lon),
        clusters=clusters,
        cluster_aspects=cluster_aspects,
    )
