# -*- coding: utf-8 -*-
"""
This module contains the various models used in the Qt model-view
methodology.
"""

import h5py
import qtpy

from qtpy.QtCore import (
    QAbstractTableModel,
    QAbstractItemModel,
    QModelIndex,
    QVariant,
    Qt,
)

from qtpy.QtGui import (
    QBrush,
    QIcon,
    QColor,

    QStandardItem,
    QStandardItemModel,
)



class TreeModel(QStandardItemModel):
    """
    Tree model showing the structure of the HDF5 file.
    """

    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['Objects', 'Attrs', 'Dataset'])

        # Add the root node and immediate children
        root = self.add_node(self, '/', self.hdf)
        for name, node in self.hdf.items():
            self.add_node(root, name, node)

    def add_node(self, parent_item, name, node):
        if name != '/':
            path = f'{parent_item.data(Qt.UserRole)}/{name}'
        else:
            path = '/'

        tree_item = QStandardItem(name)
        tree_item.setData(path, Qt.UserRole)
        tree_item.setToolTip(path)

        num_attrs = len(node.attrs)
        if num_attrs > 0:
            attrs_item = QStandardItem(str(num_attrs))
        else:
            attrs_item = QStandardItem('')

        attrs_item.setForeground(QBrush((Qt.darkGray)))

        if isinstance(node, h5py.Dataset):
            tree_item.setIcon(QIcon('icons:dataset.svg'))
            dataset_item = QStandardItem(str(node.shape))

        elif isinstance(node, h5py.Group):
            tree_item.setIcon(QIcon('icons:folder.svg'))
            dataset_item = QStandardItem('')

        dataset_item.setForeground(QBrush((Qt.darkGray)))

        parent_item.appendRow([tree_item, attrs_item, dataset_item])
        return tree_item

    def handle_expanded(self, index):
        """
        Dynamically populate the treeview
        """
        item = self.itemFromIndex(index)

        if not item.hasChildren():
            return

        item.setIcon(QIcon('icons:folder-open.svg'))

        for row in range(item.rowCount()):
            child_item = item.child(row, 0)

            if not child_item or child_item.hasChildren():
                continue

            path = child_item.data(Qt.UserRole)
            child_node = self.hdf[path]

            if isinstance(child_node, h5py.Group):
                for name, node in child_node.items():
                    self.add_node(child_item, name, node)

    def handle_collapsed(self, index):
        """
        Update the icon when collapsing a group
        """
        item = self.itemFromIndex(index)
        item.setIcon(QIcon('icons:folder.svg'))


class AttributesTableModel(QAbstractTableModel):
    """
    Model containing any attributes of a dataset in
    the HDF5 file.
    """
    HEADERS = ('Name', 'Value', 'Type')

    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.node = None
        self.column_count = 3
        self.row_count = 0

    def update_node(self, path):
        """
        Update the current node path
        """
        self.beginResetModel()
        self.node = self.hdf[path]

        self.keys = list(self.node.attrs.keys())
        self.values = list(self.node.attrs.values())

        self.row_count = len(self.keys)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.HEADERS[section]
            else:
                return str(section)

    def data(self, index, role=Qt.DisplayRole):

        if index.isValid():
            column = index.column()
            row = index.row()

            if role in (Qt.DisplayRole, Qt.ToolTipRole):
                if column == 0:
                    return self.keys[row]
                elif column == 1:
                    try:
                        return self.values[row].decode()
                    except AttributeError:
                        return str(self.values[row])
                elif column == 2:
                    return str(type(self.values[row]))


