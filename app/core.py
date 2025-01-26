import asyncio
import os
import subprocess
import time
from datetime import datetime
from threading import Event

from pypdl import Pypdl
from PyQt6.QtCore import QThreadPool
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox

from modules.gui import Ui_MainProgram
from modules.url_gen import url_generator
from utls import Worker, default_logger

script_dir = os.path.dirname(os.path.abspath(__file__))


class internal_func(Ui_MainProgram):
    def __init__(self):
        super().__init__()

    def error_msg(self, text, msg_details, title="Error", critical=False):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(f"{str(text)}     ")
        if critical:
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowIcon(QIcon(f"{script_dir}/data/images/error_r.png"))
        else:
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowIcon(QIcon(f"{script_dir}/data/images/error_y.png"))
        msg.setDetailedText(
            str(msg_details) + "\n\ncheck Full Logs [Help --> Open Logs]"
        )
        if text == "Failed To Clear Cache Files!":
            pass
        else:
            self.set_bar_0()
            self.show_bar(False)
            self.stop_btn.hide()
            self.pushButton.setEnabled(True)
            self.advancedmenu.setEnabled(True)
            self.actionclear_cache.setEnabled(True)
            self.actioninstall_From_File.setEnabled(True)
            self.actionget_using_url.setEnabled(True)
            self.pushButton.show()
        msg.exec()

    def show_error_popup(self, txt="An Error Has Occured Try Again!"):
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        msg.setWindowIcon(QIcon(f"{script_dir}/data/images/error_r.png"))
        msg.setText(f"{txt}     ")
        msg.setIcon(QMessageBox.Icon.Critical)
        if txt in ("No Logs Found!", "No Downloads Found!"):
            pass
        else:
            self.set_bar_0()
            self.show_bar(False)
            self.stop_btn.hide()
            self.pushButton.setEnabled(True)
            self.advancedmenu.setEnabled(True)
            self.actionclear_cache.setEnabled(True)
            self.actioninstall_From_File.setEnabled(True)
            self.actionget_using_url.setEnabled(True)
            self.pushButton.show()
        msg.exec()

    def show_success_popup(self, text=None):
        msg = QMessageBox()
        msg.setWindowTitle("Success")
        msg.setWindowIcon(QIcon(f"{script_dir}/data/images/success.png"))
        if text:
            msg.setText(f"{text}     ")
        else:
            msg.setText("Installation completed!     ")
        msg.setIcon(QMessageBox.Icon.Information)

        if text == "Cache Files Cleared Successfully!":
            print("Cache Files Cleared")
        else:
            self.set_bar_0()
            self.show_bar(False)
            self.stop_btn.hide()
            self.pushButton.setEnabled(True)
            self.advancedmenu.setEnabled(True)
            self.actionclear_cache.setEnabled(True)
            self.actioninstall_From_File.setEnabled(True)
            self.actionget_using_url.setEnabled(True)
            self.pushButton.show()
        msg.exec()

    def error_handler(self, n, normal=True, msg=None, critical=True):
        def log_error():
            # if path exits or not
            if os.path.exists("log.txt"):
                mode = "a"
            else:
                mode = "w"
            # write to the log file
            with open(f"{script_dir}/log.txt", mode) as f:
                current_time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
                f.write(f"[python logs] \n{current_time}\n\n")
                f.write(n[2])
                f.write(f"{82 * '-'}\n")

        # if normal show a simple popup
        if normal:
            log_error()
            self.show_error_popup()
        else:
            msg_details = f"{n[1]}"
            if msg_details == "Stoped By User!":
                self.show_success_popup("Download Stopped!")
            elif msg_details == "server returned a empty list":
                msg = "Sorry, Application not found!"
                msg_details = (
                    "Application not found in the server, Application is not supported!"
                )
                self.error_msg(msg, msg_details, "Error", critical)
            else:
                log_error()
                if msg is None:
                    msg = "An Error Has Occured Try Again!"
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
        close.setWindowIcon(QIcon(f"{script_dir}/data/images/error_y.png"))
        close.setText("Are you sure you want to exit?     ")
        close.setIcon(QMessageBox.Icon.Warning)
        close.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        close = close.exec()

        if close == QMessageBox.StandardButton.Yes:
            try:
                self.window.close()
            except:
                pass
            event.accept()
        else:
            event.ignore()


