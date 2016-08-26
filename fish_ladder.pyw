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
import ttk
import Tkinter as tk


try:
    import requests
    import bs4
except ImportError:
    print 'ERROR! Please install Python2 modules using the commands below:'
    print 'sudo pip2 install requests'
    print 'sudo pip2 install beautifulsoup4'
    sys.exit(1)

try:
    from fuzzywuzzy import fuzz
    from fuzzywuzzy import process
except ImportError:
    print 'WARNING! Please install Python2 modules to enable fuzzy matching.'
    print 'sudo pip2 install fuzzywuzzy'
    print 'sudo pip2 install python-Levenshtein'


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
        print 'Updated tlwiki.json!'

    try:
        with codecs.open('fish.json', 'r', encoding='utf8') as fp:
            fish = json.load(fp)
    except (IOError, OSError):
        fish = query_fish()
        if fish:
            with codecs.open('fish.json', 'w', encoding='utf8') as fp:
                json.dump(fish, fp, sort_keys=True, indent=2)
            print 'Updated fish.json!'
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
    if rankings:
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
            ratio = round(int(elem[2]) / games if games else 1, 2) * 100
            fish_ladder[elem[1]] = (elem[0].split()[0], ratio, elem[2], elem[3],
                                    games, elem[4])
        return fish_ladder
    else:
        print 'ERROR! Could not retrieve data from fish server, sorry :('
        #sys.exit(1)


def display_pls(wiki):
    """Display a sorted list of known players."""
    name_srt = sorted(set([n for n in wiki.values()]))
    first = ''
    players = []
    for name in name_srt:
        letter = name[0]
        if first != letter:
            first = letter
            print style.BOLD
            print letter.upper(), style.END
            players.append((letter.upper(),))
        print ' ', name
        players.append(name)
    return players


def get_fuzzy_player(player_name, wiki, real=False):
    """Get player id using fuzzy string match.
    Not available in UI mode."""
    if real:
        fishname, ratio = process.extractOne(player_name, wiki.keys())
        real_id = wiki.get(fishname)
        print u"It's {0}% {1}{2}{3}!".format(ratio, style.BOLD, real_id, style.END)
    else:
        fish_id, prob = process.extractOne(player_name, wiki.values())
        print 'It is {0}% {1}!'.format(prob, fish_id)
        print ''
        for k,v in wiki.items():
            if fuzz.ratio(v, fish_id) >= 85:
                print u'{0} --> {1}'.format(k, v)


def get_player_info(player_name, wiki, fish):
    """Get information about specific player."""
    # lowecase all wiki names first
    wiki_low = dict([(k.lower(), v) for k,v in wiki.items()])
    info_str = "wins: {0}%, won: {1}, lost: {2}, total: {3}, points: {4}"
    if player_name not in wiki.values() and player_name.lower() not in fish:
        print "Oops, you might have misstyped the name!"
        return ["Oops, you might have misstyped the name!"]
    elif player_name in wiki.values():
        player = []
        for key, val in wiki.items():
            if player_name == val:
                info = fish.get(key.lower())
                player_info = '---' if not info else info_str.format(*info[1:])
                print u"{0}, {1}, {2}".format(player_name, key, player_info)
                info = u"{0}, {1}, {2}".format(player_name, key, player_info)
                player.append(info)
        return player
    elif player_name.lower() in fish:
        wiki_name = wiki.get(player_name) or wiki_low.get(player_name.lower())
        if not wiki_name:
            print "Oops, you might have misstyped the name!"
            return ["Oops, you might have misstyped the name!"]
        print "It's " + style.BOLD + wiki_name, style.END
        return [wiki_name]


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
    fish_ladder = []
    for num, pstats in enumerate(ladder_unsort):
        if num >= top:
            break
        print pstats[0], style.BOLD, pstats[1], style.END, ' '.join(pstats[2:])
        info = pstats[0], pstats[1], ' '.join(pstats[2:])
        fish_ladder.append(info)
    return fish_ladder


def force_update():
    print 'Wait a few sec... updating information...\n'
    wiki, fish = update_data()
    try:
        os.remove('tlwiki.json')
        if fish:
            os.remove('fish.json')
    except (OSError, IOError):
        print 'ERROR: Cannot delete "{0}" or "{1}"'.format('tlwiki.json',
                                                           'fish.json')
        print "You've probably opened them in your text editor :D"
        sys.exit(1)
    return wiki, fish


