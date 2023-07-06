import html
import json
import platform
import re
import time
import warnings
from threading import Thread
from xml.dom import minidom

import requests

warnings.filterwarnings("ignore")

# using this to check if the user has decieded to stop the process


def check(Event):
    if Event.is_set():
        raise Exception("Stoped By User!")


def os_arc():
    if platform.machine().endswith("64"):
        return "x64"
    if platform.machine().endswith("32") or platform.machine().endswith("86"):
        return "x86"
    ################################
    return "arm"  # not sure wheather work or not, needs testing

# cleans My.name.1.2 -> myname


def clean_name(badname):
    name = "".join(
        [(i if (64 < ord(i) < 91 or 96 < ord(i) < 123) else "") for i in badname])
    return name.lower()


def url_generator(url, ignore_ver, all_dependencies, Event, progress_current, progress_main, emit):
    total_prog = 0
    progress_current.emit(total_prog)
    # geting product id from url
    try:
        pattern = re.compile(
            r".+\/([^\/\?]+)(?:\?|$)")
        matches = pattern.search(str(url))
        product_id = matches.group(1)
    except AttributeError:
        raise Exception(
            'No Data Found: --> [You Selected Wrong Page, Try Again!]')

    # getting cat_id and package name from the api
    details_api = f"https://storeedgefd.dsx.mp.microsoft.com/v9.0/products/{product_id}?market=US&locale=en-us&deviceFamily=Windows.Desktop"
    session = requests.Session()
    r = session.get(details_api, timeout=20)
    response = json.loads(r.text, object_hook=lambda obj:
                               {k: json.loads(v) if k == 'FulfillmentData' else v for k, v in obj.items()})
    
    if not response.get("Payload", None):
        raise Exception('No Data Found: --> [You Selected Wrong Page, Try Again!]')
        
    response_data = response["Payload"]["Skus"][0]
    data_list = response_data.get("FulfillmentData", None)
    total_prog += 20
    progress_current.emit(total_prog)

    def uwp_gen():
        nonlocal total_prog

        def parse_dict(main_dict, file_name, ignore_ver, all_dependencies):

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
                    return arg2
                return arg2

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
            remove_list = []
            curr_arch = os_arc()

            for key in names_dict:
                matches = pattern.search(key)
                if matches:
                    # all the contents of the main file [ver1,ver2,ver3,ver4]
                    content_list = names_dict[key]
                    remove_list.append(key)

                    arch = content_list[0][0]
                    _type = content_list[0][1]
                    ver = content_list[0][2]

                    if len(content_list) > 1:
                        for data in content_list[1:]:
                            if arch not in ("neutral", curr_arch) and data[0] != arch and data[0] in ("neutral", curr_arch):
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
                    final_arch = curr_arch if arch == "neutral" else arch
                    break

            # removing all the items that we have already parsed (done this way to remove runtime errors)
            for i in remove_list:
                del names_dict[i]

            final_list = []
            # checking for dependencies
            #################################################################
            for key in names_dict:
                # all the contents of the main file [ver1,ver2,ver3,ver4]
                # [(arch,type,ver),(arch,type,ver),(arch,type,ver)]
                content_list = names_dict[key]

                if all_dependencies:
                    # if all_dependencies is checked then we will just add all the files
                    for data in content_list:
                        final_list.append(full_data[(key, *data)])
                else:
                    # if all_dependencies is not checked then we will add only the files that are required
                    arch = content_list[0][0]
                    _type = content_list[0][1]
                    ver = content_list[0][2]

                    if len(content_list) > 1:
                        for data in content_list[1:]:
                            # checking arch is same as main file
                            if arch not in ("neutral", final_arch) and data[0] != arch and data[0] in ("neutral", final_arch):
                                arch = data[0]
                                _type = data[1]
                                ver = data[2]
                            else:
                                if data[0] == arch and data[1] != _type and data[1] in fav_type:
                                    _type = data[1]
                                    ver = data[2]
                                else:
                                    if data[0] == arch and data[1] == _type and data[2] != ver:
                                        # checking to see if ignore_ver is checked or not
                                        if ignore_ver:
                                            final_list.append(
                                                full_data[(key, arch, _type, ver)])
                                            ver = data[2]
                                        else:
                                            ver = greater_ver(ver, data[2])

                    # only add if arch is same as main file
                    if arch in ("neutral", final_arch):
                        final_list.append(full_data[(key, arch, _type, ver)])

            if main_file_name:
                final_list.append(main_file_name)
                file_name = main_file_name
            else:
                # since unable to detect the main file assuming it to be the first file, since its true in most cases
                file_name = final_list[0]

            return final_list, file_name

        cat_id = data_list["WuCategoryId"]
        main_file_name = data_list["PackageFamilyName"].split('_')[0]
        release_type = "Retail"

        # getting the encrypted cookie for the fe3 delivery api
        with open("./data/xml/GetCookie.xml", "r") as f:
            cookie_content = f.read()
        check(Event)
        out = session.post(
            'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
            data=cookie_content,
            headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
            verify=False, timeout=20
        )
        doc = minidom.parseString(out.text)
        total_prog += 20
        progress_current.emit(total_prog)
        # extracting the cooking from the EncryptedData tag
        cookie = doc.getElementsByTagName('EncryptedData')[
            0].firstChild.nodeValue

        # getting the update id,revision number and package name from the fe3 delivery api by providing the encrpyted cookie, cat_id, realse type
        # Map {"retail": "Retail", "release preview": "RP","insider slow": "WIS", "insider fast": "WIF"}
        with open("./data/xml/WUIDRequest.xml", "r") as f:
            cat_id_content = f.read().format(cookie, cat_id, release_type)
        check(Event)
        out = session.post(
            'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
            data=cat_id_content,
            headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
            verify=False, timeout=20
        )

        doc = minidom.parseString(html.unescape(out.text))
        total_prog += 20
        progress_current.emit(total_prog)
        filenames = {}  # {ID: filename}
        # extracting all the filenames(package name) from the xml (the file names are found inside the blockmap)
        for node in doc.getElementsByTagName('Files'):
            # using try statement to avoid errors caused when attributes are not found
            try:
                filenames[node.parentNode.parentNode.getElementsByTagName(
                    'ID')[0].firstChild.nodeValue] = f"{node.firstChild.attributes['InstallerSpecificIdentifier'].value}_{node.firstChild.attributes['FileName'].value}"
            except KeyError:
                continue
        # if the server returned no files notify the user that the app was not found
        if not filenames:
            raise Exception("server returned a empty list")

        # extracting the update id,revision number from the xml
        identities = {}  # {filename: (update_id, revision_number)}
        for node in doc.getElementsByTagName('SecuredFragment'):
            # using try statement to avoid errors caused when attributes are not found
            try:
                file_name = filenames[node.parentNode.parentNode.parentNode.getElementsByTagName('ID')[
                    0].firstChild.nodeValue]

                update_identity = node.parentNode.parentNode.firstChild
                identities[file_name] = (update_identity.attributes['UpdateID'].value,
                                         update_identity.attributes['RevisionNumber'].value)
            except KeyError:
                continue
        check(Event)
        # parsing the filenames according to latest version,favorable types,system arch
        parse_names, main_file_name = parse_dict(identities, main_file_name,
                                                 ignore_ver, all_dependencies)
        final_dict = {}  # {filename: (update_id, revision_number)}
        for value in parse_names:
            final_dict[value] = identities[value]

        # getting the download url for the files using the api
        with open("./data/xml/FE3FileUrl.xml", "r") as f:
            file_content = f.read()

        file_dict = {}  # the final result
        total_prog += 10
        progress_current.emit(total_prog)
        part = int(30 / len(final_dict))

        def geturl(updateid, revisionnumber, file_name, total_prog):
            out = session.post(
                'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx/secured',
                data=file_content.format(
                    updateid, revisionnumber, release_type),
                headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
                verify=False, timeout=20
            )
            doc = minidom.parseString(out.text)
            # checks for all the tags which have name "filelocation" and extracts the url from it
            for i in doc.getElementsByTagName("FileLocation"):
                url = i.getElementsByTagName("Url")[0].firstChild.nodeValue
                # here there are 2 filelocation tags one for the blockmap and one for the actual file so we are checking for the length of the url
                if len(url) != 99:
                    file_dict[file_name] = url
                    total_prog += part
                    progress_current.emit(total_prog)

        # using threading to concurrently get the download url for all the files
        threads = []
        for key, value in final_dict.items():
            check(Event)
            file_name = key
            updateid, revisionnumber = value
            th = Thread(target=geturl, args=(
                updateid, revisionnumber, file_name, total_prog))
            th.daemon = True
            threads.append(th)
            th.start()

        # waiting for all threads to complete
        while len(file_dict) != len(final_dict):
            check(Event)
            time.sleep(0.2)
        if emit is True:
            progress_current.emit(100)
            time.sleep(0.2)
            progress_main.emit(20)
        # uwp = True
        return file_dict, parse_names, main_file_name, True

    def non_uwp_gen():
        nonlocal total_prog
        api = f"https://storeedgefd.dsx.mp.microsoft.com/v9.0/packageManifests//{product_id}?market=US&locale=en-us&deviceFamily=Windows.Desktop"
        check(Event)

        r = session.get(api, timeout=20)
        datas = json.loads(r.text)
        
        if not datas.get("Data", None):
            raise Exception("server returned a empty list")
        
        total_prog += 20
        progress_current.emit(total_prog)

        file_name = datas["Data"]["Versions"][0]["DefaultLocale"]["PackageName"]

        installer_list = datas["Data"]["Versions"][0]["Installers"]
        download_data = set()
        for d in installer_list:
            download_data.add(
                (d["Architecture"], d["InstallerLocale"], d["InstallerType"], d["InstallerUrl"]))

        curr_arch = os_arc()
        file_dict = {}
        # casting to list for indexing
        download_data = list(download_data)
        
        # parsing
        arch = download_data[0][0]
        locale = download_data[0][1]
        installer_type = download_data[0][2]
        url = download_data[0][3]

        if len(download_data) > 1:
            for data in download_data[1:]:
                if arch not in ("neutral", curr_arch) and data[0] != arch and data[0] in ("neutral", curr_arch):
                    arch = data[0]
                    locale = data[1]
                    installer_type = data[2]
                    url = data[3]
                else:
                    if data[0] == arch and data[1] != locale and ("en" in data[1] or "us" in data[1]):
                        locale = data[1]
                        installer_type = data[2]
                        url = data[3]
                        break

        main_file_name = clean_name(file_name) + "." + installer_type
        file_dict[main_file_name] = url

        # uwp = False
        return file_dict, [main_file_name], main_file_name, False

    # check and see if the app is ump or not, return --> func_output,(ump or not)
    if data_list:
        return uwp_gen()
    else:
        return non_uwp_gen()