class core(internal_func):
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.url = None
        self.window = None
        self.stop = Event()
        self.ignore_ver = False
        self.all_dependencies = False

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
        worker = Worker(
            lambda **kwargs: asyncio.run(
                url_generator(
                    str(arg),
                    self.ignore_ver,
                    self.all_dependencies,
                    self.stop,
                    emit=True,
                    **kwargs,
                )
            )
        )
        worker.signals.result.connect(self.download_install)
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.error.connect(lambda arg: self.error_handler(arg, normal=False))
        self.threadpool.start(worker)

        self.pushButton.setEnabled(False)
        self.advancedmenu.setEnabled(False)
        self.actionclear_cache.setEnabled(False)
        self.actioninstall_From_File.setEnabled(False)
        self.actionget_using_url.setEnabled(False)
        self.show_bar(True)
        self.pushButton.hide()
        self.stop_btn.show()

    def download_install(self, arg):
        if arg is None:
            raise Exception("Stoped By User!")

        def download_install_thread(data, progress_current, progress_main):
            main_dict, final_data, file_name, uwp = data
            part = int(50 / len(final_data))
            if self.actionDedicated_Folder.isChecked():
                app_folder = "".join(file_name.split(".")[:-1])
                dwnpath = f"{script_dir}//downloads//{app_folder}/"
            else:
                dwnpath = f"{script_dir}//downloads/"
            if not os.path.exists(dwnpath):
                os.makedirs(dwnpath)
            path_lst = {}
            logger, handler = default_logger("Downloader")
            d = Pypdl(allow_reuse=True, logger=logger)
            for f_name in final_data:
                # Define the remote file to retrieve
                remote_url = main_dict[f_name]  # {f_name:url}
                # Download remote and save locally
                path = f"{dwnpath}{f_name}"

                async def new_url_gen():
                    urls = await url_generator(
                        self.url,
                        self.ignore_ver,
                        self.all_dependencies,
                        self.stop,
                        progress_current,
                        progress_main,
                        emit=False,
                    )

                    return urls[0][f_name]

                future = d.start(
                    url=remote_url,
                    file_path=path,
                    segments=10,
                    retries=3,
                    mirrors=new_url_gen,
                    block=False,
                    display=False,
                    overwrite=False,
                )

                while not d.completed:
                    download_percentage = int(d.progress) if d.progress else 0
                    progress_current.emit(download_percentage)
                    time.sleep(0.1)
                    if self.stop.is_set():  # check if the stop event is triggered
                        d.shutdown()
                        handler.close()
                        raise Exception("Stoped By User!")

                if len(d.failed) == d.total_task:
                    d.shutdown()
                    handler.close()
                    raise Exception("Download Error Occured!")

                progress_main.emit(part)

                fname_lower = (f_name.split(".")[1].split("_")[0]).lower()
                if file_name in fname_lower:
                    path_lst[path] = 1
                else:
                    path_lst[path] = 0

                future.result()
            d.shutdown()

            handler.close()
            return path_lst, uwp  # install the apps'

        worker = Worker(lambda **kwargs: download_install_thread(arg, **kwargs))
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        if self.actionDownload_Mode.isChecked():
            worker.signals.result.connect(
                lambda arg: self.show_success_popup("Download Completed!")
            )
        else:
            worker.signals.result.connect(self.install)
        worker.signals.error.connect(lambda arg: self.error_handler(arg, normal=False))
        self.threadpool.start(worker)

    def install(self, arg, **kwargs):
        self.stop_btn.hide()
        self.pushButton.show()

        def install_thread(path, progress_current, progress_main, uwp, val=True):
            def run(command):
                output = subprocess.run(
                    [
                        "C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe",
                        command,
                    ],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True,
                    text=True,
                )
                return output

            flag = 0
            main_prog_error = 0
            part = int((100 - self.mainprogressBar.value()) / len(path))

            for s_path in path.keys():
                progress_current.emit(10)
                if uwp:
                    output = run(f'Add-AppPackage "{s_path}"')
                else:
                    output = run(f'Start-Process "{s_path}"')

                if not output.returncode == 0:
                    flag = 1
                    if path[s_path] == 1:
                        main_prog_error = 1

                    with open(f"{script_dir}/log.txt", "a") as f:
                        current_time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
                        f.write(f"[powershell logs] \n{current_time}\n\n")
                        f.write(f"command: {output.args[1]}\n\n")
                        f.write(output.stderr)
                        f.write(f"{82 * '-'}\n")
                progress_current.emit(100)
                time.sleep(0.3)
                progress_main.emit(part)

            if flag == 1:
                # if the failed commands include the application package then show app not installed
                if main_prog_error == 1:
                    msg = "Failed To Install The Application!"
                    detail_msg = "The Installation has failed, try again!"
                    endresult = (msg, detail_msg, "Error", True)

                else:
                    msg = "Failed To Install Dependencies!"
                    detail_msg = "In some cases, this occurs since the dependencies are already installed on your pc. "
                    detail_msg += "So check wheather the program is installed from start menu.\n\n"
                    detail_msg += "if the app is not installed, Enable [Advanced --> Dependencies --> Ignore Version], "
                    detail_msg += "If the problem still exists Enable [Advanced --> Dependencies --> Ignore All Filters]"
                    endresult = (msg, detail_msg, "Warning")
                return endresult
            return 0

        # for standalone installer

        if isinstance(arg, str):
            path = {arg: 1}
            # if val is set to false then it wont update the progressbar
            return install_thread(path, val=False, uwp=True, **kwargs)

        path, uwp = arg
        # done this way since we can only manupulate the buttons and other qt components inside of the main thread if not it can cause issues
        worker = Worker(lambda **kwargs: install_thread(path, uwp=uwp, **kwargs))
        worker.signals.cur_progress.connect(self.cur_Progress)
        worker.signals.main_progress.connect(self.main_Progress)
        worker.signals.result.connect(self.run_success)
        worker.signals.error.connect(lambda arg: self.error_handler(arg, normal=False))
        self.threadpool.start(worker)
