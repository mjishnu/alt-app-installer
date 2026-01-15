import os
import shutil
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow

from core import core
from modules.app_selector import AppSelector
from utls import Ui_about, UrlBox, Worker, load_icon, open_browser

curr_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindowGui(core):
    def setupUi(self, *args, **kwargs):
        core.setupUi(self, *args, **kwargs)
        self.set_bar_0()
        self.show_bar(False)
        self.pushButton.clicked.connect(self.openWindow)
        self.stop_btn.clicked.connect(self.stop_func)
        self.stop_btn.hide()
        self.actioninstall_From_File.triggered.connect(self.standalone_installer)
        self.actionclear_cache.triggered.connect(self.clear_cache)
        self.actionCheck_For_Updates.triggered.connect(
            lambda: open_browser(
                "https://github.com/mjishnu/alt-app-installer/releases"
            )
        )
        self.actionAbout.triggered.connect(self.about)
        self.actionHelp.triggered.connect(
            lambda: open_browser("https://discord.com/invite/9eeN2Wve4T")
        )
        self.actionOpen_Logs.triggered.connect(self.open_Logs)
        self.actionDownloads.triggered.connect(self.open_downloads)
        self.actionIgnore_Latest_Version.triggered.connect(self.ignore_version)
        self.actionIgnore_All_filters.triggered.connect(self.ignore_All_filters)
        self.actionget_using_url.triggered.connect(self.install_url)

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

    def about(self):
        window = Ui_about()
        window.exec()

    def open_Logs(self):
        path = f"{curr_dir}/log.txt"
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.show_error_popup(txt="No Logs Found!")

    def clear_cache(self):
        def remove_file():
            def remove_(path, mode="file"):
                if mode == "file":
                    if os.path.exists(path):
                        os.remove(path)
                    else:
                        pass

                elif mode == "dir":
                    shutil.rmtree(path)

            remove_(f"{curr_dir}/log.txt")
            try:
                remove_(f"{curr_dir}/downloads", "dir")
            except FileNotFoundError:
                print("No Downloads Found!")

        worker = Worker(lambda *ars, **kwargs: remove_file())
        worker.signals.error.connect(
            lambda arg: self.error_handler(
                arg, normal=False, msg="Failed To Clear Cache Files!", critical=False
            )
        )

        self.threadpool.start(worker)
        worker.signals.result.connect(
            lambda: self.show_success_popup(text="Cache Files Cleared Successfully!")
        )

    def open_downloads(self):
        path = os.path.realpath(f"{curr_dir}/downloads")
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
            self.advancedmenu.setEnabled(False)
            self.actionclear_cache.setEnabled(False)
            self.actioninstall_From_File.setEnabled(False)
            self.actionget_using_url.setEnabled(False)
            # if the app selector window is open closing it
            try:
                self.window.close()
                self.window.deleteLater()
                del self.window
            except:
                pass

    def install_url(self):
        window = UrlBox()
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
            self.window.setWindowState(
                self.window.windowState() & ~Qt.WindowState.WindowMinimized
                | Qt.WindowState.WindowActive
            )  # if minimized then unminimize
            self.window.activateWindow()  # set focus to the currently open window
        else:  # open a new window
            self.window = QMainWindow()
            self.window.setWindowIcon(
                load_icon(f"{curr_dir}/data/images/search.png", recolor_for_dark=True)
            )
            search_app = AppSelector()
            search_app.setupUi(self.window)
            # overding the new window close event for proper cleanup
            self.window.closeEvent = close
            self.window.show()
            search_app.closed.connect(self.parser)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("QMenu::indicator { width: 0px; height: 0px; }")
    MainProgram = QMainWindow()
    ui = MainWindowGui()
    ui.setupUi(MainProgram)
    MainProgram.setWindowIcon(
        load_icon(f"{curr_dir}/data/images/main.ico", recolor_for_dark=True)
    )
    MainProgram.closeEvent = ui.closeEvent  # overiding close event
    MainProgram.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
