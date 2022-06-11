import webbrowser
import os
import subprocess
import re
import platform
from datetime import datetime
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import warnings
import time
import chromedriver_autoinstaller


current_time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
def open_browser(arg):
    webbrowser.open(arg)
    
def open_Logs():
    path = 'log.txt'
    if os.path.exists(path):
        os.startfile(path)
    else:
        self.show_error_popup()

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

def selenium_func(data_args):
    
    def get_time():
        if not os.path.exists('./config.txt'):
            with open('./config.txt', 'w') as f:
                f.write('wait_time:5')

        with open('./config.txt', 'r') as f:
            file_n = f.read()
            pattern = re.compile(r"([a-z_]+):(\d)")
            return int(pattern.search(str(file_n)).group(2))
        
    def product_id_getter(wrd):
        try:
            pattern = re.compile(r".+\/([a-zA-Z-]+)\/([a-zA-Z0-9]+)|.+")
            matches = pattern.search(str(wrd))
            return matches.group(2)
        except AttributeError:
            raise Exception(
                'No Data Found: --> [You Selected Wrong Page in App Selector, Try Again!]')
            
    wait_time = get_time()
    product_id = product_id_getter(str(data_args))

    # ignoring unwanted warning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # adding option to hide browser window
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")  # fatal
    chrome_service = ChromeService(chromedriver_autoinstaller.install(cwd=True))
    chrome_service.creationflags = subprocess.CREATE_NO_WINDOW

    # path of driver
    driver = Chrome(options=options, service=chrome_service)
    driver.get("https://store.rg-adguard.net/")

    # inputing data
    # selecting type from the options [url,productId etc] here we choose productid
    select = Select(driver.find_element(
        by=By.XPATH, value=r"/html/body/div[1]/select[1]"))
    select.select_by_value("ProductId")
    # selecting the box field and passing data to it
    box_field = driver.find_element(
        by=By.XPATH, value=r"/html/body/div[1]/input[1]")
    box_field.send_keys(product_id)

    # click on the submit button
    submit_button = driver.find_element(
        By.CSS_SELECTOR, r"body > div.center > input[type=button]:nth-child(8)"
    )
    time.sleep(wait_time-1)
    submit_button.click()
    time.sleep(wait_time+1)
    # inputing data end --------------------------

    # get contents from site
    main_dict = {}
    file = driver.find_element(
        by=By.XPATH, value="/html/body/div[1]/div/table/tbody"
    ).text.split("\n")

    # geting length of the table
    length = len(file)

    # getting size of files
    splited = [i.split(" ") for i in file]
    size = dict()
    for i in splited:
        size[i[0]] = (i[-2], i[-1])

    # looping to get all elements and adding them to a dict with {name:url}
    for i in range(length):
        file = driver.find_element_by_xpath(
            f"/html/body/div[1]/div/table/tbody/tr[{i+1}]/td[1]/a"
        )

        main_dict[file.text] = file.get_attribute("href")
    driver.quit()
    return main_dict
  
def parse_dict(args):
    
    main_dict = args
    data = list()
    bad_data = list()
    data_link = list()
    final_data = list()
    full_data = [i for i in main_dict.keys()]

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

    def is_os_64bit():
        if platform.machine().endswith("64"):
            return "x64"
        else:
            return "x86"

    # get appropriate keys

    for key, value in dict_data.items():
        if value[2] == is_os_64bit():
            final_data.append(key)
        elif value[2] == "neutral":
            final_data.append(key)

    # parsing end ----------------------------------
    return (main_dict, final_data)
