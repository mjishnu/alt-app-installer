import subprocess
from ctypes import windll
from threading import Thread
from tkinter import Tk, filedialog, ttk

windll.shcore.SetProcessDpiAwareness(1)


def run_command(filename):
    command = f'Add-AppxPackage "{filename}"'
    subprocess.run(
        ["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", command]
    )


def select_file():
    filename = filedialog.askopenfilename(initialdir="/", title="Select a File")
    if filename:
        # filename, -> cause of the comma the filename is a string else will be taken as chars a,b,d,e,f,g
        th = Thread(target=run_command, args=(filename,))
        th.start()


# Create the root window
window = Tk()

# Set window title
window.title("file Installer")

label = ttk.Label(window, text="file Installer V1.1")

label.config(font=("Courier", 12))

button_explore = ttk.Button(window, text="Select File", command=select_file)

button_exit = ttk.Button(window, text="Exit", command=window.destroy)

label.grid(column=0, row=0, padx=100, pady=10)
button_explore.grid(column=0, row=1, padx=10, pady=10)
button_exit.grid(column=0, row=2, padx=10, pady=2)

window.mainloop()
