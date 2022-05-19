# Alt-App-Installer
A Simple Program To  Download And Install Windows Store Apps

This Program basically automates the process of getting the file from https://store.rg-adguard.net/ and installs the app for the user, so all credit goes to the creator of https://store.rg-adguard.net/

- The app open an browser which allows the user to select the app they want and returns its url
- The url is then send to https://store.rg-adguard.net/ via selenium which then finds and returns the appropriate download link of the app based on the system architecture of the user from the site
- The app is then downloaded via urlib and installed via subprocess

NOTE: You can only get free apps through this if you want to install any paid apps you need to use microsoft store!

<img width="1041" alt="image" src="https://user-images.githubusercontent.com/83004520/169115064-b1cf9080-5ef1-425b-b81e-ea69114ae926.png">
<img width="893" alt="image" src="https://user-images.githubusercontent.com/83004520/169115417-15624c09-923d-4be2-a1be-ecdf47c04f24.png">

# Requirements
- [Chrome browser](https://www.google.com/intl/en_in/chrome/)

# How to use the app
- Download the alt_app_installer.exe and run it or build it from source
- Now open the alt_app_installer.exe file in the extracted folder (alt_app_installer) and run it ( the first run can take time )
- Go to options select install chrome driver and wait for it to complete a pop will appear indicating its completion
- Now click on choose app and search for the app you want to install and click on select in top bar after the page has fully loaded 
- Wait for the process to complete, afterwards check for the app in start menu
- you can also install already downloaded apps via "install from file" in "Options" 

# How to build from source

- first open a terminal run the command `git clone https://github.com/m-jishnu/Windows-Store-App-Installer`
- now install python3 and pip, go to the cloned folder and run the command `pip install -r requirement.txt`
- run the "run.bat", open the clone folder and run the command  `.\run` 
- enjoy!

# Video Guide

https://youtu.be/pFv5N1BDBUs

# FAQ

**How to solve Error popup after choosing the app?**

If you have selected the app correctly then most of the time its your internet speed, to solve this go to option click on 'set wait time' and increase the wait time

NOTE: Increasing the wait time means it will take longer to complete the installation

**Other Errors ?**

You can open an issue or ask me directly in [discord](https://discord.com/invite/cbuEkpd)
