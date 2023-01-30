import os
from datetime import datetime

from PyQt6.QtGui import QIcon,QPixmap
from PyQt6.QtWidgets import QMessageBox,QDialog
from PyQt6 import QtCore,QtWidgets

from gui import Ui_MainProgram


class Miscellaneous(Ui_MainProgram):

    def error_msg(self, text, msg_details, title="Error", critical=False):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(f'{str(text)}     ')
        if critical:
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowIcon(QIcon('./data/images/error_r.png'))
        else:
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowIcon(QIcon('./data/images/error_y.png'))
        msg.setDetailedText(str(msg_details) +
                            '\n\ncheck Full Logs [Help --> Open Logs]')
        if text == "Failed To Clear Cache Files!":
            pass
        else:
            self.set_bar_0()
            self.show_bar(False)
            self.stop_btn.hide()
            self.pushButton.setEnabled(True)
            self.menuDependencies.setEnabled(True)
            self.actionclear_cache.setEnabled(True)
            self.actioninstall_From_File.setEnabled(True)
            self.actionInstall_using_url.setEnabled(True)
            self.pushButton.show()
        msg.exec()

    def show_error_popup(self, txt="An Error Has Occured Try Again!"):
        msg = QMessageBox()
        msg.setWindowTitle('Error')
        msg.setWindowIcon(QIcon('./data/images/error_r.png'))
        msg.setText(f'{txt}     ')
        msg.setIcon(QMessageBox.Icon.Critical)
        if txt in ("No Logs Found!", "No Downloads Found!"):
            pass
        else:
            self.set_bar_0()
            self.show_bar(False)
            self.stop_btn.hide()
            self.pushButton.setEnabled(True)
            self.menuDependencies.setEnabled(True)
            self.actionclear_cache.setEnabled(True)
            self.actioninstall_From_File.setEnabled(True)
            self.actionInstall_using_url.setEnabled(True)
            self.pushButton.show()
        msg.exec()

    def show_success_popup(self, text=None):
        msg = QMessageBox()
        msg.setWindowTitle('Success')
        msg.setWindowIcon(QIcon('./data/images/success.png'))
        if text:
            msg.setText(f'{text}     ')
        else:
            msg.setText('Installation completed!     ')
        msg.setIcon(QMessageBox.Icon.Information)

        if text == "Cache Files Cleared Successfully!":
            print("Cache Files Cleared")
        else:
            self.set_bar_0()
            self.show_bar(False)
            self.stop_btn.hide()
            self.pushButton.setEnabled(True)
            self.menuDependencies.setEnabled(True)
            self.actionclear_cache.setEnabled(True)
            self.actioninstall_From_File.setEnabled(True)
            self.actionInstall_using_url.setEnabled(True)
            self.pushButton.show()
        msg.exec()

    def error_handler(self, n, normal=True, msg=None, critical=True):
        def log_error():
            # if path exits or not
            if os.path.exists('log.txt'):
                mode = 'a'
            else:
                mode = 'w'
            # write to the log file
            with open('log.txt', mode) as f:
                current_time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
                f.write(f'[python logs] \n{current_time}\n\n')
                f.write(n[2])
                f.write(f'{82*"-"}\n')

        # if normal show a simple popup
        if normal:
            log_error()
            self.show_error_popup()
        else:
            msg_details = f'{n[1]}'
            if msg_details == 'Stoped By User!':
                self.show_success_popup("Download Stopped!")
            elif msg_details == 'server returned a empty list':
                msg = 'Sorry, Application not found!'
                msg_details = "Application not found in the server, Application is not supported!"
                self.error_msg(msg, msg_details, "Error", critical)
            else:
                log_error()
                if msg is None:
                    msg = 'An Error Has Occured Try Again!'
                self.error_msg(msg, msg_details, "Error", critical)

    def run_success(self, value):
        if value == 0:
            self.show_success_popup()
        else:
            self.error_msg(*value)

    def main_Progress(self, n):
        total = self.mainprogressBar.value()
        if total + n < 100:
            total += n
        else:
            total = 100
        self.mainprogressBar.setValue(total)

    def cur_Progress(self, n):
        self.currentprogressBar.setValue(n)

    def set_bar_0(self):
        self.mainprogressBar.setValue(0)
        self.currentprogressBar.setValue(0)

    def show_bar(self, val=True):
        if val is False:
            self.currentprogressBar.hide()
            self.mainprogressBar.hide()
            self.Current_bar.hide()
            self.Main_bar.hide()
        elif val is True:
            self.currentprogressBar.show()
            self.mainprogressBar.show()
            self.Current_bar.show()
            self.Main_bar.show()

    def stop_func(self):
        self.stop.set()
        self.stop_btn.hide()
        self.pushButton.show()

    def closeEvent(self, event):
        close = QMessageBox()
        close.setWindowTitle("Confirm")
        close.setWindowIcon(QIcon('./data/images/error_y.png'))
        close.setText("Are you sure you want to exit?     ")
        close.setIcon(QMessageBox.Icon.Warning)
        close.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        close = close.exec()

        if close == QMessageBox.StandardButton.Yes:
            try:
                self.window.close()
            except:
                pass
            event.accept()
        else:
            event.ignore()
class DilalogBox(QDialog):

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
        icon.addPixmap(QPixmap("data/images/main.ico"), QIcon.Mode.Normal, QIcon.State.Off)
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
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        QtCore.QMetaObject.connectSlotsByName(Form)

        def current_url():
            self.closed.emit(str(self.install_link_lineEdit.text()))
            Form.close()

        self.install_link_ok_btn.clicked.connect(current_url)