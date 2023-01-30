import platform
import re

import webbrowser


def open_browser(arg):
    webbrowser.open(arg)


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
                    if data[0] != arch and (data[0] == "neutral" or data[0] == final_arch):
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
                                    final_list.append(full_data[(key, arch, _type, ver)])
                                    ver = data[2]
                                else:
                                    ver = greater_ver(ver, data[2])

            # only add if arch is same as main file
            if arch == "neutral" or arch == final_arch:
                final_list.append(full_data[(key, arch, _type, ver)])

    if main_file_name:
        final_list.append(main_file_name)
        file_name = main_file_name
    else:
        # since unable to detect the main file assuming it to be the first file, since its true in most cases
        file_name = final_list[0]

    return final_list,file_name
