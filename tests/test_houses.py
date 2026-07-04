import pytest

from hellenistic_astrology.core.houses import MODALITY_BY_SIGN, SIGNS, house_quality


def test_modality_covers_all_signs_in_three_groups_of_four():
    assert set(MODALITY_BY_SIGN) == set(SIGNS)
    by_modality: dict[str, int] = {}
    for modality in MODALITY_BY_SIGN.values():
        by_modality[modality] = by_modality.get(modality, 0) + 1
    assert by_modality == {"Cardinal": 4, "Fixe": 4, "Mutable": 4}


@pytest.mark.parametrize(
    "house, expected",
    [
        (1, "Angulaire"),
        (4, "Angulaire"),
        (7, "Angulaire"),
        (10, "Angulaire"),
        (2, "Succédente"),
        (5, "Succédente"),
        (8, "Succédente"),
        (11, "Succédente"),
        (3, "Cadente"),
        (6, "Cadente"),
        (9, "Cadente"),
        (12, "Cadente"),
    ],
)
def test_house_quality(house, expected):
    assert house_quality(house) == expected
