# Alt App Installer

A Program To  Download And Install Windows Store Apps

# Features

- This program can download and install microsoft store apps (appx,msix,eappx,appxbundle...) without needing microsoft store or App installer
- Auto downloads the latest app according to your system architecture (x64/x32)
- Priority for downloading [Appx,Msix,appxbundle...] over other encrypted format like Eappx which needs admin privilage to install
- Can installed already downloaded microsoft store apps (appx,msix,appxbundle...)
- Can install microsoft store apps by providing its url
- Uses custom link generation to produce download links
- Uses [concurrent/multi-part downloader](https://stackoverflow.com/questions/93642/how-do-download-accelerators-work) using a stripped version [pypdl](https://github.com/m-jishnu/pypdl) for fast downloading
- Can resume interrupted downloads
- Automatically use a new url in case current one expires
- Downloads and install app along with all dependencies 

# How it works

- The app open an browser which allows the user to select the file(application/games) they want to install and returns its url
- The url is parsed and the product key is obtained then, using Microsoft-Display-Catalog-API categoryid and file name is retrived 
- Using these data the app can send a request to Microsoft-Delivery-Optimization-service-API and retrive data of the selected application, this data is further parsed based on 
    - System architecture of the user(x64/x32)
    - Favorable type(these are decrypted file formats, which doesn't need admin privilage to install)
    - Latest version
- Then it retrives the download links for the parsed data using the API and the files are downloaded using a stripped version of [pypdl](https://github.com/m-jishnu/pypdl), which allows for concurrent/multi-part downloading this makes the download faster.It also has the ability to resume interrupted downloads and can also automatically use a new url in case current download link expires.
- Finally it installs the downloaded files via System.Management.Automation.dll using [pythonnet](https://pypi.org/project/pythonnet)

<img width="1173" alt="image" src="https://user-images.githubusercontent.com/83004520/175317632-8199f281-948e-4558-9b4a-0c8bdd2c50ee.png">
<img width="952" alt="image" src="https://user-images.githubusercontent.com/83004520/176722809-dbafa2a0-56c6-4cbc-ba8b-fe964a73e029.png">


# Requirements
- windows 10/11
- An internet connection

# How to use the app
- Download the "alt app installer.exe" and run it or build it from source
- Now open the "alt app installer.exe" file in the extracted folder ("alt app installer" folder) and run it (the first run can take time)
- click on choose app and search for the app you want to install and click on select in top bar after the page has fully loaded 
- Wait for the process to complete, afterwards check for the app in start menu
- You can also install already downloaded apps via "Install from file" in "Options" 
- You can also install the app by manually pasting its url in "Install from Link" in "Options"

# How to build from source

- Install [git](https://git-scm.com/download/win)
- Open a git bash terminal run the command `git clone https://github.com/m-jishnu/alt-app-installer`
- Now install python3 and pip, go to the cloned folder and run the command `pip install -r requirement.txt`
- Run the "run.bat" or run the command `.\run` in the terminal from the cloned folder
- Enjoy!

# Video Guide

https://youtu.be/ayIilTc-6u4

# FAQ

- How to Solve Failed to install Dependencies ?

    In some cases, this occurs since the dependencies are already installed on your pc. So check wheather the program is installed from start menu.
    if the program is still not installed, then there are 2 ways to solve this. **[only try the 2nd method if 1st method failed]**
    1. Enable Ignore Version (Options --> Dependencies --> Ignore Version), this will download all version of dependencies available for your system
    2. Enable Ignore All Filters (Options --> Dependencies --> Ignore All Filters), this will download all available dependencies (can take time)

- For other issues
    
    You can open an issue or ask me directly in [discord](https://discord.com/invite/cbuEkpd)

# Credits

[StoreLib](https://github.com/StoreDev/StoreLib): API for download link generation
