import webbrowser
import subprocess
import re
import platform
from datetime import datetime
from requests_html import HTMLSession
import time


current_time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
def open_browser(arg):
    webbrowser.open(arg)
    
def install(path):    
    flag = 0
    main_prog_error = 0
    if type(path)==str:
        all_paths = f'Add-AppPackage "{path}"'
        output = subprocess.run(
            ["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe", all_paths], capture_output=True)
        with open('log.txt', 'a') as f:
            f.write(f'[installer.py, powershell command logs] \n{current_time}\n')
            f.write(f'command: {output.args[1]}\n\n')    
            f.write(output.stderr.decode("utf-8"))           
            f.write(f'{82*"-"}\n')
        if output.returncode != 0:
            flag = 1
        msg = 'Failed To Install The Application!'
        detail_msg = f'Command Execution Failed: {output.args[1]}'
        detail_msg+='\nThe Installation has failed, try again!'
        endresult = (msg,detail_msg,"Error",True)
    elif type(path) == dict:
        outputs = list()
        for s_path in path.keys():
            all_paths = f'Add-AppPackage "{s_path}"'
            output = subprocess.run(
            ["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe", all_paths], capture_output=True)
            with open('log.txt', 'a') as f:
                f.write(f'[installer.py, powershell command logs] \n{current_time}\n')
                f.write(f'command: {output.args[1]}\n\n')    
                f.write(output.stderr.decode("utf-8"))           
                f.write(f'{82*"-"}\n')
            outputs.append(output.args[1])
            if output.returncode != 0:
                flag = 1
                if path[s_path] == 1:
                    main_prog_error = 1
                    break
        if main_prog_error == 1:
            msg = 'Failed To Install The Application!'
            detail_msg = f'Command Execution Failed: {outputs}'
            detail_msg+='\nThe Installation has failed, try again!'
            endresult = (msg,detail_msg,"Error",True)
        
        else:
            msg = 'Failed To Install Dependencies!'
            detail_msg = f'Command Execution Failed: {outputs}'
            detail_msg+='\nIn Some cases, the installation of dependencies was only unsuccessful since its already installed in your pc.\n'
            detail_msg+='So check wheather the program is installed in start menu if not, try again!'
            endresult = (msg,detail_msg,"Warning")
         
    if flag != 0:
            return endresult
    return 0

def get_data(arg):
    
    #geting product id from url
    def product_id_getter(wrd):
        try:
            pattern = re.compile(r".+\/((?:[a-zA-Z]+[0-9]|[0-9]+[a-zA-Z])[a-zA-Z0-9]*)|.+")
            matches = pattern.search(str(wrd))
            match=matches.group(1)
            
            #getting name from url
            pattern_n = re.compile(r".+\/([a-zA-Z-]+)\/|.+")
            matches_n = pattern_n.search(str(wrd))
            name=matches_n.group(1)
            
            if match == None:
                raise Exception(
                    'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')
            else:
                return match,name
        except AttributeError:
            raise Exception(
                'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')
            
    #using the api from store.adguard
    url = "https://store.rg-adguard.net/api/GetFiles"
    data = {"type":"ProductId","url":"product_id_url","ring":"RP","lang":"en-EN"}
    data["url"],file_name= product_id_getter(str(arg))
    for i in range(3):
        try:
            session = HTMLSession()
            r = session.post(url,data = data)
            #getting all the files from the html
            matches = r.html.find("a")
            break
        except:
            time.sleep(3)
            print(f"error in getting the files from the api retry:{i}")
            continue
    #parsing the results
    main_dict = dict()
    for match in matches:
        main_dict[match.text] = ' '.join(map(str, match.absolute_links))
    if len(main_dict) == 0:
        raise Exception("Sorry, Application not found. Please try again!")
    return (main_dict,file_name)

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
    main_dict,file_name = args
    file_name = file_name.split("-")[0]
    data = list()
    bad_data = list()
    data_link = list()
    final_data = list()
    fav_type = ['appx','msix','msixbundle','appxbundle'] #fav_type is a list of extensions that are easy to install without admin privileges
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
    app_data = dict() #{(name,version,type):full_name}
    final_data_get = dict() #{(name,version):full_name}
    for key, value in dict_data.items():
        if value[2] == os_arc():
            app_data[(value[0],value[1],value[-1].split('.')[1])] = key
            final_data_get[(value[0],value[1])] = key
        elif value[2] == "neutral":
            app_data[(value[0],value[1],value[-1].split('.')[1])] = key
            final_data_get[(value[0],value[1])] = key
    #getting the latest version  of the app
    name_ver_list  = list() #(name,version,type)
    name_list = list() #[name]
    repeated_name_dict = dict() #{name:(version,type)} --> {name:version}
    for key, value in app_data.items():
        name_ver_list.append(key)
        
    for name_ver in name_ver_list:
        name = name_ver[0]
        version = name_ver[1]
        type_ = name_ver[2]
        if name not in name_list:
            name_list.append(name)
            repeated_name_dict[name]=[(version,type_)]
        
        else:
            old_value = repeated_name_dict[name]
            old_value.append((version,type_))
            repeated_name_dict[name] = old_value

    for name in name_list:
        versions = list()#[version1,version2,version3,version4,version5,version6]
        indicator = None
        for name_ver in repeated_name_dict[name]: #for checking if there are any fav_type in the data
            if name_ver[1] in fav_type:
                indicator = 1  #if a fav_type is found stop letting the none fav_type in the list
            else:
                continue
        for name_ver in repeated_name_dict[name]:
            #[(version,type_),(version,type_)]
            if name_ver[1] in fav_type: 
                versions.append(name_ver[0])
            else:
                if indicator:
                    continue
                else:
                    versions.append(name_ver[0])
        if len(versions) > 1:
            repeated_name_dict[name] = latest_version(versions)
        else:
            repeated_name_dict[name] = versions[0]

    for key, value in repeated_name_dict.items():
        final_data.append(final_data_get[(key,value)])
    # parsing end ----------------------------------
    return (main_dict, final_data,file_name)
