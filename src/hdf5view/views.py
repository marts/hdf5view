# -*- coding: utf-8 -*-
"""
This module contains the main HDF5 container widget and implementations
of QAbstractItemView (ImageView and PlotView), which allow images
and y(x) plots to be shown.
"""
from qtpy.QtCore import (
    Qt,
    QModelIndex,
)

from qtpy.QtGui import (
    QFont,
    # QKeySequence,
)

from qtpy.QtWidgets import (
    QAbstractItemView,
    # QAction,
    QHeaderView,
    # QLabel,
    # QMainWindow,
    QScrollBar,
    QTableView,
    QTabBar,
    QTabWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg

from .models import (
    AttributesTableModel,
    DataTableModel,
    DatasetTableModel,
    DimsTableModel,
    TreeModel,
    ImageModel,
    PlotModel,
)




class HDF5Widget(QWidget):
    """
    Main HDF5 view container widget
    """
    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf

        self.image_views = {}
        self.plot_views = {}

        # Initialise the models
        self.tree_model = TreeModel(self.hdf)
        self.attrs_model = AttributesTableModel(self.hdf)
        self.dataset_model = DatasetTableModel(self.hdf)
        self.dims_model = DimsTableModel(self.hdf)
        self.data_model = DataTableModel(self.hdf)
        self.image_model = ImageModel(self.hdf)
        self.plot_model = PlotModel(self.hdf)

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
        self.tab_dims = {id(self.tabs.widget(0)) : list(self.dims_model.shape)}

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

        elif isinstance(self.tabs.currentWidget(), PlotView):
            self.plot_model.set_dims(self.dims_model.shape)
            self.plot_views[id_cw].update_plot()

        self.tab_dims[id_cw] = list(self.dims_model.shape)




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

        self.dims_model.update_node(path,
                                    now_on_PlotView=isinstance(self.tabs.currentWidget(),
                                                               PlotView)
                                    )
        self.dims_view.scrollToTop()

        self.data_model.update_node(path)
        self.data_view.scrollToTop()

        self.image_model.update_node(path)

        self.plot_model.update_node(path)

        id_cw = id(self.tabs.currentWidget())
        self.tab_dims[id_cw] = list(self.dims_model.shape)
        self.tab_node[id_cw] = index

        if isinstance(self.tabs.currentWidget(), ImageView):
            self.image_views[id_cw].update_image()

        if isinstance(self.tabs.currentWidget(), PlotView):
            self.plot_views[id_cw].update_plot()



    def handle_tab_changed(self):
        """
        We need to keep the dims for each tab and reset the dims_view
        when the tab is changed.
        """
        c_index = self.tree_view.currentIndex()
        o_index = self.tab_node[id(self.tabs.currentWidget())]
        o_slice = list(self.tab_dims[id(self.tabs.currentWidget())])

        if c_index != o_index:
            self.tree_view.setCurrentIndex(o_index)

        self.dims_model.beginResetModel()
        self.dims_model.shape = o_slice
        self.dims_model.endResetModel()
        self.dims_model.dataChanged.emit(QModelIndex(), QModelIndex(), [])


    def add_image(self):
        """
        Add a tab to view an image of a dataset in the hdf5 file.
        """
        c_index = self.tab_node[id(self.tabs.currentWidget())]
        path = self.tree_model.itemFromIndex(c_index).data(Qt.UserRole)
        self.dims_model.update_node(path)
        self.image_model.update_node(path)

        iv = ImageView(self.image_model, self.dims_model)
        iv.update_image()

        id_iv = id(iv)
        self.image_views[id_iv] = iv

        self.tab_dims[id_iv] = list(self.dims_model.shape)
        tree_index = self.tree_view.currentIndex()
        self.tab_node[id_iv] = tree_index

        index = self.tabs.addTab(self.image_views[id_iv], 'Image')
        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(index)
        self.tabs.blockSignals(False)



    def add_plot(self):
        """
        Add a tab to view an plot of a dataset in the hdf5 file.
        """
        c_index = self.tab_node[id(self.tabs.currentWidget())]
        path = self.tree_model.itemFromIndex(c_index).data(Qt.UserRole)
        self.dims_model.update_node(path, now_on_PlotView=True)
        self.plot_model.update_node(path)

        pv = PlotView(self.plot_model, self.dims_model)
        pv.update_plot()

        id_pv = id(pv)

        self.plot_views[id_pv] = pv

        self.tab_dims[id_pv] = list(self.dims_model.shape)
        tree_index = self.tree_view.currentIndex()
        self.tab_node[id_pv] = tree_index

        index = self.tabs.addTab(self.plot_views[id_pv], 'Plot')
        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(index)
        self.tabs.blockSignals(False)


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


class ImageView(QAbstractItemView):
    """
    Shows a greyscale or rgb(a) image view of the associated ImageModel.

    If the node of the hdf5 file has ndim > 2, the image shown can be
    changed by changing the slice (DimsTableModel). A scrollbar is
    provided which can also be used to scroll through the images
    in the first axis.

    TODO: Axis selection
          Min/Max scaling
          Histogram
          Colour maps
    """

    def __init__(self, model, dims_model):
        super().__init__()

        self.setModel(model)
        self.dims_model = dims_model

        pg.setConfigOptions(antialias=True)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOption('leftButtonPan', False)

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

        layout = QVBoxLayout()

        layout.addWidget(graphics_layout_widget)
        layout.addWidget(self.scrollbar)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.init_signals()


    def init_signals(self):
        self.image_item.scene().sigMouseMoved.connect(self.handle_mouse_moved)
        self.scrollbar.valueChanged.connect(self.handle_scroll)


    def update_image(self):
        if isinstance(self.model().image_view, type(None)):
            if self.viewbox.isVisible():
                self.viewbox.setVisible(False)

            if self.scrollbar.isVisible():
                self.scrollbar.blockSignals(True)
                self.scrollbar.setVisible(False)
                self.scrollbar.blockSignals(False)

            return

        self.image_item.setImage(self.model().image_view)

        if not self.viewbox.isVisible():
            self.viewbox.setVisible(True)

        if not self.scrollbar.isVisible():
            self.scrollbar.setVisible(True)

        if self.model().ndim > 2:
            try:
                if not self.scrollbar.isVisible():
                    self.scrollbar.setVisible(True)

                self.scrollbar.setRange(0, self.model().node.shape[0] - 1)

                if self.scrollbar.sliderPosition() != self.model().dims[0]:
                    self.scrollbar.blockSignals(True)
                    self.scrollbar.setSliderPosition(self.model().dims[0])
                    self.scrollbar.blockSignals(False)

            except TypeError:
                if self.scrollbar.isVisible():
                    self.scrollbar.blockSignals(True)
                    self.scrollbar.setVisible(False)
                    self.scrollbar.blockSignals(False)
        else:
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


    def handle_mouse_moved(self, pos):
        """
        Update the cursor position when the mouse moves
        in the image scene.
        """
        if self.viewbox.isVisible():
            try:
                max_y, max_x = self.image_item.image.shape
            except ValueError:
                max_y, max_x = self.image_item.image.shape[:2]

            scene_pos = self.viewbox.mapSceneToView(pos)

            x = int(scene_pos.x())
            y = int(scene_pos.y())

            if 0 <= x < max_x and 0 <= y < max_y:
                I = self.model().image_view[y,x]
                msg1 = f"X={x} Y={y}, value="
                try:
                    msg2 = f"{I:.3e}"
                except TypeError:
                    try:
                        msg2 = f"[{I[0]:.3e}, {I[1]:.3e}, {I[2]:.3e}, {I[3]:.3e}]"
                    except IndexError:
                        msg2 = f"[{I[0]:.3e}, {I[1]:.3e}, {I[2]:.3e}]"
                self.window().status.showMessage(msg1 + msg2)
                self.viewbox.setCursor(Qt.CrossCursor)
            else:
                self.window().status.showMessage('')
                self.viewbox.setCursor(Qt.ArrowCursor)


    def horizontalOffset(self):
        return 0

    def verticalOffset(self):
        return 0

    def moveCursor(self, cursorAction, modifiers):
        return QModelIndex()


class PlotView(QAbstractItemView):
    """
    Shows a plot view of the associated PlotModel.

    Currently a y(x) plot can be shown where x is either
    an index or a second column of data in the same
    dataset.

    TODO: Multiplots
    """
    def __init__(self, model, dims_model):
        super().__init__()

        self.setModel(model)
        self.dims_model = dims_model

        pg.setConfigOptions(antialias=True)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOption('leftButtonPan', False)

        # Main graphics layout widget
        graphics_layout_widget = pg.GraphicsLayoutWidget()

        self.plot_item = graphics_layout_widget.addPlot()

        # Create a scrollbar for moving through image frames
        self.scrollbar = QScrollBar(Qt.Horizontal)

        layout = QVBoxLayout()

        layout.addWidget(graphics_layout_widget)
        layout.addWidget(self.scrollbar)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.init_signals()

        # self.pen = (0,0,200)
        self.pen = None
        self.symbolBrush = (0,0,255)
        self.symbolPen = 'k'


    def init_signals(self):
        self.plot_item.scene().sigMouseMoved.connect(self.handle_mouse_moved)
        self.scrollbar.valueChanged.connect(self.handle_scroll)


    def update_plot(self):
        if isinstance(self.model().plot_view, type(None)):
            self.plot_item.setVisible(False)
            self.scrollbar.blockSignals(True)
            self.scrollbar.setVisible(False)
            self.scrollbar.blockSignals(False)

            return


        self.plot_item.setTitle(None)
        self.plot_item.enableAutoRange()

        self.set_up_plot()

        self.plot_item.showAxis("top")
        self.plot_item.showAxis('right')
        for i in ["bottom", "top", "left", "right"]:
            ax = self.plot_item.getAxis(i)
            ax.setPen(pg.mkPen(color='k', width=2))
            ax.setStyle(**{"tickAlpha" : 255,
                           "tickLength": -8})
        for i in ["bottom", "left"]:
            lab_font = QFont("Arial")
            lab_font.setPointSize(11)
            ax = self.plot_item.getAxis(i)
            ax.setTextPen('k')
            ax.setStyle(**{'tickFont':lab_font})
        for i in ["top", "right"]:
            self.plot_item.getAxis(i).setStyle(**{'showValues':False})


        if not self.plot_item.isVisible():
            self.plot_item.setVisible(True)

        if not self.scrollbar.isVisible():
            self.scrollbar.setVisible(True)

        if not isinstance(self.model().dims[0], slice):
            try:
                if not self.scrollbar.isVisible():
                    self.scrollbar.setVisible(True)

                self.scrollbar.setRange(0, self.model().node.shape[0] - 1)

                if self.scrollbar.sliderPosition() != self.model().dims[0]:
                    self.scrollbar.blockSignals(True)
                    self.scrollbar.setSliderPosition(self.model().dims[0])
                    self.scrollbar.blockSignals(False)

            except TypeError:
                if self.scrollbar.isVisible():
                    self.scrollbar.blockSignals(True)
                    self.scrollbar.setVisible(False)
                    self.scrollbar.blockSignals(False)

        else:
            self.scrollbar.blockSignals(True)
            self.scrollbar.setVisible(False)
            self.scrollbar.blockSignals(False)


    def set_up_plot(self):
        c_n = self.model().compound_names

        if c_n:
            if len(c_n) == 1:
                # plot a single column of data against the index
                self.plot_item.plot(self.model().plot_view[c_n[0]],
                                    pen=self.pen,
                                    symbolBrush=self.symbolBrush,
                                    symbolPen=self.symbolPen,
                                    clear=True
                                    )

            elif len(c_n) == 2:
                # plot two columns of data against each other
                self.plot_item.plot(self.model().plot_view[c_n[0]],
                                    self.model().plot_view[c_n[1]],
                                    pen=self.pen,
                                    symbolBrush=self.symbolBrush,
                                    symbolPen=self.symbolPen,
                                    clear=True
                                    )

        else:
            self.plot_item.plot(self.model().plot_view,
                                pen=self.pen,
                                symbolBrush=self.symbolBrush,
                                symbolPen=self.symbolPen,
                                clear=True
                                )

        two_cols = self.model().column_count == 2
        s_loc = [i if isinstance(j, slice) else -1 for i, j in enumerate(self.model().dims)]
        s_idx = [i for i in s_loc if i != -1]
        if two_cols:
            # here we are plotting two columns of data against each other
            if c_n:
                self.plot_item.setTitle(self.model().node.name.split('/')[-1])
                self.plot_item.titleLabel.item.setFont(QFont("Arial", 14, QFont.Bold))
                d_slice = f" [{self.dims_model.shape[0]}]" if not self.dims_model.shape[0] == ":" else ""
                x_label = f"{c_n[0]}{d_slice}"
                y_label = f"{c_n[1]}{d_slice}"
            else:
                q = list(range(self.model().node.shape[s_idx[1]]))[self.model().dims[s_idx[1]]]
                w_x = list(self.dims_model.shape)
                w_x[s_idx[1]] = str(q[0])
                w_y = list(self.dims_model.shape)
                w_y[s_idx[1]] = str(q[1])

                x_slice = f" [{', '.join(w_x)}]"
                x_label = f"{self.model().node.name.split('/')[-1]}{x_slice}"
                y_slice = f" [{', '.join(w_y)}]"
                y_label = f"{self.model().node.name.split('/')[-1]}{y_slice}"
        else:
            # here only one column of data is plotted (it may be sliced)
            x_label = 'Index'
            if c_n:
                self.plot_item.setTitle(self.model().node.name.split('/')[-1])
                self.plot_item.titleLabel.item.setFont(QFont("Arial", 14, QFont.Bold))
                y_slice = f" [{self.dims_model.shape[0]}]" if not self.dims_model.shape[0] == ":" else ""
                y_label = f"{c_n[0]}{y_slice}"
            else:
                y_slice = f" [{', '.join(self.dims_model.shape)}]" if not self.dims_model.shape == [":"] else ""
                y_label = f"{self.model().node.name.split('/')[-1]}{y_slice}"

        self.plot_item.setLabel('bottom',
                                x_label,
                                **{'font-size':'14pt', 'font':'Arial'}
                                )
        self.plot_item.setLabel('left',
                                y_label,
                                **{'font-size':'14pt', 'font':'Arial'}
                                )


    def handle_scroll(self, value):
        """
        Change the image frame on scroll
        """
        self.dims_model.beginResetModel()
        self.dims_model.shape[0] = str(value)
        self.dims_model.endResetModel()
        self.dims_model.dataChanged.emit(QModelIndex(), QModelIndex(), [])


    def handle_mouse_moved(self, pos):
        """
        Update the cursor position when the mouse moves
        in the image scene.
        """
        if self.plot_item.isVisible():
            vb = self.plot_item.getViewBox()
            x_lim, y_lim = vb.viewRange()
            x_min, x_max = x_lim
            y_min, y_max = y_lim

            scene_pos = vb.mapSceneToView(pos)

            x = scene_pos.x()
            y = scene_pos.y()

            if x_min <= x < x_max and y_min <= y < y_max:
                msg1 = f"X={x:.3e} Y={y:.3e}"
                self.window().status.showMessage(msg1)
                vb.setCursor(Qt.CrossCursor)
            else:
                self.window().status.showMessage('')
                vb.setCursor(Qt.ArrowCursor)


    def horizontalOffset(self):
        return 0

    def verticalOffset(self):
        return 0

    def moveCursor(self, cursorAction, modifiers):
        return QModelIndex()