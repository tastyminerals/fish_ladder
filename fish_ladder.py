#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Pull data from www.fishbattle.net/rank_ladder, format it and pretty-print.
"""
from __future__ import division
import argparse
import codecs
import json
import re
import os
import sys
try:
    import requests
    import bs4
except ImportError:
    print 'ERROR! Please install Python2 modules using the commands below:'
    print 'sudo pip2 install requests'
    print 'sudo pip2 install beautifulsoup4'
    sys.exit(1)

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


def update_data():
    """Get data from tl and fish and store it in json files.
    Returns:
        | *wiki* (dict) -- a dict of player nicknames, fish nick -> bw nick
        | *fish* (dict) -- a dict of fish nicknames with their record
    """
    try:
        with codecs.open('tlwiki.json', 'r', encoding='utf8') as fp:
            wiki = json.load(fp)
    except (IOError, OSError):
        wiki = query_tl_wiki()
        with codecs.open('tlwiki.json', 'w', encoding='utf8') as fp:
            json.dump(wiki, fp, sort_keys=True, indent=2)
    try:
        with codecs.open('fish.json', 'r', encoding='utf8') as fp:
            fish = json.load(fp)
    except (IOError, OSError):
        fish = query_fish()
        with codecs.open('fish.json', 'w', encoding='utf8') as fp:
            json.dump(fish, fp, sort_keys=True, indent=2)
    return wiki, fish


def query_tl_wiki():
    """
    Get and parse bw names -> fish names tables from tl wiki.
    Returns:
        *fish_names* (dict) -- a dict of player nicknames, fish nick -> bw nick
    """
    tl_page = SESSION.get('http://wiki.teamliquid.net/starcraft/Fish_Server#List_of_Known_Fish_Server_Usernames')
    tl_wiki_page = bs4.BeautifulSoup(tl_page.content, 'lxml')
    # create a dic of bw player fish nicknames and real nicknames
    fish_names = {}
    bw_name = ''
    players = tl_wiki_page.find('table', {'class': 'sortable wikitable'})
    for player in players.find_all('tr'):
        for elem in player.contents:
            if isinstance(elem, bs4.element.Tag):
                if elem.string is None:
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
                    fish_names[name.rstrip(',')] = bw_name
    return fish_names


def query_fish():
    """
    Get and format ladder ranking data from fish.
    Returns:
        *fish_ladder* (dict) -- a dict of fish nicknames with their record
    """
    fish_page = SESSION.get('http://www.fishbattle.net/rank_ladder')
    fish_rankings = bs4.BeautifulSoup(fish_page.content, 'lxml')
    rankings = fish_rankings.find('div', {'class': 'ctm'})
    ranking = [td.string for td in rankings.find_all('td')]
    # group and clean up
    grouped_ranking = []
    for i in ranking:
        if i is None:
            group = []
            grouped_ranking.append(group)
            continue
        group.append(i)
    grouped_ranking = [i for i in grouped_ranking if i]
    # create a dict, fish_nickname: (rank, win_ratio, win, lost, games, points)
    fish_ladder = {}
    # [u'1 \uc704', u'melverc', u'164', u'46', u'3381']
    for elem in grouped_ranking:
        games = int(elem[2]) + int(elem[3])
        ratio = round(int(elem[2]) / games, 2) * 100
        fish_ladder[elem[1]] = (elem[0].split()[0], ratio, elem[2], elem[3],
                                games, elem[4])
    return fish_ladder


def display_pls(wiki):
    """Display a sorted list of known players."""
    name_srt = sorted(set([n for n in wiki.values()]))
    first = ''
    for name in name_srt:
        letter = name[0]
        if first != letter:
            first = letter
            print style.BOLD
            print letter.upper(), style.END
        print ' ', name


def get_player_info(player_name, wiki, fish):
    """Get information about specific player."""
    # lowecase all wiki names first
    wiki_low = dict([(k.lower(), v) for k,v in wiki.items()])
    info_str = "wins: {0}%, won: {1}, lost: {2}, total: {3}, points: {4}"
    if player_name not in wiki.values() and player_name.lower() not in fish:
        print "Oops, you might have misstyped the name!"
        sys.exit(1)
    elif player_name in wiki.values():
        for key, val in wiki.items():
            if player_name == val:
                info = fish.get(key.lower())
                player_info = '---' if not info else info_str.format(*info[1:])
                print u" {0}, {1}, {2}".format(player_name, key, player_info)
    elif player_name.lower() in fish:
        wiki_name = wiki.get(player_name) or wiki_low.get(player_name.lower())
        if not wiki_name:
            print "Oops, you might have misstyped the name!"
            sys.exit(1)
        print " It's " + style.BOLD + wiki_name, style.END


def get_ladder(top, wiki, fish):
    """Get the ranking for top-players"""
    # lowecase all wiki names first
    wiki_low = dict([(k.lower(), v) for k,v in wiki.items()])
    # sort fish dict
    ladder_unsort = []
    for key, val in fish.items():
        stats = "wins: {0}%, won: {1}, lost: {2}, total: {3}, points: {4}".format(*val[1:])
        rank = val[0]
        ladder_unsort.append([rank, wiki_low.get(key) or 'Unknown: %s' % key,
                              stats])
    ladder_unsort.sort(key=lambda x: int(x[0]))
    for num, pstats in enumerate(ladder_unsort):
        if num >= top:
            break
        print ' ' + pstats[0], style.BOLD, pstats[1], style.END, ' '.join(pstats[2:])


def main(args):
    """Handle user args and act accordingly."""
    wiki, fish = update_data()
    if args.update:
        print 'Wait a few sec... updating information...\n'
        try:
            os.remove('tlwiki.json')
            os.remove('fish.json')
        except (OSError, IOError):
            print 'ERROR: Cannot delete "{0}" or "{1}"'.format('tlwiki.json',
                                                               'fish.json')
            print "You've probably opened them in your text editor :D"
            sys.exit(1)
        wiki, fish = update_data()
    if args.players:
        display_pls(wiki)
        print ''
    if args.player:
        get_player_info(args.player, wiki, fish)
        print ''
    if args.top:
        get_ladder(args.top, wiki, fish)
        print ''
    elif not args.top and not args.player and not args.players:
        get_ladder(20, wiki, fish)
        print ''


if __name__ == '__main__':
    SESSION = requests.session()
    prs = argparse.ArgumentParser(description="""
    Query fish server and get the relevant information about BW players.""")
    prs.add_argument('-t', '--top', type=int,
                     help='Specify the number of top players to be displayed,'
                     ' default = 20.',
                     required=False)
    prs.add_argument('-p', '--player',
                     help='Display information about specific player using his'
                     ' nickname. It can be a real nickname or fish nickname.',
                     required=False)
    prs.add_argument('-pls', '--players', action='store_true',
                     help='Display a list of currently known BW players.',
                     required=False)
    prs.add_argument('-u', '--update', action='store_true',
                     help='Fetch most recent data from tl.wiki and fish.',
                     required=False)
    args = prs.parse_args()
    main(args)
