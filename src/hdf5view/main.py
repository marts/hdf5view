# -*- coding: utf-8 -*-

import os
import sys
import argparse
#import traceback

# to force qtpy to use a particular Qt binding, uncomment the line below,
# and set the string to your preferred binding i.e. 'pyqt5', 'pyside2',
# 'pyqt6' or 'pyside6'. Otherwise, qtpy will take the first available of these.
# os.environ['QT_API'] = 'pyqt5'

import qtpy
os.environ['PYQTGRAPH_QT_LIB'] = qtpy.API_NAME


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


# def my_excepthook(e_type, value, tb):
#     """
#     Catch and print exceptions to help with debugging Qt guis.
#     """
#     m_1 = '\x1b[31m\x1b[1m'
#     m_2 = f"Unhandled error: {e_type} {value} {''.join(traceback.format_tb(tb))}"
#     m_3 = '\x1b[0m'
#     print(m_1 + m_2 + m_3)

# sys.excepthook = my_excepthook


basedir = os.path.dirname(__file__)
resource_path = os.path.join(basedir, "resources", "images")
qtpy.QtCore.QDir.addSearchPath('icons', resource_path)


def main():
    """
    Main application entry point
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')
    parser.add_argument("-f", "--file", type=str, required=False)
    args = parser.parse_args()

    if qtpy.API_NAME in ["PyQt5", "PySide2"]:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setOrganizationName('hdf5view')
    app.setApplicationName('hdf5view')
    app.setWindowIcon(QIcon('icons:hdf5view.svg'))

    window = MainWindow(app)
    window.show()

    # Open a file if supplied on command line
    if args.file:
        window.open_file(args.file)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
