import logging
from _datetime import datetime
from collections import defaultdict

import requests
from icalendar import Calendar

logger = logging.getLogger(__name__)


def calc_events(url, start_dt, end_dt=None):
    if url[:6] == 'webcal':
        url = 'https' + url[6:]

    logger.debug(url)
    resp = requests.get(url)
    cal = Calendar().from_ical(resp.text)
    logger.info(f'status: {resp.status_code} | len: {len(resp.text)}')

    if not end_dt:
        end_dt = datetime.now().replace(tzinfo=None)

    if start_dt > end_dt:
        return "Дата начала превышает дату окончания"

    events_dict = defaultdict(list)

    for component in cal.walk():
        if component.name == "VEVENT":
            event_start = component.decoded("dtstart")
            if not isinstance(event_start, datetime):
                continue

            event_start = event_start.replace(tzinfo=None)
            event_end = component.decoded("dtend").replace(tzinfo=None)
            if start_dt <= event_start <= end_dt:
                name = component.get("summary")
                event_length = round((event_end - event_start).seconds / 60)
                event_date = event_start.strftime('%d/%m')

                events_dict[name].append((event_length, event_date))

    minutes_all = 0
    reply_text = ""
    for event_name, len_date in events_dict.items():
        line = [f'{l[0]} мин ({l[1]})' for l in len_date]
        total_min = sum([l[0] for l in len_date])
        minutes_all += total_min

        reply_text += f'<b>{event_name}</b> ({total_min} мин)\n{"; ".join(line)}\n\n'

    reply_text += f'--------------------------'
    reply_text += f'\n<b>Итого:</b> {minutes_all} мин. за период с {start_dt.strftime("%d.%m")} по {end_dt.strftime("%d.%m")}'

    logger.debug(f'minutes: {minutes_all}')
    return reply_text
