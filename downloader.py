import os
import platform
import re
import time
import warnings
from urllib import request

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# ignoring unwanted warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Taking input from user
search_string = "9N0DX20HK701"  # input

# adding option to hide browser window
options = Options()
options.add_argument("--headless")
options.add_argument("--hide-scrollbars")
options.add_argument("--disable-gpu")
options.add_argument("--log-level=3")  # fatal
# path of driver
driver = webdriver.Chrome("chromedriver", options=options)
driver.get("https://store.rg-adguard.net/")

# inputing data

# selecting type from the options [url,productId etc] here we choose productid
select = Select(driver.find_element(by=By.XPATH, value=r"/html/body/div[1]/select[1]"))
select.select_by_value("ProductId")

# selecting the box field and passing data to it
box_field = driver.find_element(by=By.XPATH, value=r"/html/body/div[1]/input[1]")
box_field.send_keys(search_string)

# click on the submit button
submit_button = driver.find_element(
    By.CSS_SELECTOR, r"body > div.center > input[type=button]:nth-child(8)"
)
time.sleep(4)
submit_button.click()
time.sleep(6)

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

# get contents from site end ---------------------

# full parsing
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


del dict_data[clean_dict(dict_data)]

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

# downloader
dwnpath = "./Downloads"
if not os.path.exists(dwnpath):
    os.makedirs(dwnpath)

for i in final_data:
    # Define the remote file to retrieve
    remote_url = main_dict[i]
    # Define the filename to save data
    local_file = i
    # Download remote and save locally
    request.urlretrieve(remote_url, f"{dwnpath}/{local_file}")

# downloader end ------------------------------
