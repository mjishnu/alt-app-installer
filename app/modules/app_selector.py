# importing required libraries
from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (QLabel, QLineEdit, QMenu, QPushButton, QStatusBar,
                             QToolBar)


class CustomWebEngineView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._history = []
        self._history_index = -1
        self.urlChanged.connect(self._on_url_changed)
        self._context_menu_pos = None
        self._is_text_box = False

    def _on_url_changed(self, url):
        if self._history_index >= 0 and url == self._history[self._history_index]:
            return
        self._history = self._history[:self._history_index + 1]
        self._history.append(url)
        self._history_index += 1

    def back(self):
        if self._history_index > 0:
            self._history_index -= 1
            self.load(self._history[self._history_index])

    def forward(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self.load(self._history[self._history_index])

    def contextMenuEvent(self, event):
        # Save the position of the context menu event
        self._context_menu_pos = event.pos()

        # Check if the element under the cursor is a text box using JavaScript
        script = """
            (function() {{
                let el = document.elementFromPoint({}, {});
                return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);
            }})()
        """.format(event.x(), event.y())
        self.page().runJavaScript(script, self._on_text_box_check)

    def _on_text_box_check(self, is_text_box):
        # Save the result of the text box check
        self._is_text_box = is_text_box

        # Check if text is selected or if the context menu was triggered within a text box
        if self.selectedText() or self._is_text_box:
            menu = QMenu(self)
            copy_action = menu.addAction(QIcon("data/images/copy.png"), "Copy")
            copy_action.setShortcut("Ctrl+C")
            copy_action.triggered.connect(
                lambda: self.page().triggerAction(QWebEnginePage.WebAction.Copy))
            menu.addSeparator()
            paste_action = menu.addAction(
                QIcon("data/images/paste.png"), "Paste")
            paste_action.setShortcut("Ctrl+V")
            paste_action.triggered.connect(
                lambda: self.page().triggerAction(QWebEnginePage.WebAction.Paste))

            if not self.selectedText():
                copy_action.setDisabled(True)
            if not self._is_text_box:
                paste_action.setDisabled(True)

            # Display the menu at the cursor position
            menu.exec(self.mapToGlobal(self._context_menu_pos))

    def createWindow(self, _type):
        return self


class AppSelector(QObject):
    # creating a signal varable to signal if code execution completed
    closed = pyqtSignal(object)

    def __init__(self):
        super().__init__()

    def setupUi(self, qt_window):
        # all helper functions
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
            self.closed.emit(str(qt_window.urlbar.text()))
            qt_window.close()

        # set the title
        qt_window.setWindowTitle("App Selector")
        # creating a QWebEngineView
        qt_window.browser = CustomWebEngineView()

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
        back_btn.setIcon(QIcon('./data/images/Back.png'))

        # adding action to the back button
        # making browser go back
        back_btn.triggered.connect(qt_window.browser.back)

        # adding this action to tool bar
        navtb.addAction(back_btn)

        # similarly for forward action
        next_btn = QAction("", qt_window)
        next_btn.setStatusTip("Forward to next page")
        next_btn.setIcon(QIcon('./data/images/forward.png'))

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
        reload_btn.setIcon(QIcon('./data/images/reload.png'))

        # adding action to the reload button
        # making browser to reload
        reload_btn.triggered.connect(qt_window.browser.reload)
        navtb.addAction(reload_btn)

        # similarly for home button
        home_btn = QAction("", qt_window)
        home_btn.setStatusTip("Home page")
        home_btn.setIcon(QIcon('./data/images/home.png'))

        # adding action to the home button
        # making browser go to home
        home_btn.triggered.connect(lambda: qt_window.browser.load(
            QUrl("https://apps.microsoft.com/")))
        navtb.addAction(home_btn)

        qt_window.label2 = QLabel(qt_window)
        qt_window.label2.setText(" ")
        navtb.addWidget(qt_window.label2)

        # creating a line edit for the url
        qt_window.urlbar = QLineEdit()

        # adding select button to the tool bar
        navtb.addWidget(qt_window.urlbar)
        qt_window.label = QLabel(qt_window)
        qt_window.label.setText(
            "  Select The App ")
        qt_window.label.setStyleSheet("QLabel{font-size: 10pt;}")
        navtb.addWidget(qt_window.label)

        qt_window.select_btn = QPushButton(qt_window)
        qt_window.select_btn.setText("Select")
        qt_window.select_btn.setStatusTip("Select The File To Download")
        qt_window.select_btn.setIcon(QIcon('./data/images/ok.png'))
        qt_window.select_btn.clicked.connect(current_url)
        navtb.addWidget(qt_window.select_btn)
        qt_window.urlbar.returnPressed.connect(navigate_to_url)

# test code
# from PyQt6.QtWidgets import (QApplication, QMainWindow)
# def url_grabber():
#     import sys

#     # creating a pyQt application
#     app = QApplication(sys.argv)

#     window = QMainWindow()
#     window.setWindowIcon(QIcon('./data/images/search.png'))
#     newwindow = url_window()
#     newwindow.setupUi(window)
#     window.show()
#     app.exec()


# if __name__ == "__main__":
#     url_grabber()
