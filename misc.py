import os

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox

from gui import Ui_MainProgram
from utls import current_time


class Miscellaneous(Ui_MainProgram):
    
    def error_msg(self, text,msg_details,title="Error",critical = False):
            msg = QMessageBox()
            msg.setWindowTitle(title)
            msg.setText(f'{str(text)}     ')
            if critical:
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowIcon(QIcon('./Images/error_r.png'))
            else:
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowIcon(QIcon('./Images/error_y.png'))
            msg.setDetailedText(str(msg_details) + '\n\ncheck Full Logs [Help --> Open Logs]')
            if text == "Failed To Clear Cache Files!":
                print("Failed to clear cache")
            else:
                self.set_bar_0()
                self.show_bar(False)
                self.stop_btn.hide()
                self.pushButton.setEnabled(True)
                self.pushButton.show()
            msg.exec()
            
    def show_error_popup(self,txt="An Error Has Occured Try Again!"):
        msg = QMessageBox()
        msg.setWindowTitle('Error')
        msg.setWindowIcon(QIcon('./Images/error_r.png'))
        msg.setText(f'{txt}     ')
        msg.setIcon(QMessageBox.Icon.Critical)
        self.set_bar_0()
        self.show_bar(False)
        self.stop_btn.hide()
        self.pushButton.setEnabled(True)
        self.pushButton.show()      
        msg.exec()
        
    def show_success_popup(self,text=None):
        msg = QMessageBox()
        msg.setWindowTitle('Success')
        msg.setWindowIcon(QIcon('./Images/success.png'))
        if text:
            msg.setText(f'{text}     ')
        else:
            msg.setText('Installation completed!     ')
        msg.setIcon(QMessageBox.Icon.Information)
        
        if text =="Cache Files Cleared Successfully!":
            print("Cache Files Cleared")
        else:
            self.set_bar_0()
            self.show_bar(False)
            self.stop_btn.hide()
            self.pushButton.setEnabled(True)
            self.pushButton.show() 
        msg.exec()
        
    def error_handler(self, n,normal=True,msg = None,critical=True):
        # if path exits or not
        if os.path.exists('log.txt'):
            mode = 'a'
        else:
            mode = 'w'
        # write to the log file 
        with open('log.txt', mode) as f:
            f.write(f'[maingui.py, Thread logs] \n{current_time}\n\n')
            f.write(n[2])
            f.write(f'{82*"-"}\n')
            
        #if normal show a simple popup
        if normal:
            self.show_error_popup()
        else:
            msg_details = f'{n[1]}'
            if 'Stoped By User!' == msg_details:
                self.show_success_popup("Download Stopped!")
            else:
                if msg == None:
                    msg = 'An Error Has Occured Try Again!'
                self.error_msg(msg,msg_details,"Error",critical)

    def run_success(self,value):
        if value == 0:
            self.show_success_popup()
        else:
            self.error_msg(*value)

    def main_Progress(self, n):
        total = self.mainprogressBar.value()
        if total + n < 100:
            total += n
        else:
            total = 99
        self.mainprogressBar.setValue(total)

    def cur_Progress(self, n):
        self.currentprogressBar.setValue(n)

    def progress(self, n):
        total = self.currentprogressBar.value()
        total += n
        self.currentprogressBar.setValue(total)
        if total == 100:
            self.main_Progress(20)
 
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
        self.stop=True
        self.stop_btn.hide()
        
    def closeEvent(self, event):
        close = QMessageBox()
        close.setWindowTitle("Confirm")
        close.setWindowIcon(QIcon('./Images/error_y.png'))
        close.setText("Are you sure you want to exit?     ")
        close.setIcon(QMessageBox.Icon.Warning)
        close.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        close = close.exec()

        if close == QMessageBox.StandardButton.Yes:
            try:
                self.window.close()
            except:
                pass
            event.accept()
        else:
            event.ignore()
