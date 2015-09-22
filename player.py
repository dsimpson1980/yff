import pandas as pd


class Player(object):
    def __init__(self, **kwargs):
        self._name = None
        self._player_points = None
        for k, v in kwargs.iteritems():
            setattr(self, '_' + k, v)
        if hasattr(self, '_bye_weeks'):
            self.bye_week = int(self._bye_weeks['week'])
        if hasattr(self, '_player_points'):
            self.player_points = float(self._player_points['total'])
        if hasattr(self, '_selected_position'):
            self.selected_position = self._selected_position['position']

    @property
    def name(self):
        return self._name

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

def df_from_teams(teams, attr):
    data = {}
    for team in teams:
        data[team.name] = [getattr(player, attr) for player in team.players]
    df = pd.DataFrame(data)
    return df