# -*- coding: utf-8 -*-

from qtpy.QtCore import (
    Qt,
)

from qtpy.QtGui import (
    QKeySequence,
)

from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QHeaderView,
    QLabel,
    QMainWindow,
    QScrollBar,
    QTableView,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from .models import (
    AttributesTableModel,
    DataTableModel,
    DatasetTableModel,
    DimsTableModel,
    TreeModel,
)

import pyqtgraph as pg


class HDF5Widget(QWidget):
    """
    Main HDF5 view container widget
    """

    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf

        self.image_views = []

        # Initialise the models
        self.tree_model = TreeModel(self.hdf)
        self.attrs_model = AttributesTableModel(self.hdf)
        self.dataset_model = DatasetTableModel(self.hdf)
        self.dims_model = DimsTableModel(self.hdf)
        self.data_model = DataTableModel(self.hdf)

        # Set up the main file tree view
        self.tree_view = QTreeView(headerHidden=False)
        self.tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_view.setModel(self.tree_model)

        self.tree_view.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree_view.header().resizeSection(0, 160)
        self.tree_view.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree_view.header().setStretchLastSection(True)

        # Setup attributes table view
        self.attrs_view = QTableView()
        self.attrs_view.setModel(self.attrs_model)
        self.attrs_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attrs_view.horizontalHeader().setStretchLastSection(True)
        self.attrs_view.verticalHeader().hide()

        # Setup dataset table view
        self.dataset_view = QTableView()
        self.dataset_view.setModel(self.dataset_model)
        self.dataset_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dataset_view.horizontalHeader().setStretchLastSection(True)
        self.dataset_view.verticalHeader().hide()

        # Setup attributes table view
        self.dims_view = QTableView()

        self.dims_view.setModel(self.dims_model)
        self.dims_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dims_view.horizontalHeader().setStretchLastSection(True)
        self.dims_view.verticalHeader().hide()

        # Setup main data table view
        self.data_view = QTableView()
        self.data_view.setModel(self.data_model)

        # Create the main layout. All the other
        # associated table views are placed in
        # surrounding dock widgets.
        layout = QVBoxLayout()
        layout.addWidget(self.data_view)
        self.setLayout(layout)

        # Finally, initialise the signals for the view
        self.init_signals()

    def init_signals(self):
        """
        Initialise the view signals
        """
        # Update the table views when a tree node is selected
        self.tree_view.selectionModel().selectionChanged.connect(self.handle_selection_changed)

        # Dynamically populate more of the tree items when
        # selected to keep memory usage at a minimum.
        self.tree_view.expanded.connect(self.tree_model.handle_expanded)
        self.tree_view.collapsed.connect(self.tree_model.handle_collapsed)

        self.dims_model.dataChanged.connect(self.handle_dims_data_changed)

    def close_file(self):
        """
        Close the hdf5 file and clean up
        """
        for view in self.image_views:
            view.close()
        self.hdf.close()

    #
    # Slots
    #

    def handle_dims_data_changed(self, topLeft, bottomRight, roles):
        """
        Set the dimensions to display in the table
        """
        self.data_model.set_dims(self.dims_model.shape)

    def handle_selection_changed(self, selected, deselected):
        """
        When selection changes on the tree view
        update the node path on the models and
        refresh the data in the associated table
        views.
        """
        index = selected.indexes()[0]

        path = self.tree_model.itemFromIndex(index).data(Qt.UserRole)

        self.attrs_model.update_node(path)
        self.attrs_view.scrollToTop()

        self.dataset_model.update_node(path)
        self.dataset_view.scrollToTop()

        self.dims_model.update_node(path)
        self.dims_view.scrollToTop()

        self.data_model.update_node(path)
        self.data_view.scrollToTop()

    def add_image(self):
        """
        Add an image from the hdf5 file.
        """
        index = self.tree_view.selectedIndexes()[0]
        path = self.tree_model.itemFromIndex(index).data(Qt.UserRole)
        title = '{} - {}'.format(self.hdf.filename, path)

        data = self.hdf[path]

        image_view = ImageWindow(title, data)
        self.image_views.append(image_view)
        image_view.show()


