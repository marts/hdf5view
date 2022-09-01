# HDF5View

Simple Qt/Python based viewer for HDF5 files. Currently, it just displays a file tree, data tables and attributes. Everything is loaded dynamically, so hopefully it should be able to handle HDF5 files of any size and structure.

I hope to add pyqtgraph plotting and some image rendering soon.

## Installing

On linux (Ubuntu/Debian) I generally prefer installing the system packages of PyQt5 and/or PySide2 - in that case don't bother with uncommenting stuff in install_requires in setup.py:

```
sudo apt install python3-pyqt5 python3-h5py python3-pyqtgraph python3-qtpy
```

To install system wide, download or clone the repo. Uncomment the preferred Qt bindings in setup.py (or install system packages...see below):

```
cd hdf5view
sudo pip3 install .
```

To uninstall:

```
sudo pip3 uninstall hdf5view
```

## Running

```
hdf5view
```

or

```
hdf5view -f <hdf5file>
```

HDF5 files can also be dropped onto the application window once opened.

## Development

To setup a development environment use virtualenv:

```
python3 -m virtualenv -p python3 .
source bin/activate
pip install -e .
```

## Choosing Qt API bindings

`qtpy` is used as an abstraction layer for PyQt5/PySide2. Currently, the default is to use PyQt5. This is because the version of pyqtgraph (0.10.0) I have wouldn't work with PySide2.

Environment variables are used to set the Qt API. PyQt5 is used by default unless you set the `QT_API` environment variable. To switch to using PySide2:

```
export QT_API=pyside2
export PYQTGRAPH_QT_LIB=PySide2
```

## Building resources

Resources for the project are compiled using a resource compiler. You will need the pyqt5-dev-tools or pyside2-tools installed to recompile resources.

Depending on the bindings choice (PyQt5 or PySide2) the resources can be built with the following command:

```
# PyQt5
pyrcc5 hdf5view/resources/resources.qrc -o hdf5view/resources/resources.py

# PySide2
pyside2-rcc hdf5view/resources/resources.qrc -o hdf5view/resources/resources.py
```

## TODO:

* Actually use pyqtgraph to plot some stuff.
* Add an image view
* Add some 3D stuff
* Build a deb package
