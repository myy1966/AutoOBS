import datetime


def add_seconds(time: datetime.time, seconds: int) -> datetime.time:
    return (datetime.datetime.combine(datetime.date(2021, 1, 1), time)
            + datetime.timedelta(seconds=seconds)).time()


def sub_seconds(time: datetime.time, seconds: int) -> datetime.time:
    return (datetime.datetime.combine(datetime.date(2021, 1, 1), time)
            - datetime.timedelta(seconds=seconds)).time()


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
