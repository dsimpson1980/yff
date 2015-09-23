import os
import datetime

import yql
from yql.storage import FileTokenStore
from dateutil.relativedelta import relativedelta, TH

from data import config
from projected_stats import get_all_points
from player import Player, Team, df_from_teams


start_date = datetime.datetime(2015, 9, 10)
week_dates = [(start_date + relativedelta(weeks=x)).date() for x in range(16)]

def get_week(date=None):
    """Get the week for the 2015 nfl season that date lies within.  If date is
    before or after the 16 week season None is returned

    Parameters
    ----------
    date: datetime.date
        The date to test for the nfl week

    Returns
    -------
    int, None
        The week number or None if the date is not in the 2015 nfl season

    >>> get_week(datetime.date(2015, 9, 15))
    1
    >>> get_week(datetime.date(2015, 9, 17))
    2
    >>> get_week(datetime.date(2015, 12, 30))
    16
    >>> get_week(datetime.date(2016, 1, 10))

    """
    if date is None:
        date = datetime.datetime.now().date()
    last_start = date + relativedelta(weekday=TH(-1))
    try:
        week_num = week_dates.index(last_start) + 1
    except ValueError:
        week_num = None
    return week_num

def load_players(week=1, dialog=False, get_proj_points=False):
    consumer_key, consumer_secret = config.get_consumer_secret()
    league_key = config.get_league_key()
    y3 = yql.ThreeLegged(consumer_key, consumer_secret)
    token = get_token(y3, dialog)
    stat_categories = get_stat_categories(y3, token, league_key)
    player_stats = get_player_stats_by_roster(y3, token, league_key, week, get_proj_points)
    return player_stats, stat_categories

def get_token(y3, dialog=False):
    _cache_dir = os.path.expanduser('~/YahooFF')
    if not os.access(_cache_dir, os.R_OK):
        os.mkdir(_cache_dir)
    token_store = FileTokenStore(_cache_dir, secret='sasfasdfdasfdaf')
    stored_token = token_store.get('foo')
    if not stored_token:
        request_token, auth_url = y3.get_token_and_auth_url()
        if dialog:
            verifier = dialog(auth_url)
        else:
            print "Visit url %s and get a verifier string" % auth_url
            verifier = raw_input("Enter the code: ")
        token = y3.get_access_token(request_token, verifier)
        token_store.set('foo', token)
    else:
        token = y3.check_token(stored_token)
        if token != stored_token:
            token_store.set('foo', token)
    return token

def get_player_stats_by_roster(y3, token, league_key, week, get_proj_points=True):
    if get_proj_points:
        proj_points = get_all_points()
    query = """SELECT *
                 FROM fantasysports.teams.roster
                WHERE league_key='%s'
                  AND week=%s""" % (league_key, week)
    data_yql = y3.execute(query, token=token)
    data = {row['name']: row for row in data_yql.rows}
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
    return data

def get_teams_stats(y3, token, league_key, num_teams=12):
    data = []
    for team in range(1, num_teams + 1):
        query = """SELECT *
                     FROM fantasysports.teams.roster.stats
                    WHERE team_key='%s.t.%s'""" % (league_key, team)
        data_yql = y3.execute(query, token=token, output='json')
        data.append(data_yql.rows[0])
    return data

def get_stat_categories(y3, token, league_key):
    query = """SELECT settings.stat_categories
                 FROM fantasysports.leagues.settings
                WHERE league_key='%s'""" % league_key
    data_yql = y3.execute(query, token=token)
    stat_categories = data_yql.rows[0]
    stat_categories = stat_categories['settings']['stat_categories']['stats']['stat']
    stat_categories = {x['stat_id']: x['name'] for x in stat_categories}
    return stat_categories

def load_teams(week=1, dialog=False, get_proj_points=False, y3=None):
    league_key = config.get_league_key()
    if y3 is None:
        y3 = get_y3()
    token = get_token(y3, dialog)
    stat_categories = get_stat_categories(y3, token, league_key)
    teams = construct_teams_and_players(y3, league_key)
    if get_proj_points:
        projected_stats = get_all_points()
        for team in teams:
            for player in team.players:
                player.proj_points = projected_stats.get(player.player_id, None)
    return teams, stat_categories

def get_y3():
    consumer_key, consumer_secret = config.get_consumer_secret()
    y3 = yql.ThreeLegged(consumer_key, consumer_secret)
    return y3

def construct_teams_and_players(y3, league_key):
    token = get_token(y3)
    teams_data = get_teams_stats(y3, token, league_key)
    teams = []
    for team in teams_data:
        players = []
        roster = team.pop('roster')
        for player in roster['players']['player']:
            player_stats = player.pop('player_stats')
            player_stats = player_stats['stats']['stat']
            player['stats'] = {d['stat_id']: d['value'] for d in player_stats}
            player = Player(**player)
            players.append(player)
        teams.append(Team(players, **team))
    return teams

if __name__ == '__main__':
    teams = construct_teams_and_players()
    print df_from_teams(teams, 'player_points')
