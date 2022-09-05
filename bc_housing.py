from requests_html import AsyncHTMLSession
import configparser
import asyncio
import pandas as pd

# reading the config.ini file
CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read('config.ini')
ROOT_URL = CONFIG_INI['urls']['root_url']
TOTAL_ENTRIES = int(CONFIG_INI['additional_info']['total_entries'])
ENTRIES_PER_SESSION = int(CONFIG_INI['scrape_settings']['entries_per_session'])
FORM_KEYS = list(dict(CONFIG_INI['form_keys']).values())
FORM_VALUES = list(dict(CONFIG_INI['form_values']).values())
LICENCE_FILE = CONFIG_INI['filenames']['licence_file']
OUTPUT_FILE = CONFIG_INI['filenames']['output_file']
CONTAINER_SELECTOR = CONFIG_INI['selectors']['container_selector']
I_NAME_SELECTOR = CONFIG_INI['selectors']['i_name_selector']
H3_NAME_SELECTOR = CONFIG_INI['selectors']['h3_name_selector']
CONTACT_BOX_SELECTOR = CONFIG_INI['selectors']['contact_box_selector']
PHONES_SELECTOR = CONFIG_INI['selectors']['phones_selector']

def extract_data(html):
    data = {
        'cp_name': '',
        'inc': '',
        'lc': '',
        'lc_typ': '',
        'sts': '',
        'ownr': '',
        'addrs': '',
        'phn_num_1': '',
        'phn_num_2': '',
        'phn_num_3': '',
    }
    container = html.find(CONTAINER_SELECTOR, first=True)
    
    data['cp_name'] = container.find(I_NAME_SELECTOR, first=True).text.strip() if html.find(I_NAME_SELECTOR, first=True) else html.find(H3_NAME_SELECTOR, first=True).text.strip()
    
    infos = container.text.split('\n')
    for info in infos:
        if info.startswith('Incorporation #') or info.startswith(f'{data["cp_name"]} Incorporation #'):
            data['inc'] = info.split(':')[1].strip()
        if info.startswith('Licence #'):
            data['lc'] = info.split(':')[1].strip()
        elif info.startswith('Licence Type'):
            data['lc_typ'] = info.split(':')[1].strip()
        elif info.startswith('Status'):
            data['sts'] = info.replace('Status:', '').strip()
        elif info.startswith('Person responsible for the company'):
            data['ownr'] = info.split(':')[1].strip()

    cntc_box = container.find(CONTACT_BOX_SELECTOR, first=True)
    data['addrs'] = cntc_box.text.split(':')[1].split('(')[0].strip().replace('\n', ', ')

    phn_nums = container.find(PHONES_SELECTOR)
    count = 1
    while count <= len(phn_nums) and count <= 3:
        data[f'phn_num_{count}'] = phn_nums[count-1].text[:14]
        count += 1

    return data

async def get_data(licence):
    session = AsyncHTMLSession()
    primary_response = await session.get(ROOT_URL)
    await asyncio.sleep(10)
    
    form = dict(zip(FORM_KEYS, FORM_VALUES))
    form['__VIEWSTATE'] = primary_response.html.find('#__VIEWSTATE', first=True).attrs['value']
    form['__VIEWSTATEGENERATOR'] = primary_response.html.find('#__VIEWSTATEGENERATOR', first=True).attrs['value']
    form['ctl00$content$txtLicenceNumber'] = str(licence)

    response = await session.post(ROOT_URL, data=form)
    await session.close()

    return extract_data(response.html)

def get_licences():
    df = pd.read_csv(LICENCE_FILE)
    licences = df['licences'].values.tolist()
    return licences[START_OF_ENTRY:(START_OF_ENTRY+ENTRIES_PER_SESSION)] if (START_OF_ENTRY+ENTRIES_PER_SESSION) <= TOTAL_ENTRIES else licences[START_OF_ENTRY:TOTAL_ENTRIES]

async def get_all_data():
    licences = get_licences()

    tasks = [get_data(licence) for licence in licences]
    return await asyncio.gather(*tasks)

def catagorize(dataset):
    cp_names = []
    inc = []
    lc = []
    lc_typ = []
    sts = []
    ownr = []
    addrs = []
    phn_num_1 = []
    phn_num_2 = []
    phn_num_3 = []
    for data in dataset:
        cp_names.append(data['cp_name'])
        inc.append(data['inc'])
        lc.append(data['lc'])
        lc_typ.append(data['lc_typ'])
        sts.append(data['sts'])
        ownr.append(data['ownr'])
        addrs.append(data['addrs'])
        phn_num_1.append(data['phn_num_1'])
        phn_num_2.append(data['phn_num_2'])
        phn_num_3.append(data['phn_num_3'])
    
    return cp_names, inc, lc, lc_typ, sts, ownr, addrs, phn_num_1, phn_num_2, phn_num_3

def save_to_file(dataset):
    cp_names, inc, lc, lc_typ, sts, ownr, addrs, phn_num_1, phn_num_2, phn_num_3 = catagorize(dataset)
    df = pd.DataFrame({
        'Company Name': cp_names,
        'Incorporation#': inc,
        'License#': lc,
        'License Type' : lc_typ,
        'Status': sts,
        'Persons responsible for the company': ownr,
        'Address': addrs,
        'Phone Number 1': phn_num_1,
        'Phone Number 2': phn_num_2,
        'Phone Number 3': phn_num_3
    })

    try:
        with open(OUTPUT_FILE, 'r'):
            pass
        with open(OUTPUT_FILE, 'a', newline='') as f:
            df.to_csv(f, index=False, header=False)
    except Exception as e:
        with open(OUTPUT_FILE, 'w', newline='') as f:
            df.to_csv(f, index=False)

    return

def bc_housing():
    global START_OF_ENTRY

    CONFIG_INI = configparser.ConfigParser()
    CONFIG_INI.read('config.ini')
    START_OF_ENTRY = int(CONFIG_INI['scrape_settings']['start_of_entry'])

    result = asyncio.run(get_all_data())
    save_to_file(result)
    
    if (START_OF_ENTRY + ENTRIES_PER_SESSION) < TOTAL_ENTRIES:
        CONFIG_INI['scrape_settings']['start_of_entry'] = str(START_OF_ENTRY + ENTRIES_PER_SESSION)
    else:
        CONFIG_INI['scrape_settings']['start_of_entry'] = '0'
    
    with open('config.ini', 'w') as cf:
        CONFIG_INI.write(cf)



if __name__ == '__main__':
    bc_housing()