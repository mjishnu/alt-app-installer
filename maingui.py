import os
import shutil
import sys
import traceback
from urllib import request

from PyQt6 import QtWidgets
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from get_url import url_window
from Gui import Ui_MainProgram
from utls import install, open_browser, open_Logs, get_data,parse_dict,current_time


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
    progress = pyqtSignal(int)


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
        self.kwargs['progress'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

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

class MainWindowGui(Ui_MainProgram):
    def __init__(self):
        self.threadpool = QThreadPool()

    def setupUi(self, *args, **kwargs):
        Ui_MainProgram.setupUi(self, *args, **kwargs)
        self.set_bar_0()
        self.show_bar(False)
        self.pushButton.clicked.connect(self.openWindow)
        self.actioninstall_From_File.triggered.connect(
            self.run_installer)
        self.actionSet_Wait_Time.triggered.connect(self.set_wait_time)
        self.actionclear_cache.triggered.connect(self.clear_cache)
        self.actionCheck_For_Updates.triggered.connect(lambda: open_browser(
            'https://github.com/m-jishnu/Windows-Store-App-Installer/releases'))
        self.actionAbout.triggered.connect(lambda: open_browser(
            'https://github.com/m-jishnu/Windows-Store-App-Installer'))
        self.actionHelp.triggered.connect(lambda: open_browser(
            'https://discord.com/invite/cbuEkpd'))
        self.actionOpen_Logs.triggered.connect(open_Logs)

    def error_msg(self, text,msg_details,title="Error",critical = False):
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle(title)
            msg.setText(f'{str(text)}     ')
            if critical:
                msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            else:
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setDetailedText(str(msg_details) + '\n\ncheck Full Logs [Help --> Open Logs]')
            self.set_bar_0()
            self.show_bar(False)
            self.pushButton.setEnabled(True)
            msg.exec()
            
    def show_error_popup(self):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Error')
        msg.setText('An Error Has Occured Try Again!     ')
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        self.set_bar_0()
        self.show_bar(False)
        self.pushButton.setEnabled(True)
        msg.exec()
        
    def show_success_popup(self,text=None):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Success')
        if text:
            msg.setText(f'{text}     ')
        else:
            msg.setText('Installation completed!     ')
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        self.set_bar_0()
        self.show_bar(False)
        self.pushButton.setEnabled(True)
        msg.exec()
        
    def error_handler(self, n,normal=True):
        with open('log.txt', 'a') as f:
            f.write(f'[maingui.py, Thread logs] \n{current_time}\n\n')
            f.write(n[2])
            f.write(f'{82*"-"}\n')
        if normal:
            self.show_error_popup()
        else:
            msg = 'An Error Has Occured Try Again!'
            msg_details = f'{n[1]}'
            self.error_msg(msg,msg_details,"Error",True)

    def run_success(self,value):
        if value == 0:
            self.show_success_popup()
        else:
            self.error_msg(*value)

    def main_Progress(self, n):
        total = self.mainprogressBar.value()
        total += n
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

    def clear_cache(self):
        def remove_file():
            def remove_(path, mode='file'):
                if mode == 'file':
                    if os.path.exists(path):
                        os.remove(path)
                    else:
                        pass

                elif mode == 'dir':
                    try:
                        shutil.rmtree(path)

                    except OSError as e:
                        pass

            remove_('config.txt')
            remove_('log.txt')
            remove_('Downloads', 'dir')
            remove_('__pycache__', 'dir')
            remove_('.qt_for_python', 'dir')
            
            
        worker = Worker(lambda *ars, **kwargs: remove_file())
        worker.signals.error.connect(self.error_handler)
        
        self.threadpool.start(worker)
        worker.signals.finished.connect(lambda: self.show_success_popup(text = "Cache Files Cleared Successfully!"))

    def set_wait_time(self):
        window = QtWidgets.QWidget()
        i, okPressed = QtWidgets.QInputDialog.getInt(
            window, "Set Wait Time", "Wait time:", 5, 0, 100, 1)
        if okPressed:
            with open('./config.txt', 'w') as f:
                f.write(f'wait_time:{i}')

    def run_installer(self):
        fname = QtWidgets.QFileDialog.getOpenFileNames()
        worker = Worker(lambda *args,**kwargs: install(path=fname[0][0]))
        self.threadpool.start(worker)
        worker.signals.result.connect(self.run_success)

    def openWindow(self):
        self.window = QtWidgets.QMainWindow()
        newWindow = url_window(self.window)
        newWindow.closed.connect(self.runner)
            
    def runner(self, arg):
        worker = Worker(lambda **kwargs: self.parser(arg, **kwargs))
        worker.signals.result.connect(self.post_runner)
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.progress.connect(self.progress)
        worker.signals.error.connect(lambda *arg,**kwargs: self.error_handler(normal=False,*arg,**kwargs))
        self.threadpool.start(worker)

        self.pushButton.setEnabled(False)
        self.show_bar(True)

    def post_runner(self, arg):
        worker = Worker(lambda **kwargs: self.installer(arg, **kwargs))
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.result.connect(self.run_success)
        worker.signals.progress.connect(self.progress)
        worker.signals.error.connect(self.error_handler)
        self.threadpool.start(worker)

    def parser(self, data_args, progress_current, progress_main, progress):
        progress_main.emit(20)
        
        progress_current.emit(10)
        data_dict = dict(get_data(data_args))
        progress.emit(40)
        parse_data = parse_dict(data_dict)
        progress.emit(50)
        return parse_data
        

    def installer(self, data,  progress_current, progress_main, progress):
        main_dict, final_data = data
        dwnpath = './Downloads/'

        def Handle_Progress(blocknum, blocksize, totalsize):
            # calculate the progress
            readed_data = blocknum * blocksize
            if totalsize > 0:
                download_percentage = readed_data * 100 / totalsize
                progress_current.emit(download_percentage)

        if not os.path.exists(dwnpath):
            os.makedirs(dwnpath)

        progress_main.emit(40)
        path_lst = list()
        for f_name in final_data:
            # Define the remote file to retrieve
            remote_url = main_dict[f_name]
            # Download remote and save locally
            path = f"{dwnpath}{f_name}"
            if not os.path.exists(path):  # simple cache for same version downloads
                request.urlretrieve(remote_url, path, Handle_Progress)
                progress_main.emit(2)
            path_lst.append(path)
        progress_main.emit(10)
        return install(lst=path_lst)


def main():
    app = QtWidgets.QApplication(sys.argv)
    MainProgram = QtWidgets.QMainWindow()
    ui = MainWindowGui()
    ui.setupUi(MainProgram)
    MainProgram.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