class DatasetTableModel(QAbstractTableModel):
    """
    Model containing various descriptors of the
    dataset in the HDF5 file, currently these are:
    'name', 'dtype', 'ndim', 'shape', 'maxshape',
    'chunks', 'compression', 'shuffle', 'fletcher32'
    and 'scaleoffset'.
    """
    HEADERS = ('Name', 'Value')

    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.node = None
        self.column_count = 2
        self.row_count = 0

    def update_node(self, path):
        """
        Update the current node path
        """
        self.keys = []
        self.values = []

        self.beginResetModel()
        self.node = self.hdf[path]

        if not isinstance(self.node, h5py.Dataset):
            self.endResetModel()
            return

        self.keys = (
            'name', 'dtype', 'ndim', 'shape',
            'maxshape', 'chunks', 'compression', 'shuffle',
            'fletcher32', 'scaleoffset',
        )

        compound_names = self.node.dtype.names

        if compound_names:
            self.values = (
                str(self.node.name), str(self.node.dtype), str(self.node.ndim),
                f"{self.node.shape}  (ncols={len(compound_names)})",
                str(self.node.maxshape),
                str(self.node.chunks), str(self.node.compression),
                str(self.node.shuffle), str(self.node.fletcher32),
                str(self.node.scaleoffset),
            )

        else:
            self.values = (
                str(self.node.name), str(self.node.dtype), str(self.node.ndim),
                str(self.node.shape), str(self.node.maxshape),
                str(self.node.chunks), str(self.node.compression),
                str(self.node.shuffle), str(self.node.fletcher32),
                str(self.node.scaleoffset),
            )


        self.row_count = len(self.keys)
        self.endResetModel()


    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.HEADERS[section]
            else:
                return str(section)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            column = index.column()
            row = index.row()

            if isinstance(self.node, h5py.Dataset):
                if role in (Qt.DisplayRole, Qt.ToolTipRole):
                    if column == 0:
                        return self.keys[row]
                    elif column == 1:
                        return self.values[row]

                if role == Qt.ForegroundRole:
                    if row == 3 and column == 1 and self.node.dtype.names:
                        return QColor('red')


class DataTableModel(QAbstractTableModel):
    """
    Model containing the data in the dataset in the HDF5 file.
    """

    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.node = None
        self.row_count = 0
        self.column_count = 0
        self.ndim = 0
        self.dims = ()
        self.data_view = None
        self.compound_names = None

    def update_node(self, path):
        """
        Update the current node path
        """
        self.compound_names = None

        self.beginResetModel()

        self.row_count = 0
        self.column_count = 0

        self.dims = ()

        self.node = self.hdf[path]

        if not isinstance(self.node, h5py.Dataset):
            self.endResetModel()
            return

        self.ndim = self.node.ndim

        shape = self.node.shape

        self.compound_names = self.node.dtype.names

        if self.ndim == 0:
            self.row_count = 1
            self.column_count = 1

        elif self.ndim == 1:
            self.row_count = shape[0]
            if self.compound_names:
                self.column_count = len(self.compound_names)
            else:
                self.column_count = 1
            self.dims = tuple([slice(None)])

        elif self.ndim == 2:
            self.row_count = shape[-2]
            self.column_count = shape[-1]
            self.dims = tuple([slice(None), slice(None)])

        elif self.ndim > 2 and shape[-1] in [3, 4]:
            self.row_count = shape[-3]
            self.column_count = shape[-2]
            self.dims = tuple(([0] * (self.ndim - 3)) + [slice(None),
                                                         slice(None),
                                                         slice(None)])

        else:
            self.row_count = shape[-2]
            self.column_count = shape[-1]
            self.dims = tuple(([0] * (self.ndim - 2)) + [slice(None), slice(None)])

        self.data_view = self.node[self.dims]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if self.compound_names:
                    return self.compound_names[section]
                else:
                    if self.ndim in [0, 1]:
                        return None

                    if self.ndim == 2:
                        w = list(range(self.node.shape[1]))
                        w_e = w[self.dims[1]]
                        if isinstance(w_e, int):
                            w_e = [w_e]
                        return str(w_e[section])

                    s_loc = [i for i,j in enumerate(self.dims) if isinstance(j, slice)]
                    if self.ndim > 2:
                        if len(s_loc) >= 2:
                            idx = 1
                            w = list(range(self.node.shape[s_loc[idx]]))
                            w_e = w[self.dims[s_loc[idx]]]
                            if isinstance(w_e, int):
                                w_e = [w_e]
                            return str(w_e[section])
                        return None

            elif orientation == Qt.Vertical:
                if self.ndim == 0:
                    return None

                if self.ndim in [1, 2]:
                    w = list(range(self.node.shape[0]))
                    w_e = w[self.dims[0]]
                    if isinstance(w_e, int):
                        w_e = [w_e]

                    return str(w_e[section])

                s_loc = [i for i,j in enumerate(self.dims) if isinstance(j, slice)]
                if self.ndim > 2:
                    if len(s_loc) >= 1:
                        idx = 0
                        w = list(range(self.node.shape[s_loc[idx]]))
                        w_e = w[self.dims[s_loc[idx]]]
                        if isinstance(w_e, int):
                            w_e = [w_e]
                        return str(w_e[section])
                    return None

        super().headerData(section, orientation, role)


    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role in (Qt.DisplayRole, Qt.ToolTipRole):
                if self.compound_names:
                    name = self.compound_names[index.column()]
                    if self.data_view.ndim == 0:
                        try:
                            q = self.data_view[name].decode()
                        except AttributeError:
                            q = str(self.data_view[name])
                    else:
                        try:
                            q = self.data_view[index.row()][name].decode()
                        except AttributeError:
                            q = str(self.data_view[index.row()][name])

                    return q

                if self.ndim == 0:
                    try:
                        q = self.data_view.decode()
                    except TypeError:
                        q = str(self.data_view)
                else:
                    if self.data_view.ndim == 0:
                        try:
                            q = self.data_view.decode()
                        except AttributeError:
                            q = str(self.data_view)
                    elif self.data_view.ndim == 1:
                        try:
                            q = self.data_view[index.row()].decode()
                        except AttributeError:
                            q = str(self.data_view[index.row()])
                    elif self.data_view.ndim >= 2:
                        try:
                            q = self.data_view[index.row(), index.column()].decode()
                        except AttributeError:
                            q = str(self.data_view[index.row(), index.column()])

                return q


    def set_dims(self, dims):
        """
        This function is called if the dimensions in the
        HDF5Widget.dims_view are edited. The dimensions of
        the model are updated to match the input dimensions.
        """
        self.beginResetModel()

        self.row_count = None
        self.column_count = None

        self.dims = []
        self.shape = self.node.shape

        self.dims = get_dims_from_str(dims)

        if self.compound_names:
            if isinstance(self.dims[1], int):
                self.compound_names = tuple([self.node.dtype.names[self.dims[1]]])
            else:
                self.compound_names = self.node.dtype.names[self.dims[1]]
            self.column_count = len(self.compound_names)
            if isinstance(self.dims[0], int):
                dims = list(self.dims)
                dims[0] = slice(dims[0], dims[0] + 1, None)
                self.dims = tuple(dims)
            self.data_view = self.node[self.dims[0]][list(self.compound_names)]
            if self.data_view.ndim == 0:
                self.row_count = 1
            else:
                self.row_count = self.data_view.shape[0]

            self.endResetModel()
            return

        if self.ndim == 2 and isinstance(self.dims[0], int):
            dims = list(self.dims)
            dims[0] = slice(dims[0], dims[0] + 1, None)
            self.dims = tuple(dims)

        self.data_view = self.node[self.dims]

        try:
            self.row_count = self.data_view.shape[0]
        except IndexError:
            self.row_count = 1

        try:
            self.column_count = self.data_view.shape[1]
        except IndexError:
            self.column_count = 1

        self.endResetModel()


