#!/usr/bin/env python

import json
try:
    # Python3
    import urllib.request
    urlopen = urllib.request.urlopen
except ImportError:
    # Python2
    import urllib
    urlopen = urllib.urlopen
from datetime import date
import termios
import struct
import fcntl
import sys

restaurants = [
    {'name': 'Newton', 'kitchen': 6, 'menutype': 60},
    {'name': 'Zip', 'kitchen': 12, 'menutype': 60},
    {'name': 'Edison', 'kitchen': 2, 'menutype': 60},

    {'name': 'Pastabaari', 'kitchen': 26, 'menutype': 11},
    {'name': 'Fast Voltti', 'kitchen': 25, 'menutype': 4},
    {'name': 'Fusion Kitchen', 'kitchen': 6, 'menutype': 3},
]

# TODO: translate names to english
meal_options = [
    {'key': 'LOUNAS1', 'name': 'Rohee'},
    {'key': 'LOUNAS2', 'name': 'Rohee'},
    {'key': 'LOUNAS Kasvis-', 'name': 'Rohee'},
    {'key': 'RUOKAISA KEITTO', 'name': 'Reilu'},
    {'key': 'KEVYTKEITTO', 'name': 'Reilu kevyt'},
    {'key': 'RUOKAISA KOMPONENTTI', 'name': 'Reilu kevyt'},
]

# Style settings
RESTAURANT_NAME = '\033[33;1m'
OPTION_NAME = ''
SEPARATOR = ' > '
SEPARATOR_COLOR = '\033[32m'
MAIN_ITEM = '\033[0;1m'
EXTRA_NAMES = '\033[22;36m'
ENDC = '\033[0m'

def get_menu():
    # Determine terminal width
    cr = struct.unpack('hh', fcntl.ioctl(0, termios.TIOCGWINSZ, '1234'))
    width = cr[1]

    lang = 'fi'   # fi or en

    cmdline = sys.argv[1:]

    # See if there is -lang option on the command line
    try:
        i = cmdline.index('-lang')
        lang = cmdline.pop(i + 1)
        cmdline.pop(i)
    except ValueError:
        pass

    menu_date = date.today()

    _, week, weekday = menu_date.isocalendar()

    for r in restaurants:
        params = {
            'kitchen': r['kitchen'],
            'menutype': r['menutype'],
            'weekday': weekday,
            'week': week,
            'lang': lang,
        }
        f = urlopen('http://www.juvenes.fi/DesktopModules/Talents.LunchMenu/LunchMenuServices.asmx/GetMenuByWeekday?KitchenId=%(kitchen)s&MenuTypeId=%(menutype)s&Week=%(week)d&Weekday=%(weekday)d&lang=\'%(lang)s\'&format=json' %
            params)
        data = f.read().decode('utf-8')
        # the retrieved data is a Javascript value in form '("d": "xxx");',
        # where xxx is JSON encoded payload.
        json_string = json.loads(data.strip()[1:-2])['d']
        d = json.loads(json_string)
        if d is None:
            continue

        options = list(meal_options)
        meal_dict = {}
        for option in d['MealOptions']:
            meal_dict[option['Name']] = option
            # Also add the option to the list of known meal options, so that we
            # can show the unknown options after the defined order.
            options.append({
                'key': option['Name'],
                'name': option['Name'].capitalize(),
            })

        header_printed = False

        for option in options:
            content = meal_dict.pop(option['key'], None)
            if content is None:
                continue
            names = []
            for item in content['MenuItems']:
                names.append(item['Name'])
            main_item = names[0]
            if len(names) > 1:
                main_item += ', '

            # Filter based on arguments from the command line
            words = '%s %s %s' % (r['name'], option['name'], ' '.join(names))
            words = words.lower()
            visible = True
            for kw in cmdline:
                if kw.startswith('-'):
                    if kw[1:] in words:
                        visible = False
                        break
                else:
                    if kw not in words:
                        visible = False
                        break
            if not visible:
                continue

            if not header_printed:
                padding = width // 2 - len(r['name']) // 2
                print(RESTAURANT_NAME + ' ' * padding + r['name'] + ENDC)
                header_printed = True

            # Limit the length of extra items
            extra = ', '.join(names[1:])
            max_extra_len = width - (width // 5 + len(main_item) + len(SEPARATOR)) - 1
            if len(extra) > max_extra_len:
                extra = extra[0:max_extra_len-3] + '...'

            padding = width // 5 - len(option['name'])
            print(OPTION_NAME + ' ' * padding + option['name'] + SEPARATOR_COLOR + \
                  SEPARATOR + MAIN_ITEM + main_item + EXTRA_NAMES + extra + ENDC)

        if header_printed:
            print('')

if __name__ == '__main__':
    get_menu()
