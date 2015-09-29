from PySide import QtGui, QtCore
import sys
import webbrowser
import yql

from yahoo_tools import get_week, load_teams, get_stat_categories, get_token
from yahoo_tools import get_all_player_points
from data import config


class EnterCode(QtGui.QWidget):
    def __init__(self, auth_url):
        QtGui.QWidget.__init__(self)
        self.auth_url = auth_url

class MonitorGUI(QtGui.QMainWindow):
    def __init__(self):
        super(MonitorGUI, self).__init__()
        self.setCentralWidget(MonitorWidget())
        self.init_menu()

    def init_menu(self):
        """Initiate the drop down menus for the window"""
        self.menubar = QtGui.QMenuBar(self)
        action_menu = QtGui.QMenu('Actions')
        self.menubar.addMenu(action_menu)
        self.refresh = QtGui.QAction(
            'Refresh', action_menu, shortcut=QtGui.QKeySequence.Refresh)
        # self.refresh.triggered.connect(self.change_stat)
        action_menu.addAction(self.refresh)
        self.setup_roster_menu()
        self.setup_week_menu()

    def setup_roster_menu(self):
        self.roster_menu = QtGui.QMenu('Roster')
        self.menubar.addMenu(self.roster_menu)
        self.roster_mapper = QtCore.QSignalMapper(self)
        self.player_mapper = {}
        data = [('Full Name', 'F', 'full_name'), ('Initial', 'I', 'initial'),
                ('Bye Week', 'B', 'bye_week'),
                ('Player Points', 'P', 'player_points'),
                ('Proj Points', 'R', 'proj_points')]
        for stat, shortcut, attr in data:
            self.player_mapper[stat] = attr
            action = QtGui.QAction(
                stat, self, checkable=True,
                shortcut=QtGui.QKeySequence('Ctrl+Shift+%s' % shortcut))
            self.roster_mapper.setMapping(action, stat)
            action.triggered.connect(self.roster_mapper.map)
            self.roster_menu.addAction(action)
        for stat_id, name in self.centralWidget().stat_categories.iteritems():
            action = QtGui.QAction(name, self, checkable=True)
            self.roster_mapper.setMapping(action, name)
            action.triggered.connect(self.roster_mapper.map)
            self.roster_menu.addAction(action)
        self.roster = 'Initial'
        for action in self.roster_menu.actions():
            action.setChecked(action.text() == self.roster)
        self.roster_mapper.mapped['QString'].connect(self.change_roster_menu)

    def setup_week_menu(self):
        self.week_menu = QtGui.QMenu('Week')
        self.menubar.addMenu(self.week_menu)
        self.week_mapper = QtCore.QSignalMapper(self)
        for week in range(1, 17):
            action = QtGui.QAction('Week %s' % week, self, checkable=True)
            self.week_mapper.setMapping(action, 'Week %s' % week)
            action.triggered.connect(self.week_mapper.map)
            self.week_menu.addAction(action)
        for action in self.week_menu.actions():
            action.setChecked(action.text() == 'Week %s' % self.centralWidget().week)
        self.week_mapper.mapped['QString'].connect(self.change_week_menu)

    def change_week_menu(self, week_name):
        for action in self.week_menu.actions():
            action.setChecked(action.text() == week_name)
        week = week_name.split(' ')[1]
        if week != self.centralWidget().week:
            self.centralWidget().week = week
            #ToDo This needs to be sped up or run in the background in pieces
            self.teams = load_teams(week=week,
                dialog=self.enter_token, get_proj_points=True, y3=self.y3)
        if self.df is not None:
            self.change_stat()

    def change_roster_menu(self, how):
        self.centralWidget().roster = self.player_mapper[how]
        for action in self.roster_menu.actions():
            action.setChecked(action.text() == how)
        self.change_stat(self.centralWidget().roster)

    @staticmethod
    def action(*args, **kwargs):
        action = QtGui.QAction(*args, **kwargs)
        event = kwargs.pop('triggered', None)
        if event is not None:
            action.triggered.connect(event)
        return action

    def change_stat(self, attr):
        for col, team in enumerate(self.centralWidget().teams):
            for row, player in enumerate(team.players):
                self.centralWidget().datatable.item(row, col).setText(
                    getattr(player, attr))

