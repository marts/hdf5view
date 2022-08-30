# -*- coding: utf-8 -*-
import h5py

from qtpy.QtCore import (
    QAbstractTableModel,
    QAbstractItemModel,
    QModelIndex,
    Qt,
)

from qtpy.QtGui import (
    QBrush,
    QIcon,

    QStandardItem,
    QStandardItemModel,
)

from qtpy.QtWidgets import (
    QComboBox,
    QStyledItemDelegate,
)



class TreeModel(QStandardItemModel):

    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['Objects', 'Attrs', 'Dataset'])

        # Add the root node and immediate children
        root = self.add_node(self, self.hdf)
        for name, node in self.hdf.items():
            self.add_node(root, node)

    def add_node(self, parent_item, node):
        node_path = node.name
        node_name = node_path.split('/')[-1]

        if not node_name:
            node_name = node_path

        tree_item = QStandardItem(node_name)
        tree_item.setData(node_path, Qt.UserRole)
        tree_item.setToolTip(node_path)

        num_attrs = len(node.attrs)
        if num_attrs > 0:
            attrs_item = QStandardItem(str(num_attrs))
        else:
            attrs_item = QStandardItem('')

        attrs_item.setForeground(QBrush((Qt.darkGray)))

        if isinstance(node, h5py.Dataset):
            tree_item.setIcon(QIcon(':/images/dataset.svg'))
            dataset_item = QStandardItem(str(node.shape))

        elif isinstance(node, h5py.Group):
            tree_item.setIcon(QIcon(':/images/folder.svg'))
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

        item.setIcon(QIcon(':/images/folder-open.svg'))

        for row in range(item.rowCount()):
            child_item = item.child(row, 0)

            if not child_item or child_item.hasChildren():
                continue

            path = child_item.data(Qt.UserRole)
            child_node = self.hdf[path]

            if isinstance(child_node, h5py.Group):
                for node in child_node.values():
                    self.add_node(child_item, node)

    def handle_collapsed(self, index):
        """
        Update the icon when collapsing a group
        """
        item = self.itemFromIndex(index)
        item.setIcon(QIcon(':/images/folder.svg'))


class AttributesTableModel(QAbstractTableModel):

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
                    return str(self.values[row])
                elif column == 2:
                    return str(type(self.values[row]))


