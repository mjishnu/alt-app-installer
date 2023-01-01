import requests
from xml.dom import minidom
import html
from threading import Thread
import warnings
import re
from utls import parse_dict

warnings.filterwarnings("ignore")

def url_generator(url):
    # geting product id from url
    try:
        pattern = re.compile(
            r".+\/((?:[a-zA-Z]+[0-9]|[0-9]+[a-zA-Z])[a-zA-Z0-9]*)|.+")
        matches = pattern.search(str(url))
        product_id = matches.group(1)

        if product_id is None:
            raise Exception(
                'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')

    except AttributeError:
        raise Exception(
            'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')

    #getting cat_id and package name from the api
    details_api = "https://displaycatalog.mp.microsoft.com/v7.0/products/"

    data = {"bigIds": product_id, "market": "US", "languages": "en"}

    session = requests.Session()
    r = session.get(details_api, params=data)
    data_list = r.text

    pattern1 = re.compile('"WuCategoryId":"([^}]*)","PackageFamilyName"')
    pattern2 = re.compile('"PackageFamilyName":"([^}]*)","SkuId')
    match1 = pattern1.search(str(data_list))
    match2 = pattern2.search(str(data_list))

    cat_id = match1.group(1) 
    main_file_name = match2.group(1).split('_')[0]
    release_type = "Retail"

    #getting the encrypted cookie for the fe3 delivery api
    with open("./data/xml/GetCookie.xml", "r") as f:
        cookie_content = f.read()

    out = session.post(
        'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
        data=cookie_content,
        headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
        verify=False
    )
    doc = minidom.parseString(out.text)

    #extracting the cooking from the EncryptedData tag
    cookie = doc.getElementsByTagName('EncryptedData')[0].firstChild.nodeValue

    #getting the update id,revision number and package name from the fe3 delivery api by providing the encrpyted cookie, cat_id, realse type
    # Map {"retail": "Retail", "release preview": "RP","insider slow": "WIS", "insider fast": "WIF"}
    with open("./data/xml/WUIDRequest.xml", "r") as f:
        cat_id_content = f.read().format(cookie, cat_id, release_type)

    out = session.post(
        'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
        data=cat_id_content,
        headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
        verify=False
    )
    
    doc = minidom.parseString(html.unescape(out.text))
    filenames = {} #{ID: filename}
    #extracting all the filenames(package name) from the xml (the file names are found inside the blockmap)
    for node in doc.getElementsByTagName('Files'):
        filenames[node.parentNode.parentNode.getElementsByTagName(
            'ID')[0].firstChild.nodeValue] = f"{node.firstChild.attributes['InstallerSpecificIdentifier'].value}_{node.firstChild.attributes['FileName'].value}"
        pass
    
    #extracting the update id,revision number from the xml
    identities = {} #{filename: (update_id, revision_number)}
    for node in doc.getElementsByTagName('SecuredFragment'):
        file_name = filenames[node.parentNode.parentNode.parentNode.getElementsByTagName('ID')[
            0].firstChild.nodeValue]

        update_identity = node.parentNode.parentNode.firstChild
        identities[file_name] = (update_identity.attributes['UpdateID'].value,
                                update_identity.attributes['RevisionNumber'].value)
                                
    #parsing the filenames according to latest version,favorable types,system arch
    parse_names = parse_dict(identities,main_file_name)
    final_dict = {} #{filename: (update_id, revision_number)}
    for value in parse_names:
        final_dict[value] = identities[value]

    #getting the download url for the files using the api
    with open("./data/xml/FE3FileUrl.xml", "r") as f:
        file_content = f.read()
    
    file_dict = {} #the final result
    def geturl(updateid, revisionnumber, file_name):
        out = session.post(
            'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx/secured',
            data=file_content.format(updateid, revisionnumber, release_type),
            headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
            verify=False
        )
        doc = minidom.parseString(out.text)
        #checks for all the tags which have name "filelocation" and extracts the url from it
        for i in doc.getElementsByTagName("FileLocation"):
            url = i.getElementsByTagName("Url")[0].firstChild.nodeValue
            #here there are 2 filelocation tags one for the blockmap and one for the actual file so we are checking for the length of the url
            if (len(url) != 99):
                file_dict[file_name] = url

    #using threading to concurrently get the download url for all the files 
    threads = []
    for key,value in final_dict.items():
        file_name = key
        updateid,revisionnumber = value
        th = Thread(target=geturl, args=(updateid, revisionnumber, file_name))
        th.daemon = True
        threads.append(th)
        th.start()

    #waiting for all threads to complete
    for th in threads:
        th.join()

    
    return file_dict,parse_names,main_file_name

def get_data(arg):

    main_dict,name_list,file_name = url_generator(arg)
    if len(main_dict) == 0:
        #can implement backup apis here
        pass

    return main_dict,name_list,file_name