import yql
from yql.storage import FileTokenStore
import os
import yaml


def get_yaml_data(filename='data.yaml', *args):
    with open(filename, 'r') as f:
        y = yaml.load(f)
    return tuple([y[arg] for arg in args]) if len(args) > 1 else y[args[0]]

def get_consumer_secret(filename='data.yaml'):
    return get_yaml_data(filename, 'consumer', 'secret')

def get_league_number(filename='data.yaml'):
    return get_yaml_data(filename, 'league_number')

def get_league_key(filename='data.yaml'):
    data = get_yaml_data(filename, 'league', 'league_number')
    return '%s.l.%s' % data

def main(keyfile=None):
    load_players(keyfile)


def load_players(keyfile=None, week=1, dialog=False, stats=False):
    #ToDo Need to add dialog/popup to add initial consumer_key and secret
    #ToDo data file should be encrypted in some manner on the local machine
    if keyfile == None:
        keyfile = 'data.yaml'
    consumer_key, consumer_secret = get_consumer_secret(keyfile)
    league_key = get_league_key(keyfile)

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
    return data, stat_categories

if __name__ == '__main__':
    main()
