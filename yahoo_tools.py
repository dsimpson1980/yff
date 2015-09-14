import pandas as pd
import yql
from yql.storage import FileTokenStore
import os
from PySide import QtGui

def main(keyfile=None):
    load_players(keyfile)


def load_players(keyfile=None, week=1, dialog=False):
    #ToDo Need to add dialog/popup to add initial consumer_key and secret
    #ToDo data file should be encrypted in some manner on the local machine
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
    return {row['name']: row for row in data_yql.rows}

if __name__ == '__main__':
    main()
