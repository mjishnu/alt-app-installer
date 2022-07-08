# importing required libraries
from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (QApplication, QLabel, QLineEdit, QMainWindow,
                             QPushButton, QStatusBar, QToolBar)


# creating main window class
class url_window(object):

    # creating a signal varable to signal if code execution completed
    closed = pyqtSignal(object)
    # constructor

    def __init__(self):
        super().__init__()
        # creating a signal to to get run next code after this executes
        
        def setupUi(self,MainProgram):
        # set the title
            MainProgram.setWindowTitle("App Selector") #so on 

            # creating a QWebEngineView
            self.browser = QWebEngineView()

            # setting default browser url as google
            self.browser.setUrl(
                QUrl("https://apps.microsoft.com/"))

            # adding action when url get changed
            self.browser.urlChanged.connect(self.update_urlbar)

            # set this browser as central widget or main window
            self.setCentralWidget(self.browser)

            # creating a status bar object
            self.status = QStatusBar()

            # adding status bar to the main window
            self.setStatusBar(self.status)

            # creating QToolBar for navigation
            navtb = QToolBar("Navigation")

            # adding this tool bar tot he main window
            self.addToolBar(navtb)

            # adding actions to the tool bar
            # creating a action for back
            back_btn = QAction("", self)

            # setting status tip
            back_btn.setStatusTip("Back to previous page")
            back_btn.setIcon(QIcon('Images/Back.png'))

            # adding action to the back button
            # making browser go back
            back_btn.triggered.connect(self.browser.back)

            # adding this action to tool bar
            navtb.addAction(back_btn)

            # similarly for forward action
            next_btn = QAction("", self)
            next_btn.setStatusTip("Forward to next page")
            next_btn.setIcon(QIcon('Images/forward.png'))

            # adding action to the next button
            # making browser go forward
            next_btn.triggered.connect(self.browser.forward)
            navtb.addAction(next_btn)

            self.label1 = QLabel(self)
            self.label1.setText("  ")
            navtb.addWidget(self.label1)

            # similarly for reload action
            reload_btn = QAction("", self)
            reload_btn.setStatusTip("Reload page")
            reload_btn.setIcon(QIcon('Images/reload.png'))

            # adding action to the reload button
            # making browser to reload
            reload_btn.triggered.connect(self.browser.reload)
            navtb.addAction(reload_btn)

            self.label2 = QLabel(self)
            self.label2.setText(" ")
            navtb.addWidget(self.label2)

            # creating a line edit for the url
            self.urlbar = QLineEdit()

            # adding this to the tool bar
            navtb.addWidget(self.urlbar)
            self.label = QLabel(self)
            self.label.setText(
                "  Select The App ")
            self.label.setStyleSheet("QLabel{font-size: 10pt;}")
            navtb.addWidget(self.label)

            self.select_btn = QPushButton(self)
            self.select_btn.setText("Select")
            self.select_btn.setStatusTip("Select The File To Download")
            self.select_btn.setIcon(QIcon('Images/ok.png'))
            self.select_btn.clicked.connect(self.current_url)
            navtb.addWidget(self.select_btn)
            self.urlbar.returnPressed.connect(self.navigate_to_url)
            # showing all the components
            self.show()

        def navigate_to_url(self):

            # getting url and converting it to QUrl object
            q = QUrl(self.urlbar.text())

            # if url is scheme is blank
            if q.scheme() == "":
                # set url scheme to html
                q.setScheme("http")

            # set the url to the browser
            self.browser.setUrl(q)

        # method for updating url
        # this method is called by the QWebEngineView object
        def update_urlbar(self, q):

            # setting text to the url bar
            self.urlbar.setText(q.toString())

            # setting cursor position of the url bar
            self.urlbar.setCursorPosition(0)

        def current_url(self):
            self.close()
            self.closed.emit(str(self.urlbar.text()))


def url_grabber():
    import sys

    # creating a pyQt5 application
    app = QApplication(sys.argv)

    window = url_window().setupUi()
    # window.resize(600, 400)
    # loop
    app.exec()


if __name__ == "__main__":
    url_grabber()
#needs to change all to mainwindow ....