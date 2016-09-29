#!/usr/bin/env python3
"""
Get the real BW nickname given fish server nickname.
Keep local db updated from tl.net.
"""
import argparse
import codecs
import json
import re
import os
import sys


TLURL = "http://wiki.teamliquid.net/starcraft/Fish_Server#List_of_Known_Fish_Server_Usernames"


try:
    import requests
    import bs4
except ImportError:
    print('ERROR! Please install Python modules using the commands below:')
    print('pip install requests')
    print('pip install beautifulsoup4')
    sys.exit(1)


try:
    from fuzzywuzzy import fuzz
    from fuzzywuzzy import process
except ImportError:
    print('WARNING! Please install Python modules to enable fuzzy matching.')
    print('pip install fuzzywuzzy')
    print('pip install python-Levenshtein')


# for those who likes colors
class style:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


race2color = {'Protoss':style.GREEN,
              'Zerg':style.RED,
              'Terran':style.BLUE,
              'Random':style.UNDERLINE}


def update_data():
    """Get data from tl and store it in json files.
    Returns:
        | *wiki* (dict) -- a dict of player nicknames, fish nick -> bw nick
    """
    try:
        with codecs.open('tlwiki.json', 'r', encoding='utf8') as fp:
            wiki = json.load(fp)
    except (IOError, OSError):
        wiki = parse_tl_wiki()
        with codecs.open('tlwiki.json', 'w', encoding='utf8') as fp:
            json.dump(wiki, fp, sort_keys=True, indent=2)
    return wiki


def parse_tl_wiki():
    """
    Get and parse bw names -> fish names tables from tl wiki.
    Returns:
        *fish_names* (dict) -- a dict of player nicknames, fish nick -> bw nick
    """
    tl_page = SESSION.get(TLURL)
    tl_wiki_page = bs4.BeautifulSoup(tl_page.content, 'lxml')
    # create a dic of bw player fish nicknames and real nicknames
    fish_names = {}
    bw_name = ''
    players = tl_wiki_page.find('table', {'class': 'sortable wikitable'})
    for player in players.find_all('tr'):
        for elem in player.contents:
            if isinstance(elem, bs4.element.Tag):
                if elem.string is None:
                    race_elem = elem.find_all('img')
                    if race_elem:
                        race = race_elem[0].attrs.get('alt')
                    resultset = elem.find_all('a')
                    if not resultset:
                        continue
                    bw_name = re.sub(r' ?\(Player\) ?', '',
                                     resultset[0].attrs.get('title'))
                    continue
                if not bw_name:
                    continue
                # construct fish name -> bw name dic
                for name in elem.string.split():
                    fish_names[name.rstrip(',')] = bw_name,race
    return fish_names


def get_all(wiki):
    """Display a sorted list of all known BW players."""
    name_srt = sorted(set([n[0][0]+race2color[n[1]]+n[0]+style.END
                      for n in wiki.values()]))
    first = ''
    players = []
    for name in name_srt:
        letter = name[0]
        if first != letter:
            first = letter
            print(style.BOLD)
            print(letter.upper(), style.END)
            players.append((letter.upper(),))
        print(' ', name[1:])


def bwid(player_name, wiki):
    """Get BW id using fuzzy string match."""
    fishname, ratio = process.extractOne(player_name, wiki.keys())
    if ratio <= 75:
        print("Oops, not found in fish database.")
        return 0
    real_id = wiki.get(fishname)
    real_id = '{0}{1}{2}'.format(race2color[real_id[1] or 'Random'],
                                 real_id[0], style.END)
    print(u"It's {0}% {1}{2}{3}".format(ratio, style.BOLD, real_id, style.END))


def fishids(bwid, wiki):
    """Get fish ids given BW id."""
    #remove race info to use fuzzywuzzy
    norace_wiki = {k:v[0] for k,v in wiki.items()}
    fish_id, prob = process.extractOne(bwid, norace_wiki.values())
    race = dict(wiki.values()).get(bwid)
    if not race:
        print('Please check your spelling!')
    for k,v in wiki.items():
        if bwid == v[0]:
            fishid = '{0}{1}{2}'.format(race2color[race], k, style.END)
            print(u'{0}{1}{2}'.format(style.BOLD,fishid,style.END))


def force_update():
    print("Wait a few sec... updating players' database...")
    try:
        os.remove('tlwiki.json')
    except (OSError, IOError):
        print('ERROR: Cannot delete "{0}".'.format('tlwiki.json'))
        print("You've probably opened them in your text editor :D")
        sys.exit(1)
    wiki = update_data()
    return wiki


def main(args):
    """Handle user args and act accordingly."""
    wiki = update_data()
    if args.update:
        wiki = force_update()
    if args.all:
        get_all(wiki)
    if args.fishids:
        fishids(args.fishids, wiki)
    if args.player:
        bwid(args.player, wiki)


if __name__ == '__main__':
    SESSION = requests.session()
    prs = argparse.ArgumentParser(description="""
    Reveal who hides under particular fish id.
    Green - Protoss, Blue - Terran, Red - Zerg.""",
    formatter_class=argparse.RawTextHelpFormatter)
    prs.add_argument('-p', '--player',
                     help='Get BW id.',
                     required=False)
    prs.add_argument('-f', '--fishids',
                     help='Get all fish ids given BW id.',
                     required=False)
    prs.add_argument('-all', '--all', action='store_true',
                     help='Display a list of currently known BW players.',
                     required=False)
    prs.add_argument('-u', '--update', action='store_true',
                     help='Fetch most recent data from tl.wiki.',
                     required=False)
    args = prs.parse_args()
    main(args)
