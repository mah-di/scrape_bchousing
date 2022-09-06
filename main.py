if __name__ == "__main__":
    import configparser
    import time
    from datetime import timedelta
    from get_licences import get_licences
    from bc_housing import bc_housing

    CONFIG_INI = configparser.ConfigParser()
    CONFIG_INI.read("config.ini")
    TOTAL_ENTRIES = int(CONFIG_INI['additional_info']['total_entries'])
    MAX_RETRIES = int(CONFIG_INI['scrape_settings']['max_retries'])
    LICENCE_FILE = CONFIG_INI['filenames']['licence_file']

    try:
        with open(LICENCE_FILE, 'r'):
            pass
    except FileNotFoundError:
        print('Collecting necessary information...', end='\n\n')
        get_licences()

    print('Starting Scraping...' , end='\n\n')
    retries = 0
    start = time.perf_counter()
    while True:
        start_of_session = time.perf_counter()
        try:
            bc_housing()
            retries = 0
            session_time = timedelta(seconds=(time.perf_counter() - start_of_session))
            print(f'Session successful! Session runtime: {session_time}', end='\n\n')
            
            CONFIG_INI.read("config.ini")
            START_OF_ENTRY = CONFIG_INI['scrape_settings']['start_of_entry']
            if START_OF_ENTRY == '0':
                end = time.perf_counter()
                print(f'Scraping Done! Total runtime: {timedelta(seconds=(end - start))}')
                break

            print(f'Scraping of {START_OF_ENTRY} data out of {TOTAL_ENTRIES} data done. 120 seconds till the next scraping session starts.', end='\n\n')
            time.sleep(60)
            print('60 seconds till the next session starts.', end='\n\n')
            time.sleep(30)
            print('30 seconds till the next session starts.', end='\n\n')
            time.sleep(20)
            print('10 seconds till the next session starts.', end='\n\n')
            time.sleep(10)
            print('Starting next session.', end='\n\n')
        
        except Exception as e:
            if retries == MAX_RETRIES:
                print(f'Maximum retry limit reached, exiting program.\nError: {e}')
                break
            print(f'An unexpected error occured while scraping. Retrying in 30 seconds. (Retries left: {MAX_RETRIES-retries})')
            time.sleep(30)
            retries += 1
            print('Retrying...', end='\n\n')