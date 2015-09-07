import pandas as pd
import yql
from yql.storage import FileTokenStore
import os

def main(keyfile=None):
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
                  AND week=1""" % league_key
    data_yql = y3.execute(query, token=token)
    data = pd.DataFrame(data_yql.rows[0]['roster']['players']['player'])
    filtered_data = map(lambda x: (x[1]['selected_position']['position'], x[1]['name']['full']), data[['name', 'selected_position']].iterrows())
    for position, name in filtered_data:
        print position, name

if __name__ == '__main__':
    main()
