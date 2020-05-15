from datetime import datetime

import pytest
import taskhuddler.utils as utils
from dateutil.parser import parse

Range = utils.Range


@pytest.mark.parametrize(
    "r1,r2,expected",
    (
        (Range(start=datetime(2017, 1, 15), end=datetime(2017, 5, 10)), Range(start=datetime(2017, 3, 20), end=datetime(2017, 9, 15)), True),
        (Range(start=datetime(2017, 6, 15), end=datetime(2017, 6, 15)), Range(start=datetime(2017, 6, 11), end=datetime(2017, 6, 18)), True),
        (Range(start=datetime(2017, 1, 10), end=datetime(2017, 5, 10)), Range(start=datetime(2017, 6, 10), end=datetime(2017, 9, 10)), False),
        (
            Range(start=parse("2017-06-10 09:00:00"), end=parse("2017-06-10 10:00:00")),
            Range(start=parse("2017-06-10 09:50:00"), end=parse("2017-06-10 10:10:00")),
            True,
        ),
        (
            Range(start=parse("2017-06-10 09:00:00"), end=parse("2017-06-10 10:00:00")),
            Range(start=parse("2017-06-10 10:50:00"), end=parse("2017-06-11 10:10:00")),
            False,
        ),
    ),
)
def test_should_merge(r1, r2, expected):
    assert utils.should_merge(r1, r2) == expected


@pytest.mark.parametrize(
    "r1,r2,expected",
    (
        (
            Range(start=datetime(2017, 1, 15), end=datetime(2017, 5, 10)),
            Range(start=datetime(2017, 3, 20), end=datetime(2017, 9, 15)),
            Range(start=datetime(2017, 1, 15), end=datetime(2017, 9, 15)),
        ),
        (
            Range(start=datetime(2017, 6, 15), end=datetime(2017, 6, 15)),
            Range(start=datetime(2017, 6, 11), end=datetime(2017, 6, 18)),
            Range(start=datetime(2017, 6, 11), end=datetime(2017, 6, 18)),
        ),
        (
            Range(start=datetime(2017, 5, 5), end=datetime(2017, 5, 10)),
            Range(start=datetime(2017, 5, 1), end=datetime(2017, 5, 15)),
            Range(start=datetime(2017, 5, 1), end=datetime(2017, 5, 15)),
        ),
    ),
)
def test_merge_dates(r1, r2, expected):
    assert utils.merge_dates(r1, r2) == expected


@pytest.mark.parametrize(
    "r1,r2", ((Range(start=datetime(2017, 1, 10), end=datetime(2017, 5, 10)), Range(start=datetime(2017, 6, 10), end=datetime(2017, 9, 10))),)
)
def test_merge_dates_bad_args(r1, r2):
    with pytest.raises(ValueError):
        utils.merge_dates(r1, r2)


@pytest.mark.parametrize(
    "dt_list,expected",
    [
        (
            [
                Range(start=datetime(2017, 1, 15), end=datetime(2017, 2, 15)),
                Range(start=datetime(2017, 5, 1), end=datetime(2017, 5, 15)),
                Range(start=datetime(2017, 2, 1), end=datetime(2017, 2, 25)),
                Range(start=datetime(2017, 5, 5), end=datetime(2017, 5, 10)),
                Range(start=datetime(2017, 5, 14), end=datetime(2017, 6, 29)),
            ],
            [Range(start=datetime(2017, 1, 15), end=datetime(2017, 2, 25)), Range(start=datetime(2017, 5, 1), end=datetime(2017, 6, 29))],
        )
    ],
)
def test_merge_date_list(dt_list, expected):
    assert utils.merge_date_list(dt_list) == expected
