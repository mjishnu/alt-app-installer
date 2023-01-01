import requests
from xml.dom import minidom
import html
from threading import Thread
import warnings
import re


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

    #getting cat id and other details
    details_api = "https://displaycatalog.mp.microsoft.com/v7.0/products/"

    data = {"bigIds": product_id, "market": "US", "languages": "en"}

    session = requests.Session()
    r = session.get(details_api, params=data)
    data_list = r.text

    pattern1 = re.compile('"WuCategoryId":"([^}]*)","PackageFamilyName"')
    pattern2 = re.compile('"PackageFamilyName":"([^}]*)","SkuId')
    match1 = pattern1.search(str(data_list))
    match2 = pattern2.search(str(data_list))

    cat_id = match1.group(1) #wucategoryid
    file_name = match2.group(1).split('_')[0]

    #trying to get download links
    release_type = "Retail"
    with open("./data/xml/GetCookie.xml", "r") as f:
        cookie_content = f.read()

    out = session.post(
        'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
        data=cookie_content,
        headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
        verify=False
    )
    doc1 = minidom.parseString(out.text)
    cookie = doc1.getElementsByTagName('EncryptedData')[0].firstChild.nodeValue

    with open("./data/xml/WUIDRequest.xml", "r") as f:
        cat_id_content = f.read().format(cookie, cat_id, release_type)
        

    out = session.post(
        'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
        data=cat_id_content,
        headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
        verify=False
    )
    
    doc1 = minidom.parseString(html.unescape(out.text))
    filenames = {}
    for node in doc1.getElementsByTagName('Files'):
        filenames[node.parentNode.parentNode.getElementsByTagName(
            'ID')[0].firstChild.nodeValue] = f"{node.firstChild.attributes['InstallerSpecificIdentifier'].value}_{node.firstChild.attributes['FileName'].value}"
        pass

    identities = []
    for node in doc1.getElementsByTagName('SecuredFragment'):
        filename = filenames[node.parentNode.parentNode.parentNode.getElementsByTagName('ID')[
            0].firstChild.nodeValue]
        update_identity = node.parentNode.parentNode.firstChild
        identities += [(update_identity.attributes['UpdateID'].value,
                        update_identity.attributes['RevisionNumber'].value, filename)]

    with open("./data/xml/FE3FileUrl.xml", "r") as f:
        file_content = f.read()


    def geturl(i, v, f):
        out = session.post(
            'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx/secured',
            data=file_content.format(i, v, release_type),
            headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
            verify=False
        )
        doc2 = minidom.parseString(out.text)
        for i in doc2.getElementsByTagName("FileLocation"):
            url = i.getElementsByTagName("Url")[0].firstChild.nodeValue
            file_dict[f] = url

    threads = []
    file_dict = {}
    for i, v, f in identities:
        th = Thread(target=geturl, args=(i, v, f))
        th.daemon = True
        threads.append(th)
        th.start()

    for th in threads:
        th.join()

    
    return file_dict,file_name