class ImageWindow(QMainWindow):

    def __init__(self, title, data):
        super().__init__()

        self.data = data

        self.setWindowTitle(title)

        self.init_actions()
        self.init_menus()
        self.init_toolbars()
        self.init_central_widget()
        self.init_statusbar()

    def init_actions(self):
        """
        Initialise actions
        """
        self.close_action = QAction(
            '&Close',
            self,
            shortcut=QKeySequence.Close,
            statusTip='Close image',
            triggered=self.close,
        )

    def init_menus(self):
        """
        Initialise menus
        """
        menu = self.menuBar()

        # Image menu
        self.file_menu = menu.addMenu('&Image')
        self.file_menu.addAction(self.close_action)

    def init_toolbars(self):
        """
        Initialise the toobars
        """
        self.file_toolbar = self.addToolBar('Image')
        self.file_toolbar.setObjectName('image_toolbar')
        self.file_toolbar.addAction(self.close_action)

    def init_central_widget(self):
        """
        Initialise the central widget
        """
        self.image_view = ImageView(self.data)
        self.setCentralWidget(self.image_view)

    def init_statusbar(self):
        """
        Initialise statusbar        """

        self.status = self.statusBar()
        self.status.addPermanentWidget(self.image_view.position_label)
        self.status.addPermanentWidget(self.image_view.frame_label)


class ImageView(QWidget):
    """
    Very rough image view, work in progress.

    TODO: Axis selection
          Min/Max scaling
          Histogram
          Colour maps
    """

    def __init__(self, data):
        super().__init__()

        self.data = data

        # Statusbar widgets
        self.position_label = QLabel()
        self.frame_label = QLabel()

        # Main graphics layout widget
        graphics_layout_widget = pg.GraphicsLayoutWidget()

        # Graphics layout widget view box
        self.viewbox = graphics_layout_widget.addViewBox()
        self.viewbox.setAspectLocked(True)

        # Add image item to view box
        self.image_item = pg.ImageItem(border='w')
        self.viewbox.addItem(self.image_item)

        # Create a scrollbar for moving through image frames
        self.scrollbar = QScrollBar(Qt.Horizontal)

        if data.ndim == 3:
            # TODO: Set image range based on max/min?
            self.image_item.setImage(data[0])
            self.scrollbar.setRange(0, data.shape[0] - 1)
            self.scrollbar.valueChanged.connect(self.handle_scroll)
        elif data.ndim == 2:
            self.image_item.setImage(data[:], autoLevels=True)
            self.image_item.setBorder(None)
            self.scrollbar.setRange(0, 0)
            self.scrollbar.hide()
        else:
            pass
        # TODO: Handle the wrong sized data

        self.handle_scroll(0)

        layout = QVBoxLayout()

        layout.addWidget(graphics_layout_widget)
        layout.addWidget(self.scrollbar)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.init_signals()

    def init_signals(self):
        self.image_item.scene().sigMouseMoved.connect(self.handle_mouse_moved)

    def handle_scroll(self, value):
        """
        Change the image frame on scroll
        """
        self.image_item.setImage(self.data[value])
        self.frame_label.setText('Frame={}'.format(value))

    def handle_mouse_moved(self, pos):
        """
        Update the cursor position when the mouse moves
        in the image scene.
        """
        max_x, max_y = self.image_item.image.shape

        scene_pos = self.viewbox.mapSceneToView(pos)

        x = int(scene_pos.x())
        y = int(scene_pos.y())

        if x >= 0 and x < max_x and y >= 0 and max_y:
            self.position_label.setText('X={} Y={}'.format(x, y))
            self.viewbox.setCursor(Qt.CrossCursor)
        else:
            self.position_label.setText('')
            self.viewbox.setCursor(Qt.ArrowCursor)
