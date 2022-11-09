import pickle
import sys
import workers

from windows import *
from PyQt5.QtWidgets import *


def debug_trap(*args):
    print(args)


sys.excepthook = debug_trap

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()

    sys.exit(app.exec())