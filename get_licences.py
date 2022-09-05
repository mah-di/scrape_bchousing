from requests_html import HTMLSession
import configparser
import pandas as pd

# Reading the config.ini file
CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read('config.ini')
ROOT_URL = CONFIG_INI['urls']['root_url']
TOTAL_ENTRIES = int(CONFIG_INI['additional_info']['total_entries'])
LICENCES_SELECTOR = CONFIG_INI['selectors']['licences_selector']
LICENCE_FILE = CONFIG_INI['filenames']['licence_file']

def get_licence_list():
    session = HTMLSession()
    response = session.get(ROOT_URL)
    scripts = """
        btn = document.querySelector('#ctl00_content_cmdSearch')
        btn.click()
    """
    response.html.render(script=scripts, sleep=10)
    options = response.html.find(LICENCES_SELECTOR)
    licence_list = []
    for option in options:
        licence_list.append(option.attrs['value'])

    if len(licence_list) != TOTAL_ENTRIES:
        licence_list = get_licence_list()
    
    return licence_list

def write_to_csv(licence_list):
    dict = {'licences': licence_list}
    df = pd.DataFrame(dict)
    df.to_csv(LICENCE_FILE)    
    return

def get_licences():
    licence_list = get_licence_list()
    write_to_csv(licence_list)
    return

if __name__ == '__main__':
    get_licences()