def main(args):
    """Handle user args and act accordingly."""
    wiki, fish = update_data()
    if args.update:
        wiki, fish = force_update()
    if args.players:
        display_pls(wiki)
        print ''
    if args.player:
        get_player_info(args.player, wiki, fish)
        print ''
    if args.fuzzyreal:
        get_fuzzy_player(args.fuzzyreal, wiki, True)
        print ''
    if args.fuzzyfish:
        get_fuzzy_player(args.fuzzyfish, wiki)
        print ''
    if args.top:
        get_ladder(args.top, wiki, fish)
        print ''
    elif not any([args.top, args.player, args.players, args.fuzzyreal, args.fuzzyfish]):
        get_ladder(20, wiki, fish)
        print ''


class FishUI(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        # resizing main UI
        self.grid(sticky='nsew')
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        master.minsize(height=300, width=400)
        self.master = master
        self.wiki, self.fish = update_data()
        self._build_gui()
    def press_return(self, *args):
        if self.Entry0 is self.focus_get():
            self.get_fish()
        elif self.Entry1 is self.focus_get():
            self.get_player()

    def ctrl_a(self, callback=False):
        # checking which text widget has focus
        if self.Entry0 is self.focus_get():
            self.Entry0.select_range(0, 'end')
        elif self.Entry1 is self.focus_get():
            self.Entry1.select_range(0, 'end')
        elif self.Text0 is self.focus_get():
            self.Text0.tag_add('sel', '1.0', 'end')
        elif self.Text1 is self.focus_get():
            self.Text1.tag_add('sel', '1.0', 'end')
        return 'break'

    def clear_text1(self):
        # reset highighting
        self.Text1.tag_delete('style')
        # reload text
        self.Text1.delete('1.0', 'end')

    def get_pls(self):
        self.Text1.tag_delete('style')
        self.Text1.delete('1.0', 'end')
        pls = display_pls(self.wiki)
        for p in pls:
            if isinstance(p, tuple):
                self.Text1.insert(tk.END, '\n'+p[0]+'\n')
                continue
            self.Text1.insert(tk.END, p+'\n')
        #pls = '\n'.join(pls)
        #self.Text1.insert(tk.END, pls)

    def get_fish(self):
        fish_query = self.Entry0.get().strip()
        try:
            fish_query = int(fish_query)
        except ValueError:
            return
        if 0 > fish_query > 99999:
            return
        ladder_str = get_ladder(int(fish_query), self.wiki, self.fish)
        print ladder_str
        ladder = '\n'.join([' '.join(lad) for lad in ladder_str])

        # reset highighting
        self.Text0.tag_delete('style')
        # reload text
        self.Text0.delete('1.0', 'end')
        self.Text0.insert(tk.END, ladder)

    def get_player(self):
        player_query = self.Entry1.get().strip()
        player_str = get_player_info(player_query, self.wiki, self.fish)
        player = '\n'.join(player_str) + '\n\n'
        self.Text1.insert('1.0', player)

    def update_data(self):
        self.wiki, self.fish = force_update()

    def _build_gui(self):
        def make_resizable(elem, row, col, colspan, rowspan, stick):
            elem.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
                      sticky=stick)
            elem.grid_columnconfigure(col, weight=1)
            elem.grid_rowconfigure(row, weight=1)

        self.Main = ttk.Frame(self, borderwidth='2', relief='flat')
        self.Main.grid(columnspan=2, rowspan=1, sticky='nsew', pady=1, padx=1)
        self.Main.grid_columnconfigure(0, weight=1)
        self.Main.grid_columnconfigure(1, weight=1)  # do not get hidden
        self.Main.grid_rowconfigure(0, weight=3)
        self.Main.grid_rowconfigure(1, weight=1)
        self.Main.grid_rowconfigure(2, weight=1)
        # header
        self.DataFr = ttk.Frame(self.Main, borderwidth='2', relief='flat')
        make_resizable(self.DataFr, 0, 0, 2, 2, 'nsew')
        self.LadderLab = ttk.Label(self.DataFr,
                                   font='TkDefaultFont 10 bold',
                                   text='Fish Ladder')
        self.LadderLab.grid(row=0, column=0, sticky='w')
        self.PlayerLab = ttk.Label(self.DataFr,
                                   font='TkDefaultFont 10 bold',
                                   text='Player Information')
        self.PlayerLab.grid(row=0, column=1, sticky='w')

        # Ladder pane
        self.LadderFr = ttk.Frame(self.DataFr, borderwidth='2', relief='flat')
        make_resizable(self.LadderFr, 1, 0, 1, 1, 'wn')
        self.Entry0 = ttk.Entry(self.LadderFr, font='TkDefaultFont 12', width=5)
        self.Entry0.grid(row=0, column=0, columnspan=1, sticky='w')
        self.Entry0.bind('<Control-a>', self.ctrl_a)
        self.Entry0.bind('<Return>', self.press_return, '+')
        self.FishButt = ttk.Button(self.LadderFr, padding=(-10, 2), text='Get',
                                   command=self.get_fish, takefocus=True)
        self.FishButt.grid(row=0, column=1, sticky='w')
        self.Update = ttk.Button(self.LadderFr, padding=(-10, 2), text='Update',
                                 command=self.update_data, takefocus=True)
        self.Update.grid(row=0, column=2, sticky='w')
        # Left Text field
        self.LadderFrInner = ttk.Frame(self.DataFr, borderwidth='2', relief='groove')
        make_resizable(self.LadderFrInner, 2, 0, 1, 1, 'nsew')
        self.Text0 = tk.Text(self.LadderFrInner, font='TkDefaultFont 10', height=25,
                            width=55, undo=True, takefocus=0)
        make_resizable(self.Text0, 0, 0, 1, 1, 'nsew')
        self.Text0.bind('<Control-a>', self.ctrl_a)

        # Player pane
        self.PlayerFr = ttk.Frame(self.DataFr, borderwidth='2', relief='flat')
        make_resizable(self.PlayerFr, 1, 1, 1, 1, 'wn')
        self.Entry1 = ttk.Entry(self.PlayerFr, font='TkDefaultFont 12', width=25)
        self.Entry1.grid(row=0, column=0, columnspan=2, sticky='w')
        self.Entry1.bind('<Control-a>', self.ctrl_a)
        self.Entry1.bind('<Return>', self.press_return, '+')
        self.PlButt = ttk.Button(self.PlayerFr, padding=(-10, 2), text='Get',
                                 command=self.get_player, takefocus=True)
        self.PlButt.grid(row=0, column=1, sticky='e')
        self.Clear = ttk.Button(self.PlayerFr, padding=(-15, 2), text='Clear',
                                command=self.clear_text1, takefocus=True)
        self.Clear.grid(row=0, column=2, sticky='e')
        self.Pls = ttk.Button(self.PlayerFr, padding=(-10, 2), text='Players',
                              command=self.get_pls, takefocus=True)
        self.Pls.grid(row=0, column=3, sticky='e')
        # Right Text field
        self.PlFrInner = ttk.Frame(self.DataFr, borderwidth='2', relief='groove')
        make_resizable(self.PlFrInner, 2, 1, 1, 1, 'nsew')
        self.Text1 = tk.Text(self.PlFrInner, font='TkDefaultFont 10', height=25,
                             width=60, undo=True, takefocus=0)
        make_resizable(self.Text1, 0, 1, 1, 1, 'nsew')
        self.Text1.bind('<Control-a>', self.ctrl_a)
        # Exit pane
        self.ExitFr = ttk.Frame(self, width=500, borderwidth='2', relief='flat')
        make_resizable(self.ExitFr, 3, 0, 1, 1, 'ew')
        self.Exit = ttk.Button(self.ExitFr, padding=(0, 0), text='Exit',
                                 command=self.master.destroy, takefocus=True)
        self.Exit.grid(row=0, column=1)