class DatasetTableModel(QAbstractTableModel):

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

        if isinstance(self.node, h5py.Dataset):
            self.keys = (
                'name', 'dtype', 'ndim', 'shape',
                'maxshape', 'chunks', 'compression', 'shuffle',
                'fletcher32', 'scaleoffset',
            )

            self.values = (
                str(self.node.name), str(self.node.dtype), str(self.node.ndim), str(self.node.shape),
                str(self.node.maxshape), str(self.node.chunks), str(self.node.compression), str(self.node.shuffle),
                str(self.node.fletcher32), str(self.node.scaleoffset),
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

            if role in (Qt.DisplayRole, Qt.ToolTipRole):
                if column == 0:
                    return self.keys[row]
                elif column == 1:
                    return self.values[row]


class DataTableModel(QAbstractTableModel):

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

        if isinstance(self.node, h5py.Dataset):

            self.ndim = self.node.ndim

            shape = self.node.shape

            self.compound_names = self.node.dtype.names

            if self.ndim == 1:
                self.row_count = shape[0]

                if self.compound_names:
                    self.column_count = len(self.compound_names)
                else:
                    self.column_count = 1

            elif self.ndim >= 2:
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
            if self.compound_names and orientation == Qt.Horizontal:
                return self.compound_names[section]
            else:
                return str(section)

        super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):

        if index.isValid():
            if role in (Qt.DisplayRole, Qt.ToolTipRole):
                if self.ndim == 1:
                    if self.compound_names:
                        name = self.compound_names[index.column()]
                        return str(self.node[index.row(), name])
                    else:
                        return str(self.node[index.row()])

                elif self.ndim == 2:
                    return str(self.node[index.row(), index.column()])

                elif self.ndim > 2:
                    if self.data_view.ndim == 0:
                        return str(self.data_view)
                    elif self.data_view.ndim == 1:
                        return str(self.data_view[index.row()])
                    elif self.data_view.ndim >= 2:
                        return str(self.data_view[index.row(), index.column()])

    def set_dims(self, dims):

        self.beginResetModel()

        row_count = None
        column_count = None

        self.dims = []
        shape = self.node.shape

        for i, value in enumerate(dims):

            try:
                v = int(value)
                self.dims.append(v)
            except (ValueError, TypeError):
                if ':' in value:
                    value = value.strip()
                    # https://stackoverflow.com/questions/680826/python-create-slice-object-from-string/23895339
                    s = slice(*map(lambda x: int(x.strip()) if x.strip() else None, value.split(':')))
                    self.dims.append(s)

        self.dims = tuple(self.dims)
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


        if isinstance(self.node, h5py.Dataset):

            self.ndim = self.node.ndim

            shape = self.node.shape

            self.compound_names = self.node.dtype.names

            if self.ndim == 1:
                self.row_count = shape[0]

                if self.compound_names:
                    self.column_count = len(self.compound_names)
                else:
                    self.column_count = 1

            elif self.ndim >= 2:
                self.row_count = shape[-2]
                self.column_count = shape[-1]
                self.dims = tuple(([0] * (self.ndim - 2)) + [slice(None), slice(None)])
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
        if index.isValid():
            if role in (Qt.DisplayRole, Qt.ToolTipRole):
                if self.ndim == 2:
                    return self.node[index.row(), index.column()]

                elif self.ndim > 2:
                    if self.image_view.ndim >= 2:
                        return self.image_view[index.row(), index.column()]


    def set_dims(self, dims):
        self.beginResetModel()

        self.row_count = None
        self.column_count = None
        self.dims = []
        self.image_view = None

        for i, value in enumerate(dims):
            try:
                v = int(value)
                self.dims.append(v)
            except (ValueError, TypeError):
                if ':' in value:
                    value = value.strip()
                    # https://stackoverflow.com/questions/680826/python-create-slice-object-from-string/23895339
                    s = slice(*map(lambda x: int(x.strip()) if x.strip() else None, value.split(':')))
                    self.dims.append(s)

        if self.ndim == 2:
            self.dims = [slice(None), slice(None)]

        self.dims = tuple(self.dims)

        if len(self.dims) >= 2:
            self.image_view = self.node[self.dims]
            self.row_count = self.image_view.shape[0]
            self.column_count = self.image_view.shape[1]

        else:
            self.row_count = 1
            self.column_count = 1

        self.endResetModel()


class DimsTableModel(QAbstractTableModel):

    def __init__(self, hdf):
        super().__init__()

        self.hdf = hdf
        self.node = None
        self.column_count = 0
        self.row_count = 1
        self.shape = ()

    def update_node(self, path):
        """
        Update the current node path
        """
        self.column_count = 0
        self.shape = []

        self.beginResetModel()
        self.node = self.hdf[path]

        if isinstance(self.node, h5py.Dataset) and self.node.ndim > 2:
            self.shape = (['0'] * (self.node.ndim - 2)) + [':', ':']
            self.column_count = len(self.shape)

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
                return Qt.AlignCenter

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
                    if num < 0 or num >= self.node.shape[column]:
                        return False

                except ValueError:
                    return False

            self.shape[column] = value
            self.dataChanged.emit(index, index, [])
            return True

        return False


class ComboBoxItemDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        row = index.row()

        model = index.model()
        max_value = model.node.shape[row]

        # Create the combobox and populate it
        cb = QComboBox(parent)
        for i in range(max_value):
            cb.addItem(str(i))
        cb.addItem(':')

        return cb

    def setEditorData(self, editor, index):
        cb = editor

        # Get the index of the text in the combobox that
        # matches the current value of the item
        currentText = index.data(Qt.DisplayRole)
        cbIndex = cb.findText(currentText)

        if cbIndex != -1:
            cb.setCurrentIndex(cbIndex)

    def setModelData(self, editor, model, index):
        cb = editor
        model.setData(index, cb.currentText(), Qt.EditRole)
