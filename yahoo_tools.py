import pandas as pd
import yql
from yql.storage import FileTokenStore
import os

def main(keyfile=None):
    load_players(keyfile)


def load_players(keyfile=None, week=1):
    if keyfile == None:
        keyfile = 'data'
    f = open(keyfile, "r")
    keys = f.read().split()
    f.close()

    if len(keys) != 3:
        raise RuntimeError('Incorrect number of keys found in ' + keyfile)

    consumer_key, consumer_secret, league_key = keys

    y3 = yql.ThreeLegged(consumer_key, consumer_secret)
    _cache_dir = os.path.expanduser('~/YahooFF')
    if not os.access(_cache_dir, os.R_OK):
        os.mkdir(_cache_dir)
    token_store = FileTokenStore(_cache_dir, secret='sasfasdfdasfdaf')
    stored_token = token_store.get('foo')
    if not stored_token:
        # Do the dance
        request_token, auth_url = y3.get_token_and_auth_url()
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
    all_data = {}

    def get_name(x):
        if x['last'] == None:
            return x['first']
        else:
            return x['first'][0] + '.' + x['last']
    for row in data_yql.rows:
        data = pd.DataFrame(row['roster']['players']['player'])
        filtered_data = map(get_name, data['name'])
        all_data[row['name']] = filtered_data
    idx = map(lambda x: x['position'], data['selected_position'])
    # player_id = lambda x: int(x['player_id'])
    # points = lambda x: float(x['player_points']['total'])
    # bye_week = lambda x: int(x['bye_weeks']['week'])
    # name = lambda x: x['name']['full']
    # stats = []
    # for team in xrange(1, 13):
    #     query = """SELECT *
    #                  FROM fantasysports.teams.roster.stats
    #                 WHERE team_key='%s.t.%s'
    #                   AND week=%s""" % (league_key, team, week)
    #     data_yql = y3.execute(query, token=token)
    #     data = data_yql.rows[0]['roster']['players']['player']
    #     stats.append(dict(map(lambda x: (player_id(x), dict(
    #         points=points(x), name=name(x), bye_week=bye_week(x))), data)))
    # print stats
    return pd.DataFrame(all_data, index=idx)

if __name__ == '__main__':
    main()
