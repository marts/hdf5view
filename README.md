# hdf5view

Simple Qt/Python based viewer for HDF5 files. Displays a file tree, data tables and attributes and can render greyscale images of any nodes which have two or more dimensions. Everything is loaded dynamically, so hopefully it should be able to handle HDF5 files of any size and structure.


## 1. Installing

#### Qt API Bindings

One of [pyqt5](https://www.riverbankcomputing.com/software/pyqt/), [pyside2](https://pyside.org), [pyqt6](https://www.riverbankcomputing.com/software/pyqt/) or [pyside6](https://pyside.org) is required in order to be able to run hdf5view. Please install one of these e.g. with pip:

```
pip install pyqt5
```

or on linux (Ubuntu/Debian), you can install a system package:

```
sudo apt install python3-pyqt5
```

[qtpy](https://github.com/spyder-ide/qtpy) is used as an abstraction layer for pyqt5/pyside2/pyqt6/pyside6. If you have any of these Qt API bindings installed, qtpy will take the first available one in the order shown in the previous sentence. hdf5view works with all of the bindings. If you have more than one of the bindings installed and want to specify which one should be used for hdf5view, you can do this by setting the `QT_API` environment variable before running hdf5view.

For example: if you have pyqt5 and pyside2 installed and you want hdf5view to use PySide2, on Windows PowerShell:

```
$env:QT_API = 'pyside2'
```

or on linux (Ubuntu/Debian)

```
export QT_API=pyside2
```

before running HDF5View


#### Other Dependencies

The other dependencies are [qtpy](https://github.com/spyder-ide/qtpy), [h5py](https://www.h5py.org/) and [pyqtgraph](https://www.pyqtgraph.org/). Currently installed versions of these dependencies will not be overwritten by installing hdf5view. If these are not already present on your system, they will be installed during the installation of hdf5view. 

If you prefer to install them in advance, you can use pip:

```
pip install h5py, qtpy, pyqtgraph
```

or on linux to install system packages:

```
sudo apt install python3-h5py python3-pyqtgraph python3-qtpy
```

Note: [pyqtgraph](https://www.pyqtgraph.org/) 0.12 supports all of pyqt5, pyside2, pyqt6 or pyside6. Older versions of pyqtgraph may not support all of them.


#### hdf5view

To install the current release from PyPI system-wide on Windows:

```
pip install hdf5view
```

or on linux:

```
sudo pip3 install hdf5view
```

To install the current development version, download or clone the repo and install either system-wide on Windows:

```
cd hdf5view
pip install .
```

or on linux:

```
cd hdf5view
sudo pip3 install .
```

You could also use the flag -e with the pip command to install in editable mode, then you can pull changes from the repo and they are automatically available on your system.

To setup an isolated development environment using virtualenv:

```
python3 -m virtualenv -p python3 .
source bin/activate
pip install -e .
```

To uninstall hdf5view:

```
pip uninstall hdf5view
```

or:

```
sudo pip3 uninstall hdf5view
```

## 2. Running

From the terminal:

```
hdf5view
```

or

```
hdf5view -f <hdf5file>
```

HDF5 files can also be dropped onto the application window once opened.

You can also create a desktop link to start the program for convenience. A Windows icon file hdf5view.ico is provided in the folder hdf5view/resources/images.

## 3. Usage

The structure of the HDF5 file can be navigated using the tree view on the left hand side. The central panel displays a table of the data at the node selected. If the node has more than two dimensions, a 2D slice of the data is displayed in the table. On the right hand side you can see and modify the slice shown; and see details of the node and any associated attributes.

To display a greyscale image of the data at a particular node, click the image icon on the toolbar at the top of the window. This will open an Image tab at the current node. The image is initially take from the last two dimensions of the node. A scrollbar is provided, which currently can be used to scroll through the first dimension of the node. You can alternatively change the slice manually and the scrollbar will move accordingly. You can have several image tabs open at once. Image tabs remember the node and slice if you switch to a different tab and back. Switching to a different node results in the default behaviour that the image shown is the last two dimensions of the first index of the first dimension.

## 4. Testing

Currently there are no unit tests for this package. The gui has been tested with qtpy=2.2.0, pyqtgraph=0.12.4 and h5py=3.7.0 in combination with pyqt5=5.15.7, pyside2=5.15.2.1, pyqt6=6.3.1 and pyside6=6.3.2, and it works with all of the Qt API bindings.

## 5. Issues

If there are any issues, please feel free to use the [issues mechanism on github](https://github.com/marts/hdf5view/issues) to get in touch.

## TODO:

* Add xy plots in pyqtgraph
* Add a more complex slice view/delegate
* Add some 3D stuff