class MonitorWidget(QtGui.QWidget):
    def __init__(self):
        super(MonitorWidget, self).__init__()
        self.week = get_week()
        if self.week is None:
            self.week = 1
        consumer_key, consumer_secret = config.get_consumer_secret()
        self.y3 = yql.ThreeLegged(consumer_key, consumer_secret)
        self.token = get_token(self.y3)
        self.league_key = config.get_league_key()
        self.stat_categories = get_stat_categories(
            self.y3, self.token, self.league_key)
        self.roster = 'initial'
        self.teams = load_teams(self.week, self.enter_token, y3=self.y3)
        self.datatable = None
        self.initialise_table()
        self.refresh_rate = 10000
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_player_points)
        self.timer.start(self.refresh_rate)

    def update_player_points(self):
        """Fetch the player_points for all players and update the Player objects
        If player_points is currently be viewed then the table is updated
        """
        player_points = get_all_player_points(self.y3, self.token, self.league_key)
        for team in self.teams:
            for player in team.players:
                player.set_player_points(player_points[player.player_id])
        if self.roster == 'player_points':
            self.update_table()

    def initialise_table(self, attr='initial'):
        """Initialise the self.datatable object and populate with the default
        attribute attr from each player

        Parameters
        ----------
        attr: str
            The attr to use for the initial population of the table.  Defaults
            to 'initial'
        """
        self.datatable = QtGui.QTableWidget(parent=self)
        self.datatable.setGeometry(0, 0, 1400, 600)
        self.datatable.setColumnCount(len(self.teams))
        self.datatable.setRowCount(len(self.teams[0].players))
        team_names = []
        for col, team in enumerate(self.teams):
            team_names.append(team.name)
            for row, player in enumerate(team.players):
                self.datatable.setItem(
                    row, col, QtGui.QTableWidgetItem(getattr(player, attr)))
        self.datatable.setHorizontalHeaderLabels(team_names)
        positions = ['QB', 'WR', 'WR', 'RB', 'RB', 'TE', 'W/R/T', 'K', 'DEF']
        positions += ['BN'] * 6
        self.datatable.setVerticalHeaderLabels(positions)

    def update_table(self):
        """Check if the any of the values in the datatable have changed in
        comparison to self.teams and the player attribute set in self.roster.
        If a cell value has changed then the cell is highlighted for the
        default amount of time
        """
        for col, team in enumerate(self.teams):
            for row, player in enumerate(team.players):
                value = getattr(player, self.roster)
                if self.datatable.item(row, col).text() != value:
                    self.highlightCell(row, col, value=value)

    def highlightCell(self, row, col, timelimit=3000, color='red', value=None):
        """Highlight the cell background in the color specified.  After the
        timelimit the cell background is set to white

        Parameters
        ----------
        row: int
            The row indexed from 0 for the datatable
        col: int
            The column indexed from 0 for the datatable
        timelimit: int
            The time in milliseconds before the cell background is set to white.
            Defaults to 3000
        color: str
            The color the cell is to be highlighted.  Must be acceptable by
            QtCore.QColor().  Defaults to 'red'.
        value: str, int
            If set the text of the cell will be set to value.  Defaults to None.
        """
        cell = self.datatable.item(row, col)
        if value is not None:
            cell.setText(value)
        cell.setBackground(QtGui.QColor(color))
        timer = QtCore.QTimer()
        timer.singleShot(timelimit,
                         lambda: cell.setBackground(QtGui.QColor('white')))

    def enter_token(self, auth_url):
        text = '''<a href='%s'>%s</a> Enter Code:''' % (auth_url, auth_url)
        webbrowser.open(auth_url)
        verifier, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', text)
        return str(verifier) if ok else None

def main():
    """Main method for the app"""
    app = QtGui.QApplication(sys.argv)
    pandas_viewer = MonitorGUI()
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()
