import datetime as dt
import pytest

from apps.feeds.date_utils import str_to_datetime
from apps.feeds.date_utils import ParseDatetimeError


def test_str_to_datetime_success():
    """
    Test converting a str datetime to a python native
    datetime object
    """
    str_date_time = "Sat, 04 Jul 2020 01:43:00 +0200"

    dt_obj = str_to_datetime(str_date_time)

    assert isinstance(dt_obj, dt.datetime)
    assert (dt.datetime.strftime(dt_obj, "%a, %d %b %Y %H:%M:%S %z")) == str_date_time


@pytest.mark.parametrize(
    "str_datetime, expected_output",[("", None),("foo", None),],
)
def test_str_to_datetime_invalid(str_datetime, expected_output):
    """
    Test converting an invalid str datetime
    to a python native datetime object
    """
    assert str_to_datetime(str_datetime) == expected_output
