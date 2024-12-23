import pytest

from datetime import datetime, timedelta

from cmdapp.utils import Text


def test_convert_datetime():
    converter = Text.convert_to_datetime
    assert converter("now") == datetime.now()
    assert converter("today") == datetime.today().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    assert converter("+10.days") == datetime.now() + timedelta(days=10)
    assert converter("<5.week") == datetime.now() - timedelta(weeks=5)
    assert converter("201213") == datetime(2020, 12, 13, 0, 0, 0, 0)
    assert converter("201211091") == datetime(2012, 11, 9, 10, 0, 0, 0)
    assert converter("20121109120532123987") == datetime(2012, 11, 9, 12, 5, 32, 123987)
    with pytest.raises(ValueError):
        converter("2012130912053")
    with pytest.raises(ValueError):
        converter("yesterday")


def test_telex_convert():
    converter = Text.convert_to_telex
    assert converter("xin chaof vieejt nam") == "xin chào việt nam"
    assert converter("xin chào việt nam") == "xin chào việt nam"


def test_ascii_convert():
    converter = Text.convert_to_ascii
    assert converter("xin chao viet nam") == "xin chao viet nam"
    assert converter("xin chào việt nam") == "xin chao viet nam"
