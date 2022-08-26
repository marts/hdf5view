# -*- coding: utf-8 -*-

from qtpy.QtCore import (
    Qt,
    QModelIndex,
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
    QTabBar,
    QTabWidget,
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
    ImageModel,
)

import pyqtgraph as pg




class HDF5Widget(QWidget):
    """
    Main HDF5 view container widget
    """

    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf

        self.image_views = {}

        # Initialise the models
        self.tree_model = TreeModel(self.hdf)
        self.attrs_model = AttributesTableModel(self.hdf)
        self.dataset_model = DatasetTableModel(self.hdf)
        self.dims_model = DimsTableModel(self.hdf)
        self.data_model = DataTableModel(self.hdf)
        self.image_model = ImageModel(self.hdf)

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

        # Setup dims table view
        self.dims_view = QTableView()
        self.dims_view.setModel(self.dims_model)
        self.dims_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dims_view.horizontalHeader().setStretchLastSection(True)
        self.dims_view.verticalHeader().hide()

        # Setup main data table view
        self.data_view = QTableView()
        self.data_view.setModel(self.data_model)

        # Setup tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.South)
        self.tabs.setTabsClosable(True)

        self.tabs.addTab(self.data_view, 'Table')

        self.tabs.tabBar().tabButton(0, QTabBar.RightSide).deleteLater()
        self.tabs.tabBar().setTabButton(0, QTabBar.RightSide, None)
        self.tabs.tabCloseRequested.connect(self.handle_close_tab)

        # Create the main layout. All the other
        # associated table views are placed in
        # surrounding dock widgets.
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # save the current dims state of each tab so that it can be
        # restored when the tab is changed
        self.tab_dims = {id(self.tabs.widget(0)) : [i for i in self.dims_model.shape]}

        # container to save the current node (selected node of the tree)
        # for each tab so that it can be restored when the tab is changed.
        self.tab_node = {}

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

        self.tabs.currentChanged.connect(self.handle_tab_changed)
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
        id_cw = id(self.tabs.currentWidget())

        if isinstance(self.tabs.currentWidget(), QTableView):
            self.data_model.set_dims(self.dims_model.shape)

        elif isinstance(self.tabs.currentWidget(), ImageView):
            self.image_model.set_dims(self.dims_model.shape)
            self.image_views[id_cw].update_image()

        self.tab_dims[id_cw] = [i for i in self.dims_model.shape]




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

        self.image_model.update_node(path)

        id_cw = id(self.tabs.currentWidget())
        self.tab_dims[id_cw] = [i for i in self.dims_model.shape]
        self.tab_node[id_cw] = index

        if isinstance(self.tabs.currentWidget(), ImageView):
            self.image_views[id_cw].update_image()



    def handle_tab_changed(self):
        """
        We need to keep the dims for each tab and reset the dims_view
        when the tab is changed.
        """
        c_index = self.tree_view.currentIndex()
        o_index = self.tab_node[id(self.tabs.currentWidget())]
        o_slice = self.tab_dims[id(self.tabs.currentWidget())]

        if c_index != o_index:
            self.tree_view.setCurrentIndex(o_index)

        self.tab_dims[id(self.tabs.currentWidget())] = o_slice

        self.dims_model.beginResetModel()
        self.dims_model.shape = self.tab_dims[id(self.tabs.currentWidget())]
        self.dims_model.endResetModel()
        self.dims_model.dataChanged.emit(QModelIndex(), QModelIndex(), [])


    def add_image(self):
        """
        Add an image from the hdf5 file.
        """
        # index = self.tree_view.selectedIndexes()[0]
        # path = self.tree_model.itemFromIndex(index).data(Qt.UserRole)
        # title = '{} - {}'.format(self.hdf.filename, path)

        # data = self.hdf[path]

        #image_view = ImageWindow(title, data)
        #self.image_views.append(image_view)
        #image_view.show()

        iv = ImageView(self.image_model, self.dims_model)

        id_iv = id(iv)

        self.image_views[id_iv] = iv

        self.tab_dims[id_iv] = [i for i in self.dims_model.shape]
        tree_index = self.tree_view.currentIndex()
        self.tab_node[id_iv] = tree_index

        index = self.tabs.addTab(self.image_views[id_iv], 'Image')
        self.tabs.setCurrentIndex(index)


    def handle_close_tab(self, index):
        """
        Close a tab
        """
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        self.tab_dims.pop(id(widget))
        self.tab_node.pop(id(widget))
        if isinstance(widget, ImageView):
            self.image_views.pop(id(widget))
        widget.deleteLater()


