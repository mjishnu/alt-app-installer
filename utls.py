import platform
import re
import subprocess
import time
import webbrowser
from datetime import datetime
import json

from requests_html import HTMLSession


def open_browser(arg):
    webbrowser.open(arg)


def install(path):
    flag = 0
    main_prog_error = 0
    if isinstance(path, str):
        path = {path: 1}

    outputs = []
    for s_path in path.keys():
        all_paths = f'Add-AppPackage "{s_path}"'
        output = subprocess.run(
            ["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe", all_paths], capture_output=True)
        with open('log.txt', 'a') as f:
            current_time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
            f.write(f'[powershell logs] \n{current_time}\n')
            f.write(f'command: {output.args[1]}\n\n')
            f.write(output.stderr.decode("utf-8"))
            f.write(f'{82*"-"}\n')
        outputs.append(output.args[1])
        # if command failed
        if output.returncode != 0:
            flag = 1
            # if the failed commands include the application package then show app not installed
            if path[s_path] == 1:
                main_prog_error = 1
                break
    if main_prog_error == 1:
        msg = 'Failed To Install The Application!'
        detail_msg = f'Command Execution Failed: {outputs}'
        detail_msg += '\nThe Installation has failed, try again!'
        endresult = (msg, detail_msg, "Error", True)

    else:
        msg = 'Failed To Install Dependencies!'
        detail_msg = f'Command Execution Failed: {outputs}'
        detail_msg += '\nIn Some cases, the installation of dependencies was only unsuccessful since its already installed in your pc.\n'
        detail_msg += 'So check wheather the program is installed in start menu if not, try again!'
        endresult = (msg, detail_msg, "Warning")
    if flag != 0:
        return endresult
    return 0


def get_data(arg):

    # geting product id from url
    def product_id_getter(wrd):
        try:
            pattern = re.compile(
                r".+\/((?:[a-zA-Z]+[0-9]|[0-9]+[a-zA-Z])[a-zA-Z0-9]*)|.+")
            matches = pattern.search(str(wrd))
            match = matches.group(1)

            # getting name from url
            name = wrd.split("/")[5]

            if match is None:
                raise Exception(
                    'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')
            return match, name
        except AttributeError:
            raise Exception(
                'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')

    main_dict = {}
    Id, file_name = product_id_getter(str(arg))
    data_list = None
    try:
        # using the api from rg.adguard
        url = "https://store.rg-adguard.net/api/GetFiles"
        data = {"type": "ProductId", "url": Id, "ring": "RP", "lang": "en-EN"}
        for i in range(3):
            try:
                session = HTMLSession()
                r = session.post(url, data=data)
                # getting all the files from the html
                data_list = r.html.find("a")
                break
            except:
                time.sleep(3)
                print(
                    f"error in getting the files from the rg.adguard api retry:{i}")
                continue

        # parsing the results
        if data_list:
            for data in data_list:
                main_dict[data.text] = ' '.join(map(str, data.absolute_links))
        if len(main_dict) == 0:
            raise
    except:
        # using StoreWeb Api as a fallback
        url = "https://xwebstore.herokuapp.com/api/Packages"
        data = {"inputform": "ProductId",
                "id": Id, "environment": "Production"}
        for i in range(3):
            try:
                session = HTMLSession()
                r = session.get(url, params=data)
                data_list = json.loads(r.text)
                break
            except:
                time.sleep(3)
                print(
                    f"error in getting the files from the storeWeb api retry:{i}")
                continue

        if data_list:
            for data in data_list:
                main_dict[data["packagefilename"]] = data["packagedownloadurl"]

        if len(main_dict) == 0:
            raise Exception("Sorry, Application not found. Please try again!")

    return (main_dict, file_name)

# main function for getting the right links


