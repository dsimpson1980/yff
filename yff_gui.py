from PySide import QtGui, QtCore
import sys
import pandas as pd
import webbrowser
import yql

from yahoo_tools import get_week, load_teams, get_stat_categories, get_token
from yahoo_tools import get_all_player_points
from data import config


class EnterCode(QtGui.QWidget):
    def __init__(self, auth_url):
        QtGui.QWidget.__init__(self)
        self.auth_url = auth_url

class MainWidget(QtGui.QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

class MonitorGUI(QtGui.QMainWindow):
    def __init__(self):
        super(MonitorGUI, self).__init__()
        self.setCentralWidget(MyWidget())

class MyWidget(QtGui.QWidget):
    def __init__(self):
        super(MyWidget, self).__init__()
        self.monitor_widget = MonitorWidget()
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.monitor_widget)
        self.setLayout(vbox)

class MonitorWidget(MainWidget):
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
        self.datatable = QtGui.QTableWidget(parent=self)
        self.datatable.setGeometry(0, 0, 1200, 600)
        self.teams = load_teams(self.week, self.enter_token, y3=self.y3)
        self.datatable.setColumnCount(len(self.teams))
        self.datatable.setRowCount(len(self.teams[0].players))
        team_names = []
        for col, team in enumerate(self.teams):
            team_names.append(team.name)
            for row, player in enumerate(team.players):
                self.datatable.setItem(row, col, QtGui.QTableWidgetItem(player.initial))
        self.datatable.setHorizontalHeaderLabels(team_names)
        positions = ['QB', 'WR', 'WR', 'RB', 'RB', 'TE', 'W/R/T', 'K', 'DEF']
        positions += ['BN'] * 6
        self.datatable.setVerticalHeaderLabels(positions)

    def enter_token(self, auth_url):
        text = '''<a href='%s'>%s</a> Enter Code:''' % (auth_url, auth_url)
        webbrowser.open(auth_url)
        verifier, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', text)
        return str(verifier) if ok else None

class PandasViewer(QtGui.QMainWindow):
    """Main window for the GUI"""

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.week = get_week()
        if self.week is None:
            self.week = 1
        consumer_key, consumer_secret = config.get_consumer_secret()
        self.y3 = yql.ThreeLegged(consumer_key, consumer_secret)
        self.token = get_token(self.y3)
        self.league_key = config.get_league_key()
        self.obj = load_teams(
            week=self.week, dialog=self.enter_token, y3=self.y3)
        self.stat_categories = get_stat_categories(
            self.y3, self.token, self.league_key)
        self.inv_stat_categories = {
            v: k for k, v in self.stat_categories.iteritems()}
        self.df = pd.DataFrame()
        self.displayed_df = pd.DataFrame()
        window = QtGui.QWidget()
        self.setCentralWidget(window)
        main_layout = QtGui.QVBoxLayout()
        window.setLayout(main_layout)
        splitter = QtGui.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QtGui.QWidget()
        left_layout = QtGui.QVBoxLayout()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        self.tree_widget = TreeWidget(self, obj=self.obj)
        self.tree_widget.selection_made.connect(self.dataframe_changed)
        left_layout.addWidget(self.tree_widget)
        self.df_viewer = DataFrameTableView(None)
        left_layout.addWidget(self.df_viewer)
        self.init_menu()
        self.change_stat()
        # self.refresh_timer = QtCore.QTimer()
        # self.refresh_timer.timeout.connect(self.test)
        # self.refresh_timer.start(10000)

    def test(self):
        player_points = get_all_player_points(
            self.y3, self.token, self.league_key)

    def dataframe_changed(self, df):
        """Set the dataframe in the dataframe viewer to df

        Parameters
        ----------
        df: pd.DataFrame
            The dataframe to set
        """
        self.df = df
        self.displayed_df = self.df
        self.df_viewer.set_dataframe(self.displayed_df)

    def init_menu(self):
        """Initiate the drop down menus for the window"""
        self.menubar = QtGui.QMenuBar(self)
        action_menu = QtGui.QMenu('Actions')
        self.menubar.addMenu(action_menu)
        self.refresh = QtGui.QAction(
            'Refresh', action_menu, shortcut=QtGui.QKeySequence.Refresh)
        self.refresh.triggered.connect(self.change_stat)
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
        for stat_id, name in self.stat_categories.iteritems():
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
            action.setChecked(action.text() == 'Week %s' % self.week)
        self.week_mapper.mapped['QString'].connect(self.change_week_menu)

    def change_week_menu(self, week_name):
        for action in self.week_menu.actions():
            action.setChecked(action.text() == week_name)
        week = week_name.split(' ')[1]
        if week != self.week:
            self.week = week
            #ToDo This needs to be sped up or run in the background in pieces
            self.obj, _ = load_teams(week=self.week,
                dialog=self.enter_token, get_proj_points=True, y3=self.y3)
        if self.df is not None:
            self.change_stat()

    def change_roster_menu(self, how):
        self.roster = how
        for action in self.roster_menu.actions():
            action.setChecked(action.text() == how)
        if self.df is not None:
            # self.dataframe_changed(self.df)
            self.change_stat()

    @staticmethod
    def action(*args, **kwargs):
        action = QtGui.QAction(*args, **kwargs)
        event = kwargs.pop('triggered', None)
        if event is not None:
            action.triggered.connect(event)
        return action

    def change_stat(self):
        import player
        df = player.df_from_teams(self.obj, self.player_mapper[self.roster])
        self.dataframe_changed(df)

    def reset_all(self):
        self.df = pd.DataFrame()
        self.displayed_df = pd.DataFrame()


def main():
    """Main method for the app"""
    app = QtGui.QApplication(sys.argv)
    pandas_viewer = MonitorGUI()
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()
