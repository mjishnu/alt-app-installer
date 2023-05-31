import os
import shutil
import sys
import time
import traceback
from datetime import datetime
from threading import Event

import clr
from PyQt6.QtCore import (QObject, QRunnable, Qt, QThreadPool, pyqtSignal,
                          pyqtSlot)
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QMainWindow

from downloader import Downloader
from get_url import url_window
from misc import DilalogBox, Miscellaneous
from url_gen import url_generator
from utls import open_browser

dll_path = os.path.abspath(r"data\System.Management.Automation.dll")
clr.AddReference(dll_path)

try:
    # changing directory to (__file__ directory),used for a single-file option in pyinstaller to display image properly
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


class MainWindowGui(Miscellaneous):
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.url = None
        self.stop = Event()
        self.ignore_ver = False
        self.all_dependencies = False

    def setupUi(self, *args, **kwargs):
        Miscellaneous.setupUi(self, *args, **kwargs)
        self.set_bar_0()
        self.show_bar(False)
        self.pushButton.clicked.connect(self.openWindow)
        self.stop_btn.clicked.connect(self.stop_func)
        self.stop_btn.hide()
        self.actioninstall_From_File.triggered.connect(
            self.standalone_installer)
        self.actionclear_cache.triggered.connect(self.clear_cache)
        self.actionCheck_For_Updates.triggered.connect(lambda: open_browser(
            'https://github.com/m-jishnu/alt-app-installer/releases'))
        self.actionAbout.triggered.connect(lambda: open_browser(
            'https://github.com/m-jishnu/alt-app-installer'))
        self.actionHelp.triggered.connect(lambda: open_browser(
            'https://discord.com/invite/9eeN2Wve4T'))
        self.actionOpen_Logs.triggered.connect(self.open_Logs)
        self.actionDownloads.triggered.connect(self.open_downloads)
        self.actionIgnore_Latest_Version.triggered.connect(self.ignore_version)
        self.actionIgnore_All_filters.triggered.connect(
            self.ignore_All_filters)
        self.actionInstall_using_url.triggered.connect(self.install_url)

    def ignore_version(self):
        if self.actionIgnore_Latest_Version.isChecked():
            self.ignore_ver = True
        else:
            self.ignore_ver = False

    def ignore_All_filters(self):
        if self.actionIgnore_All_filters.isChecked():
            self.all_dependencies = True
            self.actionIgnore_Latest_Version.setChecked(True)
            self.actionIgnore_Latest_Version.setEnabled(False)
        else:
            self.all_dependencies = False
            self.actionIgnore_Latest_Version.setChecked(False)
            self.actionIgnore_Latest_Version.setEnabled(True)

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
                    shutil.rmtree(path)

            remove_('log.txt')
            try:
                remove_('downloads', 'dir')
            except FileNotFoundError:
                print("No Downloads Found!")

        worker = Worker(lambda *ars, **kwargs: remove_file())
        worker.signals.error.connect(lambda arg: self.error_handler(
            arg, normal=False, msg="Failed To Clear Cache Files!", critical=False))

        self.threadpool.start(worker)
        worker.signals.result.connect(lambda: self.show_success_popup(
            text="Cache Files Cleared Successfully!"))

    def open_downloads(self):
        path = os.path.realpath("./downloads")
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.show_error_popup(txt="No Downloads Found!")

    # standalone installer for predownloaded files
    def standalone_installer(self):
        def error(arg):
            self.pushButton.setEnabled(True)
            self.show_bar(False)

        fname = QFileDialog.getOpenFileNames()[0]
        if fname:
            worker = Worker(lambda **kwargs: self.install(fname[0], **kwargs))
            worker.signals.cur_progress.connect(self.cur_Progress)
            worker.signals.main_progress.connect(self.main_Progress)
            worker.signals.result.connect(self.run_success)
            worker.signals.error.connect(error)
            self.threadpool.start(worker)
            self.show_bar(True)
            self.pushButton.setEnabled(False)
            self.menuDependencies.setEnabled(False)
            self.actionclear_cache.setEnabled(False)
            self.actioninstall_From_File.setEnabled(False)
            self.actionInstall_using_url.setEnabled(False)
            # if the app selector window is open closing it
            try:
                self.window.close()
                self.window.deleteLater()
                del self.window
            except:
                pass

    def install_url(self):
        window = DilalogBox()
        window.closed.connect(self.parser)
        window.exec()

    def openWindow(self):
        # close event for the new window
        def close(event):
            self.window.deleteLater()
            del self.window
            event.accept()

        try:
            self.window  # checking if self.window already exist
        except:
            self.window = False  # if not set it to false aka the window is not open

        if self.window:  # if it has value then change focus to the already open window
            self.window.setWindowState(self.window.windowState(
            ) & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)  # if minimized then unminimize
            self.window.activateWindow()  # set focus to the currently open window
        else:  # open a new window
            self.window = QMainWindow()
            self.window.setWindowIcon(QIcon('./data/images/search.png'))
            search_app = url_window()
            search_app.setupUi(self.window)
            # overding the new window close event for proper cleanup
            self.window.closeEvent = close
            self.window.show()
            search_app.closed.connect(self.parser)

    def parser(self, arg):
        self.stop.clear()
        # if the window is open closing it before starting the parser
        try:
            self.window.close()
            self.window.deleteLater()
            del self.window
        except:
            pass

        self.url = arg  # saving the url for future uses
        worker = Worker(lambda **kwargs: url_generator(str(arg), self.ignore_ver,
                                                       self.all_dependencies, self.stop, emit=True, **kwargs))
        worker.signals.result.connect(self.download_install)
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.error.connect(
            lambda arg: self.error_handler(arg, normal=False))
        self.threadpool.start(worker)

        self.pushButton.setEnabled(False)
        self.menuDependencies.setEnabled(False)
        self.actionclear_cache.setEnabled(False)
        self.actioninstall_From_File.setEnabled(False)
        self.actionInstall_using_url.setEnabled(False)
        self.show_bar(True)
        self.pushButton.hide()
        self.stop_btn.show()

    def download_install(self, arg):
        if arg is None:
            raise Exception("Stoped By User!")

        def download_install_thread(data,  progress_current, progress_main):
            main_dict, final_data, file_name = data
            part = int(50 / len(final_data))
            abs_path = os.getcwd()
            dwnpath = f'{abs_path}/downloads/'
            if not os.path.exists(dwnpath):
                os.makedirs(dwnpath)
            path_lst = {}
            d = Downloader(self.stop)
            for f_name in final_data:
                # Define the remote file to retrieve
                remote_url = main_dict[f_name]  # {f_name:url}
                # Download remote and save locally
                path = f"{dwnpath}{f_name}"
                if not os.path.exists(path):  # don't download if it exists already
                    new_url_gen = lambda: url_generator(self.url, self.ignore_ver, self.all_dependencies,
                                                            self.stop, progress_current, progress_main, emit=False)[0][f_name]
                    
                    d.start(remote_url, path, 20,retries=5, retry_func=new_url_gen,block=False)
                    while d.progress != 100:
                        download_percentage = int(d.progress)
                        progress_current.emit(download_percentage)
                        time.sleep(0.1)
                        if self.stop.is_set():  # check if the stop event is triggered
                            raise Exception("Stoped By User!")
                        elif d.Failed:  
                            raise Exception("Download Error Occured!")

                    progress_main.emit(part)

                fname_lower = (f_name.split(".")[1].split("_")[0]).lower()
                if file_name in fname_lower:
                    path_lst[path] = 1
                else:
                    path_lst[path] = 0
            return path_lst  # install the apps'

        worker = Worker(
            lambda **kwargs: download_install_thread(arg, **kwargs))
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.result.connect(self.install)
        worker.signals.error.connect(
            lambda arg: self.error_handler(arg, normal=False))
        self.threadpool.start(worker)

    def install(self, arg, **kwargs):
        # importing the system management.Automation dlls powershell funcs
        from System.Management.Automation import PowerShell

        self.stop_btn.hide()
        self.pushButton.show()

        def install_thread(path, progress_current, progress_main, val=True):
            flag = 0
            main_prog_error = 0
            part = int((100 - self.mainprogressBar.value()) / len(path))

            # helper func for getting progress from powershell
            def Progress(source, e):
                prog = int(source[e.Index].PercentComplete)
                # to remove -1 from the progress bar
                progress_current.emit(prog if prog > 0 else 0)
                if not val:
                    progress_main.emit(prog if prog > 0 else 0)

            # helper func for getting error from powershell
            def error(source, e):
                nonlocal flag, main_prog_error

                flag = 1
                if path[s_path] == 1:
                    main_prog_error = 1

                with open('log.txt', 'a') as f:
                    current_time = datetime.now().strftime(
                        "[%d-%m-%Y %H:%M:%S]")
                    f.write(f'[powershell logs] \n{current_time}\n\n')
                    f.write(f'Package Name: {s_path.split("/")[-1]}\n\n')
                    f.write(str(source[e.Index].Exception.Message))
                    f.write(f'{82*"-"}\n')

            for s_path in path.keys():
                # C# command run using pythonnet via system.management.automation dll
                ps = PowerShell.Create()
                ps.Streams.Progress.DataAdded += Progress
                ps.Streams.Error.DataAdded += error
                ps.AddCommand("Add-AppxPackage")
                ps.AddParameter("Path", s_path)

                try:
                    ps.Invoke()
                except Exception as e:
                    print(e)

                time.sleep(0.3)
                progress_main.emit(part)

            # if the failed commands include the application package then show app not installed
            if main_prog_error == 1:
                msg = 'Failed To Install The Application!'
                detail_msg = 'The Installation has failed, try again!'
                endresult = (msg, detail_msg, "Error", True)

            else:
                msg = 'Failed To Install Dependencies!'
                detail_msg = 'In some cases, this occurs since the dependencies are already installed on your pc. '
                detail_msg += 'So check wheather the program is installed from start menu.\n\n'
                detail_msg += 'if the app is not installed, Enable [Dependencies --> Ignore Version], '
                detail_msg += 'If the problem still exists Enable [Dependencies --> Ignore All Filters]'
                endresult = (msg, detail_msg, "Warning")
            if flag != 0:
                return endresult
            return 0
        # for standalone installer
        if isinstance(arg, str):
            path = {arg: 1}
            # if val is set to false then it wont update the progressbar
            return install_thread(path, val=False, **kwargs)

        # done this way since we can only manupulate the buttons and other qt components inside of the main thread if not it can cause issues
        worker = Worker(lambda **kwargs: install_thread(arg, **kwargs))
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.result.connect(self.run_success)
        worker.signals.error.connect(
            lambda arg: self.error_handler(arg, normal=False))
        self.threadpool.start(worker)
