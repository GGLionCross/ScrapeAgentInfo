from python_utils import cprint, load_json
from classes.Exceptions import RestartScrape
from classes.scraper_classes import Bhhs
from classes.scraper_classes import Coldwell
from classes.scraper_classes import Compass
from classes.scraper_classes import KellerWilliams
from classes.scraper_classes import RealtorCom
import config as cfg

SOURCE = cfg.source
USER_DATA_PATH = cfg.chrome_options['user_data_path']
PROFILE_PATH = cfg.chrome_options['profile_path']
TIMEOUT_DEFAULT = cfg.timeouts['default']
LOCATIONS = cfg.locations

def get_scraper(source):
    if source == 'bhhs':
        return Bhhs(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=LOCATIONS[source],
            timeout_default=TIMEOUT_DEFAULT
        )
    elif source == 'coldwell':
        return Coldwell(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=LOCATIONS[source],
            timeout_default=TIMEOUT_DEFAULT
        )
    elif source == 'compass':
        return Compass(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=LOCATIONS[source],
            timeout_default=TIMEOUT_DEFAULT
        )
    elif source == 'kw':
        return KellerWilliams(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=LOCATIONS[source],
            timeout_default=TIMEOUT_DEFAULT
        )
    elif source == 'realtor':
        return RealtorCom(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=LOCATIONS[source],
            timeout_default=TIMEOUT_DEFAULT
        )

def main():
    cprint('Running <g>scrape-agent-info.py<w>...')
    done = False
    while not done:
        try:
            scraper = get_scraper(SOURCE)
            scraper.scrape()
            done = True
        except RestartScrape:
            scraper.close()
    scraper.close()
    cprint('Finished <g>scrape-agent-info.py<w>.')

if __name__ == '__main__':
    main()