import platform
import re
import subprocess
import time
import webbrowser
from datetime import datetime

from requests_html import HTMLSession

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
            #if command failed
            if output.returncode != 0:
                flag = 1
                #if the failed commands include the application package then show app not installed
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
    for i in range(5):
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

#main function for getting the right links
def parse_dict(args):  
    
    main_dict,file_name = args
    file_name = file_name.split("-")[0]

    def greater_ver(arg1, arg2):
        first = arg1.split(".")
        second = arg2.split(".")
        if first[0] > second[0]:
            return arg1
        elif first[0] == second[0]:
            if first[1] > second[1]:
                return arg1
            elif first[1] == second[1]:
                if first[2] > second[2]:
                    return arg1
                elif first[2] == second[2]:
                    if first[3] > second[3]:
                        return arg1
                    else:
                        return arg2
                else:
                    return arg2
            else:
                return arg2
        else:
            return arg2

    #cleans My.name.1.2 -> myname
    def clean_name(badname):
        name = ''
        for i in badname.split("."):
            try:
                int(i)
            except:
                name += i
        return name.lower()


    def os_arc():
        if platform.machine().endswith("64"):
            return "x64"
        elif platform.machine().endswith("32") or platform.machine().endswith("86"): 
            return "x86"
        else:
            ################################ 
            return "arm" #not sure wheather work or not, needs testing 
            ################################ 

    pattern = re.compile(r".+\.BlockMap")
    full_data = {} #{(name,arch,type,version):full_name}

    for key in main_dict.keys():
        matches = pattern.search(str(key))
        # removing block map files
        if not matches:
            #['Microsoft.VCLibs.140.00', '14.0.30704.0', 'x86', '', '8wekyb3d8bbwe.appx']
            temp =  key.split("_")

            #contains [name,arch,type,version]
            content_lst = (clean_name(temp[0]),temp[2],temp[-1].split(".")[1],temp[1]) #temp[-1].split(".")[1] = type[appx,msix, etc]
            full_data[content_lst] = key

    names_dict = {} # dict of repeated_names {repeated_name:[ver1,ver2,ver3,ver4]} 
    for value in full_data.keys():
        if value[0] not in names_dict:
            names_dict[value[0]] = [value[1:]]
        else:
            names_dict[value[0]] += [value[1:]]

    final_arch  = None #arch of main file
    fav_type = ['appx','msix','msixbundle','appxbundle'] #fav_type is a list of extensions that are easy to install without admin privileges

    # get the full file name list of the main file (eg: spotify.appx, minecraft.appx)
    pattern = re.compile(file_name.lower())
    #getting the name of the main_appx file 
    for key in names_dict.keys():
        matches = pattern.search(key)
        if matches:
            #all the contents of the main file [ver1,ver2,ver3,ver4]
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
                                    ver = greater_ver(ver,data[2])

            file_name = full_data[(key,arch,_type,ver)]
            final_arch = os_arc() if arch == "neutral" else arch
            break

    final_list = []
    #checking for dependencies
    #################################################################
    for key in names_dict.keys():
        #all the contents of the main file [ver1,ver2,ver3,ver4]
        content_list = names_dict[key]

        arch = content_list[0][0]
        _type = content_list[0][1]
        ver = content_list[0][2]

        if len(content_list) > 1:
            for data in content_list[1:]:
                    #checking arch is same as main file
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
                                ver = greater_ver(ver,data[2])

        final_list.append(full_data[(key,arch,_type,ver)])
        
    final_list.append(file_name)

    return (main_dict, final_list,file_name)
    