# class ImageWindow(QMainWindow):

#     def __init__(self, title, data):
#         super().__init__()

#         self.data = data

#         self.setWindowTitle(title)

#         self.init_actions()
#         self.init_menus()
#         self.init_toolbars()
#         self.init_central_widget()
#         self.init_statusbar()

#     def init_actions(self):
#         """
#         Initialise actions
#         """
#         self.close_action = QAction(
#             '&Close',
#             self,
#             shortcut=QKeySequence.Close,
#             statusTip='Close image',
#             triggered=self.close,
#         )

#     def init_menus(self):
#         """
#         Initialise menus
#         """
#         menu = self.menuBar()

#         # Image menu
#         self.file_menu = menu.addMenu('&Image')
#         self.file_menu.addAction(self.close_action)

#     def init_toolbars(self):
#         """
#         Initialise the toobars
#         """
#         self.file_toolbar = self.addToolBar('Image')
#         self.file_toolbar.setObjectName('image_toolbar')
#         self.file_toolbar.addAction(self.close_action)

#     def init_central_widget(self):
#         """
#         Initialise the central widget
#         """
#         self.image_view = ImageView(self.data)
#         self.setCentralWidget(self.image_view)

#     def init_statusbar(self):
#         """
#         Initialise statusbar        """

#         self.status = self.statusBar()
#         self.status.addPermanentWidget(self.image_view.position_label)
#         self.status.addPermanentWidget(self.image_view.frame_label)


class ImageView(QAbstractItemView):
    """
    Very rough image view, work in progress.

    TODO: Axis selection
          Min/Max scaling
          Histogram
          Colour maps
    """

    def __init__(self, model, dims_model):
        super().__init__()

        self.setModel(model)
        self.dims_model = dims_model
        # Statusbar widgets
        self.position_label = QLabel()
        self.frame_label = QLabel()

        # Main graphics layout widget
        graphics_layout_widget = pg.GraphicsLayoutWidget()

        # Graphics layout widget view box
        self.viewbox = graphics_layout_widget.addViewBox()
        self.viewbox.setAspectLocked(True)
        self.viewbox.invertY(True)

        # Add image item to view box
        self.image_item = pg.ImageItem(border='w')
        self.viewbox.addItem(self.image_item)
        self.image_item.setOpts(axisOrder="row-major")

        # Create a scrollbar for moving through image frames
        self.scrollbar = QScrollBar(Qt.Horizontal)

        self.image_item.setImage(self.model().image_view)
        self.scrollbar.setRange(0, self.model().node.shape[0] - 1)
        self.scrollbar.valueChanged.connect(self.handle_scroll)

        layout = QVBoxLayout()

        layout.addWidget(graphics_layout_widget)
        layout.addWidget(self.scrollbar)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.init_signals()

    def init_signals(self):
        self.image_item.scene().sigMouseMoved.connect(self.handle_mouse_moved)

    def update_image(self):
        if not self.scrollbar.isVisible():
            self.scrollbar.setVisible(True)

        self.image_item.setImage(self.model().image_view)

        try:
            if self.scrollbar.sliderPosition() != self.model().dims[0]:
                self.scrollbar.blockSignals(True)
                self.scrollbar.setSliderPosition(self.model().dims[0])
                self.scrollbar.blockSignals(False)

        except (IndexError, TypeError):
            self.scrollbar.blockSignals(True)
            self.scrollbar.setVisible(False)
            self.scrollbar.blockSignals(False)



    def handle_scroll(self, value):
        """
        Change the image frame on scroll
        """
        self.dims_model.beginResetModel()
        self.dims_model.shape[0] = str(value)
        self.dims_model.endResetModel()
        self.dims_model.dataChanged.emit(QModelIndex(), QModelIndex(), [])
        # self.frame_label.setText('Frame={}'.format(value))

    def handle_mouse_moved(self, pos):
        """
        Update the cursor position when the mouse moves
        in the image scene.
        """
        max_y, max_x = self.image_item.image.shape

        scene_pos = self.viewbox.mapSceneToView(pos)

        x = int(scene_pos.x())
        y = int(scene_pos.y())

        if x >= 0 and x < max_x and y >= 0 and y < max_y:
            self.position_label.setText('X={} Y={}'.format(x, y))
            self.viewbox.setCursor(Qt.CrossCursor)
        else:
            self.position_label.setText('')
            self.viewbox.setCursor(Qt.ArrowCursor)

    def horizontalOffset(self):
        return 0

    def verticalOffset(self):
        return 0

    def moveCursor(self, cursorAction, modifiers):
        return QModelIndex()
