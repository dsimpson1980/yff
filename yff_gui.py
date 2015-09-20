from PySide import QtGui, QtCore
import sys
import pandas as pd

from yahoo_tools import load_players, get_week
import webbrowser


class EnterCode(QtGui.QWidget):
    def __init__(self, auth_url):
        QtGui.QWidget.__init__(self)
        self.auth_url = auth_url

class TreeWidgetItem(QtGui.QTreeWidgetItem):
    def __init__(self, *args):
        self.keys = args
        non_none_keys = [k for k in args if k is not None]
        key = [] if len(non_none_keys) == 0 else [str(non_none_keys[-1])]
        QtGui.QTreeWidgetItem.__init__(self, key)


class TreeWidget(QtGui.QTreeWidget):
    selection_made = QtCore.Signal((pd.DataFrame, ))

    def __init__(self, parent=None, obj=None):
        QtGui.QTreeWidget.__init__(self, parent)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setColumnCount(1)
        self.setHeaderLabel(None)
        self.header().close()
        self.set_tree(obj)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

    def set_tree(self, obj):
        self.clear()
        self.obj = obj
        root = self.invisibleRootItem()
        self.create_branch(root, obj)

    def create_branch(self, root, obj):
        if isinstance(obj, dict):
            for key, value in obj.iteritems():
                twig = TreeWidgetItem(key)
                root.addChild(twig)
                self.create_branch(twig, value)
        elif isinstance(obj, list):
            for n, value in enumerate(obj):
                twig = TreeWidgetItem(n)
                root.addChild(twig)
                self.create_branch(twig, value)
        else:
            leaf = TreeWidgetItem(obj)
            root.addChild(leaf)

    def selectionChanged(self, selected, deselected):
        pass


class DataFrameTableView(QtGui.QTableView):

    def __init__(self, df):
        """Initiate the TableView with pd.DataFrame df

        Parameters
        ----------
        df: pd.DataFrame
            The DataFrame to display in the TableView

        Returns
        -------
        DataFrameTableView
        """
        QtGui.QTableView.__init__(self)
        self.resize(1000, 500)
        if df is not None:
            self.set_dataframe(df)

    def set_dataframe(self, df):
        """Setter for the dataframe property

        Parameters
        ----------

        df: pd.DataFrame
            The pd.DataFrame to set the property
        """
        table_model = DataFrameTableModel(self, df)
        self.df = df
        self.setModel(table_model)
        self.resizeColumnsToContents()


class DataFrameTableModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, df):
        """Initiate the Table Model from a parent object, that should be a
        QtGui.QTableView and an initial pd.DataFrame, df

        Parameters
        ----------
        parent: QtGui.QTableView
            The parent object for the the instance
        df: pd.DataFrame
            The pd.DataFrame used to initialise the model

        Returns
        -------
        DataFrameTableModel
        """
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.df = df

    def rowCount(self, parent):
        """Returns the length of the DataFrame property of the parent object

        Parameters
        ----------
        parent: The parent object used to extract the DataFrame to measure

        Returns
        -------
        int
        """
        return len(self.df)

    def columnCount(self, parent):
        """Returns the number of columns in the DataFrame with a plus one for
        the index column

        Parameters
        ----------
        parent: The parent object used to extract the DataFrame to measure

        Returns
        -------
        int
        """
        return len(self.df.columns) + 1

    def data(self, index, role):
        """Used to extract the data from the DataFrame for the row and column
        specified in the index

        Parameters
        ----------
        index: QtCore.QModelIndex
            The index object to use to lookup data in the DataFrame
        role: int

        Returns
        -------
        str
        """
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            value = None
        else:
            col, row = index.column(), index.row()
            if col == 0:
                value = self.df.index[row]
            else:
                value = str(self.df.iloc[row, col-1])
        return value

    def headerData(self, idx, orientation, role):
        """Returns the column name of the dataframe at idx or 'Timestamp' if the
         idx = 0

        idx: int
            The integer index of the column header, 0 indicates the index
        orientation: QtCore.Qt.Orientation
            Indicates the orientation of the object, either QtCore.Qt.Horizontal
            or QtCore.Qt.Vertical
        role: int

        Returns
        -------
        str
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            value = 'Position' if idx == 0 else self.df.columns[idx-1]
        else:
            value = None
        return value


class PandasViewer(QtGui.QMainWindow):
    """Main window for the GUI"""

    def __init__(self, obj=None):
        """Initiate pandas viewer

        Parameters
        ----------
        obj: pd.Series, pd.DataFrame, pd.Panel, dict
            The obj to iterate through to allow selection

        Returns
        -------
        PandasViewer

        Examples
        --------
        # >>> timestamps = pd.date_range('1-Apr-14', '30-Apr-14')
        # >>> dataframe = pd.DataFrame(np.random.rand(len(timestamps), 2), index=timestamps)
        # >>> app = QtGui.QApplication(sys.argv)
        # >>> PandasViewer(dataframe) #doctest: +ELLIPSIS
        <viewer_gui.PandasViewer object at ...>
        """
        QtGui.QMainWindow.__init__(self)
        self.week = get_week()
        if self.week is None:
            self.week = 1
        if not obj:
            obj, stat_categories = load_players(week=self.week,
                dialog=self.enter_token, get_proj_points=True)
        if isinstance(obj, (pd.Series, pd.DataFrame, pd.Panel)):
            obj = {str(type(obj)): obj}
        self.stat_categories = stat_categories
        self.inv_stat_categories = {v: k for k, v in stat_categories.iteritems()}
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
        self.obj = obj
        self.tree_widget = TreeWidget(self, obj=obj)
        self.tree_widget.selection_made.connect(self.dataframe_changed)
        left_layout.addWidget(self.tree_widget)
        self.df_viewer = DataFrameTableView(None)
        left_layout.addWidget(self.df_viewer)
        self.init_menu()
        self.change_stat()

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
        for how, key in [('Full Name', 'F'), ('Initial', 'I'),
                         ('Bye Week', 'B'), ('Player Points', 'P'),
                         ('Proj Points', 'R')]:
            action = QtGui.QAction(
                how, self, checkable=True,
                shortcut=QtGui.QKeySequence('Ctrl+Shift+%s' % key))
            self.roster_mapper.setMapping(action, how)
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
        self.week = week_name.split(' ')[1]
        for action in self.week_menu.actions():
            action.setChecked(action.text() == week_name)
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
        def get_name_initial(x):
            if x['name']['last'] == None:
                return x['name']['first']
            else:
                return x['name']['first'][0] + '.' + x['name']['last']

        def get_name_full(x):
            return x['name']['full']

        def get_bye_week(x):
            return x['bye_weeks']['week']

        def get_player_points(x):
            return x['player_points']['total']

        def get_proj_points(x):
            return x['proj_points']

        def get_stat(x):
            stats = x['player_stats']['stats']['stat']
            stat = [stat['value'] for stat in stats if stat['stat_id'] == self.inv_stat_categories[self.roster]]
            stat = 'na' if len(stat) == 0 else stat[0]
            return stat
        mapper = {'Full Name': get_name_full, 'Initial': get_name_initial,
                  'Bye Week': get_bye_week, 'Player Points': get_player_points,
                  'Proj Points': get_proj_points}
        all_data = {}
        for name, row in self.obj.iteritems():
            data = row['roster']['players']['player']
            filtered_data = map(mapper.get(self.roster, get_stat), data)
            all_data[name] = filtered_data
        idx = map(lambda x: x['selected_position']['position'], data)
        df = pd.DataFrame(all_data, index=idx)
        self.dataframe_changed(df)

    def reset_all(self):
        self.df = pd.DataFrame()
        self.displayed_df = pd.DataFrame()

    def enter_token(self, auth_url):
        text = '''<a href='%s'>%s</a> Enter Code:''' % (auth_url, auth_url)
        webbrowser.open(auth_url)
        verifier, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', text)
        return str(verifier) if ok else None


def main():
    """Main method for the app"""
    app = QtGui.QApplication(sys.argv)
    pandas_viewer = PandasViewer()
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()