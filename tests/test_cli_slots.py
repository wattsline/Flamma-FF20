from ff20.cli import parse_slots


def test_parse_slots():
    assert parse_slots("0,1,5-7") == [0, 1, 5, 6, 7]
