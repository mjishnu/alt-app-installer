import webbrowser
import subprocess
import re
import platform
from datetime import datetime
from requests_html import HTMLSession


current_time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
def open_browser(arg):
    webbrowser.open(arg)
    
def install(path=None, lst=None):    
    if lst:
        all_paths = str()
        for path in lst:
            all_paths += f'Add-AppPackage "{path}";'
    elif path:
        all_paths = f'Add-AppPackage "{path}"'

    output = subprocess.run(
        ["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe", all_paths], capture_output=True)
    with open('log.txt', 'a') as f:
        f.write(f'[installer.py, powershell command logs] \n{current_time}\n')
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

def get_data(arg):
    
    #geting product id from url
    def product_id_getter(wrd):
        try:
            pattern = re.compile(r".+\/([a-zA-Z-]+)\/((?:[a-zA-Z]+[0-9]|[0-9]+[a-zA-Z])[a-zA-Z0-9]*)|.+")
            matches = pattern.search(str(wrd))
            match=matches.group(2)

            if match == None:
                raise Exception(
                    'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')
            else:
                return match
        except AttributeError:
            raise Exception(
                'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')
            
    #using the api from store.adguard
    url = "https://store.rg-adguard.net/api/GetFiles"
    data = {"type":"ProductId","url":"product_id_url","ring":"RP","lang":"en-EN"}
    data["url"]= product_id_getter(str(arg))
    session = HTMLSession()
    r = session.post(url,data = data)
    
    #getting all the files from the html
    matches = r.html.find("a")
    
    #parsing the results
    main_dict = dict()
    for match in matches:
        main_dict[match.text] = ' '.join(map(str, match.absolute_links))
    if len(main_dict) == 0:
        raise Exception("Sorry, Application not found. Please try again!")
    return main_dict

def greater_ver(arg, n):
    first = arg.split(".")
    second = n.split(".")
    if first[0] > second[0]:
        return arg
    elif first[0] == second[0]:
        if first[1] > second[1]:
            return arg
        elif first[1] == second[1]:
            if first[2] > second[2]:
                return arg
            elif first[2] == second[2]:
                if first[3] > second[3]:
                    return arg
                else:
                    return n
            else:
                return n
        else:
            return n
    else:
        return n
    
def parse_dict(args):
    
    main_dict = args
    data = list()
    bad_data = list()
    data_link = list()
    final_data = list()
    full_data = [keys for keys in main_dict.keys()]

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

    def os_arc():
        if platform.machine().endswith("64"):
            return "x64"
        else:
            return "x86"
        
    def latest_version(lst):
        max = lst[0]
        for i in lst:
            if greater_ver(i,max) == i:
                max = i
        return max


    # get the data according to device architecture
    app_data = dict()
    for key, value in dict_data.items():
        if value[2] == os_arc():
            app_data[(value[0],value[1])] = key
        elif value[2] == "neutral":
            app_data[(value[0],value[1])] = key
    
    #getting the latest version  of the app
    name_ver_list  = list()
    name_list = list()
    repeated_name_dict = dict()
    for key, value in app_data.items():
        name_ver_list.append(key)
        
    for name_ver in name_ver_list:
        name = name_ver[0]
        version = name_ver[1]
        if name not in name_list:
            name_list.append(name)
            repeated_name_dict[name]=[version]
        
        else:
            old_value = repeated_name_dict[name]
            old_value.append(version)
            repeated_name_dict[name] = old_value
            
    for name in name_list:
        if len(repeated_name_dict[name]) > 1:
            versions = repeated_name_dict[name]
            repeated_name_dict[name] = latest_version(versions)
        else:
            repeated_name_dict[name] = repeated_name_dict[name][0]
    
    for key, value in repeated_name_dict.items():
        final_data.append(app_data[(key,value)])
        
    # parsing end ----------------------------------
    return (main_dict, final_data)
