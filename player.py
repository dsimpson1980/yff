class Player(object):
    def __init__(self, **kwargs):
        self._name = None
        for k, v in kwargs.iteritems():
            setattr(self, '_' + k, v)
        if hasattr(self, '_bye_weeks'):
            self.bye_week = self._bye_weeks['week']

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
        self.name = None
        for k, v in kwargs.iteritems():
            setattr(self, '_' + k, v)
        self.bench = [player_id for player_id, data in players
                      if data['position'] == 'BN']
        self.played = [player_id for player_id, data in players
                      if data['position'] != 'BN']

    def __repr__(self):
        return 'Team(%s)' % self.name
