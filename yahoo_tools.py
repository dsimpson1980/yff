import os
import datetime

import yql
from yql.storage import FileTokenStore
from dateutil.relativedelta import relativedelta, TH

from data import config
from projected_stats import get_all_points
from player import Player, Team


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

def get_token(y3, dialog=None):
    """Check if there is a cached token and if so retrieve it else ask the user
    for a new token using dialog.

    The cached token is stored in ~/YahooFF/

    Parameters
    ----------
    y3:
    dialog:

    Returns
    -------
    yql.YahooToken
        Either the cached token or a newly requested token
    """
    _cache_dir = os.path.expanduser('~/YahooFF')
    if not os.access(_cache_dir, os.R_OK):
        os.mkdir(_cache_dir)
    token_store = FileTokenStore(_cache_dir, secret='sasfasdfdasfdaf')
    stored_token = token_store.get('foo')
    if not stored_token:
        request_token, auth_url = y3.get_token_and_auth_url()
        if dialog is not None:
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

def get_teams_stats(y3, token, league_key, week, num_teams=12):
    """Query the y3 connection and retunr the player stats data as a list of
    dicts

    Parameters
    ----------
    y3: yql.ThreeLegged
        The connection to use to query teams and player data
    token: yql.YahooToken
        Tooken to use to secure y3
    league_key: str
        The league_key to use in the query in the form XXX.l.XXXX
    week: int
        The week to query for player stats
    num_teams: int
        The number of teams in the league.  Defaults to 12.

    Returns
    -------
    list
        the list of the raw data returned from the query in json format/list of
        dicts
    """
    data = []
    for team in range(1, num_teams + 1):
        query = """SELECT *
                     FROM fantasysports.teams.roster.stats
                    WHERE team_key='%s.t.%s'""" % (league_key, team)
        data_yql = y3.execute(query, token=token, output='json')
        data.append(data_yql.rows[0])
    return data

def get_stat_categories(y3, token, league_key):
    """Return the stat_categories for the nfl league, a dict mapping stat_id to
    stat description

    Parameters
    ----------
    y3: yql.ThreeLegged
        The connection to use for the yql query
    token: yql.YahooToken
        The token used to secure the y3 connection
    league_key: str
        The league_key to use for the query in the form XXX.l.XXXX

    Returns
    -------
    dict
        The dict mapping stat_id to stat description.  Keys are unicode strings
        as are values
    """
    query = """SELECT settings.stat_categories
                 FROM fantasysports.leagues.settings
                WHERE league_key='%s'""" % league_key
    data_yql = y3.execute(query, token=token)
    stat_categories = data_yql.rows[0]
    stat_categories = stat_categories['settings']['stat_categories']['stats']['stat']
    stat_categories = {x['stat_id']: x['name'] for x in stat_categories}
    return stat_categories

def load_teams(week=None, dialog=None, get_proj_points=False, y3=None):
    """Queries yql and created a list of Team objects containing a list of
    player objects

    Parameters
    ----------
    week: int
        The week to query.  Defaults to None
    dialog: method
         Method returning a token, defaults to None
    get_proj_points: bool
        If set to True calls get_all_points and appends proj_points to all
        player objects.  Defaults to False
    y3: yql.ThreeLegged
        The oauth connection to use for queries.  If None then get_y3() will be
        called.  Defaults to None

    Returns
    -------
    list[team]
        A list of the team objects that were created by the yql query
    """
    league_key = config.get_league_key()
    if y3 is None:
        y3 = get_y3()
    token = get_token(y3, dialog)
    teams = construct_teams_and_players(y3, token, league_key, week)
    if get_proj_points:
        projected_stats = get_all_points()
        for team in teams:
            for player in team.players:
                player.proj_points = projected_stats.get(player.player_id, None)
    return teams

def get_y3():
    """Return an oauth connection from yql using consumer_key and
    consumer_secret that is either cached or requested from the user

    Parameters
    ----------
    None

    Returns
    -------
    yql.ThreeLegged
    """
    consumer_key, consumer_secret = config.get_consumer_secret()
    y3 = yql.ThreeLegged(consumer_key, consumer_secret)
    return y3

def get_all_player_points(y3, token, league_key, num_teams=12):
    """Queries the y3 connection to return a dict of player_id and player_points
    for use in updating player objects

    Parameters
    ----------
    y3: yql.ThreeLegged
        The yql connection
    token: yql.YahooToken
        The token used to secure y3
    league_key: str
        The league_key to query in the form XXX.l.XXXX
    num_teams: int
        The number of teams in the league.  Defaults to 12

    Returns
    -------
    dict
        The dict of player_id and player_points
    """
    player_points = {}
    for team in range(1, num_teams + 1):
        query = """SELECT roster.players.player
                     FROM fantasysports.teams.roster.stats
                    WHERE team_key='%s.t.%s'""" % (league_key, team)
        data_yql = y3.execute(query, token=token).rows
        for player in data_yql:
            player = player['roster']['players']['player']
            player_points[player['player_id']] = player['player_points']['total']
    return player_points

def get_matchup_points(y3, token, league_key):
    """Extract points and projected points from each of the matchups in
     fantasysports.leagues.scoreboard

    Parameters
    ----------
    y3: yql.ThreeLegged
        The active connection for yql queries
    token: yql.YahooToken
        The token used for the y3 connection
    league_key: str
        The league key in the form XXX.l.XXXX

    Returns
    -------
    list(list(dict))
        A list with length the number of matchups in the league = num_teams /2
        Each sublist is the first and second team.  Each dict is the team name,
        points, and projected_points
    """
    query = """SELECT *
                 FROM fantasysports.leagues.scoreboard
                WHERE league_key = '%s'""" % league_key
    data_yql = y3.execute(query, token=token).rows[0]
    matchups = data_yql['scoreboard']['matchups']['matchup']

    def extract_matchup(team):
        """Extract dict consisting of team name, points and projected points

        Parameters
        ----------
        team: dict
            The team dict extracted from matchup in yahoo

        Returns
        -------
        dict:
            dict of name, points, and projected_points
        """
        result = dict(name=team['name'])
        result['points'] = team['team_points']['total']
        result['projected_points'] = team['team_projected_points']['total']
        return result
    matchups = [[extract_matchup(t) for t in m['teams']['team']] for m in matchups]
    return matchups

def construct_teams_and_players(y3, token, league_key, week):
    """Construct a list of Team objects from querying y3 using get_team_stats

    Parameters
    ----------
    y3: yql.ThreeLegged
        The connection to use to query teams and player data
    token: yql.YahooToken
        Tooken to use to secure y3
    league_key: str
        The league_key to use in the query in the form XXX.l.XXXX
    week: int
        The week to query for player stats

    Returns
    -------
    list[Team]
        The list of Team objects constructed from the query data
    """
    teams_data = get_teams_stats(y3, token, league_key, week)
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