class ImageModel(QAbstractItemModel):
    """
    Model containing data from the dataset in the HDF5 file,
    in a form suitable for plotting as an image.
    """
    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.node = None
        self.row_count = 0
        self.column_count = 0
        self.ndim = 0
        self.dims = ()
        self.image_view = None
        self.compound_names = None


    def update_node(self, path):
        """
        Update the current node path
        """
        self.compound_names = None

        self.beginResetModel()

        self.row_count = 0
        self.column_count = 0

        self.dims = ()

        self.node = self.hdf[path]

        self.image_view = None

        if not isinstance(self.node, h5py.Dataset) or self.node.dtype == 'object':
            self.endResetModel()
            return

        self.ndim = self.node.ndim

        shape = self.node.shape

        self.compound_names = self.node.dtype.names

        if self.ndim == 0:
            self.row_count = 1
            self.column_count = 1

        elif self.ndim == 1:
            self.row_count = shape[0]

            if self.compound_names:
                self.column_count = len(self.compound_names)
            else:
                self.column_count = 1

        elif self.ndim == 2:
            self.row_count = shape[-2]
            self.column_count = shape[-1]
            self.dims = tuple([slice(None), slice(None)])
            self.image_view = self.node[self.dims]

        elif self.ndim > 2 and shape[-1] in [3, 4]:
            self.row_count = shape[-3]
            self.column_count = shape[-2]
            self.dims = tuple(([0] * (self.ndim - 3)) + [slice(None),
                                                         slice(None),
                                                         slice(None)])
            self.image_view = self.node[self.dims]

        else:
            self.row_count = shape[-2]
            self.column_count = shape[-1]
            self.dims = tuple(([0] * (self.ndim - 2)) + [slice(None),
                                                         slice(None)])
            self.image_view = self.node[self.dims]

        self.endResetModel()

    def parent(self, childIndex=QModelIndex()):
        return self.createIndex()

    def index(self, row, column, parentIndex=QModelIndex()):
        return self.createIndex()

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if self.compound_names and orientation == Qt.Horizontal:
                return self.compound_names[section]
            else:
                return str(section)

        super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        """
        This function must be implemented when subclassing
        QAbstractItemModel. As the ImageView class does not need
        this function, a default QVariant() is returned, as
        recommended in the docs.
        """
        if index.isValid():
            if role in (Qt.DisplayRole, Qt.ToolTipRole):
                return QVariant()


    def set_dims(self, dims):
        """
        This function is called if the dimensions in the
        HDF5Widget.dims_view are edited. The dimensions of
        the model are updated to match the input dimensions.
        """
        self.beginResetModel()

        self.row_count = None
        self.column_count = None
        self.dims = []
        self.image_view = None

        self.dims = get_dims_from_str(dims)

        if len(self.dims) >= 2 and not self.node.dtype == 'object':
            self.image_view = self.node[self.dims]
            shape = self.image_view.shape
            if self.image_view.ndim == 2:
                self.row_count = shape[-2]
                self.column_count = shape[-1]

            elif self.image_view.ndim == 3 and shape[-1] in [3, 4]:
                self.row_count = shape[-3]
                self.column_count = shape[-2]

            else:
                self.image_view = None
                self.row_count = 1
                self.column_count = 1

        else:
            self.row_count = 1
            self.column_count = 1

        self.endResetModel()


