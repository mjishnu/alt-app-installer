# importing required libraries
from PyQt6.QtCore import QUrl, pyqtSignal,QObject
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (QApplication, QLabel, QLineEdit, QMainWindow,
                             QPushButton, QStatusBar, QToolBar)


# creating main window class
class url_window(QObject):
    # creating a signal varable to signal if code execution completed
    closed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        
        
    def setupUi(self,qt_window):
        #all helper functions
        def navigate_to_url():

            # getting url and converting it to QUrl object
            q = QUrl(qt_window.urlbar.text())

            # if url is scheme is blank
            if q.scheme() == "":
                # set url scheme to html
                q.setScheme("http")

            # set the url to the browser
            qt_window.browser.setUrl(q)

        # method for updating url
        # this method is called by the QWebEngineView object
        def update_urlbar(q):

            # setting text to the url bar
            qt_window.urlbar.setText(q.toString())

            # setting cursor position of the url bar
            qt_window.urlbar.setCursorPosition(0)

        def current_url():
            qt_window.close()
            self.closed.emit(str(qt_window.urlbar.text()))

        # set the title
        qt_window.setWindowTitle("App Selector")
        # creating a QWebEngineView
        qt_window.browser = QWebEngineView()

        # setting default browser url as google
        qt_window.browser.setUrl(
            QUrl("https://apps.microsoft.com/"))

        # adding action when url get changed
        qt_window.browser.urlChanged.connect(update_urlbar)

        # set this browser as central widget or main window
        qt_window.setCentralWidget(qt_window.browser)

        # creating a status bar object
        qt_window.status = QStatusBar()

        # adding status bar to the main window
        qt_window.setStatusBar(qt_window.status)

        # creating QToolBar for navigation
        navtb = QToolBar("Navigation")

        # adding this tool bar tot he main window
        qt_window.addToolBar(navtb)

        # adding actions to the tool bar
        # creating a action for back
        back_btn = QAction("", qt_window)

        # setting status tip
        back_btn.setStatusTip("Back to previous page")
        back_btn.setIcon(QIcon('Images/Back.png'))

        # adding action to the back button
        # making browser go back
        back_btn.triggered.connect(qt_window.browser.back)

        # adding this action to tool bar
        navtb.addAction(back_btn)

        # similarly for forward action
        next_btn = QAction("", qt_window)
        next_btn.setStatusTip("Forward to next page")
        next_btn.setIcon(QIcon('Images/forward.png'))

        # adding action to the next button
        # making browser go forward
        next_btn.triggered.connect(qt_window.browser.forward)
        navtb.addAction(next_btn)

        qt_window.label1 = QLabel(qt_window)
        qt_window.label1.setText("  ")
        navtb.addWidget(qt_window.label1)

        # similarly for reload action
        reload_btn = QAction("", qt_window)
        reload_btn.setStatusTip("Reload page")
        reload_btn.setIcon(QIcon('Images/reload.png'))

        # adding action to the reload button
        # making browser to reload
        reload_btn.triggered.connect(qt_window.browser.reload)
        navtb.addAction(reload_btn)

        qt_window.label2 = QLabel(qt_window)
        qt_window.label2.setText(" ")
        navtb.addWidget(qt_window.label2)

        # creating a line edit for the url
        qt_window.urlbar = QLineEdit()

        # adding this to the tool bar
        navtb.addWidget(qt_window.urlbar)
        qt_window.label = QLabel(qt_window)
        qt_window.label.setText(
            "  Select The App ")
        qt_window.label.setStyleSheet("QLabel{font-size: 10pt;}")
        navtb.addWidget(qt_window.label)

        qt_window.select_btn = QPushButton(qt_window)
        qt_window.select_btn.setText("Select")
        qt_window.select_btn.setStatusTip("Select The File To Download")
        qt_window.select_btn.setIcon(QIcon('Images/ok.png'))
        qt_window.select_btn.clicked.connect(current_url)
        navtb.addWidget(qt_window.select_btn)
        qt_window.urlbar.returnPressed.connect(navigate_to_url)
        
def url_grabber():
    import sys

    # creating a pyQt application
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowIcon(QIcon('./Images/search.png'))
    newwindow = url_window()
    newwindow.setupUi(window)
    window.show()
    # window.resize(600, 400)
    # loop
    app.exec()


if __name__ == "__main__":
    url_grabber()