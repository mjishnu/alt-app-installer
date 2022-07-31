import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from maingui import MainWindowGui, QMainWindow


def main():
    app = QApplication(sys.argv)
    MainProgram = QMainWindow()
    ui = MainWindowGui()
    ui.setupUi(MainProgram)
    MainProgram.setWindowIcon(QIcon('./Images/main.ico'))
    MainProgram.closeEvent = ui.closeEvent #overiding close event
    MainProgram.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()