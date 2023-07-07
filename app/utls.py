import sys
import traceback
import webbrowser

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog


class UrlBox(QDialog):

    closed = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(390, 49)
        Form.setMinimumSize(QtCore.QSize(300, 49))
        Form.setMaximumSize(QtCore.QSize(600, 49))
        Form.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        Form.setWindowTitle("Enter URL")
        icon = QIcon()
        icon.addPixmap(QPixmap("data/images/main.ico"),
                       QIcon.Mode.Normal, QIcon.State.Off)
        Form.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.install_link_lineEdit = QtWidgets.QLineEdit(Form)
        self.install_link_lineEdit.setInputMask("")
        self.install_link_lineEdit.setText("")
        self.install_link_lineEdit.setClearButtonEnabled(False)
        self.install_link_lineEdit.setObjectName("install_link_lineEdit")
        self.horizontalLayout.addWidget(self.install_link_lineEdit)
        self.install_link_ok_btn = QtWidgets.QPushButton(Form)
        self.install_link_ok_btn.setObjectName("install_link_ok_btn")
        self.install_link_ok_btn.setText("OK")
        self.horizontalLayout.addWidget(self.install_link_ok_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        QtCore.QMetaObject.connectSlotsByName(Form)

        def current_url():
            self.closed.emit(str(self.install_link_lineEdit.text()))
            Form.close()

        self.install_link_ok_btn.clicked.connect(current_url)


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    cur_progress = pyqtSignal(int)
    main_progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                    kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_current'] = self.signals.cur_progress
        self.kwargs['progress_main'] = self.signals.main_progress

    @pyqtSlot()
    def run(self):
        '''Initialise the runner function with passed args, kwargs.'''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.signals.started.emit()
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            # Return the result of the processing
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()  # Done


def open_browser(arg):
    webbrowser.open(arg)
