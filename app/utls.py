import sys
import traceback
import webbrowser

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtWidgets import QDialog
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))


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
        icon.addPixmap(
            QPixmap(f"{curr_dir}/data/images/main.ico"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
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
            20,
            40,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.verticalLayout.addItem(spacerItem)
        QtCore.QMetaObject.connectSlotsByName(Form)

        def current_url():
            self.closed.emit(str(self.install_link_lineEdit.text()))
            Form.close()

        self.install_link_ok_btn.clicked.connect(current_url)


class WorkerSignals(QObject):
    """
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

    """

    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    cur_progress = pyqtSignal(int)
    main_progress = pyqtSignal(int)


class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                    kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs["progress_current"] = self.signals.cur_progress
        self.kwargs["progress_main"] = self.signals.main_progress

    @pyqtSlot()
    def run(self):
        """Initialise the runner function with passed args, kwargs."""
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


class Ui_about(QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def setupUi(self, about):
        about.setObjectName("about")
        about.resize(315, 200)
        about.setMaximumSize(QtCore.QSize(327, 218))
        icon = QIcon()
        icon.addPixmap(
            QPixmap(f"{curr_dir}/data/images/main.ico"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        about.setWindowIcon(icon)
        self.gridLayout = QtWidgets.QGridLayout(about)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.horizontalLayout_2.addItem(spacerItem)
        self.label = QtWidgets.QLabel(parent=about)
        font = QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(15)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        spacerItem1 = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.horizontalLayout_2.addItem(spacerItem1)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 1, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem2 = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.horizontalLayout.addItem(spacerItem2)
        self.imagetitle = QtWidgets.QLabel(parent=about)
        self.imagetitle.setMaximumSize(QtCore.QSize(90, 90))
        self.imagetitle.setText("")
        self.imagetitle.setPixmap(QPixmap(f"{curr_dir}/data/images/installer_icon.png"))
        self.imagetitle.setScaledContents(True)
        self.imagetitle.setObjectName("imagetitle")
        self.horizontalLayout.addWidget(self.imagetitle)
        spacerItem3 = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.horizontalLayout.addItem(spacerItem3)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 1, 1, 1)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        spacerItem4 = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.horizontalLayout_5.addItem(spacerItem4)
        self.label_2 = QtWidgets.QLabel(parent=about)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_5.addWidget(self.label_2)
        spacerItem5 = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.horizontalLayout_5.addItem(spacerItem5)
        self.gridLayout.addLayout(self.horizontalLayout_5, 3, 1, 1, 1)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        spacerItem6 = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.horizontalLayout_6.addItem(spacerItem6)
        self.label_3 = QtWidgets.QLabel(parent=about)
        font = QFont()
        font.setPointSize(10)
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_3.setOpenExternalLinks(True)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_6.addWidget(self.label_3)
        spacerItem7 = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.horizontalLayout_6.addItem(spacerItem7)
        self.gridLayout.addLayout(self.horizontalLayout_6, 4, 1, 1, 1)
        spacerItem8 = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.gridLayout.addItem(spacerItem8, 5, 1, 1, 1)
        spacerItem9 = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.gridLayout.addItem(spacerItem9, 0, 1, 1, 1)
        self.label.setText("Alt App Installer 2.6.8")
        self.label_2.setText("© 2022 - 2024 Jishnu M")
        urlLink = '<a href="http://github.com/m-jishnu/alt-app-installer" style="text-decoration: none; color: black;">github.com/m-jishnu/alt-app-installer</a>'
        self.label_3.setText(urlLink)
        self.setWindowTitle("About")
        self.label_3.setOpenExternalLinks(True)
