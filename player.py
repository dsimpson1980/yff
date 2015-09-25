import pandas as pd


class Player(object):
    def __init__(self, **kwargs):
        self._name = None
        self._player_points = None
        self.proj_points = None
        self._player_id = None
        for k, v in kwargs.iteritems():
            setattr(self, '_' + k, v)
        if hasattr(self, '_bye_weeks'):
            self.bye_week = int(self._bye_weeks['week'])
        if hasattr(self, '_player_points'):
            self.player_points = float(self._player_points['total'])
        if hasattr(self, '_selected_position'):
            self.selected_position = self._selected_position['position']
        if hasattr(self, '_name'):
            self.full_name = self._name['full']

    @property
    def name(self):
        return self._name

    def set_last_name(self, value):
        self._name['last'] = value

    @property
    def player_id(self):
        return self._player_id

    @property
    def initial(self):
        if self.name['last'] is None:
            result = self.name['full']
        else:
            result = self.name['first'][0] + '.' + self.name['last']
        return result

    def __repr__(self):
        return 'Player(%s)' % self.initial

class Team(object):
    def __init__(self, players, **kwargs):
        self.players = players
        self._name = None
        for k, v in kwargs.iteritems():
            setattr(self, '_' + k, v)
        self.bench = self.played = []
        for player in players:
            attr = self.bench if player.selected_position == 'BN' else self.played
            attr.append(player)

    def __repr__(self):
        return 'Team(%s)' % self._name

    @property
    def name(self):
        return self._name

    def proj_points(self):
        return sum([player.proj_points for player in self.played])

    def points(self):
        return sum([player.player_points for player in self.played])

def df_from_teams(teams, attr, with_initial=True):
    data = {}
    if with_initial and attr not in ['initial', 'full_name']:
        fn = lambda x: '%s %s' % (x.initial, getattr(x, attr))
    else:
        fn = lambda x: getattr(x, attr)
    for team in teams:
        data[team.name] = map(fn, team.players)
    df = pd.DataFrame(data)
    return df