def parse_dict(args):

    def greater_ver(arg1, arg2):
        first = arg1.split(".")
        second = arg2.split(".")
        if first[0] > second[0]:
            return arg1
        if first[0] == second[0]:
            if first[1] > second[1]:
                return arg1
            if first[1] == second[1]:
                if first[2] > second[2]:
                    return arg1
                if first[2] == second[2]:
                    if first[3] > second[3]:
                        return arg1
                    return arg2
                return arg2
            else:
                return arg2
        else:
            return arg2

    # cleans My.name.1.2 -> myname
    def clean_name(badname):
        name = "".join(
            [(i if (64 < ord(i) < 91 or 96 < ord(i) < 123) else "") for i in badname])
        return name.lower()

    def os_arc():
        if platform.machine().endswith("64"):
            return "x64"
        if platform.machine().endswith("32") or platform.machine().endswith("86"):
            return "x86"
        ################################
        return "arm"  # not sure wheather work or not, needs testing

    main_dict, file_name = args
    # removing all non string elements
    file_name = clean_name(file_name.split("-")[0])

    pattern = re.compile(r".+\.BlockMap")
    full_data = {}  # {(name,arch,type,version):full_name}

    for key in main_dict.keys():
        matches = pattern.search(str(key))
        # removing block map files
        if not matches:
            #['Microsoft.VCLibs.140.00', '14.0.30704.0', 'x86', '', '8wekyb3d8bbwe.appx']
            temp = key.split("_")
            #contains [name,arch,type,version]
            # temp[-1].split(".")[1] = type[appx,msix, etc]
            content_lst = (clean_name(temp[0]), temp[2].lower(
            ), temp[-1].split(".")[1].lower(), temp[1])
            full_data[content_lst] = key

    # dict of repeated_names {repeated_name:[ver1,ver2,ver3,ver4]}
    names_dict = {}
    for value in full_data:
        if value[0] not in names_dict:
            names_dict[value[0]] = [value[1:]]
        else:
            names_dict[value[0]] += [value[1:]]

    final_arch = None  # arch of main file
    # fav_type is a list of extensions that are easy to install without admin privileges
    fav_type = ['appx', 'msix', 'msixbundle', 'appxbundle']
    main_file_name = None
    # get the full file name list of the main file (eg: spotify.appx, minecraft.appx)
    pattern = re.compile(file_name)
    # getting the name of the main_appx file
    for key in names_dict:
        matches = pattern.search(key)
        if matches:
            # all the contents of the main file [ver1,ver2,ver3,ver4]
            content_list = names_dict[key]
            del names_dict[key]

            arch = content_list[0][0]
            _type = content_list[0][1]
            ver = content_list[0][2]

            if len(content_list) > 1:
                for data in content_list[1:]:
                    if data[0] != arch and (data[0] == "neutral" or data[0] == os_arc()):
                        arch = data[0]
                        _type = data[1]
                        ver = data[2]
                    else:
                        if data[0] == arch and data[1] != _type and data[1] in fav_type:
                            _type = data[1]
                            ver = data[2]
                        else:
                            if data[0] == arch and data[1] == _type and data[2] != ver:
                                ver = greater_ver(ver, data[2])

            main_file_name = full_data[(key, arch, _type, ver)]
            final_arch = os_arc() if arch == "neutral" else arch
            break

    final_list = []
    # checking for dependencies
    #################################################################
    for key in names_dict:
        # all the contents of the main file [ver1,ver2,ver3,ver4]
        content_list = names_dict[key]

        arch = content_list[0][0]
        _type = content_list[0][1]
        ver = content_list[0][2]

        if len(content_list) > 1:
            for data in content_list[1:]:
                # checking arch is same as main file
                if data[0] != arch and data[0] == final_arch:
                    arch = data[0]
                    _type = data[1]
                    ver = data[2]
                else:
                    if data[0] == arch and data[1] != _type and data[1] in fav_type:
                        _type = data[1]
                        ver = data[2]
                    else:
                        if data[0] == arch and data[1] == _type and data[2] != ver:
                            ver = greater_ver(ver, data[2])

        final_list.append(full_data[(key, arch, _type, ver)])

    if main_file_name:
        final_list.append(main_file_name)
        file_name = main_file_name
    else:
        # since unable to detect the main file assuming it to be the first file, since its true in most cases
        file_name = final_list[0]

    return (main_dict, final_list, file_name)
