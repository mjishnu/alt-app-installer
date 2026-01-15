param([switch]$debug)

echo 'switching folder'
cd D:\Code\projects\python_projects\builder

echo 'removing old folders'
rm -r build
rm "alt app installer.spec"
rm -r dist

echo 'building the app'

if ($debug) {
    echo 'debug mode'
    pyinstaller "D:\Code\projects\python_projects\alt-app-installer\app\main.py" --upx-dir="D:\Code\projects\python_projects\builder\upx" --add-data="D:\Code\projects\python_projects\alt-app-installer\app\data\xml\*:data\xml\\" --add-data="D:\Code\projects\python_projects\alt-app-installer\app\data\images\*:data\images\\" --icon "D:\Code\projects\python_projects\alt-app-installer\app\data\images\main.ico" -n "altappinstaller"
}

else {
    pyinstaller "D:\Code\projects\python_projects\alt-app-installer\app\main.py" --upx-dir="D:\Code\projects\python_projects\builder\upx" --add-data="D:\Code\projects\python_projects\alt-app-installer\app\data\xml\*:data\xml\\" --add-data="D:\Code\projects\python_projects\alt-app-installer\app\data\images\*:data\images\\" --icon "D:\Code\projects\python_projects\alt-app-installer\app\data\images\main.ico" -n "altappinstaller" --windowed
}