def run_gui():
    root = tk.Tk()
    root.title('Fish Ladder 0.2')
    # root.geometry("1000x630")  # gui size at startup
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.resizable(True, True)
    root.update()
    # ttk_theme = ttk.Style()
    # you can use ttk themes here ('clam', 'alt', 'classic', 'default')
    # ttk_theme.theme_use('clam')
    gui = FishUI(root)
    gui.mainloop()


if __name__ == '__main__':
    SESSION = requests.session()
    prs = argparse.ArgumentParser(description="""
    Query fish server and get the relevant information about BW players.""")
    prs.add_argument('-t', '--top', type=int,
                     help='Specify the number of top players to be displayed, '
                     'default = 20.',
                     required=False)
    prs.add_argument('-p', '--player',
                     help='Display information about specific player using his '
                     'nickname. It can be a real nickname or fish nickname.',
                     required=False)
    prs.add_argument('-fr', '--fuzzyreal',
                     help='Get a real id using fuzzy matching.',
                     required=False)
    prs.add_argument('-ff', '--fuzzyfish',
                     help='Get a list of fish ids using fuzzy matching.',
                     required=False)
    prs.add_argument('-pls', '--players', action='store_true',
                     help='Display a list of currently known BW players.',
                     required=False)
    prs.add_argument('-u', '--update', action='store_true',
                     help='Fetch most recent data from tl.wiki and fish.',
                     required=False)
    args = prs.parse_args()
    if any([args.top, args.player, args.players, args.fuzzyreal, args.fuzzyfish, args.update]):
        main(args)
    else:
        run_gui()