class PlotModel(QAbstractItemModel):
    """
    Model containing data from a dataset of the HDF5 file,
    in a form suitable for plotting as y(x), where x is
    usually an index.
    """
    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.node = None
        self.row_count = 0
        self.column_count = 0
        self.ndim = 0
        self.dims = ()
        self.plot_view = None
        self.compound_names = None


    def update_node(self, path):
        """
        Update the current node path
        """
        self.beginResetModel()

        self.node = self.hdf[path]
        self.row_count = 0
        self.column_count = 0
        self.ndim = 0
        self.dims = ()
        self.plot_view = None
        self.compound_names = None

        if not isinstance(self.node, h5py.Dataset) or self.node.dtype == 'object':
            self.endResetModel()
            return

        self.ndim = self.node.ndim

        shape = self.node.shape

        self.compound_names = self.node.dtype.names

        if self.ndim == 0:
            self.row_count = 1
            self.column_count = 1
            self.endResetModel()
            return

        if self.ndim == 1:
            self.row_count = shape[0]
            self.dims = tuple([slice(None)])

            if self.compound_names:
                self.column_count = 1
                self.dims = tuple([slice(None), 0])
                self.compound_names = tuple([self.node.dtype.names[0]])
                self.plot_view = self.node[self.dims[0]][list(self.compound_names)]
                self.endResetModel()
                return

        elif self.ndim == 2:
            self.row_count = shape[-2]
            self.dims = tuple([slice(None), 0])

        elif self.ndim > 2 and shape[-1] in [3, 4]:
            self.row_count = shape[-3]
            self.dims = tuple(([0] * (self.ndim - 3)) + [slice(None), 0, 0])

        else:
            self.row_count = shape[-2]
            self.dims = tuple(([0] * (self.ndim - 2)) + [slice(None), 0])

        self.column_count = 1
        self.plot_view = self.node[self.dims]
        self.endResetModel()


    def parent(self, childIndex=QModelIndex()):
        return self.createIndex()

    def index(self, row, column, parentIndex=QModelIndex()):
        return self.createIndex()

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if self.compound_names and orientation == Qt.Horizontal:
                return self.compound_names[section]
            else:
                return str(section)

        super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        """
        This function must be implemented when subclassing
        QAbstractItemModel. As the PlotView class does not need
        this function, a default QVariant() is returned, as
        recommended in the docs.
        """
        if index.isValid():
            if role in (Qt.DisplayRole, Qt.ToolTipRole):
                return QVariant()


    def set_dims(self, dims):
        """
        This function is called if the dimensions in the
        HDF5Widget.dims_view are edited. The dimensions of
        the model are updated to match the input dimensions.
        """
        self.beginResetModel()

        self.row_count = None
        self.column_count = None
        self.dims = ()
        self.plot_view = None

        self.dims = get_dims_from_str(dims)

        if len(self.dims) >= 1 and not self.node.dtype == 'object':
            if not any(isinstance(i, slice) for i in self.dims):
                self.row_count = 1
                self.column_count = 1
                self.endResetModel()
                return

            if not self.compound_names:
                self.plot_view = self.node[self.dims]
                shape = self.plot_view.shape
                self.row_count = shape[0]

                if self.plot_view.ndim == 1:
                    self.column_count = 1

                elif self.plot_view.ndim == 2 and shape[-1] == 2:
                    self.column_count = 2

                else:
                    self.plot_view = None
                    self.column_count = 1

            else:
                if isinstance(self.dims[1], int):
                    self.compound_names = tuple([self.node.dtype.names[self.dims[1]]])
                else:
                    self.compound_names = self.node.dtype.names[self.dims[1]]
                self.column_count = len(self.compound_names)
                if self.column_count in [1, 2]:
                    self.plot_view = self.node[self.dims[0]][list(self.compound_names)]
                    self.row_count = self.plot_view.shape[0]
                else:
                    self.row_count = 1
                    self.column_count = 1

        else:
            self.row_count = 1
            self.column_count = 1

        self.endResetModel()


