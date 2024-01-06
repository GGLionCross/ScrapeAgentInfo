from python_utils import cprint, pause, print_trace
from classes.Exceptions import RestartScrape
from classes.scraper_classes import BhhsScraper
from classes.scraper_classes import ColdwellScraper
from classes.scraper_classes import CompassScraper
from classes.scraper_classes import KellerWilliamsScraper
from classes.scraper_classes import RealtorComScraper
import config as cfg
from cookies import realtor_com_cookies


def get_scraper(source):
    if source == "bhhs":
        return BhhsScraper(
            chrome_options=cfg.chrome_options,
            bmp_options=cfg.bmp_options,
            locations=cfg.locations[source],
            timeout_default=cfg.timeouts["default"],
        )
    elif source == "coldwell":
        return ColdwellScraper(
            chrome_options=cfg.chrome_options,
            bmp_options=cfg.bmp_options,
            locations=cfg.locations[source],
            timeout_default=cfg.timeouts["default"],
        )
    elif source == "compass":
        return CompassScraper(
            chrome_options=cfg.chrome_options,
            locations=cfg.locations[source],
            timeout_default=cfg.timeouts["default"],
        )
    elif source == "kw":
        return KellerWilliamsScraper(
            chrome_options=cfg.chrome_options,
            bmp_options=cfg.bmp_options,
            locations=cfg.locations[source],
            timeout_default=cfg.timeouts["default"],
        )
    elif source == "realtor.com":
        return RealtorComScraper(
            chrome_options=cfg.chrome_options,
            cookies=realtor_com_cookies,
            bmp_options=cfg.bmp_options,
            locations=cfg.locations[source],
            timeout_default=cfg.timeouts["default"],
        )


def main():
    cprint("<g>Scraping agent info...")
    done = False
    while not done:
        try:
            scraper = get_scraper(cfg.source)
            scraper.scrape()
            pause()  # Temporary for testing
            done = True
        except RestartScrape:
            scraper.close()
        except Exception as e:
            print_trace()
            pause()
            break  # Temporary for testing
    scraper.close()
    cprint("Finished <g>scrape-agent-info.py<w>.")


if __name__ == "__main__":
    main()
