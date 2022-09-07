# -*- coding: utf-8 -*-

"""
Checks to see if any of PyQt5, PySide5, PyQt6 or PySide6 are installed and
takes the first one found. In this case, the requirement will be already
satisfied in steup().
If no Qt bindings are currently installed, defaults to PyQt5 and this will
be installed by setup()

QtPy is an abstraction layer on top of Qt bindings for swapping between
PyQt5, PySide2, PyQt6 and PySide6
"""
import importlib.util

from setuptools import setup, find_packages

from hdf5view import __version__


if importlib.util.find_spec("PyQt5") is not None:
    QT_BINDINGS = "PyQt5"
elif importlib.util.find_spec("PySide2") is not None:
    QT_BINDINGS = "PySide2"
elif importlib.util.find_spec("PyQt6") is not None:
    QT_BINDINGS = "PyQt6"
elif importlib.util.find_spec("PySide6") is not None:
    QT_BINDINGS = "PySide6"
else:
    QT_BINDINGS = "PyQt5"


LD_1 = 'HDF5View is a python based HDF5 file viewer built on'
LD_2 = 'PyQt5/PySide2/PyQt6/PySide6, h5py and pyqtgraph.'

setup(
    name='hdf5view',
    version=__version__,
    description='HDF5 file viewer',
    long_description=" ".join([LD_1,LD_2]),
    license='MIT',
    url='https://github.com/marts/hdf5view/',
    author='Martin Swarbrick',
    author_email='martin.swarbrick@gmail.com',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop'
        'Intended Audience :: Science/Research',
        'License :: MIT',
        'Operating System :: POSIX',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering :: Visualization',
    ],

    keywords='',
    packages=find_packages('.'),
    install_requires=[
        'h5py',
        QT_BINDINGS,
        'QtPy',
        'pyqtgraph',
    ],
    zip_safe=False,
    include_package_data=True,
    package_data={
    },
    data_files=(
    ),
    entry_points={
        'gui_scripts': [
            'hdf5view=hdf5view.main:main',
        ],
    },
)
