DAYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')


def is_open(hours, moment):
    if not hours:
        return True
    now = moment.strftime('%H:%M')
    today = DAYS[moment.weekday()]
    yesterday = DAYS[moment.weekday() - 1]
    for start, end in hours.get(today, []):
        if (start <= now < end) if start < end else now >= start:
            return True
    return any(start > end and now < end for start, end in hours.get(yesterday, []))
