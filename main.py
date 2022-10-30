import pickle
import sys
import requestwrk

from windows import *
from PyQt5.QtWidgets import *

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()

    sys.exit(app.exec())