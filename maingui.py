import os
import shutil
import sys
import time
import traceback

from PyQt6.QtCore import (QObject, QRunnable, Qt, QThreadPool, pyqtSignal,
                          pyqtSlot)
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QMainWindow

from downloader import Downloader
from get_url import url_window
from misc import Miscellaneous
from utls import install, open_browser
from url_gen import get_data

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


class MainWindowGui(Miscellaneous):
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.url = None
        self.stop = False
        self.window_open = True

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
            'https://discord.com/invite/cbuEkpd'))
        self.actionOpen_Logs.triggered.connect(self.open_Logs)
        self.actionDownloads.triggered.connect(self.open_downloads)

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
            remove_('Downloads', 'dir')

        worker = Worker(lambda *ars, **kwargs: remove_file())
        worker.signals.error.connect(lambda arg: self.error_handler(
            arg, normal=False, msg="Failed To Clear Cache Files!", critical=False))

        self.threadpool.start(worker)
        worker.signals.result.connect(lambda: self.show_success_popup(
            text="Cache Files Cleared Successfully!"))

    def open_downloads(self):
        path = os.path.realpath("./Downloads")
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.show_error_popup(txt="No Downloads Found!")

    # standalone installer for predownloaded files
    def standalone_installer(self):
        fname = QFileDialog.getOpenFileNames()
        worker = Worker(lambda *args, **kwargs: install(fname[0][0]))
        self.threadpool.start(worker)
        worker.signals.result.connect(self.run_success)

    def openWindow(self):
        self.stop = False

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
            self.window.show()
            # overiding close event for effictive memory management
            self.window.closeEvent = close
            search_app.closed.connect(self.parser)

    def parser(self, arg):

        def parser_thread(data_args, progress_current, progress_main, progress):
            progress_main.emit(20)
            progress_current.emit(10)
            #returning the parsed data
            data_dict = get_data(str(data_args))
            progress.emit(90)
            return data_dict

        self.url = arg  # saving the url for future uses
        worker = Worker(lambda **kwargs: parser_thread(arg, **kwargs))
        worker.signals.result.connect(self.download_install)
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.progress.connect(self.progress)
        worker.signals.error.connect(
            lambda arg: self.error_handler(arg, normal=False))
        self.threadpool.start(worker)

        self.pushButton.setEnabled(False)
        self.show_bar(True)

    def download_install(self, arg):


        def download_install_thread(data,  progress_current, progress_main, **kwargs):
            main_dict, final_data, file_name = data
            abs_path = os.getcwd()
            dwnpath = f'{abs_path}/Downloads/'
            if not os.path.exists(dwnpath):
                os.makedirs(dwnpath)

            progress_main.emit(40)
            path_lst = {}
            for f_name in final_data:
                # Define the remote file to retrieve
                remote_url = main_dict[f_name]  # {f_name:url}
                # Download remote and save locally
                path = f"{dwnpath}{f_name}"
                if not os.path.exists(path):  # don't download if it exists already

                    d = Downloader()

                    def f_download(url, path, threads):
                        time.sleep(2)
                        try:
                            d.download(url, path, threads)
                        except:
                            print("download failed getting new url directly!")
                            for _ in range(10):
                                time.sleep(4)
                                try:
                                    # getting the new url from the api
                                    url = get_data(self.url)[0][f_name]
                                    d.download(url, path, threads)
                                    success = True
                                    break      # as soon as it works, break out of the loop
                                except:
                                    print("exception occured: ", _)
                                    continue
                            if success is not True:
                                d.alive = False

                    # concurrent download so we can get the download progress
                    worker = Worker(
                        lambda *args, **kwargs: f_download(remote_url, path, 20))
                    self.threadpool.start(worker)

                    while d.progress != 100 and d.alive is True:
                        download_percentage = int(d.progress)
                        progress_current.emit(download_percentage)
                        time.sleep(0.2)
                        if self.stop:
                            d.dic['paused'] = self.stop
                            time.sleep(3)
                            break
                    progress_main.emit(2)

                    if self.stop:
                        raise Exception("Stoped By User!")

                    if d.alive is False:
                        raise Exception(
                            "Download Error Occured Try again Later!")

                fname_lower = (f_name.split(".")[1].split("_")[0]).lower()
                if file_name in fname_lower:
                    path_lst[path] = 1
                else:
                    path_lst[path] = 0

            self.stop_btn.hide()
            self.pushButton.show()
            progress_main.emit(100)
            return install(path_lst)  # install the apps'

        worker = Worker(
            lambda **kwargs: download_install_thread(arg, **kwargs))
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.result.connect(self.run_success)
        worker.signals.progress.connect(self.progress)
        worker.signals.error.connect(
            lambda arg: self.error_handler(arg, normal=False))
        self.threadpool.start(worker)
        self.pushButton.hide()
        self.stop_btn.show()
