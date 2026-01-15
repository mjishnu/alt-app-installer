import asyncio
import datetime
import html
import json
import os
import platform
import re
import time
import warnings
from xml.dom import minidom

import aiohttp

warnings.filterwarnings("ignore")
# parent directory for absloute path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# using this to check if the user has decieded to stop the process


def check(Event):
    if Event.is_set():
        raise Exception("Stoped By User!")


def os_arc():
    machine = platform.machine().lower()

    if machine.endswith("arm64"):
        return "arm64"
    if machine.endswith("64"):
        return "x64"
    if machine.endswith("32") or machine.endswith("86"):
        return "x86"
    else:
        return "arm"


# cleans My.name.1.2 -> myname
def clean_name(badname):
    name = "".join(
        [(i if (64 < ord(i) < 91 or 96 < ord(i) < 123) else "") for i in badname]
    )
    return name.lower()


def parse_iso_datetime(iso_str):
    """Parse ISO 8601 datetime string, handling 'Z' suffix and >6 digit fractions."""
    # Replace 'Z' with '+00:00' for UTC (needed for Python < 3.11)
    if iso_str.endswith("Z"):
        iso_str = iso_str[:-1] + "+00:00"
    # Truncate fractional seconds to 6 digits (microseconds) if longer
    match = re.match(r"(.+\.\d{6})\d+(.*)$", iso_str)
    if match:
        iso_str = match.group(1) + match.group(2)
    return datetime.datetime.fromisoformat(iso_str)


def select_latest(content_list, curr_arch, ignore_ver=False):
    # Score function returns a tuple, higher is better
    def score(item):
        fav_type = {"appx", "msix", "msixbundle", "appxbundle"}
        arch, ext, modified_str, version_str = item
        # 2 = exact arch, 1 = neutral, 0 = something else
        arch_score = 2 if arch == curr_arch else (1 if arch == "neutral" else 0)
        # 1 = favorable type, 0 = other
        type_score = 1 if ext in fav_type else 0
        if ignore_ver:
            dt = 0
            ver_tuple = (0, 0, 0, 0)
        else:
            dt = parse_iso_datetime(modified_str)
            ver_tuple = tuple(map(int, version_str.split(".")))
        # The “score” is a tuple that Python compares in order
        # Higher arch_score > better type_score > later date > bigger version
        return (arch_score, type_score, dt, ver_tuple)

    # Filter to arch in (curr_arch, "neutral") so we don’t pick nonsense arch
    candidates = [item for item in content_list if item[0] in (curr_arch, "neutral")]
    if not candidates:
        candidates = content_list  # fallback if no matching arch at all

    # Pick the item with the best score
    best = max(candidates, key=score)
    return best


