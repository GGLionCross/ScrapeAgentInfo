from python_utils import cprint, load_json
from classes.Coldwell import Coldwell
from classes.Compass import Compass
from classes.KellerWilliams import KellerWilliams
from classes.Realtor import Realtor

CONFIG = load_json("config.json")
SOURCE = CONFIG["source"]
USER_DATA_PATH = CONFIG["chrome_options"]["user_data_path"]
PROFILE_PATH = CONFIG["chrome_options"]["profile_path"]
TIMEOUT_DEFAULT = CONFIG["timeouts"]["default"]
LOCATIONS = CONFIG["locations"]
COLDWELL_LOCATIONS = CONFIG["coldwell_locations"]
COMPASS_LOCATIONS = CONFIG["compass_locations"]
KW_LOCATIONS = CONFIG["kw_locations"]
REALTOR_LOCATIONS = CONFIG["realtor_locations"]
OUTPUT_CSV = CONFIG["output_csv"]

def get_scraper(source):
    if source == "coldwell":
        return Coldwell(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=COLDWELL_LOCATIONS,
            output_csv=OUTPUT_CSV,
            timeout_default=TIMEOUT_DEFAULT
        )
    elif source == "compass":
        return Compass(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=COMPASS_LOCATIONS,
            output_csv=OUTPUT_CSV,
            timeout_default=TIMEOUT_DEFAULT
        )
    elif source == "kw":
        return KellerWilliams(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=KW_LOCATIONS,
            output_csv=OUTPUT_CSV,
            timeout_default=TIMEOUT_DEFAULT
        )
    elif source == "realtor":
        return Realtor(
            user_data_path=USER_DATA_PATH,
            profile_path=PROFILE_PATH,
            locations=REALTOR_LOCATIONS,
            output_csv=OUTPUT_CSV,
            timeout_default=TIMEOUT_DEFAULT
        )

def main():
    scraper = get_scraper(SOURCE)
    scraper.scrape()

if __name__ == "__main__":
    main()