from ast import If
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback
import warnings
import webbrowser
from datetime import datetime
from subprocess import CREATE_NO_WINDOW
from urllib import request

import chromedriver_autoinstaller
from PyQt6 import QtWidgets
from PyQt6.QtCore import (QObject, QProcess, QRunnable, QThreadPool,
                          pyqtSignal, pyqtSlot)
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from get_url import MainWindow
from Gui import Ui_MainProgram


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
        self.current_time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")

    def setupUi(self, *args, **kwargs):
        Ui_MainProgram.setupUi(self, *args, **kwargs)
        self.set_bar_0()
        self.show_bar(False)
        self.pushButton.clicked.connect(self.openWindow)
        self.actioninstall_From_File.triggered.connect(
            self.run_installer)
        self.actionSet_Wait_Time.triggered.connect(self.set_wait_time)
        self.actionclear_cache.triggered.connect(self.clear_cache)
        self.actionCheck_For_Updates.triggered.connect(lambda: self.open_browser(
            'https://github.com/m-jishnu/Windows-Store-App-Installer/releases'))
        self.actionAbout.triggered.connect(lambda: self.open_browser(
            'https://github.com/m-jishnu/Windows-Store-App-Installer'))
        self.actionHelp.triggered.connect(lambda: self.open_browser(
            'https://discord.com/invite/cbuEkpd'))
        self.actionOpen_Logs.triggered.connect(self.open_Logs)

    def open_browser(self, arg):
        webbrowser.open(arg)

    def open_Logs(self):
        path = 'log.txt'
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.show_error_popup()

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

    def run_success(self,value):
        if value == 0:
            self.show_success_popup()
        else:
            self.error_msg(*value)


    def run_installer(self):
        fname = QtWidgets.QFileDialog.getOpenFileNames()
        worker = Worker(lambda *args,**kwargs: self.install(path=fname[0][0]))
        self.threadpool.start(worker)
        worker.signals.result.connect(self.run_success)

    def openWindow(self):
        self.window = QtWidgets.QMainWindow()
        newWindow = MainWindow(self.window)
        newWindow.closed.connect(self.runner)

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

    def error_handler(self, n,normal=True):
        with open('log.txt', 'a') as f:
            f.write(f'[maingui.py, Thread logs] \n{self.current_time}\n\n')
            f.write(n[2])
            f.write(f'{82*"-"}\n')
        if normal:
            self.show_error_popup()
        else:
            msg = 'An Error Has Occured Try Again!'
            msg_details = f'{n[1]}'
            self.error_msg(msg,msg_details,"Error",True)
            
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

    def parser(self, data_args, progress_current, progress_main, progress):

        def pg(arg):
            progress.emit(arg)

        # ignoring unwanted warning
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        def get_time():
            if not os.path.exists('./config.txt'):
                with open('./config.txt', 'w') as f:
                    f.write('wait_time:5')

            with open('./config.txt', 'r') as f:
                file_n = f.read()
                pattern = re.compile(r"([a-z_]+):(\d)")
                return int(pattern.search(str(file_n)).group(2))

        wait_time = get_time()

        pg(10)
        progress_main.emit(20)

        # parsing and getting product id

        def product_id_getter(wrd):
            try:
                pattern = re.compile(r".+\/([a-zA-Z-]+)\/([a-zA-Z0-9]+)|.+")
                matches = pattern.search(str(wrd))
                return matches.group(2)
            except AttributeError:
                raise Exception(
                    'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')

        # passing parsed data into product id
        product_id = product_id_getter(str(data_args))

        # adding option to hide browser window
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")  # fatal
        chrome_service = ChromeService(chromedriver_autoinstaller.install(cwd=True))
        chrome_service.creationflags = CREATE_NO_WINDOW

        # path of driver
        driver = Chrome(options=options, service=chrome_service)
        driver.get("https://store.rg-adguard.net/")

        # inputing data
        # selecting type from the options [url,productId etc] here we choose productid
        select = Select(driver.find_element(
            by=By.XPATH, value=r"/html/body/div[1]/select[1]"))
        select.select_by_value("ProductId")
        pg(40)
        # selecting the box field and passing data to it
        box_field = driver.find_element(
            by=By.XPATH, value=r"/html/body/div[1]/input[1]")
        box_field.send_keys(product_id)

        # click on the submit button
        submit_button = driver.find_element(
            By.CSS_SELECTOR, r"body > div.center > input[type=button]:nth-child(8)"
        )
        pg(50)
        time.sleep(wait_time-1)
        pg(50)
        submit_button.click()
        time.sleep(wait_time+1)
        pg(50)
        # inputing data end --------------------------

        # get contents from site
        main_dict = {}
        file = driver.find_element(
            by=By.XPATH, value="/html/body/div[1]/div/table/tbody"
        ).text.split("\n")

        # geting length of the table
        length = len(file)

        # getting size of files
        splited = [i.split(" ") for i in file]
        size = dict()
        for i in splited:
            size[i[0]] = (i[-2], i[-1])

        # looping to get all elements and adding them to a dict with {name:url}
        for i in range(length):
            file = driver.find_element_by_xpath(
                f"/html/body/div[1]/div/table/tbody/tr[{i+1}]/td[1]/a"
            )

            main_dict[file.text] = file.get_attribute("href")

        driver.quit()

        # get contents from site end ---------------------
        pg(50)
        # full parsing
        data = list()
        bad_data = list()
        data_link = list()
        final_data = list()

        full_data = [i for i in main_dict.keys()]

        # using regular expression
        pattern = re.compile(r".+\.BlockMap")

        for i in full_data:

            matches = pattern.search(str(i))

            try:
                bad_data.append(matches.group(0))
            except AttributeError:
                pass

            if i not in bad_data:
                data_link.append(i)
                data.append(i.split("_"))

        for str_list in data:
            while "" in str_list:
                str_list.remove("")

        # making dict
        zip_obj = zip(data_link, data)
        dict_data = dict(zip_obj)

        # cleaning and only choosing latest version
        pg(50)

        def clean_dict(lst):
            for key1, value1 in lst.items():
                for key2, value2 in lst.items():
                    if (
                        value1[0] == value2[0]
                        and value1[2] == value2[2]
                        and value1[-1] == value2[-1]
                    ):
                        if value1[1] > value2[1]:
                            return key2

        try:
            del dict_data[clean_dict(dict_data)]
        except KeyError:
            pass
        # check device archtecture

        def is_os_64bit():
            if platform.machine().endswith("64"):
                return "x64"
            else:
                return "x86"

        # get appropriate keys

        for key, value in dict_data.items():
            if value[2] == is_os_64bit():
                final_data.append(key)
            elif value[2] == "neutral":
                final_data.append(key)

        # parsing end ----------------------------------
        pg(50)
        return (main_dict, final_data)

    def install(self, path=None, lst=None):
        if lst:
            all_paths = str()
            for path in lst:
                all_paths += f'Add-AppPackage "{path}";'
        elif path:
            all_paths = f'Add-AppPackage "{path}"'

        output = subprocess.run(
            ["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe", all_paths], capture_output=True)
        with open('log.txt', 'a') as f:
            f.write(f'[installer.py, powershell command logs] \n{self.current_time}\n')
            f.write(f'command: {output.args[1]}\n\n')    
            f.write(output.stderr.decode("utf-8"))           
            f.write(f'{82*"-"}\n')
            msg = 'Failed To Install The Application!'
            detail_msg = f'Command Execution Failed: {output.args[1]}'
            if output.returncode != 0:
                if lst != None:
                    detail_msg+='\nIn Some cases, the installation of dependencies was only unsuccessful since its already installed in your pc.\n'
                    detail_msg+='So check wheather the program is installed in start menu if not, try again!'
                    return (msg,detail_msg,"Warning")
                elif path != None:
                    detail_msg+='\nThe Installation has failed, try again!'
                    return (msg,detail_msg,"Error",True)
            return 0
            
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
        return self.install(lst=path_lst)


def main():
    app = QtWidgets.QApplication(sys.argv)
    MainProgram = QtWidgets.QMainWindow()
    ui = MainWindowGui()
    ui.setupUi(MainProgram)
    MainProgram.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