async def url_generator(
    url, ignore_ver, all_dependencies, Event, progress_current, progress_main, emit
):
    async def uwp_gen(session):
        nonlocal total_prog

        def parse_dict(main_dict, file_name):
            file_name = clean_name(file_name.split("-")[0])
            pattern = re.compile(r".+\.BlockMap")
            full_data = {}

            for key, value in main_dict.items():
                if not pattern.search(str(key)):
                    temp = key.split("_")
                    content_lst = (
                        clean_name(temp[0]),
                        temp[2].lower(),
                        temp[-1].split(".")[1].lower(),
                        value,
                        temp[1],
                    )
                    full_data[content_lst] = key

            names_dict = {}
            for v in full_data:
                names_dict.setdefault(v[0], []).append(v[1:])

            file_arch, main_file_name, main_file_name_key = None, None, None
            pat_main = re.compile(file_name)
            sys_arch = os_arc()
            for k in names_dict:
                if pat_main.search(k):
                    content_list = names_dict[k]
                    main_file_name_key = k
                    arch, ext, modifed, ver = select_latest(content_list, sys_arch)
                    main_file_name = full_data[(k, arch, ext, modifed, ver)]
                    file_arch = sys_arch if arch == "neutral" else arch
                    break

            del names_dict[main_file_name_key]

            final_list = []
            for k in names_dict:
                content_list = names_dict[k]
                if all_dependencies:
                    for data in content_list:
                        final_list.append(full_data[(k, *data)])
                else:
                    arch, ext, modifed, ver = select_latest(content_list, file_arch)
                    final_list.append(full_data[(k, arch, ext, modifed, ver)])

            if main_file_name:
                final_list.append(main_file_name)
                file_name = main_file_name
            else:
                file_name = final_list[0] if final_list else file_name

            return final_list, file_name

        cat_id = data_list["WuCategoryId"]
        main_file_name = data_list["PackageFamilyName"].split("_")[0]
        release_type = "Retail"

        # getting the encrypted cookie for the fe3 delivery api
        with open(rf"{parent_dir}\data\xml\GetCookie.xml", "r") as f:
            cookie_content = f.read()
        check(Event)
        out = await (
            await session.post(
                "https://fe3cr.delivery.mp.microsoft.com/ClientWebService/client.asmx",
                data=cookie_content,
                headers={"Content-Type": "application/soap+xml; charset=utf-8"},
            )
        ).text()
        doc = minidom.parseString(out)
        total_prog += 20
        progress_current.emit(total_prog)
        # extracting the cooking from the EncryptedData tag
        cookie = doc.getElementsByTagName("EncryptedData")[0].firstChild.nodeValue

        # getting the update id,revision number and package name from the fe3 delivery api by providing the encrpyted cookie, cat_id, realse type
        # Map {"retail": "Retail", "release preview": "RP","insider slow": "WIS", "insider fast": "WIF"}
        with open(rf"{parent_dir}\data\xml\WUIDRequest.xml", "r") as f:
            cat_id_content = f.read().format(cookie, cat_id, release_type)
        check(Event)
        out = await (
            await session.post(
                "https://fe3cr.delivery.mp.microsoft.com/ClientWebService/client.asmx",
                data=cat_id_content,
                headers={"Content-Type": "application/soap+xml; charset=utf-8"},
            )
        ).text()

        doc = minidom.parseString(html.unescape(out))
        total_prog += 20
        progress_current.emit(total_prog)
        filenames = {}  # {ID: filename}
        # extracting all the filenames(package name) from the xml (the file names are found inside the blockmap)
        for node in doc.getElementsByTagName("Files"):
            # using try statement to avoid errors caused when attributes are not found
            try:
                filenames[
                    node.parentNode.parentNode.getElementsByTagName("ID")[
                        0
                    ].firstChild.nodeValue
                ] = (
                    f"{node.firstChild.attributes['InstallerSpecificIdentifier'].value}_{node.firstChild.attributes['FileName'].value}",
                    node.firstChild.attributes["Modified"].value,
                )
            except KeyError:
                continue
        # if the server returned no files notify the user that the app was not found
        if not filenames:
            raise Exception("server returned a empty list")

        # extracting the update id,revision number from the xml
        identities = {}  # {filename: (update_id, revision_number)}
        name_modified = {}  # {filename: (update_id, revision_number, modified)}
        for node in doc.getElementsByTagName("SecuredFragment"):
            # using try statement to avoid errors caused when attributes are not found
            try:
                file_name, modifed = filenames[
                    node.parentNode.parentNode.parentNode.getElementsByTagName("ID")[
                        0
                    ].firstChild.nodeValue
                ]

                update_identity = node.parentNode.parentNode.firstChild
                name_modified[file_name] = modifed
                identities[file_name] = (
                    update_identity.attributes["UpdateID"].value,
                    update_identity.attributes["RevisionNumber"].value,
                )
            except KeyError:
                continue
        check(Event)
        # parsing the filenames according to latest version,favorable types,system arch
        parse_names, main_file_name = parse_dict(name_modified, main_file_name)
        final_dict = {}  # {filename: (update_id, revision_number)}
        for value in parse_names:
            final_dict[value] = identities[value]

        # getting the download url for the files using the api
        with open(rf"{parent_dir}\data\xml\FE3FileUrl.xml", "r") as f:
            file_content = f.read()

        file_dict = {}  # the final result
        total_prog += 10
        progress_current.emit(total_prog)
        part = int(30 / len(final_dict))

        async def geturl(updateid, revisionnumber, file_name, total_prog):
            out = await (
                await session.post(
                    "https://fe3cr.delivery.mp.microsoft.com/ClientWebService/client.asmx/secured",
                    data=file_content.format(updateid, revisionnumber, release_type),
                    headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                )
            ).text()
            doc = minidom.parseString(out)
            # checks for all the tags which have name "filelocation" and extracts the url from it
            for i in doc.getElementsByTagName("FileLocation"):
                url = i.getElementsByTagName("Url")[0].firstChild.nodeValue
                # here there are 2 filelocation tags one for the blockmap and one for the actual file so we are checking for the length of the url
                if len(url) != 99:
                    file_dict[file_name] = url
                    total_prog += part
                    progress_current.emit(total_prog)

        # creating a list of tasks to be executed
        tasks = []
        for key, value in final_dict.items():
            check(Event)
            file_name = key
            updateid, revisionnumber = value
            tasks.append(
                asyncio.create_task(
                    geturl(updateid, revisionnumber, file_name, total_prog)
                )
            )

        await asyncio.gather(*tasks)

        # # waiting for all threads to complete
        if len(file_dict) != len(final_dict):
            raise Exception("server returned a incomplete list")

        if emit is True:
            progress_current.emit(100)
            time.sleep(0.2)
            progress_main.emit(20)
        # uwp = True
        return file_dict, parse_names, main_file_name, True

    async def non_uwp_gen(session):
        nonlocal total_prog
        api = f"https://storeedgefd.dsx.mp.microsoft.com/v9.0/packageManifests//{product_id}?market=US&locale=en-us&deviceFamily=Windows.Desktop"
        check(Event)

        data = await (await session.get(api)).text()
        datas = json.loads(data)

        if not datas.get("Data", None):
            raise Exception("server returned a empty list")

        total_prog += 20
        progress_current.emit(total_prog)

        file_name = datas["Data"]["Versions"][0]["DefaultLocale"]["PackageName"]

        installer_list = datas["Data"]["Versions"][0]["Installers"]
        download_data = set()
        for d in installer_list:
            download_data.add(
                (
                    d["Architecture"],
                    d["InstallerLocale"],
                    d["InstallerType"],
                    d["InstallerUrl"],
                )
            )

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
                if (
                    arch not in ("neutral", curr_arch)
                    and data[0] != arch
                    and data[0] in ("neutral", curr_arch)
                ):
                    arch = data[0]
                    locale = data[1]
                    installer_type = data[2]
                    url = data[3]
                else:
                    if (
                        data[0] == arch
                        and data[1] != locale
                        and ("us" in data[1] or "en" in data[1])
                    ):
                        locale = data[1]
                        installer_type = data[2]
                        url = data[3]
                        break

        main_file_name = clean_name(file_name) + "." + installer_type
        file_dict[main_file_name] = url

        # uwp = False
        return file_dict, [main_file_name], main_file_name, False

    total_prog = 0
    progress_current.emit(total_prog)
    # geting product id from url
    try:
        pattern = re.compile(r".+\/([^\/\?]+)(?:\?|$)")
        matches = pattern.search(str(url))
        product_id = matches.group(1)
    except AttributeError:
        raise Exception("No Data Found: --> [You Selected Wrong Page, Try Again!]")

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=60), raise_for_status=True
    ) as session:
        # getting cat_id and package name from the api
        details_api = f"https://storeedgefd.dsx.mp.microsoft.com/v9.0/products/{product_id}?market=US&locale=en-us&deviceFamily=Windows.Desktop"
        data = await (await session.get(details_api)).text()
        response = json.loads(
            data,
            object_hook=lambda obj: {
                k: json.loads(v) if k == "FulfillmentData" else v
                for k, v in obj.items()
            },
        )

        if not response.get("Payload", None):
            raise Exception("No Data Found: --> [You Selected Wrong Page, Try Again!]")

        response_data = response["Payload"]["Skus"][0]
        data_list = response_data.get("FulfillmentData", None)
        total_prog += 20
        progress_current.emit(total_prog)

        # check and see if the app is ump or not, return --> func_output,(ump or not)
        if data_list:
            return await uwp_gen(session)
        else:
            return await non_uwp_gen(session)
