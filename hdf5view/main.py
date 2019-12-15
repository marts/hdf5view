# -*- coding: utf-8 -*-

import os
import sys
import argparse

if not os.environ.get('QT_API'):  # noqa
    os.environ['QT_API'] = 'pyqt5'

if not os.environ.get('PYQTGRAPH_QT_LIB'):  # noqa
    os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

from qtpy.QtCore import (
    Qt,
)

from qtpy.QtGui import (
    QIcon,
)

from qtpy.QtWidgets import (
    QApplication,
)

from . import __version__
from .mainwindow import MainWindow
from .resources import resources  # noqa


def main():
    """
    Main application entry point
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument("-f", "--file", type=str, required=False)
    args = parser.parse_args()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setOrganizationName('hdf5view')
    app.setApplicationName('hdf5view')
    app.setWindowIcon(QIcon(':/images/hdf5view.svg'))

    window = MainWindow(app)
    window.show()

    # Open a file if supplied on command line
    if args.file:
        window.open_file(args.file)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