class DimsTableModel(QAbstractTableModel):
    """
    Model containing the current dimensions of the dataset.
    This model is editable, allowing the user to change
    the indexing of the dataset and therefore view
    different slices.
    """
    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.node = None
        self.column_count = 0
        self.row_count = 1
        self.shape = ()
        self.compound_names = None

    def update_node(self, path, now_on_PlotView=False):
        """
        Update the current node path
        """
        self.compound_names = None
        self.column_count = 0
        self.shape = []

        self.beginResetModel()
        self.node = self.hdf[path]

        if not isinstance(self.node, h5py.Dataset) or self.node.dtype == 'object':
            self.endResetModel()
            return

        self.compound_names = self.node.dtype.names

        if self.node.ndim == 1:
            if self.compound_names:
                self.shape = [':', ':']
                self.column_count = 2
                if now_on_PlotView:
                    self.shape[-1] = '0'

            else:
                self.shape = [':']
                self.column_count = 1

        elif self.node.ndim == 2:
            self.shape = [':', ':']
            self.column_count = 2
            if now_on_PlotView:
                self.shape[-1] = '0'

        elif self.node.ndim > 2:
            if self.node.shape[-1] in [3, 4]:
                self.shape = (['0'] * (self.node.ndim - 3)) + [':', ':', ':']
                self.column_count = len(self.shape)
                if now_on_PlotView:
                    self.shape[-2] = '0'
                    self.shape[-1] = '0'

            else:
                self.shape = (['0'] * (self.node.ndim - 2)) + [':', ':']
                self.column_count = len(self.shape)
                if now_on_PlotView:
                    self.shape[-1] = '0'

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return str(section)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return self.shape[index.column()]

            elif role == Qt.TextAlignmentRole:
                if qtpy.API_NAME in ["PyQt5", "PySide2"]:
                    return Qt.AlignCenter

                else:
                    return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignHCenter


    def flags(self, index):
        flags = super().flags(index)
        flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role):

        if index.isValid() and role == Qt.EditRole:
            column = index.column()
            value = value.strip()

            if ':' not in value:
                try:
                    num = int(value)
                    if self.compound_names and column == 1:
                        if num < 0 or num >= len(self.node.dtype.names):
                            return False
                    else:
                        if num < 0 or num >= self.node.shape[column]:
                            return False

                except ValueError:
                    return False

            self.shape[column] = value
            self.dataChanged.emit(index, index, [])
            return True

        return False


def get_dims_from_str(dims_as_str):
    """
    Takes a tuple of strings describing the desired dimensions
    input by the user into the hdf5widget.dims_view and turns it
    into a tuple of ints and/or slices, which can be used to
    index the dataset at the node.

    The method to create slices from strings is given here:
    https://stackoverflow.com/questions/680826/python-create-slice-object-from-string/23895339

    Parameters
    ----------
    dims_as_str : Tuple
        Tuple of strings describing the dimensions (dims)
        e.g. ("0", "0", ":") or ("2:6:2", ":", "2", "3")

    Returns
    -------
    dims : Tuple
       Tuple of ints and/or slices to be used as an indexing object
       for array indexing, e.g. (0, 0, slice(None)) or
       (slice(2, 6, 2), slice(none), 2, 3), corresponding to the two
       examples given above for dims_as_str

    """
    dims = []
    for i, value in enumerate(dims_as_str):
        try:
            v = int(value)
            dims.append(v)
        except (ValueError, TypeError):
            if ':' in value:
                value = value.strip()
                s = slice(*map(lambda x: int(x.strip()) if x.strip() else None, value.split(':')))
                dims.append(s)

    dims = tuple(dims)

    return dims
