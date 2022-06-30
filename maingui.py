import os
import shutil
import sys
import time
import traceback

from PyQt6 import QtWidgets
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from downloader import Downloader
from get_url import url_window
from gui import Ui_MainProgram
from utls import current_time, get_data, install, open_browser, parse_dict
from PyQt6.QtGui import QIcon

try:
    os.chdir(sys._MEIPASS)
except Exception:
    pass

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
        self.url = None
        self.stop = False
            
    def setupUi(self, *args, **kwargs):
        Ui_MainProgram.setupUi(self, *args, **kwargs)
        self.set_bar_0()
        self.show_bar(False)
        self.pushButton.clicked.connect(self.openWindow)
        self.stop_btn.clicked.connect(self.stop_func)
        self.stop_btn.hide()
        self.actioninstall_From_File.triggered.connect(
            self.run_installer)
        self.actionclear_cache.triggered.connect(self.clear_cache)
        self.actionCheck_For_Updates.triggered.connect(lambda: open_browser(
            'https://github.com/m-jishnu/Windows-Store-App-Installer/releases'))
        self.actionAbout.triggered.connect(lambda: open_browser(
            'https://github.com/m-jishnu/Windows-Store-App-Installer'))
        self.actionHelp.triggered.connect(lambda: open_browser(
            'https://discord.com/invite/cbuEkpd'))
        self.actionOpen_Logs.triggered.connect(self.open_Logs)


    def error_msg(self, text,msg_details,title="Error",critical = False):
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle(title)
            msg.setText(f'{str(text)}     ')
            if critical:
                msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                msg.setWindowIcon(QIcon('./Images/error_r.png'))
            else:
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setWindowIcon(QIcon('./Images/error_y.png'))
            msg.setDetailedText(str(msg_details) + '\n\ncheck Full Logs [Help --> Open Logs]')
            self.set_bar_0()
            self.show_bar(False)
            self.stop_btn.hide()
            self.pushButton.setEnabled(True)
            self.pushButton.show()
            msg.exec()
            
    def show_error_popup(self,txt="An Error Has Occured Try Again!"):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Error')
        msg.setWindowIcon(QIcon('./Images/error_r.png'))
        msg.setText(f'{txt}     ')
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        self.set_bar_0()
        self.show_bar(False)
        self.stop_btn.hide()
        self.pushButton.setEnabled(True)
        self.pushButton.show()      
        msg.exec()
        
    def show_success_popup(self,text=None):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Success')
        msg.setWindowIcon(QIcon('./Images/success.png'))
        if text:
            msg.setText(f'{text}     ')
        else:
            msg.setText('Installation completed!     ')
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        self.set_bar_0()
        self.show_bar(False)
        self.stop_btn.hide()
        self.pushButton.setEnabled(True)
        self.pushButton.show() 
        msg.exec()
        
    def error_handler(self, n,normal=True,msg = None):
        if os.path.exists('log.txt'):
            mode = 'a'
        else:
            mode = 'w'
        with open('log.txt', mode) as f:
            f.write(f'[maingui.py, Thread logs] \n{current_time}\n\n')
            f.write(n[2])
            f.write(f'{82*"-"}\n')
        if normal:
            self.show_error_popup()
        else:
            if msg == None:
                msg = 'An Error Has Occured Try Again!'
            else:
                msg = f'{n[1]}'
            msg_details = f'{n[1]}'
            self.error_msg(msg,msg_details,"Error",True)

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
        self.pushButton.show()
        self.pushButton.setEnabled(True)
        self.show_bar(False)
    

    def open_Logs(self):
        path = 'log.txt'
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.show_error_popup(txt="No Logs Found!")

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

            remove_('log.txt')
            remove_('Downloads', 'dir')
            remove_('__pycache__', 'dir')
            remove_('.qt_for_python', 'dir')
            
            
        worker = Worker(lambda *ars, **kwargs: remove_file())
        worker.signals.error.connect(self.error_handler)
        
        self.threadpool.start(worker)
        worker.signals.finished.connect(lambda: self.show_success_popup(text = "Cache Files Cleared Successfully!"))
    
    def run_installer(self):
        fname = QtWidgets.QFileDialog.getOpenFileNames()
        worker = Worker(lambda *args,**kwargs: install(fname[0][0]))
        self.threadpool.start(worker)
        worker.signals.result.connect(self.run_success)

    def openWindow(self):
        self.stop = False
        self.window = QtWidgets.QMainWindow()
        self.window.setWindowIcon(QIcon('./Images/search.png'))
        newWindow = url_window(self.window)
        newWindow.closed.connect(self.pre_runner)
        
    def pre_runner(self, arg):
        self.url = arg
        self.runner(self.url)
            
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
        worker.signals.error.connect(lambda *arg,**kwargs: self.error_handler(normal=False,*arg,msg=True))
        self.threadpool.start(worker)
        
        self.stop_btn.show()
       

    def parser(self, data_args, progress_current, progress_main, progress):
        progress_main.emit(20)
        progress_current.emit(10)
        data_dict = get_data(str(data_args))
        progress.emit(40)
        parse_data = parse_dict(data_dict)
        progress.emit(50)
        return parse_data
        

    def installer(self, data,  progress_current, progress_main, progress):
        main_dict, final_data,file_name = data
        abs = os.getcwd()
        dwnpath = f'{abs}/Downloads/'
        if not os.path.exists(dwnpath):
            os.makedirs(dwnpath)

        progress_main.emit(40)
        path_lst = dict()
        for f_name in final_data:
            # Define the remote file to retrieve
            remote_url = main_dict[f_name] # ,get_data(self.url)[0][f_name] #(main_dict,f_name)[0] = main_dict ={f_name:url}
            # Download remote and save locally
            path = f"{dwnpath}{f_name}"
            if not os.path.exists(path): #don't download if it exists already
                
                d = Downloader()
                def f_download(url,path,threads):
                    time.sleep(2)
                    try:
                        d.download(url,path,threads)
                    except:
                        print("download failed getting new url directly!")
                        for _ in range(10):
                            time.sleep(4)
                            try:
                                url = get_data(self.url)[0][f_name]     #getting the new url from the api
                                d.download(url,path,threads)
                                break      # as soon as it works, break out of the loop
                            except:
                                print("exception occured: ",_)
                                continue
                        d.alive = False
                            
                worker = Worker(lambda *args,**kwargs: f_download(remote_url,path,10)) #concurrent download so we can get the download progress
                self.threadpool.start(worker)
                
                while d.progress !=100 and d.alive == True:
                    download_percentage = int(d.progress)
                    progress_current.emit(download_percentage)
                    time.sleep(0.2)
                    if self.stop:
                        d.dic['paused'] = self.stop
                        break
                progress_main.emit(2)
                
                if self.stop:
                    raise Exception("Stoped By User!")
                
                if d.alive ==False:
                    raise Exception("Download Error Occured Try again Later!")
                
            fname_lower = (f_name.split(".")[1].split("_")[0]).lower()
            if file_name in fname_lower:
                path_lst[path]=1
            else:
                path_lst[path]=0
        progress_main.emit(100)
        return install(path_lst)

def main():
    app = QtWidgets.QApplication(sys.argv)
    MainProgram = QtWidgets.QMainWindow()
    ui = MainWindowGui()
    ui.setupUi(MainProgram)
    MainProgram.setWindowIcon(QIcon('./Images/main.ico'))
    MainProgram.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
