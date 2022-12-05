# -*- coding: utf-8 -*-

import os
import h5py

from qtpy import API_NAME

from qtpy.QtCore import (
    Qt,
    QRect,
    QSettings,
)

from qtpy.QtGui import (
    QIcon,
    QKeySequence,
)

from qtpy.QtWidgets import (
    QAction,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
)

from .views import HDF5Widget
from . import __version__

WINDOW_TITLE = 'HDF5View'
MAX_RECENT_FILES = 10


class MainWindow(QMainWindow):

    def __init__(self, app):
        super().__init__()

        self.recent_file_actions = []

        self.setAcceptDrops(True)

        self.app = app
        self.setWindowTitle(WINDOW_TITLE)

        self.init_actions()
        self.init_menus()
        self.init_toolbars()
        self.init_statusbar()
        self.init_dock_widgets()
        self.init_central_widget()

        self.load_settings()
        self.update_file_menus()

    def init_actions(self):
        """
        Initialise actions
        """
        self.open_action = QAction(
            QIcon('icons:folder-open.svg'),
            '&Open...',
            self,
            shortcut=QKeySequence.Open,
            statusTip='Open file',
            triggered=self.handle_open_file,
        )

        for i in range(MAX_RECENT_FILES):
            self.recent_file_actions.append(
                QAction(
                    self,
                    visible=False,
                    triggered=self.handle_open_recent_file,
                )
            )

        self.close_action = QAction(
            '&Close',
            self,
            shortcut=QKeySequence.Close,
            statusTip='Close file',
            triggered=self.handle_close_file,
        )
        self.close_action.setEnabled(False)

        self.close_all_action = QAction(
            'Close &All',
            self,
            statusTip='Close all files',
            triggered=self.handle_close_all_files,
        )
        self.close_all_action.setEnabled(False)

        self.quit_action = QAction(
            '&Quit',
            self,
            shortcut=QKeySequence.Quit,
            statusTip='Exit application',
            triggered=self.close,
        )

        self.prefs_action = QAction(
            '&Preferences...',
            self,
            shortcut=QKeySequence.Preferences,
            statusTip='Preferences',
            triggered=self.handle_open_prefs,
        )

        self.about_action = QAction(
            '&About...',
            self,
            statusTip='About',
            triggered=self.handle_open_about,
        )

        #
        # Plot/image actions
        #

        self.add_image_action = QAction(
            QIcon('icons:image.svg'),
            'Add &Image',
            self,
            statusTip='Add image',
            triggered=self.handle_add_image,
        )

        self.add_plot_action = QAction(
            QIcon('icons:plot.svg'),
            'Add &Plot',
            self,
            statusTip='Add plot',
            triggered=self.handle_add_plot,
        )
        self.add_plot_action.setEnabled(False)

    def init_menus(self):
        """
        Initialise menus
        """
        menu = self.menuBar()

        # File menu
        self.file_menu = menu.addMenu('&File')
        self.file_menu.addAction(self.open_action)

        # Add recent file submenu and items
        self.recent_menu = self.file_menu.addMenu('&Recent')

        for action in self.recent_file_actions:
            self.recent_menu.addAction(action)

        self.file_menu.addSeparator()
        self.file_menu.addAction(self.close_action)
        self.file_menu.addAction(self.close_all_action)

        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_action)

        # Edit menu - TODO
        # self.edit_menu = menu.addMenu('&Edit')
        # self.edit_menu.addAction(self.prefs_action)

        # View menu
        self.view_menu = menu.addMenu('&View')

        # Help menu
        self.help_menu = menu.addMenu('&Help')
        self.help_menu.addAction(self.about_action)

    def init_toolbars(self):
        """
        Initialise the toobars
        """
        self.file_toolbar = self.addToolBar('File')
        self.file_toolbar.setObjectName('file_toolbar')
        self.file_toolbar.addAction(self.open_action)

        self.plots_toolbar = self.addToolBar('Plots')
        self.plots_toolbar.setObjectName('plots_toolbar')
        self.plots_toolbar.addAction(self.add_image_action)
        self.plots_toolbar.addAction(self.add_plot_action)

        self.plots_toolbar.setEnabled(False)

    def init_statusbar(self):
        """
        Initialise statusbar
        """
        self.status = self.statusBar()

    def init_dock_widgets(self):
        """
        Initialise the doc widgets
        """
        MIN_DOCK_WIDTH = 240

        self.tree_dock = QDockWidget('File structure', self)
        self.tree_dock.setObjectName('tree_dock')
        self.tree_dock.setMinimumWidth(MIN_DOCK_WIDTH)

        self.attrs_dock = QDockWidget('Attributes', self)
        self.attrs_dock.setObjectName('attrs_dock')
        self.attrs_dock.setMinimumWidth(MIN_DOCK_WIDTH)

        self.dataset_dock = QDockWidget('Dataset', self)
        self.dataset_dock.setObjectName('dataset_dock')
        self.dataset_dock.setMinimumWidth(MIN_DOCK_WIDTH)

        self.dims_dock = QDockWidget('Slice', self)
        self.dims_dock.setObjectName('dims_dock')
        self.dims_dock.setMinimumWidth(MIN_DOCK_WIDTH)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.attrs_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dataset_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dims_dock)

        self.view_menu.addActions([
            self.tree_dock.toggleViewAction(),
            self.attrs_dock.toggleViewAction(),
            self.dataset_dock.toggleViewAction(),
            self.dims_dock.toggleViewAction(),
        ])

    def init_central_widget(self):
        """
        Initialise the central widget
        """
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.handle_close_file)
        self.tabs.currentChanged.connect(self.handle_tab_changed)

        self.setCentralWidget(self.tabs)

    def open_file(self, filename):
        """
        Open a hdf5 file
        """
        try:
            hdf = h5py.File(filename, 'r')
        except OSError as e:
            hdf = None
            QMessageBox.critical(
                self,
                'File loading error',
                '<p>{}</p><p>{}</p>'.format(e, filename)
            )

        # Remove filename to recent files. If it is valid
        # it gets added back at the top of the list.
        if filename in self.recent_files:
            self.recent_files.remove(filename)

        if hdf:
            # Add filename to top of recent files list
            self.recent_files.insert(0, filename)

            # ensure not more than MAX_RECENT_FILES are kept:
            if len(self.recent_files) > MAX_RECENT_FILES:
                self.recent_files = self.recent_files[:MAX_RECENT_FILES]

            # Create a new widget and tab for the file
            # and select it.
            hdf_widget = HDF5Widget(hdf)
            hdf_widget.tree_view.selectionModel().selectionChanged.connect(self.handle_tree_selection_changed)

            index = self.tabs.addTab(hdf_widget, os.path.basename(filename))
            self.tabs.setCurrentIndex(index)

        self.update_file_menus()

    def load_settings(self):
        """
        Load application settings from settings file
        """
        settings = QSettings()

        # Restore the window geometry
        geometry = settings.value('geometry')

        if geometry and not geometry.isEmpty():
            self.restoreGeometry(geometry)
        else:
            if API_NAME in ["PyQt6", "PySide6"]:
                geometry = self.app.screens()[0].availableGeometry()
            else:
                geometry = self.app.desktop().availableGeometry(self)
            self.setGeometry(QRect(0,
                                   0,
                                   int(geometry.width() * 0.8),
                                   int(geometry.height() * 0.7)))

        # Restore the window state
        window_state = settings.value('windowState')

        if window_state and not window_state.isEmpty():
            self.restoreState(window_state)

        # Load the recent files list
        self.recent_files = settings.value('recentFiles') or []
        if isinstance(self.recent_files, str):
            self.recent_files = [self.recent_files]

    def save_settings(self):
        """
        Save applications settings to file
        """
        settings = QSettings()

        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('windowState', self.saveState())
        settings.setValue('recentFiles', self.recent_files)

    def get_dropped_files(self, event):
        """
        Get a list of files dropped onto the application
        """
        return [url.toLocalFile() for url in event.mimeData().urls() if os.path.isfile(url.toLocalFile())]

    def update_file_menus(self):
        """
        Update the files menus, enabling/disabling options
        """
        count = self.tabs.count()
        self.close_action.setEnabled(count > 0)
        self.close_all_action.setEnabled(count > 1)

        for index, filename in enumerate(self.recent_files):
            action = self.recent_file_actions[index]
            action.setText(filename)
            action.setVisible(True)

    #
    # Slots
    #

    def handle_tab_changed(self, index):
        """
        Handle the tab changing and set the
        views doc views appropriately.
        """
        title = WINDOW_TITLE

        hdf5widget = self.tabs.currentWidget()

        if hdf5widget:
            title = '{} - {}'.format(title, hdf5widget.hdf.filename)

            self.tree_dock.setWidget(hdf5widget.tree_view)
            self.attrs_dock.setWidget(hdf5widget.attrs_view)
            self.dataset_dock.setWidget(hdf5widget.dataset_view)
            self.dims_dock.setWidget(hdf5widget.dims_view)
        else:
            self.tree_dock.setWidget(None)
            self.attrs_dock.setWidget(None)
            self.dataset_dock.setWidget(None)
            self.dims_dock.setWidget(None)

        self.setWindowTitle(title)
        self.tabs.setMovable(bool(self.tabs.count() > 1))

        # Enable/disable the plots toolbar
        self.handle_tree_selection_changed()

    def handle_open_file(self):
        """
        Open a file
        """
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self,
            'QFileDialog.getOpenFileName()',
            '',
            'HDF5 Files (*.hdf *.h5 *.hdf5);; All Files (*.*)',
            options=options
        )

        if filename:
            self.open_file(filename)

    def handle_open_recent_file(self):
        """
        Open a file from the recent files list
        """
        self.open_file(self.sender().text())

    def handle_close_file(self, index=None):
        """
        Close a file
        """
        if index is None:
            index = self.tabs.currentIndex()

        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)

        # TODO: Clean up/close file
        # widget.close_file()
        widget.deleteLater()

        # Update the close/close all menu items
        self.update_file_menus()

    def handle_close_all_files(self):
        """
        Close all open files
        """
        count = self.tabs.count()
        for index in reversed(range(count)):
            self.handle_close_file(index)

    def handle_open_prefs(self):
        """
        Show the prefs dialog
        """
        QMessageBox.information(
            self,
            'Preferences',
            '<p>TODO...</p>'
        )

    def handle_open_about(self):
        """
        Show the about dialog
        """
        QMessageBox.about(
            self,
            'About {}'.format(WINDOW_TITLE),
            (
                '<p>HDF5View {version}</p>'
                '<p>Copyright(c) 2019 - Martin Swarbrick</p>'
            ).format(version=__version__)
        )

    def handle_tree_selection_changed(self):
        """
        Enable/disable the plots toolbar when
        the tree selection changes.
        """
        self.plots_toolbar.setEnabled(False)

        hdf5widget = self.tabs.currentWidget()

        if not hdf5widget:
            return

        indexes = hdf5widget.tree_view.selectedIndexes()

        if not indexes:
            return

        index = indexes[0]
        path = hdf5widget.tree_model.itemFromIndex(index).data(Qt.UserRole)
        obj = hdf5widget.hdf[path]
        self.plots_toolbar.setEnabled(isinstance(obj, h5py.Dataset))

    def handle_add_image(self):
        """
        Display an image window
        """
        hdf5widget = self.tabs.currentWidget()
        hdf5widget.add_image()

    def handle_add_plot(self):
        """
        Display a plot window
        """
        pass

    #
    # Events
    #

    def dragEnterEvent(self, event):
        """
        Accept any of the dropped files?
        """
        event.accept() if self.get_dropped_files(event) else event.ignore()

    def dropEvent(self, event):
        """
        Open dropped files
        """
        for file in self.get_dropped_files(event):
            self.open_file(file)

    def closeEvent(self, event):
        """
        The application is closing so tidy up
        """
        self.handle_close_all_files()
        self.save_settings()
        super().closeEvent(event)
