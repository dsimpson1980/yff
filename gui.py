from PySide import QtGui, QtCore
import sys
import pandas as pd

from yahoo_tools import load_players


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
        self.setHeaderLabels()
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
        if not obj: obj = {}
        QtGui.QMainWindow.__init__(self)
        if isinstance(obj, (pd.Series, pd.DataFrame, pd.Panel)):
            obj = {str(type(obj)): obj}
        self.freq = None
        self.agg = None
        self.filepath = None
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
        self.load_players()
        self.init_menu()

    def dataframe_changed(self, df):
        """Set the dataframe in the dataframe viewer to df

        Parameters
        ----------
        df: pd.DataFrame
            The dataframe to set
        """
        self.df = df
        self.displayed_df = self.df if self.freq is None else self.df.resample(
            self.freq, how=self.agg)
        self.df_viewer.set_dataframe(self.displayed_df)

    def init_menu(self):
        """Initiate the drop down menus for the window"""
        menubar = QtGui.QMenuBar(self)
        action_menu = QtGui.QMenu('Actions')
        menubar.addMenu(action_menu)
        self.refresh = QtGui.QAction(
            'Refresh', action_menu, shortcut=QtGui.QKeySequence.Refresh)
        self.refresh.triggered.connect(self.load_players)
        action_menu.addAction(self.refresh)

    @staticmethod
    def action(*args, **kwargs):
        action = QtGui.QAction(*args, **kwargs)
        event = kwargs.pop('triggered', None)
        if event is not None:
            action.triggered.connect(event)
        return action

    def load_players(self):
        df = load_players()
        self.dataframe_changed(df)

    def reset_all(self):
        [action.setChecked(False) for action in self.freq_submenu.actions()]
        [action.setChecked(False) for action in self.agg_submenu.actions()]
        self.legend_action.setChecked(True)
        self.freq = None
        self.agg = None
        self.df = pd.DataFrame()
        self.displayed_df = pd.DataFrame()


def main():
    """Main method for the app"""
    app = QtGui.QApplication(sys.argv)
    d = {'toplevel%s' % x:
             {'middlelevel%s' % y:
                  {'bottomlevel%s' % z: z
                   for z in range(3)} for y in range(4)} for x in range(5)}
    d = load_players('data', raw=True)
    pandas_viewer = PandasViewer(d)
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()