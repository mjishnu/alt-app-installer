# Alt App Installer

A Program To  Download And Install Windows Store Apps

# Features

- This program can download and install microsoft store apps (appx,msix,eappx,appxbundle...) without needing microsoft store or App installer
- Auto downloads the latest app according to your system architecture (x64/x32)
- Priority for downloading (Appx,Msix,appxbundle..) over other encrypted format like Eappx which needs admin permision to install
- Uses Parrel/chunk downloader for fast downloading
- Downloads and install app along with all dependencies 

# How it works
This Program basically automates the process of getting the file from https://store.rg-adguard.net/ by using the store.rg-adguard api and installs the app for the user, so credit goes to the creator of https://store.rg-adguard.net/

- The app open an browser which allows the user to select the file(application/games) they want and returns its url
- The url parsed and the product key is send to the api via requests-html which then finds and returns the appropriate download links(contains both the app and the dependencies) if file is not found then it retries 3 time.Then the links are further parsed based on the system architecture of the user then checked if they are of favorable type(these are decrpted file formats easy to install and doesnt need admin privilage to install) and latest version available
- Then the app downlads the file via pySmartDL(which allows for concurrent downloading in chunks this makes download faster) and finally installs it via subprocess

<img width="1041" alt="image" src="https://user-images.githubusercontent.com/83004520/169115064-b1cf9080-5ef1-425b-b81e-ea69114ae926.png">
<img width="893" alt="image" src="https://user-images.githubusercontent.com/83004520/169115417-15624c09-923d-4be2-a1be-ecdf47c04f24.png">

# Requirements
- windows 10/11
- An internet connection

# How to use the app
- Download the alt_app_installer.exe and run it or build it from source
- Now open the alt_app_installer.exe file in the extracted folder (alt_app_installer folder) and run it (the first run can take time)
- click on choose app and search for the app you want to install and click on select in top bar after the page has fully loaded 
- Wait for the process to complete, afterwards check for the app in start menu
- you can also install already downloaded apps via "install from file" in "Options" 

# How to build from source

- first open a terminal run the command `git clone https://github.com/m-jishnu/Windows-Store-App-Installer`
- now install python3 and pip, go to the cloned folder and run the command `pip install -r requirement.txt`
- run the "run.bat", open the clone folder and run the command  `.\run` 
- enjoy!

# Video Guide

https://bit.ly/3LPHfu8

# FAQ

You can open an issue or ask me directly in [discord](https://discord.com/invite/cbuEkpd)

# Limitation and future plans

- The current Major Limitation is the download link provided by "store.rg-adguard.net", It has an expire time of 10-15 min.The downloader used in the app address this issue by removing the bandwidth limitations but it isn't a full fix since if the user has a slow internet then after the expire time the download will fail.

- To solve this we would need to make a custom downloader which not only downloads in chunks but when an error is occured requests for new link from the "store.rg-adguard.net" api and resumes the download while using the previously downloaded data.
