import datetime

from tripsphere.common.v1 import date_pb2


def date_to_proto(date: datetime.date | None) -> date_pb2.Date | None:
    if date is None:
        return None
    return date_pb2.Date(
        year=date.year,
        month=date.month,
        day=date.day,
    )
