from dateutil import parser


class ParseDatetimeError(Exception):
    pass


def str_to_datetime(str_datetime):
    if not str_datetime:
        return None

    try:
        datetime_obj = parser.parse(str_datetime)
    except parser._parser.ParserError as exc:
        # published_at field is optional
        return None
    return datetime_obj
