import os

import yql
from yql.storage import FileTokenStore

from data.extract import get_consumer_secret, get_league_key
from projected_stats import get_all_points

def load_players(keyfile=None, week=1, dialog=False, get_proj_points=False):
    #ToDo Need to add dialog/popup to add initial consumer_key and secret
    #ToDo data file should be encrypted in some manner on the local machine
    args = [] if keyfile is None else [keyfile]
    consumer_key, consumer_secret = get_consumer_secret(*args)
    league_key = get_league_key(*args)

    y3 = yql.ThreeLegged(consumer_key, consumer_secret)
    _cache_dir = os.path.expanduser('~/YahooFF')
    if not os.access(_cache_dir, os.R_OK):
        os.mkdir(_cache_dir)
    token_store = FileTokenStore(_cache_dir, secret='sasfasdfdasfdaf')
    stored_token = token_store.get('foo')
    if not stored_token:
        # Do the dance
        request_token, auth_url = y3.get_token_and_auth_url()
        if dialog:
            verifier = dialog(auth_url)
        else:
            print "Visit url %s and get a verifier string" % auth_url
            verifier = raw_input("Enter the code: ")
        token = y3.get_access_token(request_token, verifier)
        token_store.set('foo', token)
    else:
        # Check access_token is within 1hour-old and if not refresh it
        # and stash it
        token = y3.check_token(stored_token)
        if token != stored_token:
            token_store.set('foo', token)
    query = """SELECT *
                 FROM fantasysports.teams.roster
                WHERE league_key='%s'
                  AND week=%s""" % (league_key, week)
    data_yql = y3.execute(query, token=token)
    data = {row['name']: row for row in data_yql.rows}
    query = """SELECT settings.stat_categories
                 FROM fantasysports.leagues.settings
                WHERE league_key='%s'""" % league_key
    data_yql = y3.execute(query, token=token)
    stat_categories = data_yql.rows[0]
    stat_categories = stat_categories['settings']['stat_categories']['stats']['stat']
    stat_categories = {x['stat_id']: x['name'] for x in stat_categories}
    if get_proj_points:
        proj_points = get_all_points()
    for team in range(1, 13):
        query = """SELECT name, roster.players.player
                     FROM fantasysports.teams.roster.stats
                    WHERE team_key='%s.t.%s'
                      AND week=%s""" % (league_key, team, week)
        data_yql = y3.execute(query, token=token).rows
        name = data_yql[0]['name']
        for n, player in enumerate(data[name]['roster']['players']['player']):
            for k in ['player_stats', 'player_points']:
                player[k] = data_yql[n]['roster']['players']['player'][k]
            if get_proj_points:
                player['proj_points'] = proj_points[team - 1][n]
    return data, stat_categories
