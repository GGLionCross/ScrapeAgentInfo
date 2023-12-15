class BadUrl(Exception):
    # Raise this when url gets redirected unexpectedly
    pass

class RestartScrape(Exception):
    # Raise this when you wish to restart the scraper
    pass