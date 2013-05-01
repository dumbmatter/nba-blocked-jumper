#!/usr/bin/env python

from __future__ import division

import copy
import json
import re
from collections import defaultdict

# A number between 2007 and 2012, or "All"
SEASON = 'All'


def player_stats():
    return {
        'before': {
            'fg': 0,
            'fga': 0
        },
        'after': {
            'fg': 0,
            'fga': 0
        },
        'other': {
            'fg': 0,
            'fga': 0
        },
        'num_with_block': 0
    }


def merge_dicts(x, y):
    for k in y.keys():
        x[k]['before']['fg'] += y[k]['before']['fg']
        x[k]['before']['fga'] += y[k]['before']['fga']
        x[k]['after']['fg'] += y[k]['after']['fg']
        x[k]['after']['fga'] += y[k]['after']['fga']
        x[k]['other']['fg'] += y[k]['other']['fg']
        x[k]['other']['fga'] += y[k]['other']['fga']
        x[k]['num_with_block'] += y[k]['num_with_block']


def update_total(total, y):
    for k in y.keys():
        total['before']['fg'] += y[k]['before']['fg']
        total['before']['fga'] += y[k]['before']['fga']
        total['after']['fg'] += y[k]['after']['fg']
        total['after']['fga'] += y[k]['after']['fga']
        total['other']['fg'] += y[k]['other']['fg']
        total['other']['fga'] += y[k]['other']['fga']
        total['num_with_block'] += y[k]['num_with_block']


def find_max_min(stats, cutoff):
    max_player = ''
    max_val = -100
    min_player = ''
    min_val = 100
    for k in stats.keys():
        if stats[k]['before']['fga'] > cutoff and stats[k]['after']['fga'] > cutoff:
            diff = stats[k]['before']['fg'] / stats[k]['before']['fga'] - stats[k]['after']['fg'] / stats[k]['after']['fga']
            if diff > max_val:
                max_val = diff
                max_player = k
            if diff < min_val:
                min_val = diff
                min_player = k
#            print "\n"
#            print_header(k)
#            print_summary(stats[k])
    return [max_player, min_player]


def print_header(txt):
    print txt
    print ''.join(['-' for i in txt])


def print_summary(stats):
    print "Before block:          %d%% (%d FGA)" % (100 * stats['before']['fg'] / stats['before']['fga'], stats['before']['fga'])
    print "After block:           %d%% (%d FGA)" % (100 * stats['after']['fg'] / stats['after']['fga'], stats['after']['fga'])
    print "Never blocked in game: %d%% (%d FGA)" % (100 * stats['other']['fg'] / stats['other']['fga'], stats['other']['fga'])
    print "Overall:               %d%% (%d FGA)" % (100 * (stats['before']['fg'] + stats['after']['fg'] + stats['other']['fg']) / (stats['before']['fga'] + stats['after']['fga'] + stats['other']['fga']), stats['before']['fga'] + stats['after']['fga'] + stats['other']['fga'])

f = open('playbyplay%s.txt' % SEASON)

num_games = 0
game_id = ''
stats = defaultdict(player_stats)
stats_total = player_stats()
stats_temp = defaultdict(player_stats)

for line in f:
    row = line.split('\t')

    # Check for a new game
    if row[0] != game_id:
#        print 'NEW GAME ', len(stats), len(stats_temp)
        merge_dicts(stats, stats_temp)
        update_total(stats_total, stats_temp)

        game_id = row[0]
        stats_temp = defaultdict(player_stats)
        num_games += 1

    if ('Jump' in row[3] and 'hot' in row[3]) or '3pt Shot' in row[3]:
        abbrev = re.findall('\[([A-Z]+).*?\]', row[3])[0]
        name = re.findall('\[.*?\] (.+?) ', row[3])[0]

        # Fix for players listed with first/second initial
        if name[-1] == '.' and len(name) <= 3:
            name = re.findall('\[.*?\] (.+? .+?) ', row[3])[0]

        player_id = '%s (%s)' % (name, abbrev)

        # Is this the first blocked jumper for this player this game?
        if ' Missed Block' in row[3] and stats_temp[player_id]['num_with_block'] == 0:
            # Mark all recorded shots by this player this game as "before" a block
            stats_temp[player_id]['before'] = copy.deepcopy(stats_temp[player_id]['other'])
            stats_temp[player_id]['other'] = {
                'fg': 0,
                'fga': 0
            }
            stats_temp[player_id]['num_with_block'] = 1
#            print 'BLOCKED JUMPER: ', player_id

        # Track all made shots as either "after" or "other"; "before" is populated above
        elif ' Made' in row[3]:
            if stats_temp[player_id]['num_with_block']:
                stats_temp[player_id]['after']['fg'] += 1
                stats_temp[player_id]['after']['fga'] += 1
            else:
                stats_temp[player_id]['other']['fg'] += 1
                stats_temp[player_id]['other']['fga'] += 1

        # Track all missed shots *except* the first blocked jumper
        elif ' Missed' in row[3]:
            if stats_temp[player_id]['num_with_block']:
                stats_temp[player_id]['after']['fga'] += 1
            else:
                stats_temp[player_id]['other']['fga'] += 1

        # This should never be reached
        else:
            print 'WTF IS THIS ', row[3]

print_header("League-wide FG% on jump shots before/after a blocked jumper")
print_summary(stats_total)

cutoff = 25
out = []
for k in stats.keys():
    if stats[k]['before']['fga'] > cutoff and stats[k]['after']['fga'] > cutoff:
        out.append({
            'name': k,
            'fgp_before': stats[k]['before']['fg'] / stats[k]['before']['fga'],
            'fgp_after': stats[k]['after']['fg'] / stats[k]['after']['fga'],
            'fgp_overall': (stats[k]['before']['fg'] + stats[k]['after']['fg'] + stats[k]['other']['fg']) / (stats[k]['before']['fga'] + stats[k]['after']['fga'] + stats[k]['other']['fga']),
            'fga_before': stats[k]['before']['fga'],
            'fga_after': stats[k]['after']['fga'],
            'fga_overall': stats[k]['before']['fga'] + stats[k]['after']['fga'] + stats[k]['other']['fga']
        })

with open("output.json", "w") as f:
    f.write(json.dumps(out, sort_keys=True, indent=4))
