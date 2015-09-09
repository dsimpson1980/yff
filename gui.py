from PySide import QtGui, QtCore
import os
import sys
import pandas as pd
import numpy as np


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
        self.resize(500, 500)
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
        from yahoo_tools import load_players
        df = load_players()
        self.dataframe_changed(df)

    def change_freq(self, freq):
        """Resample the original pd.DataFrame to frequency freq

        Parameters
        ----------
        freq: str
            The frequency to resample the dataframe to
        """
        self.freq = freq
        for action in self.freq_submenu.actions():
            action.setChecked(action.text() == freq)
        if self.df is not None:
            self.dataframe_changed(self.df)

    def change_agg(self, how):
        """Change the method of aggregation/resample

        Parameters
        ----------
        how: str
            The method to use for resample parameter how
        """
        self.agg = how
        for action in self.agg_submenu.actions():
            action.setChecked(action.text() == how)
        if self.df is not None:
            self.dataframe_changed(self.df)

    def change_legend(self):
        """Set the visibility of the subplot legend to match the checked status
        of the submenu item.  The submenu item is checkable and as such changes
        state automatically when clicked
        """
        self.df_plot_viewer.legend.set_visible(self.legend_action.isChecked())
        self.df_plot_viewer.draw()

    def change_strip_zeros(self):
        """Strip the zeros from the displayed data"""
        self.dataframe_changed(self.df)

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
    pandas_viewer = PandasViewer()
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()